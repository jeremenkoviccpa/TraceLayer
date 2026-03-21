import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.api_key import ApiKey
from models.evidence import Evidence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestEvidenceRequest(BaseModel):
    control: str
    evidence_type: str
    source_id: str
    data: dict[str, Any]


async def get_api_key_company(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """Dependency that authenticates via API key Bearer token.

    Reads the Authorization header, hashes the token with SHA-256,
    looks it up in api_keys, verifies it is not revoked, and updates
    last_used_at. Returns the ApiKey row (which carries company_id).
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    raw_key = auth_header[len("Bearer "):]
    if not raw_key:
        raise HTTPException(status_code=401, detail="API key must not be empty")

    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()

    result = await db.execute(select(ApiKey).where(ApiKey.key_hash == key_hash))
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if api_key.revoked:
        raise HTTPException(status_code=401, detail="API key has been revoked")

    # Update last_used_at in-place; commit happens after the route handler
    api_key.last_used_at = datetime.now(timezone.utc)

    return api_key


@router.post("/evidence", status_code=201)
async def ingest_evidence(
    body: IngestEvidenceRequest,
    api_key: ApiKey = Depends(get_api_key_company),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a single evidence item from a CI/CD pipeline or external tool.

    Authentication is via API key (Authorization: Bearer <key>), NOT a JWT.
    The evidence is inserted under the company that owns the API key.
    The integration field is set to "ci_cd" to identify the source.
    Duplicate evidence (same company/integration/evidence_type/source_id) is
    silently ignored to keep collectors idempotent.
    """
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    company_id = api_key.company_id

    stmt = (
        pg_insert(Evidence)
        .values(
            id=uuid.uuid4(),
            company_id=company_id,
            integration="ci_cd",
            control=body.control,
            evidence_type=body.evidence_type,
            source_id=body.source_id,
            timestamp=datetime.now(timezone.utc),
            data=body.data,
        )
        .on_conflict_do_nothing(
            index_elements=["company_id", "integration", "evidence_type", "source_id"]
        )
    )
    await db.execute(stmt)
    await db.commit()

    logger.info(
        "Evidence ingested: company=%s control=%s evidence_type=%s source_id=%s",
        company_id,
        body.control,
        body.evidence_type,
        body.source_id,
    )

    return {"status": "created"}
