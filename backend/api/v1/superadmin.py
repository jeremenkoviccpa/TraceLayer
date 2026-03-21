"""
Super-admin API — only accessible to emails listed in INTERNAL_ADMINS env var.
Provides company and user management for internal operators.
"""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.company import Company
from models.user import User
from services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/super-admin", tags=["super-admin"])


# ── Auth guard ────────────────────────────────────────────────────────────────

async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.email not in settings.internal_admins_list:
        raise HTTPException(status_code=403, detail="Super-admin access required.")
    return current_user


# ── Schemas ───────────────────────────────────────────────────────────────────

class CompanyRow(BaseModel):
    id: str
    name: str
    plan: str
    subscription_status: Optional[str]
    is_partner_account: bool
    created_at: datetime
    user_count: int
    admin_emails: list[str]

    class Config:
        from_attributes = True


class PatchCompanyBody(BaseModel):
    plan: Optional[str] = None
    is_partner_account: Optional[bool] = None
    reset_subscription: Optional[bool] = None  # wipe billing fields → free


class UserRow(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PatchUserBody(BaseModel):
    role: Optional[str] = None
    email_verified: Optional[bool] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/companies", response_model=list[CompanyRow])
async def list_companies(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all companies with user counts and admin emails."""
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()

    rows = []
    for c in companies:
        users_result = await db.execute(
            select(User).where(User.company_id == c.id)
        )
        users = users_result.scalars().all()
        admin_emails = [u.email for u in users if u.role == "admin"]
        rows.append(CompanyRow(
            id=str(c.id),
            name=c.name,
            plan=c.plan,
            subscription_status=c.subscription_status,
            is_partner_account=c.is_partner_account,
            created_at=c.created_at,
            user_count=len(users),
            admin_emails=admin_emails,
        ))
    return rows


@router.patch("/companies/{company_id}", response_model=CompanyRow)
async def patch_company(
    company_id: uuid.UUID,
    body: PatchCompanyBody,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a company's plan or partner status."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if body.plan is not None:
        if body.plan not in ("free", "growth"):
            raise HTTPException(status_code=400, detail="Plan must be 'free' or 'growth'")
        company.plan = body.plan

    if body.is_partner_account is not None:
        company.is_partner_account = body.is_partner_account

    if body.reset_subscription:
        company.plan = "free"
        company.subscription_status = None
        company.ls_subscription_id = None
        company.ls_customer_id = None

    await audit_service.log_action(
        db=db,
        company_id=company.id,
        action="superadmin.company_updated",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"changes": body.model_dump(exclude_none=True)},
    )
    await db.commit()
    await db.refresh(company)

    users_result = await db.execute(select(User).where(User.company_id == company.id))
    users = users_result.scalars().all()
    return CompanyRow(
        id=str(company.id),
        name=company.name,
        plan=company.plan,
        subscription_status=company.subscription_status,
        is_partner_account=company.is_partner_account,
        created_at=company.created_at,
        user_count=len(users),
        admin_emails=[u.email for u in users if u.role == "admin"],
    )


@router.get("/companies/{company_id}/users", response_model=list[UserRow])
async def list_company_users(
    company_id: uuid.UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.company_id == company_id))
    users = result.scalars().all()
    return [
        UserRow(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            email_verified=u.email_verified,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/companies/{company_id}/users/{user_id}", response_model=UserRow)
async def patch_company_user(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    body: PatchUserBody,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role within a company."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        if body.role not in ("admin", "member", "viewer"):
            raise HTTPException(status_code=400, detail="Role must be admin, member, or viewer")
        user.role = body.role

    if body.email_verified is not None:
        user.email_verified = body.email_verified

    await audit_service.log_action(
        db=db,
        company_id=company_id,
        action="superadmin.user_updated",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"target_user_id": str(user_id), "changes": body.model_dump(exclude_none=True)},
    )
    await db.commit()
    await db.refresh(user)
    return UserRow(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.delete("/companies/{company_id}", status_code=204)
async def delete_company(
    company_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a company and all its associated data."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await audit_service.log_action(
        db=db,
        company_id=company_id,
        action="superadmin.company_deleted",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"company_name": company.name},
    )
    await db.commit()

    # Use raw SQL so Postgres CASCADE constraints handle child records
    await db.execute(text("DELETE FROM companies WHERE id = :id"), {"id": company_id})
    await db.commit()
    return Response(status_code=204)


@router.delete("/companies/{company_id}/users/{user_id}", status_code=204)
async def delete_company_user(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from a company."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return Response(status_code=204)
