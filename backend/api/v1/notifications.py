import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.company import Company
from models.user import User
from services import audit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationPrefsResponse(BaseModel):
    prefs: dict[str, Any]
    slack_webhook_url: Optional[str]


class NotificationPrefsUpdate(BaseModel):
    prefs: dict[str, Any]
    slack_webhook_url: Optional[str] = None


@router.get("/prefs", response_model=NotificationPrefsResponse)
async def get_notification_prefs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the company's notification preferences and Slack webhook URL."""
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return NotificationPrefsResponse(
        prefs=company.notification_prefs or {},
        slack_webhook_url=company.slack_webhook_url,
    )


@router.put("/prefs", response_model=NotificationPrefsResponse)
async def update_notification_prefs(
    body: NotificationPrefsUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update the company's notification preferences and Slack webhook URL. Admin only."""
    result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    company.notification_prefs = body.prefs
    company.slack_webhook_url = body.slack_webhook_url

    await audit_service.log_action(
        db=db,
        company_id=current_user.company_id,
        action="company.notification_prefs_updated",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"prefs": body.prefs, "slack_webhook_set": body.slack_webhook_url is not None},
    )
    await db.commit()
    await db.refresh(company)

    return NotificationPrefsResponse(
        prefs=company.notification_prefs or {},
        slack_webhook_url=company.slack_webhook_url,
    )
