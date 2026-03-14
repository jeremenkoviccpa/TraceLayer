import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import hash_password
from models.company import Company
from models.invitation import Invitation
from models.user import User

INVITE_EXPIRY_DAYS = 7


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def list_members(company_id: uuid.UUID, db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.company_id == company_id))
    return list(result.scalars().all())


async def remove_member(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    requesting_user_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    if user_id == requesting_user_id:
        raise ValueError("You cannot remove yourself")

    result = await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return False

    await db.delete(user)
    await db.commit()
    return True


async def create_invitation(
    company_id: uuid.UUID,
    invited_by: uuid.UUID,
    email: str,
    role: str,
    db: AsyncSession,
    frontend_url: str = "http://localhost:3000",
) -> tuple[Invitation, str]:
    # Check if user already exists in this company
    existing = await db.execute(
        select(User).where(User.email == email, User.company_id == company_id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"{email} is already a member of this organization")

    # Revoke any existing pending invite for this email
    old = await db.execute(
        select(Invitation).where(
            Invitation.company_id == company_id,
            Invitation.email == email,
            Invitation.accepted_at.is_(None),
        )
    )
    for old_invite in old.scalars().all():
        await db.delete(old_invite)

    raw_token = secrets.token_urlsafe(32)
    invitation = Invitation(
        company_id=company_id,
        invited_by=invited_by,
        email=email,
        token_hash=_hash_token(raw_token),
        role=role,
        expires_at=datetime.now(timezone.utc) + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    invite_url = f"{frontend_url}/accept-invite?token={raw_token}"
    return invitation, invite_url


async def list_invitations(company_id: uuid.UUID, db: AsyncSession) -> list[Invitation]:
    result = await db.execute(
        select(Invitation).where(
            Invitation.company_id == company_id,
            Invitation.accepted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def revoke_invitation(
    company_id: uuid.UUID,
    invitation_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    result = await db.execute(
        select(Invitation).where(
            Invitation.id == invitation_id,
            Invitation.company_id == company_id,
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        return False
    await db.delete(invite)
    await db.commit()
    return True


async def accept_invitation(
    raw_token: str,
    password: str,
    db: AsyncSession,
) -> User:
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(Invitation).where(
            Invitation.token_hash == token_hash,
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(timezone.utc),
        )
    )
    invite = result.scalar_one_or_none()
    if not invite:
        raise ValueError("Invalid or expired invitation token")

    # Check if email already registered globally (different company)
    existing = await db.execute(select(User).where(User.email == invite.email))
    if existing.scalar_one_or_none():
        raise ValueError("An account with this email already exists")

    user = User(
        email=invite.email,
        password_hash=hash_password(password),
        company_id=invite.company_id,
        role=invite.role,
    )
    db.add(user)

    invite.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user
