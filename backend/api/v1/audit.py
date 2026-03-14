import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.audit_log import AuditLog
from models.user import User
from schemas.audit import AuditLogResponse
from services.audit_service import ACTION_LABELS
from utils.pagination import Page

router = APIRouter(prefix="/audit-log", tags=["audit"])


@router.get("", response_model=Page[AuditLogResponse])
async def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    action: Optional[str] = Query(None),
    user_email: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [AuditLog.company_id == current_user.company_id]
    if action:
        filters.append(AuditLog.action == action)
    if user_email:
        filters.append(AuditLog.user_email.ilike(f"%{user_email}%"))
    if date_from:
        filters.append(AuditLog.created_at >= date_from)
    if date_to:
        filters.append(AuditLog.created_at <= date_to)

    where = and_(*filters)

    total_result = await db.execute(select(func.count()).select_from(AuditLog).where(where))
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    result = await db.execute(
        select(AuditLog).where(where).order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
    )
    items = result.scalars().all()

    rows = [
        AuditLogResponse(
            id=item.id,
            company_id=item.company_id,
            user_id=item.user_id,
            user_email=item.user_email,
            action=item.action,
            action_label=ACTION_LABELS.get(item.action, item.action),
            resource_type=item.resource_type,
            resource_id=item.resource_id,
            metadata_=item.metadata_,
            ip_address=item.ip_address,
            created_at=item.created_at,
        )
        for item in items
    ]

    return Page(
        items=rows,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
