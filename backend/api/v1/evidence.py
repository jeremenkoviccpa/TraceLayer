import csv
import io
import logging
import math
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.associations import evidence_controls
from models.evidence import Evidence
from models.user import User
from schemas.evidence import EvidenceResponse
from services.evidence_service import list_evidence
from utils.pagination import Page

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("", response_model=Page[EvidenceResponse])
async def get_evidence(
    control: Optional[str] = Query(None),
    integration: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_evidence(
        company_id=current_user.company_id,
        db=db,
        control=control,
        integration=integration,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.post("/upload", response_model=EvidenceResponse, status_code=201)
async def upload_evidence_file(
    file: UploadFile,
    control: str = Form(...),
    evidence_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file as evidence and store it in Supabase Storage."""
    file_bytes = await file.read()
    file_name = file.filename or "upload"
    file_size = len(file_bytes)

    storage_path = f"evidence/{current_user.company_id}/{uuid.uuid4()}/{file_name}"
    storage_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
        f"{settings.storage_bucket}/{storage_path}"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            storage_url,
            content=file_bytes,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_key}",
                "Content-Type": file.content_type or "application/octet-stream",
                "x-upsert": "true",
            },
        )

    if resp.status_code not in (200, 201):
        logger.error("Supabase Storage upload failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="File upload to storage failed")

    public_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{settings.storage_bucket}/{storage_path}"
    )

    evidence = Evidence(
        company_id=current_user.company_id,
        integration="manual",
        control=control,
        evidence_type=evidence_type,
        source_id=file_name,
        timestamp=datetime.now(timezone.utc),
        data={
            "file_url": public_url,
            "file_name": file_name,
            "file_size": file_size,
            "uploaded_by": current_user.email,
        },
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


@router.get("/export")
async def export_evidence_csv(
    control: Optional[str] = Query(None),
    integration: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download all matching evidence as a CSV file."""
    items, _ = await list_evidence(
        company_id=current_user.company_id,
        db=db,
        control=control,
        integration=integration,
        page=1,
        page_size=10_000,
    )

    def _generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["id", "integration", "control", "evidence_type", "source_id", "timestamp"])
        yield buf.getvalue()
        for item in items:
            buf.seek(0)
            buf.truncate(0)
            writer.writerow([
                str(item.id),
                item.integration,
                item.control,
                item.evidence_type,
                item.source_id,
                item.timestamp.isoformat() if item.timestamp else "",
            ])
            yield buf.getvalue()

    filename = f"evidence_{current_user.company_id}.csv"
    return StreamingResponse(
        _generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class BulkDeleteRequest(BaseModel):
    ids: list[uuid.UUID]


@router.delete("/bulk", status_code=204)
async def delete_evidence_bulk(
    body: BulkDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple evidence records by ID. Only deletes records owned by the caller's company."""
    if not body.ids:
        return
    # Delete junction rows first to avoid FK violation
    await db.execute(
        delete(evidence_controls).where(
            evidence_controls.c.evidence_id.in_(body.ids)
        )
    )
    await db.execute(
        delete(Evidence).where(
            Evidence.id.in_(body.ids),
            Evidence.company_id == current_user.company_id,
        )
    )
    await db.commit()
