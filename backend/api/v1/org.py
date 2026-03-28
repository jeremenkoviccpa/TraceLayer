import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.user import User
from schemas.auth import TokenResponse
from schemas.org import AcceptInviteRequest, CompanyResponse, InvitationResponse, InviteRequest, MemberResponse, UpdateCompanyRequest
from models.company import Company
from sqlalchemy import select
from services.audit_service import log_action
from services.email_service import send_invite_email
from services.org_service import (
    accept_invitation,
    create_invitation,
    list_invitations,
    list_members,
    remove_member,
    revoke_invitation,
)
from core.security import create_access_token, create_refresh_token
from models.refresh_token import RefreshToken
from datetime import datetime, timedelta, timezone
from core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/org", tags=["org"])


@router.get("/company", response_model=CompanyResponse)
async def get_company(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.get("/onboarding-status")
async def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Granular onboarding completion flags for the dashboard checklist."""
    from models.evidence import Evidence
    from models.integration import Integration
    from models.report import Report
    from models.risk import Risk
    from models.training import TrainingRecord
    from models.vendor import Vendor
    from sqlalchemy import func

    cid = current_user.company_id

    async def _has(model):
        res = await db.execute(select(func.count()).where(model.company_id == cid))
        return (res.scalar() or 0) > 0

    member_count_res = await db.execute(
        select(func.count()).where(User.company_id == cid)
    )
    has_member = (member_count_res.scalar() or 0) > 1

    return {
        "has_integration":  await _has(Integration),
        "has_evidence":     await _has(Evidence),
        "has_vendor":       await _has(Vendor),
        "has_member":       has_member,
        "has_training":     await _has(TrainingRecord),
        "has_report":       await _has(Report),
        "has_risk":         await _has(Risk),
    }


@router.post("/onboarding/complete", status_code=204)
async def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark onboarding as completed for the current user's company."""
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.onboarding_completed = True
    await db.commit()


@router.patch("/company", response_model=CompanyResponse)
async def update_company(
    body: UpdateCompanyRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    company.name = body.name
    if body.gst_number is not None:
        company.gst_number = body.gst_number.strip() or None
    await db.commit()
    await db.refresh(company)
    await log_action(db, current_user.company_id, "company.updated",
        user_id=current_user.id, user_email=current_user.email,
        metadata={"name": body.name})
    return company


@router.get("/members", response_model=list[MemberResponse])
async def get_members(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_members(current_user.company_id, db)


@router.delete("/members/{user_id}", status_code=204)
async def delete_member(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        removed = await remove_member(current_user.company_id, user_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not removed:
        raise HTTPException(status_code=404, detail="Member not found")
    await log_action(db, current_user.company_id, "member.removed",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="user", resource_id=str(user_id))


@router.get("/invites", response_model=list[InvitationResponse])
async def get_invitations(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    invites = await list_invitations(current_user.company_id, db)
    # Build response — invite_url is returned as placeholder since it's in the DB without the raw token
    return [
        InvitationResponse(
            id=i.id,
            email=i.email,
            role=i.role,
            invite_url="(already sent — token not re-displayable)",
            expires_at=i.expires_at,
            accepted_at=i.accepted_at,
            created_at=i.created_at,
        )
        for i in invites
    ]


@router.post("/invites", response_model=InvitationResponse, status_code=201)
async def invite_member(
    body: InviteRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    try:
        invite, invite_url = await create_invitation(
            company_id=current_user.company_id,
            invited_by=current_user.id,
            email=body.email,
            role=body.role,
            db=db,
            frontend_url=settings.app_frontend_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Fetch company name (can't access lazy relationship in async context)
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "your organization"

    # Send invite email (non-blocking — failure doesn't abort the request)
    try:
        send_invite_email(
            to=invite.email,
            invite_url=invite_url,
            company_name=company_name,
            invited_by=current_user.email,
        )
    except Exception as exc:
        logger.warning("Failed to send invite email to %s: %s", invite.email, exc)

    await log_action(db, current_user.company_id, "member.invited",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="invitation", resource_id=str(invite.id),
        metadata={"email": invite.email, "role": invite.role})
    return InvitationResponse(
        id=invite.id,
        email=invite.email,
        role=invite.role,
        invite_url=invite_url,
        expires_at=invite.expires_at,
        accepted_at=invite.accepted_at,
        created_at=invite.created_at,
    )


@router.delete("/invites/{invite_id}", status_code=204)
async def cancel_invitation(
    invite_id: uuid.UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    removed = await revoke_invitation(current_user.company_id, invite_id, db)
    if not removed:
        raise HTTPException(status_code=404, detail="Invitation not found")


@router.post("/invites/accept", response_model=TokenResponse)
async def accept_invite(
    body: AcceptInviteRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await accept_invitation(body.token, body.password, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = create_access_token(str(user.id), str(user.company_id))
    raw_refresh, refresh_hash = create_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


# ── GDPR ─────────────────────────────────────────────────────────────────────

@router.get("/account/export")
async def export_account_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GDPR data export — returns all data belonging to the current user's company."""
    from models.evidence import Evidence
    from models.integration import Integration
    from models.audit_log import AuditLog
    from sqlalchemy import select

    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()

    members_result = await db.execute(
        select(User).where(User.company_id == current_user.company_id)
    )
    members = members_result.scalars().all()

    integrations_result = await db.execute(
        select(Integration).where(Integration.company_id == current_user.company_id)
    )
    integrations = integrations_result.scalars().all()

    evidence_result = await db.execute(
        select(Evidence).where(Evidence.company_id == current_user.company_id)
    )
    evidence_items = evidence_result.scalars().all()

    audit_result = await db.execute(
        select(AuditLog).where(AuditLog.company_id == current_user.company_id)
    )
    audit_logs = audit_result.scalars().all()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "company": {
            "id": str(company.id),
            "name": company.name,
            "plan": company.plan,
            "created_at": company.created_at.isoformat(),
        } if company else None,
        "members": [
            {"id": str(m.id), "email": m.email, "role": m.role, "created_at": m.created_at.isoformat()}
            for m in members
        ],
        "integrations": [
            {"type": i.integration_type, "status": i.status, "created_at": i.created_at.isoformat()}
            for i in integrations
        ],
        "evidence_count": len(evidence_items),
        "audit_log": [
            {
                "action": a.action,
                "user_email": a.user_email,
                "resource_type": a.resource_type,
                "created_at": a.created_at.isoformat(),
            }
            for a in audit_logs
        ],
    }


@router.delete("/account", status_code=204)
async def delete_account(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """GDPR right to erasure — permanently deletes the company and all associated data.
    Admin only. This action is irreversible.
    """
    from models.evidence import Evidence
    from models.associations import evidence_controls
    from models.integration import Integration
    from models.audit_log import AuditLog
    from models.refresh_token import RefreshToken
    from models.password_reset_token import PasswordResetToken
    from models.email_verification_token import EmailVerificationToken
    from models.report import Report
    from models.risk import Risk
    from models.vendor import Vendor
    from models.policy import Policy
    from models.training import TrainingRecord
    from models.pen_test import PenTest
    from models.access_review import AccessReview
    from models.manual_control import ManualControl
    from models.score_snapshot import ScoreSnapshot
    from models.document import Document
    from models.invitation import Invitation
    from models.audit_session import AuditSession
    from models.trust_page import TrustPage
    from models.api_key import ApiKey
    from sqlalchemy import delete

    company_id = current_user.company_id

    # Collect member IDs before deleting users
    members_result = await db.execute(select(User).where(User.company_id == company_id))
    member_ids = [m.id for m in members_result.scalars().all()]

    # Delete all company-scoped data (order respects FK constraints)
    await db.execute(delete(AuditLog).where(AuditLog.company_id == company_id))
    await db.execute(delete(ScoreSnapshot).where(ScoreSnapshot.company_id == company_id))
    # Clear evidence_controls join table before deleting evidence rows (FK constraint)
    evidence_ids = (
        await db.execute(select(Evidence.id).where(Evidence.company_id == company_id))
    ).scalars().all()
    if evidence_ids:
        await db.execute(
            evidence_controls.delete().where(evidence_controls.c.evidence_id.in_(evidence_ids))
        )
    await db.execute(delete(Evidence).where(Evidence.company_id == company_id))
    await db.execute(delete(ManualControl).where(ManualControl.company_id == company_id))
    await db.execute(delete(Integration).where(Integration.company_id == company_id))
    await db.execute(delete(Risk).where(Risk.company_id == company_id))
    await db.execute(delete(Vendor).where(Vendor.company_id == company_id))
    await db.execute(delete(Policy).where(Policy.company_id == company_id))
    await db.execute(delete(TrainingRecord).where(TrainingRecord.company_id == company_id))
    await db.execute(delete(PenTest).where(PenTest.company_id == company_id))
    await db.execute(delete(AccessReview).where(AccessReview.company_id == company_id))
    await db.execute(delete(Document).where(Document.company_id == company_id))
    await db.execute(delete(Report).where(Report.company_id == company_id))
    await db.execute(delete(AuditSession).where(AuditSession.company_id == company_id))
    await db.execute(delete(TrustPage).where(TrustPage.company_id == company_id))
    await db.execute(delete(Invitation).where(Invitation.company_id == company_id))
    await db.execute(delete(ApiKey).where(ApiKey.company_id == company_id))

    # Delete per-user tokens
    for uid in member_ids:
        await db.execute(delete(RefreshToken).where(RefreshToken.user_id == uid))
        await db.execute(delete(PasswordResetToken).where(PasswordResetToken.user_id == uid))
        await db.execute(delete(EmailVerificationToken).where(EmailVerificationToken.user_id == uid))

    # Delete users then company last
    await db.execute(delete(User).where(User.company_id == company_id))
    await db.execute(delete(Company).where(Company.id == company_id))

    await db.commit()
    logger.info("GDPR account deletion: company=%s", company_id)
