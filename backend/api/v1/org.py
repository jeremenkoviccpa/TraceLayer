import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.user import User
from schemas.auth import TokenResponse, UserResponse
from schemas.org import AcceptInviteRequest, CompanyResponse, InvitationResponse, InviteRequest, MemberResponse, UpdateCompanyRequest
from models.company import Company
from sqlalchemy import select
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
    await db.commit()
    await db.refresh(company)
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
            frontend_url=settings.frontend_url,
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
    from core.security import create_refresh_token, hash_token
    raw_refresh, refresh_hash = create_refresh_token()
    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(refresh_token)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)
