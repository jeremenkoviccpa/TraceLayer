"""
Admin API — framework versioning management.

All endpoints require the caller to be in the INTERNAL_ADMINS list
(same guard used by the super-admin router).  These are internal
operator endpoints; they are never exposed to regular customers.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.framework_source_manifest import FrameworkSourceManifest
from models.framework_update_request import FrameworkUpdateRequest
from models.user import User
from services.framework_monitor_service import (
    approve_request,
    check_all_frameworks,
    reject_request,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/framework-updates", tags=["admin-framework-updates"])


# ---------------------------------------------------------------------------
# Auth guard
# ---------------------------------------------------------------------------

async def require_internal_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Allow only emails listed in the INTERNAL_ADMINS env var."""
    if current_user.email not in settings.internal_admins_list:
        raise HTTPException(status_code=403, detail="Internal admin access required.")
    return current_user


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class FrameworkUpdateRequestRow(BaseModel):
    id: str
    framework_key: str
    detected_at: datetime
    source_url: str
    new_hash: str
    old_hash: Optional[str]
    status: str
    reviewed_by: Optional[str]
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FrameworkUpdateRequestDetail(FrameworkUpdateRequestRow):
    """Extended response that includes the full ai_extraction_json blob."""
    ai_extraction_json: Optional[Any]


class FrameworkSourceManifestRow(BaseModel):
    id: str
    framework_key: str
    source_url: str
    current_version: str
    last_checked_at: Optional[datetime]
    last_hash: Optional[str]
    pending_update: bool
    pending_update_detected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewBody(BaseModel):
    notes: Optional[str] = None


class CheckNowResponse(BaseModel):
    checked: int
    changed: int
    frameworks_with_updates: list[str]


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _row_to_summary(req: FrameworkUpdateRequest) -> FrameworkUpdateRequestRow:
    return FrameworkUpdateRequestRow(
        id=str(req.id),
        framework_key=req.framework_key,
        detected_at=req.detected_at,
        source_url=req.source_url,
        new_hash=req.new_hash,
        old_hash=req.old_hash,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        review_notes=req.review_notes,
        created_at=req.created_at,
    )


def _row_to_detail(req: FrameworkUpdateRequest) -> FrameworkUpdateRequestDetail:
    return FrameworkUpdateRequestDetail(
        id=str(req.id),
        framework_key=req.framework_key,
        detected_at=req.detected_at,
        source_url=req.source_url,
        new_hash=req.new_hash,
        old_hash=req.old_hash,
        ai_extraction_json=req.ai_extraction_json,
        status=req.status,
        reviewed_by=req.reviewed_by,
        reviewed_at=req.reviewed_at,
        review_notes=req.review_notes,
        created_at=req.created_at,
    )


# ---------------------------------------------------------------------------
# Routes — update requests
# ---------------------------------------------------------------------------

@router.get("", response_model=list[FrameworkUpdateRequestRow])
async def list_framework_update_requests(
    _: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all framework update requests, pending ones first then by detection date."""
    result = await db.execute(
        select(FrameworkUpdateRequest).order_by(
            # pending=0 in alphabetical order so negate to bring them first
            FrameworkUpdateRequest.status.desc(),  # pending > rejected > approved alphabetically — explicit case below
            FrameworkUpdateRequest.detected_at.desc(),
        )
    )
    # SQLAlchemy can't easily do CASE ordering in a portable way here; fetch
    # all and sort in Python so pending rows always appear first.
    rows = list(result.scalars().all())
    rows.sort(key=lambda r: (0 if r.status == "pending" else 1, r.detected_at), reverse=False)
    rows.sort(key=lambda r: r.detected_at, reverse=True)
    rows.sort(key=lambda r: 0 if r.status == "pending" else 1)

    return [_row_to_summary(r) for r in rows]


@router.get("/{request_id}", response_model=FrameworkUpdateRequestDetail)
async def get_framework_update_request(
    request_id: uuid.UUID,
    _: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """Fetch a single update request including the full ai_extraction_json."""
    result = await db.execute(
        select(FrameworkUpdateRequest).where(FrameworkUpdateRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if req is None:
        raise HTTPException(status_code=404, detail="Framework update request not found")
    return _row_to_detail(req)


@router.post("/{request_id}/approve", response_model=FrameworkUpdateRequestDetail)
async def approve_framework_update_request(
    request_id: uuid.UUID,
    body: ReviewBody,
    current_user: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending framework update request."""
    try:
        req = await approve_request(
            request_id=request_id,
            reviewed_by=current_user.email,
            notes=body.notes,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    logger.info(
        "Framework update request %s approved by %s",
        request_id,
        current_user.email,
    )
    return _row_to_detail(req)


@router.post("/{request_id}/reject", response_model=FrameworkUpdateRequestDetail)
async def reject_framework_update_request(
    request_id: uuid.UUID,
    body: ReviewBody,
    current_user: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """Reject a pending framework update request."""
    try:
        req = await reject_request(
            request_id=request_id,
            reviewed_by=current_user.email,
            notes=body.notes,
            db=db,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    logger.info(
        "Framework update request %s rejected by %s",
        request_id,
        current_user.email,
    )
    return _row_to_detail(req)


# ---------------------------------------------------------------------------
# Routes — source manifests  (separate prefix, registered via the same router)
# ---------------------------------------------------------------------------

manifests_router = APIRouter(prefix="/admin/framework-manifests", tags=["admin-framework-updates"])


@manifests_router.get("", response_model=list[FrameworkSourceManifestRow])
async def list_framework_manifests(
    _: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all source manifests with last_checked_at and pending_update status."""
    result = await db.execute(
        select(FrameworkSourceManifest).order_by(FrameworkSourceManifest.framework_key)
    )
    manifests = result.scalars().all()
    return [
        FrameworkSourceManifestRow(
            id=str(m.id),
            framework_key=m.framework_key,
            source_url=m.source_url,
            current_version=m.current_version,
            last_checked_at=m.last_checked_at,
            last_hash=m.last_hash,
            pending_update=m.pending_update,
            pending_update_detected_at=m.pending_update_detected_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
        for m in manifests
    ]


@manifests_router.post("/check-now", response_model=CheckNowResponse)
async def check_manifests_now(
    _: User = Depends(require_internal_admin),
    db: AsyncSession = Depends(get_db),
):
    """Trigger an immediate check of all framework source manifests."""
    logger.info("Manual framework manifest check triggered via admin API")
    results = await check_all_frameworks(db)
    changed = [r for r in results if r.get("changed")]
    return CheckNowResponse(
        checked=len(results),
        changed=len(changed),
        frameworks_with_updates=[r["framework"] for r in changed],
    )
