"""
Send Day 1 / Day 3 / Day 7 activation nudge emails to admin users
who registered N days ago and still haven't connected any integration.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.integration import Integration
from models.user import User
from services import email_service

logger = logging.getLogger(__name__)


async def _admins_in_window(db, days_ago: int) -> list[User]:
    """Return admin users whose account is ~N days old (±1 h window)."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days_ago) - timedelta(hours=1)
    window_end = now - timedelta(days=days_ago) + timedelta(hours=1)

    result = await db.execute(
        select(User)
        .where(User.role == "admin")
        .where(User.created_at >= window_start)
        .where(User.created_at <= window_end)
    )
    return result.scalars().all()


async def _has_active_integration(db, company_id) -> bool:
    result = await db.execute(
        select(Integration)
        .where(Integration.company_id == company_id)
        .where(Integration.status == "active")
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def send_activation_nudges() -> None:
    """
    Scheduled daily job. Checks for admin users at the Day 1, 3, 7 marks
    who have no active integration and haven't received that nudge yet.
    """
    async with AsyncSessionLocal() as db:
        for day, flag in [(1, "nudge_day1_sent"), (3, "nudge_day3_sent"), (7, "nudge_day7_sent")]:
            users = await _admins_in_window(db, day)
            for user in users:
                if getattr(user, flag):
                    continue  # already sent
                if await _has_active_integration(db, user.company_id):
                    # They connected — mark sent so we don't check again, skip email
                    setattr(user, flag, True)
                    continue
                try:
                    email_service.send_activation_nudge_email(user.email, day=day)
                    setattr(user, flag, True)
                    logger.info("Sent Day %d nudge to %s", day, user.email)
                except Exception:
                    logger.exception("Failed to send Day %d nudge to %s", day, user.email)

        await db.commit()
