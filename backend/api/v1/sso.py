"""Authenticated SSO management endpoints — configure OIDC per company (admin only, Growth plan)."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.sso_config import SSOConfig
from models.user import User
from schemas.sso import SSOConfigCreate, SSOConfigOut, SSOConfigUpdate
from services.sso_service import (
    encrypt_secret,
    fetch_oidc_discovery,
)
from services.audit_service import log_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sso", tags=["sso"])


async def _require_growth(current_user: User, db: AsyncSession) -> None:
    from sqlalchemy import select as sa_select
    from models.company import Company
    result = await db.execute(sa_select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company or company.plan not in ("growth", "partner"):
        raise HTTPException(status_code=402, detail="SSO is available on the Growth plan.")


@router.get("/config", response_model=SSOConfigOut | None)
async def get_sso_config(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the company's current SSO configuration."""
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == current_user.company_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        return None
    return config


@router.post("/config", response_model=SSOConfigOut)
async def upsert_sso_config(
    body: SSOConfigCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create or replace the company's SSO configuration. Validates OIDC discovery on save."""
    await _require_growth(current_user, db)

    # Validate issuer by fetching discovery document
    try:
        await fetch_oidc_discovery(body.issuer)
    except Exception:
        raise HTTPException(
            status_code=422,
            detail=f"Could not reach OIDC discovery URL for issuer '{body.issuer}'. "
                   "Check that the issuer URL is correct and publicly accessible.",
        )

    # Check domain uniqueness across other companies
    domain_result = await db.execute(
        select(SSOConfig).where(
            SSOConfig.domain == body.domain,
            SSOConfig.company_id != current_user.company_id,
        )
    )
    if domain_result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This domain is already configured for another account.")

    existing_result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == current_user.company_id)
    )
    config = existing_result.scalar_one_or_none()

    encrypted_secret = encrypt_secret(body.client_secret)

    if config:
        config.domain = body.domain
        config.issuer = body.issuer
        config.client_id = body.client_id
        config.client_secret_enc = encrypted_secret
        config.scopes = body.scopes
        config.enabled = True
    else:
        config = SSOConfig(
            company_id=current_user.company_id,
            domain=body.domain,
            issuer=body.issuer,
            client_id=body.client_id,
            client_secret_enc=encrypted_secret,
            scopes=body.scopes,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    await log_action(db, current_user.company_id, "sso.configured", user_id=current_user.id, user_email=current_user.email)
    logger.info("SSO configured: company=%s domain=%s issuer=%s", current_user.company_id, body.domain, body.issuer)
    return config


@router.patch("/config", response_model=SSOConfigOut)
async def update_sso_config(
    body: SSOConfigUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Partially update SSO configuration (e.g. toggle enabled)."""
    await _require_growth(current_user, db)

    result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == current_user.company_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No SSO configuration found.")

    if body.domain is not None:
        config.domain = body.domain.lower().strip().lstrip("@")
    if body.issuer is not None:
        config.issuer = body.issuer.rstrip("/")
    if body.client_id is not None:
        config.client_id = body.client_id
    if body.client_secret is not None:
        config.client_secret_enc = encrypt_secret(body.client_secret)
    if body.scopes is not None:
        config.scopes = body.scopes
    if body.enabled is not None:
        config.enabled = body.enabled

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/config", status_code=204)
async def delete_sso_config(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove SSO configuration entirely."""
    result = await db.execute(
        select(SSOConfig).where(SSOConfig.company_id == current_user.company_id)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No SSO configuration found.")

    await db.delete(config)
    await db.commit()
    await log_action(db, current_user.company_id, "sso.removed", user_id=current_user.id, user_email=current_user.email)
