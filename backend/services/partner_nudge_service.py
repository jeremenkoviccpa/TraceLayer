"""
Send Day 1 / Day 3 / Day 7 onboarding nudge emails to partner admin users
who registered N days ago and still haven't added their first client.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.company import Company
from models.partner_client_payment import PartnerClientPayment
from models.user import User
from services import email_service

logger = logging.getLogger(__name__)


async def _partner_admins_in_window(db, days_ago: int) -> list[User]:
    """Return partner admin users whose account is ~N days old (±1 h window)."""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days_ago) - timedelta(hours=1)
    window_end   = now - timedelta(days=days_ago) + timedelta(hours=1)

    result = await db.execute(
        select(User)
        .join(Company, Company.id == User.company_id)
        .where(User.role == "admin")
        .where(Company.is_partner_account.is_(True))
        .where(User.created_at >= window_start)
        .where(User.created_at <= window_end)
    )
    return result.scalars().all()


async def _client_count(db, partner_company_id) -> int:
    """Return number of client workspaces the partner has provisioned."""
    result = await db.execute(
        select(PartnerClientPayment)
        .where(PartnerClientPayment.partner_company_id == partner_company_id)
        .where(PartnerClientPayment.client_company_id.isnot(None))
    )
    return len(result.scalars().all())


async def send_partner_nudges() -> None:
    """
    Scheduled daily job. Sends Day 1, 3, 7 partner onboarding nudges to partner
    admin users who have not yet provisioned their first client workspace.
    """
    async with AsyncSessionLocal() as db:
        for day, flag in [
            (1, "partner_nudge_day1_sent"),
            (3, "partner_nudge_day3_sent"),
            (7, "partner_nudge_day7_sent"),
        ]:
            users = await _partner_admins_in_window(db, day)
            for user in users:
                if getattr(user, flag):
                    continue  # already sent
                count = await _client_count(db, user.company_id)
                if count > 0:
                    # They've added a client — mark flag, skip email
                    setattr(user, flag, True)
                    continue
                try:
                    email_service.send_partner_nudge_email(user.email, day=day, client_count=count)
                    setattr(user, flag, True)
                    logger.info("Sent partner Day %d nudge to %s", day, user.email)
                except Exception:
                    logger.exception("Failed to send partner Day %d nudge to %s", day, user.email)

        await db.commit()
