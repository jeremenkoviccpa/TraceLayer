"""Public SSO endpoints — domain check, OIDC login initiation, OIDC callback."""
import logging
import secrets
import urllib.parse
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import create_access_token, create_refresh_token, hash_password
from models.company import Company
from models.refresh_token import RefreshToken
from models.sso_config import SSOConfig, SSOState
from models.user import User
from schemas.sso import SSOCheckOut
from services.audit_service import log_action
from services.email_service import send_welcome_email
from services.sso_service import (
    build_authorization_url,
    decrypt_secret,
    exchange_code_for_tokens,
    fetch_jwks,
    fetch_oidc_discovery,
    sso_callback_uri,
    validate_id_token,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_SSO_STATE_TTL_MINUTES = 10


@router.get("/sso/check", response_model=SSOCheckOut)
async def sso_check(domain: str, db: AsyncSession = Depends(get_db)):
    """Check if a domain has SSO configured. Called from the login page on email blur."""
    domain = domain.lower().strip()
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.domain == domain, SSOConfig.enabled.is_(True))
    )
    config = result.scalar_one_or_none()
    if not config:
        return SSOCheckOut(sso_enabled=False)
    return SSOCheckOut(sso_enabled=True, company_id=config.company_id)


@router.get("/sso/{company_id}/login")
async def sso_login(company_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Initiate OIDC flow — redirect user to the identity provider."""
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == company_id, SSOConfig.enabled.is_(True))
    )
    config = result.scalar_one_or_none()
    if not config:
        return RedirectResponse(f"{settings.app_frontend_url}/login?error=sso_not_configured")

    try:
        discovery = await fetch_oidc_discovery(config.issuer)
    except Exception:
        logger.exception("SSO: OIDC discovery failed for issuer=%s", config.issuer)
        return RedirectResponse(f"{settings.app_frontend_url}/login?error=sso_discovery_failed")

    # Store state in DB to prevent CSRF
    state_id = uuid.uuid4()
    db.add(SSOState(
        id=state_id,
        company_id=company_id,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=_SSO_STATE_TTL_MINUTES),
    ))
    await db.commit()

    auth_url = build_authorization_url(
        authorization_endpoint=discovery["authorization_endpoint"],
        client_id=config.client_id,
        redirect_uri=sso_callback_uri(settings.backend_url, company_id),
        state=str(state_id),
        scopes=config.scopes,
    )
    return RedirectResponse(auth_url)


@router.get("/sso/{company_id}/callback")
async def sso_callback(
    company_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    code: str = "",
    state: str = "",
    error: str = "",
    db: AsyncSession = Depends(get_db),
):
    """OIDC callback — exchange code, validate ID token, issue TraceLayer JWT."""
    frontend_error_url = f"{settings.app_frontend_url}/login?error="

    if error:
        logger.warning("SSO callback received error from IdP: %s", error)
        return RedirectResponse(f"{frontend_error_url}sso_idp_error")

    if not code or not state:
        return RedirectResponse(f"{frontend_error_url}sso_missing_params")

    # Validate state token
    try:
        state_uuid = uuid.UUID(state)
    except ValueError:
        return RedirectResponse(f"{frontend_error_url}sso_invalid_state")

    state_result = await db.execute(
        select(SSOState).where(
            SSOState.id == state_uuid,
            SSOState.company_id == company_id,
            SSOState.used.is_(False),
            SSOState.expires_at > datetime.now(timezone.utc),
        )
    )
    state_row = state_result.scalar_one_or_none()
    if not state_row:
        return RedirectResponse(f"{frontend_error_url}sso_invalid_state")

    # Mark state used immediately to prevent replay
    state_row.used = True
    await db.flush()

    # Load SSO config
    config_result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == company_id, SSOConfig.enabled.is_(True))
    )
    config = config_result.scalar_one_or_none()
    if not config:
        return RedirectResponse(f"{frontend_error_url}sso_not_configured")

    try:
        discovery = await fetch_oidc_discovery(config.issuer)
        client_secret = decrypt_secret(config.client_secret_enc)

        token_data = await exchange_code_for_tokens(
            token_endpoint=discovery["token_endpoint"],
            code=code,
            client_id=config.client_id,
            client_secret=client_secret,
            redirect_uri=sso_callback_uri(settings.backend_url, company_id),
        )

        id_token = token_data.get("id_token")
        if not id_token:
            raise ValueError("No id_token in token response")

        jwks_keys = await fetch_jwks(discovery["jwks_uri"])
        claims = validate_id_token(id_token, jwks_keys, config.issuer, config.client_id)

    except Exception:
        logger.exception("SSO: token validation failed for company=%s", company_id)
        await db.commit()
        return RedirectResponse(f"{frontend_error_url}sso_token_failed")

    email: str = claims["email"]
    full_name: str = claims.get("name", "") or claims.get("given_name", "")

    # Find or create user — must belong to the SSO company
    user_result = await db.execute(select(User).where(User.email == email))
    user = user_result.scalar_one_or_none()
    is_new_user = user is None

    if user and str(user.company_id) != str(company_id):
        # Email registered under a different company — block
        logger.warning("SSO: email %s belongs to company %s, not %s", email, user.company_id, company_id)
        await db.commit()
        return RedirectResponse(f"{frontend_error_url}sso_email_conflict")

    if not user:
        # Auto-provision user into the SSO company
        company_result = await db.execute(select(Company).where(Company.id == company_id))
        company = company_result.scalar_one_or_none()
        if not company:
            await db.commit()
            return RedirectResponse(f"{frontend_error_url}sso_company_not_found")

        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(secrets.token_hex(32)),
            company_id=company_id,
            role="member",
            email_verified=True,
        )
        db.add(user)
        await db.flush()

        background_tasks.add_task(_send_welcome_bg, user.email, company.name)

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    ))
    await db.commit()

    await log_action(db, user.company_id, "user.sso_login", user_id=user.id, user_email=user.email)

    params: dict = {"access_token": access_token, "refresh_token": raw_refresh}
    if is_new_user:
        params["new_user"] = "1"
    return RedirectResponse(f"{settings.app_frontend_url}/auth/callback?{urllib.parse.urlencode(params)}")


def _send_welcome_bg(email: str, company_name: str) -> None:
    try:
        send_welcome_email(email, company_name)
    except Exception:
        logger.exception("SSO welcome email failed for %s", email)
