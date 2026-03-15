import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.security import create_access_token, create_refresh_token, hash_password
from models.company import Company
from models.refresh_token import RefreshToken
from models.user import User
from services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@router.get("/google")
async def google_login():
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": f"{settings.backend_url}/v1/auth/google/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}")


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
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
        company_name = (
            f"{full_name.split()[0]}'s workspace"
            if full_name
            else email.split("@")[0]
        )
        company = Company(name=company_name, onboarding_completed=False)
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

    params = {"access_token": access_token, "refresh_token": raw_refresh}
    if is_new_user:
        params["new_user"] = "1"
    qs = urllib.parse.urlencode(params)
    return RedirectResponse(f"{settings.app_frontend_url}/auth/callback?{qs}")
