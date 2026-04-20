"""Nango OAuth completion — called by the frontend after the Nango popup succeeds."""
import logging
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.scheduler import schedule_integration
from core.database import get_db
from core.deps import get_current_user
from models.integration import Integration
from models.user import User
from services import audit_service, data_flow_service
from services.billing_service import check_integration_limit
from utils.encryption import encrypt_credentials
from utils.nango import NANGO_PROVIDER_MAP, get_nango_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations/nango", tags=["integrations-nango"])


class NangoCompleteRequest(BaseModel):
    integration_type: str
    connection_id: str


@router.post("/complete", status_code=201)
async def nango_complete(
    body: NangoCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Persist a Nango OAuth connection after the frontend popup completes.
    Validates the connection is live, discovers any extra metadata (e.g. GitHub org),
    then upserts the integration and triggers first evidence collection.
    """
    provider_config_key = NANGO_PROVIDER_MAP.get(body.integration_type)
    if not provider_config_key:
        raise HTTPException(400, f"'{body.integration_type}' does not support Nango OAuth")

    try:
        await check_integration_limit(current_user.company_id, db)
    except ValueError as e:
        raise HTTPException(402, str(e))

    try:
        token = await get_nango_token(body.connection_id, provider_config_key)
    except httpx.HTTPStatusError as e:
        raise HTTPException(422, f"Nango connection invalid: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(422, f"Nango connection error: {e}")

    extra: dict = {}
    if body.integration_type == "github":
        extra = await _discover_github_org(token)

    credentials = {
        "auth_type": "nango",
        "connection_id": body.connection_id,
        "provider_config_key": provider_config_key,
        **extra,
    }

    result = await db.execute(
        select(Integration).where(
            Integration.company_id == current_user.company_id,
            Integration.integration_type == body.integration_type,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.credentials_enc = encrypt_credentials(credentials)
        existing.status = "active"
        existing.last_error = None
    else:
        db.add(Integration(
            company_id=current_user.company_id,
            integration_type=body.integration_type,
            credentials_enc=encrypt_credentials(credentials),
        ))
    await db.commit()

    await data_flow_service.add_flow_for_integration(
        current_user.company_id, body.integration_type, db
    )
    schedule_integration(str(current_user.company_id), body.integration_type, run_now=True)
    await audit_service.log_action(
        db, current_user.company_id, "integration.connected",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="integration", resource_id=body.integration_type,
        metadata={"via": "nango"},
    )
    return {"status": "connected", "integration_type": body.integration_type}


async def _discover_github_org(token: str) -> dict:
    """Auto-discover the GitHub org or username from a fresh OAuth token."""
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    async with httpx.AsyncClient(timeout=10) as client:
        orgs_r = await client.get("https://api.github.com/user/orgs", headers=headers)
        orgs = orgs_r.json() if orgs_r.status_code == 200 else []
        user_r = await client.get("https://api.github.com/user", headers=headers)
        username = user_r.json().get("login", "") if user_r.status_code == 200 else ""
    org = orgs[0]["login"] if orgs else username
    return {"org": org}
