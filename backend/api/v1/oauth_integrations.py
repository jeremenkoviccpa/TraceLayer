"""
OAuth 2.0 authorization for integrations that support it.

Supported providers: github, slack, linear, notion

Flow:
  1. GET /v1/integrations/oauth/{provider}/authorize  (auth required)
     → returns {url} to redirect the user's browser to
  2. User authorizes on the provider's site
  3. Provider redirects to GET /v1/integrations/oauth/{provider}/callback?code=xxx&state=yyy
  4. Backend exchanges code → access_token, stores integration, redirects to frontend
"""
import secrets
import time
import logging
import uuid
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.scheduler import schedule_integration
from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.user import User
from services.billing_service import check_integration_limit
from services.integration_service import connect_integration
from services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/oauth", tags=["integrations-oauth"])

# ── In-memory state store (single-instance Railway deployment) ────────────────
# state_token → {company_id, user_id, provider, expires_at}
_states: dict[str, dict] = {}
_STATE_TTL = 600  # 10 minutes


def _make_state(company_id: str, user_id: str, provider: str) -> str:
    state = secrets.token_urlsafe(32)
    _states[state] = {
        "company_id": company_id,
        "user_id": user_id,
        "provider": provider,
        "expires_at": time.time() + _STATE_TTL,
    }
    return state


def _consume_state(state: str) -> dict | None:
    entry = _states.pop(state, None)
    if entry and entry["expires_at"] > time.time():
        return entry
    return None


# ── Provider configs ───────────────────────────────────────────────────────────

def _callback_url(provider: str) -> str:
    return f"{settings.backend_url}/v1/integrations/oauth/{provider}/callback"


PROVIDER_CONFIGS = {
    "github": {
        "authorize_url": "https://github.com/login/oauth/authorize",
        "scopes": "read:org read:user repo",
        "client_id_field": "github_oauth_client_id",
    },
    "slack": {
        "authorize_url": "https://slack.com/oauth/v2/authorize",
        "scopes": "channels:read,users:read,team:read",
        "client_id_field": "slack_oauth_client_id",
    },
    "linear": {
        "authorize_url": "https://linear.app/oauth/authorize",
        "scopes": "read",
        "client_id_field": "linear_oauth_client_id",
    },
    "notion": {
        "authorize_url": "https://api.notion.com/v1/oauth/authorize",
        "scopes": None,  # Notion doesn't use scope param
        "client_id_field": "notion_oauth_client_id",
    },
}


def _get_client_id(provider: str) -> str:
    field = PROVIDER_CONFIGS[provider]["client_id_field"]
    return getattr(settings, field, "")


def _get_client_secret(provider: str) -> str:
    field = PROVIDER_CONFIGS[provider]["client_id_field"].replace("_id", "_secret")
    return getattr(settings, field, "")


# ── Routes ─────────────────────────────────────────────────────────────────────

class OAuthAuthorizeResponse(BaseModel):
    url: str


@router.get("/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def get_authorize_url(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if provider not in PROVIDER_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Unknown OAuth provider: {provider}")

    client_id = _get_client_id(provider)
    if not client_id:
        raise HTTPException(
            status_code=501,
            detail=f"OAuth for {provider} is not configured on this server.",
        )

    try:
        await check_integration_limit(current_user.company_id, db)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))

    state = _make_state(
        str(current_user.company_id),
        str(current_user.id),
        provider,
    )

    cfg = PROVIDER_CONFIGS[provider]
    params: dict = {
        "client_id": client_id,
        "state": state,
        "redirect_uri": _callback_url(provider),
    }
    if cfg["scopes"]:
        params["scope"] = cfg["scopes"]
    if provider == "linear":
        params["response_type"] = "code"
    if provider == "notion":
        params["response_type"] = "code"
        params["owner"] = "user"

    url = cfg["authorize_url"] + "?" + urlencode(params)
    return OAuthAuthorizeResponse(url=url)


@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = "",
    state: str = "",
    error: str = "",
    db: AsyncSession = Depends(get_db),
):
    frontend_base = settings.app_frontend_url

    if error:
        logger.warning("OAuth %s error: %s", provider, error)
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_error={provider}&reason={error}",
            status_code=302,
        )

    entry = _consume_state(state)
    if not entry:
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_error={provider}&reason=invalid_state",
            status_code=302,
        )

    company_id = uuid.UUID(entry["company_id"])
    user_id = uuid.UUID(entry["user_id"])

    try:
        credentials = await _exchange_code(provider, code)
    except Exception as exc:
        logger.exception("OAuth %s token exchange failed: %s", provider, exc)
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_error={provider}&reason=token_exchange_failed",
            status_code=302,
        )

    try:
        integration = await connect_integration(company_id, provider, credentials, db)
    except ValueError as exc:
        return RedirectResponse(
            url=f"{frontend_base}/integrations?oauth_error={provider}&reason={str(exc)[:80]}",
            status_code=302,
        )

    schedule_integration(str(company_id), provider, run_now=True)
    await audit_service.log_action(
        db, company_id, "integration.connected",
        user_id=user_id, user_email=None,
        resource_type="integration", resource_id=provider,
        metadata={"via": "oauth"},
    )

    return RedirectResponse(
        url=f"{frontend_base}/integrations?oauth_success={provider}",
        status_code=302,
    )


# ── Token exchange helpers ─────────────────────────────────────────────────────

async def _exchange_code(provider: str, code: str) -> dict:
    if provider == "github":
        return await _github_exchange(code)
    if provider == "slack":
        return await _slack_exchange(code)
    if provider == "linear":
        return await _linear_exchange(code)
    if provider == "notion":
        return await _notion_exchange(code)
    raise ValueError(f"Unknown provider: {provider}")


async def _github_exchange(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": _get_client_id("github"),
                "client_secret": _get_client_secret("github"),
                "code": code,
                "redirect_uri": _callback_url("github"),
            },
        )
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise ValueError(data.get("error_description", data["error"]))
        token = data["access_token"]

        # Discover the org/username automatically
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        orgs_r = await client.get("https://api.github.com/user/orgs", headers=headers)
        orgs = orgs_r.json() if orgs_r.status_code == 200 else []
        user_r = await client.get("https://api.github.com/user", headers=headers)
        username = user_r.json().get("login", "") if user_r.status_code == 200 else ""
        org = orgs[0]["login"] if orgs else username

        return {"token": token, "org": org}


async def _slack_exchange(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": _get_client_id("slack"),
                "client_secret": _get_client_secret("slack"),
                "code": code,
                "redirect_uri": _callback_url("slack"),
            },
        )
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise ValueError(data.get("error", "Slack OAuth failed"))
        # Bot token is the top-level access_token when bot scopes are used
        bot_token = data.get("access_token") or data.get("bot", {}).get("bot_access_token", "")
        return {"bot_token": bot_token}


async def _linear_exchange(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.linear.app/oauth/token",
            data={
                "client_id": _get_client_id("linear"),
                "client_secret": _get_client_secret("linear"),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _callback_url("linear"),
            },
        )
        r.raise_for_status()
        data = r.json()
        return {"api_key": data["access_token"]}


async def _notion_exchange(code: str) -> dict:
    import base64
    cid = _get_client_id("notion")
    csec = _get_client_secret("notion")
    basic = base64.b64encode(f"{cid}:{csec}".encode()).decode()
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            "https://api.notion.com/v1/oauth/token",
            headers={
                "Authorization": f"Basic {basic}",
                "Content-Type": "application/json",
            },
            json={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": _callback_url("notion"),
            },
        )
        r.raise_for_status()
        data = r.json()
        return {"api_key": data["access_token"]}
