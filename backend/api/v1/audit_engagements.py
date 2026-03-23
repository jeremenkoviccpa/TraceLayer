import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.config import settings
from models.audit_comment import AuditComment
from models.audit_engagement import AuditEngagement
from models.company import Company
from models.manual_control import ManualControl
from models.user import User
from schemas.audit_engagement import AuditEngagementCreate, AuditEngagementResponse, AuditEngagementView
from services.compliance_service import get_compliance_score
from services.email_service import send_audit_invitation_email

logger = logging.getLogger(__name__)


# ── Comment schemas ───────────────────────────────────────────────────────────

class AuditCommentOut(BaseModel):
    id: uuid.UUID
    engagement_id: uuid.UUID
    author_name: str
    author_role: str
    body: str
    item_type: Optional[str] = None
    item_ref: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditCommentCreate(BaseModel):
    body: str
    item_type: Optional[str] = None
    item_ref: Optional[str] = None


class AuditorCommentCreate(BaseModel):
    body: str
    item_type: Optional[str] = None
    item_ref: Optional[str] = None
router = APIRouter(prefix="/audit-engagements", tags=["audit-engagements"])

# Imported here to avoid circular imports at module level
_MANUAL_CONTROLS: dict = {}


def _get_manual_controls() -> dict:
    global _MANUAL_CONTROLS
    if not _MANUAL_CONTROLS:
        from api.v1.compliance import _MANUAL_CONTROLS as _mc
        _MANUAL_CONTROLS = _mc
    return _MANUAL_CONTROLS


def _access_link(token: str) -> str:
    return f"{settings.app_frontend_url}/audit/{token}"


def _to_response(e: AuditEngagement) -> AuditEngagementResponse:
    return AuditEngagementResponse(
        id=e.id,
        framework=e.framework,
        obs_start=e.obs_start,
        obs_end=e.obs_end,
        auditor_email=e.auditor_email,
        auditor_name=e.auditor_name,
        auditor_firm=e.auditor_firm,
        status=e.status,
        created_at=e.created_at,
        expires_at=e.expires_at,
        last_accessed_at=e.last_accessed_at,
        access_link=_access_link(e.access_token),
    )


@router.get("", response_model=list[AuditEngagementResponse])
async def list_engagements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement)
        .where(AuditEngagement.customer_company_id == current_user.company_id)
        .order_by(AuditEngagement.created_at.desc())
    )
    return [_to_response(e) for e in result.scalars().all()]


@router.post("", response_model=AuditEngagementResponse)
async def create_engagement(
    body: AuditEngagementCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    company = await db.get(Company, current_user.company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    engagement = AuditEngagement(
        customer_company_id=current_user.company_id,
        framework=body.framework,
        obs_start=body.obs_start,
        obs_end=body.obs_end,
        auditor_email=body.auditor_email,
        auditor_name=body.auditor_name,
        auditor_firm=body.auditor_firm,
        status="active",
        expires_at=datetime.now(timezone.utc) + timedelta(days=180),
    )
    db.add(engagement)
    await db.commit()
    await db.refresh(engagement)

    if body.send_email:
        try:
            send_audit_invitation_email(
                to=body.auditor_email,
                auditor_name=body.auditor_name or body.auditor_email,
                customer_name=company.name,
                framework=body.framework,
                obs_start=body.obs_start,
                obs_end=body.obs_end,
                access_link=_access_link(engagement.access_token),
            )
        except Exception:
            logger.exception("Failed to send audit invitation email for engagement=%s", engagement.id)

    return _to_response(engagement)


@router.delete("/{engagement_id}")
async def revoke_engagement(
    engagement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement).where(
            AuditEngagement.id == engagement_id,
            AuditEngagement.customer_company_id == current_user.company_id,
        )
    )
    engagement = result.scalar_one_or_none()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    engagement.status = "revoked"
    await db.commit()
    return {"ok": True}


@router.get("/view/{token}", response_model=AuditEngagementView)
async def view_engagement_public(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required. Returns compliance snapshot for an audit engagement."""
    result = await db.execute(
        select(AuditEngagement).where(AuditEngagement.access_token == token)
    )
    engagement = result.scalar_one_or_none()

    if not engagement:
        raise HTTPException(status_code=404, detail="Audit link not found or has expired")

    if engagement.status != "active":
        raise HTTPException(status_code=410, detail="This audit link has been revoked")

    if engagement.expires_at and datetime.now(timezone.utc) > engagement.expires_at:
        raise HTTPException(status_code=410, detail="This audit link has expired")

    # Update last accessed timestamp
    engagement.last_accessed_at = datetime.now(timezone.utc)
    await db.commit()

    company = await db.get(Company, engagement.customer_company_id)
    customer_name = company.name if company else "Unknown"

    # Get current compliance score for the customer
    score_data = await get_compliance_score(engagement.customer_company_id, engagement.framework, db)

    # Get manual controls
    mc_defs = _get_manual_controls().get(engagement.framework.lower().replace("-", "_"), [])
    mc_result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == engagement.customer_company_id,
            ManualControl.framework == engagement.framework,
        )
    )
    mc_records = {m.control_id: m for m in mc_result.scalars().all()}

    manual_controls = [
        {
            "control_id": defn["control_id"],
            "name": defn["name"],
            "description": defn["description"],
            "status": mc_records[defn["control_id"]].status if defn["control_id"] in mc_records else "pending",
        }
        for defn in mc_defs
    ]

    return AuditEngagementView(
        id=engagement.id,
        framework=engagement.framework,
        obs_start=engagement.obs_start,
        obs_end=engagement.obs_end,
        auditor_email=engagement.auditor_email,
        auditor_name=engagement.auditor_name,
        auditor_firm=engagement.auditor_firm,
        customer_name=customer_name,
        created_at=engagement.created_at,
        score=score_data.score,
        passing_controls=score_data.passing_controls,
        failing_controls=score_data.failing_controls,
        evidence_count=score_data.evidence_count,
        controls=[c.model_dump() for c in score_data.controls],
        manual_controls=manual_controls,
    )


# ── Comments (company side, JWT auth) ─────────────────────────────────────────

@router.get("/{engagement_id}/comments", response_model=list[AuditCommentOut])
async def list_comments(
    engagement_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement).where(
            AuditEngagement.id == engagement_id,
            AuditEngagement.customer_company_id == current_user.company_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Engagement not found")

    comments = await db.execute(
        select(AuditComment)
        .where(AuditComment.engagement_id == engagement_id)
        .order_by(AuditComment.created_at)
    )
    return comments.scalars().all()


@router.post("/{engagement_id}/comments", response_model=AuditCommentOut)
async def add_comment(
    engagement_id: uuid.UUID,
    body: AuditCommentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement).where(
            AuditEngagement.id == engagement_id,
            AuditEngagement.customer_company_id == current_user.company_id,
        )
    )
    engagement = result.scalar_one_or_none()
    if not engagement:
        raise HTTPException(status_code=404, detail="Engagement not found")

    display_name = current_user.full_name or current_user.email
    comment = AuditComment(
        engagement_id=engagement_id,
        company_id=current_user.company_id,
        author_name=display_name,
        author_role="team",
        author_user_id=current_user.id,
        body=body.body.strip(),
        item_type=body.item_type,
        item_ref=body.item_ref,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


# ── Comments (auditor side, token auth) ───────────────────────────────────────

@router.get("/by-token/{token}/comments", response_model=list[AuditCommentOut])
async def list_comments_auditor(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement).where(AuditEngagement.access_token == token)
    )
    engagement = result.scalar_one_or_none()
    if not engagement or engagement.status != "active":
        raise HTTPException(status_code=404, detail="Engagement not found or inactive")

    comments = await db.execute(
        select(AuditComment)
        .where(AuditComment.engagement_id == engagement.id)
        .order_by(AuditComment.created_at)
    )
    return comments.scalars().all()


@router.post("/by-token/{token}/comments", response_model=AuditCommentOut)
async def add_comment_auditor(
    token: str,
    body: AuditorCommentCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditEngagement).where(AuditEngagement.access_token == token)
    )
    engagement = result.scalar_one_or_none()
    if not engagement or engagement.status != "active":
        raise HTTPException(status_code=404, detail="Engagement not found or inactive")

    author = engagement.auditor_name or engagement.auditor_email
    comment = AuditComment(
        engagement_id=engagement.id,
        company_id=engagement.customer_company_id,
        author_name=author,
        author_role="auditor",
        body=body.body.strip(),
        item_type=body.item_type,
        item_ref=body.item_ref,
    )
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment
