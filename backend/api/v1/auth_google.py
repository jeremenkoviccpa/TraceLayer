import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx

logger = logging.getLogger(__name__)
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import create_access_token, create_refresh_token, hash_password
from services.email_service import send_partner_welcome_email, send_welcome_email
from models.company import Company
from models.refresh_token import RefreshToken
from models.user import User
from services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


def _send_welcome_bg(email_fn, to: str, company_name: str) -> None:
    """Background task wrapper — logs failures but never raises."""
    try:
        email_fn(to, company_name)
        logger.info("Welcome email sent to %s", to)
    except Exception:
        logger.exception("Welcome email failed for %s — check RESEND_API_KEY and domain verification in Resend dashboard", to)


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google")
async def google_login(account_type: str = "company"):
    # Encode account_type in state so the callback knows what kind of account to create
    state = account_type if account_type in ("company", "partner") else "company"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": state,
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str, background_tasks: BackgroundTasks, state: str = "company", db: AsyncSession = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        token_res = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": f"{settings.backend_url}/v1/auth/google/callback",
            "grant_type": "authorization_code",
        })
        if not token_res.is_success:
            logger.error(
                "Google token exchange failed: status=%s body=%s redirect_uri=%s frontend_url=%s",
                token_res.status_code,
                token_res.text,
                f"{settings.backend_url}/v1/auth/google/callback",
                settings.app_frontend_url,
            )
            return RedirectResponse(f"{settings.app_frontend_url}/login?error=google_failed")

        token_data = token_res.json()

        userinfo_res = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_res.json()

    email = userinfo.get("email")
    if not email:
        return RedirectResponse(f"{settings.app_frontend_url}/login?error=no_email")

    full_name = userinfo.get("name", "")

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    is_new_user = user is None

    if not user:
        is_partner = state == "partner"
        company_name = (
            f"{full_name.split()[0]}'s workspace"
            if full_name
            else email.split("@")[0]
        )
        company = Company(
            name=company_name,
            onboarding_completed=is_partner,  # partners skip onboarding
            is_partner_account=is_partner,
            plan="partner" if is_partner else "free",
        )
        db.add(company)
        await db.flush()

        user = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(secrets.token_hex(32)),
            company_id=company.id,
            role="admin",
            email_verified=True,
        )
        db.add(user)
        await db.flush()

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    ))
    await db.commit()

    await log_action(db, user.company_id, "user.login", user_id=user.id, user_email=user.email)

    # Fetch company to determine account type for redirect
    from sqlalchemy import select as sa_select
    from models.company import Company as CompanyModel
    company_result = await db.execute(sa_select(CompanyModel).where(CompanyModel.id == user.company_id))
    company_row = company_result.scalar_one_or_none()
    is_partner = company_row.is_partner_account if company_row else False

    if is_new_user and company_row:
        email_fn = send_partner_welcome_email if is_partner else send_welcome_email
        background_tasks.add_task(_send_welcome_bg, email_fn, user.email, company_row.name)

    params = {"access_token": access_token, "refresh_token": raw_refresh}
    if is_new_user:
        params["new_user"] = "1"
    if is_partner:
        params["is_partner"] = "1"
    qs = urllib.parse.urlencode(params)
    return RedirectResponse(f"{settings.app_frontend_url}/auth/callback?{qs}")
