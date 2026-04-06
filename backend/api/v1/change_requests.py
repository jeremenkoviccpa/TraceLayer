"""Change management — SOC 2 CC8.1 request-to-deployment lifecycle tracking."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.change_request import ChangeRequest
from models.user import User
from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/change-requests", tags=["change-requests"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ChangeRequestCreate(BaseModel):
    title: str
    description: Optional[str] = None
    change_type: str = "code"
    risk_level: str = "medium"
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    rollback_plan: Optional[str] = None
    ticket_url: Optional[str] = None
    pr_url: Optional[str] = None


class ChangeRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    change_type: Optional[str] = None
    risk_level: Optional[str] = None
    requester_name: Optional[str] = None
    requester_email: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    rollback_plan: Optional[str] = None
    ticket_url: Optional[str] = None
    pr_url: Optional[str] = None


class ApproveBody(BaseModel):
    approver_name: str
    approver_email: Optional[str] = None


class RejectBody(BaseModel):
    rejection_reason: str


# ── Serializer ────────────────────────────────────────────────────────────────

def _to_dict(cr: ChangeRequest) -> dict:
    return {
        "id": str(cr.id),
        "company_id": str(cr.company_id),
        "title": cr.title,
        "description": cr.description,
        "change_type": cr.change_type,
        "risk_level": cr.risk_level,
        "status": cr.status,
        "requester_name": cr.requester_name,
        "requester_email": cr.requester_email,
        "approver_name": cr.approver_name,
        "approver_email": cr.approver_email,
        "approved_at": cr.approved_at,
        "rejected_at": cr.rejected_at,
        "rejection_reason": cr.rejection_reason,
        "scheduled_at": cr.scheduled_at,
        "deployed_at": cr.deployed_at,
        "closed_at": cr.closed_at,
        "rollback_plan": cr.rollback_plan,
        "ticket_url": cr.ticket_url,
        "pr_url": cr.pr_url,
        "created_by_id": str(cr.created_by_id) if cr.created_by_id else None,
        "created_at": cr.created_at,
        "updated_at": cr.updated_at,
    }


# ── Helper ────────────────────────────────────────────────────────────────────

async def _get_cr(
    cr_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> ChangeRequest:
    cr = (await db.execute(
        select(ChangeRequest).where(
            ChangeRequest.id == cr_id,
            ChangeRequest.company_id == company_id,
        )
    )).scalar_one_or_none()
    if not cr:
        raise HTTPException(status_code=404, detail="Change request not found")
    return cr


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_change_requests(
    status: Optional[str] = Query(None),
    change_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(ChangeRequest).where(ChangeRequest.company_id == current_user.company_id)
    if status:
        q = q.where(ChangeRequest.status == status)
    if change_type:
        q = q.where(ChangeRequest.change_type == change_type)
    if risk_level:
        q = q.where(ChangeRequest.risk_level == risk_level)
    q = q.order_by(ChangeRequest.created_at.desc())
    result = await db.execute(q)
    return [_to_dict(cr) for cr in result.scalars().all()]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return aggregate counts by status and risk level."""
    rows = await db.execute(
        select(ChangeRequest.status, func.count().label("cnt"))
        .where(ChangeRequest.company_id == current_user.company_id)
        .group_by(ChangeRequest.status)
    )
    by_status: dict[str, int] = {}
    for row in rows:
        by_status[row.status] = row.cnt

    risk_rows = await db.execute(
        select(ChangeRequest.risk_level, func.count().label("cnt"))
        .where(ChangeRequest.company_id == current_user.company_id)
        .group_by(ChangeRequest.risk_level)
    )
    by_risk: dict[str, int] = {}
    for row in risk_rows:
        by_risk[row.risk_level] = row.cnt

    open_statuses = {"draft", "submitted", "approved", "in_progress"}
    open_count = sum(v for k, v in by_status.items() if k in open_statuses)
    total = sum(by_status.values())

    return {
        "total": total,
        "by_status": {
            "draft": by_status.get("draft", 0),
            "submitted": by_status.get("submitted", 0),
            "approved": by_status.get("approved", 0),
            "in_progress": by_status.get("in_progress", 0),
            "deployed": by_status.get("deployed", 0),
            "closed": by_status.get("closed", 0),
            "rejected": by_status.get("rejected", 0),
            "failed": by_status.get("failed", 0),
        },
        "by_risk": {
            "low": by_risk.get("low", 0),
            "medium": by_risk.get("medium", 0),
            "high": by_risk.get("high", 0),
            "critical": by_risk.get("critical", 0),
        },
        "open_count": open_count,
    }


@router.post("", status_code=201)
async def create_change_request(
    body: ChangeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    cr = ChangeRequest(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        title=body.title,
        description=body.description,
        change_type=body.change_type,
        risk_level=body.risk_level,
        status="draft",
        requester_name=body.requester_name,
        requester_email=body.requester_email,
        scheduled_at=body.scheduled_at,
        rollback_plan=body.rollback_plan,
        ticket_url=body.ticket_url,
        pr_url=body.pr_url,
        created_by_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(cr)
    await db.commit()
    await db.refresh(cr)
    await log_action(db, current_user.company_id, "change_request.created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="change_request", resource_id=str(cr.id),
                     metadata={"title": body.title})
    return _to_dict(cr)


@router.get("/{cr_id}")
async def get_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    return _to_dict(cr)


@router.patch("/{cr_id}")
async def update_change_request(
    cr_id: uuid.UUID,
    body: ChangeRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cr, field, value)
    cr.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/submit")
async def submit_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft requests can be submitted")
    cr.status = "submitted"
    cr.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/approve")
async def approve_change_request(
    cr_id: uuid.UUID,
    body: ApproveBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted requests can be approved")
    now = datetime.now(timezone.utc)
    cr.status = "approved"
    cr.approver_name = body.approver_name
    cr.approver_email = body.approver_email
    cr.approved_at = now
    cr.updated_at = now
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/reject")
async def reject_change_request(
    cr_id: uuid.UUID,
    body: RejectBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted requests can be rejected")
    now = datetime.now(timezone.utc)
    cr.status = "rejected"
    cr.rejection_reason = body.rejection_reason
    cr.rejected_at = now
    cr.updated_at = now
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/start")
async def start_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "approved":
        raise HTTPException(status_code=400, detail="Only approved requests can be started")
    cr.status = "in_progress"
    cr.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/deploy")
async def deploy_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "in_progress":
        raise HTTPException(status_code=400, detail="Only in-progress requests can be deployed")
    now = datetime.now(timezone.utc)
    cr.status = "deployed"
    cr.deployed_at = now
    cr.updated_at = now
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/fail")
async def fail_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "in_progress":
        raise HTTPException(status_code=400, detail="Only in-progress requests can be marked failed")
    cr.status = "failed"
    cr.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.post("/{cr_id}/close")
async def close_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status not in ("deployed", "failed"):
        raise HTTPException(status_code=400, detail="Only deployed or failed requests can be closed")
    now = datetime.now(timezone.utc)
    cr.status = "closed"
    cr.closed_at = now
    cr.updated_at = now
    await db.commit()
    await db.refresh(cr)
    return _to_dict(cr)


@router.delete("/{cr_id}", status_code=204)
async def delete_change_request(
    cr_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cr = await _get_cr(cr_id, current_user.company_id, db)
    if cr.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft requests can be deleted")
    await db.delete(cr)
    await db.commit()
