import hashlib
import logging
import secrets
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.api_key import ApiKey
from models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


class CreateApiKeyRequest(BaseModel):
    name: str


class ApiKeyCreatedResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    raw_key: str
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: uuid.UUID
    name: str
    key_prefix: str
    created_at: datetime
    last_used_at: datetime | None
    revoked: bool


@router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new API key for CI/CD evidence ingestion. The raw key is returned once and never stored."""
    raw_key = secrets.token_hex(32)  # 64-char hex string, 32 bytes of entropy
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    api_key = ApiKey(
        company_id=current_user.company_id,
        name=body.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    logger.info("API key created: company=%s name=%s prefix=%s", current_user.company_id, body.name, key_prefix)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_key=raw_key,
        created_at=api_key.created_at,
    )


@router.get("", response_model=list[ApiKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all API keys for the company (raw key is never returned)."""
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.company_id == current_user.company_id)
        .order_by(ApiKey.created_at.desc())
    )
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            name=k.name,
            key_prefix=k.key_prefix,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            revoked=k.revoked,
        )
        for k in keys
    ]


@router.delete("/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Revoke an API key (soft delete). Revoked keys are rejected on ingest."""
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.id == key_id,
            ApiKey.company_id == current_user.company_id,
        )
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")

    api_key.revoked = True
    await db.commit()
    logger.info("API key revoked: company=%s key_id=%s", current_user.company_id, key_id)
