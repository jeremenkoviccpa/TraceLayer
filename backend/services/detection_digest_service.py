"""
Nightly digest email: summarize what auto-detection created overnight.
Runs at 03:00 UTC — after risk detection (02:00) and auto-detection (02:15).
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionFactory
from models.background_check import BackgroundCheck
from models.company import Company
from models.incident import Incident
from models.risk import Risk
from models.training import TrainingRecord
from models.user import User

logger = logging.getLogger(__name__)

_WINDOW_HOURS = 25  # slightly over 24 h to handle minor drift


async def run_detection_digest_for_company(
    db: AsyncSession, company_id
) -> bool:
    """Count overnight auto-detections and email admins. Returns True if sent."""
    since = datetime.now(timezone.utc) - timedelta(hours=_WINDOW_HOURS)

    async def _count(model):
        result = await db.execute(
            select(func.count()).where(
                model.company_id == company_id,
                model.auto_detected == True,  # noqa: E712
                model.created_at >= since,
            )
        )
        return result.scalar() or 0

    risks      = await _count(Risk)
    training   = await _count(TrainingRecord)
    bgchecks   = await _count(BackgroundCheck)
    incidents  = await _count(Incident)
    total      = risks + training + bgchecks + incidents

    if total == 0:
        return False

    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        return False

    admins_result = await db.execute(
        select(User).where(
            User.company_id == company_id,
            User.role.in_(["admin", "owner"]),
        )
    )
    admins = admins_result.scalars().all()
    if not admins:
        return False

    from services.email_service import send_auto_detection_digest

    sent = False
    for admin in admins:
        try:
            send_auto_detection_digest(
                to=admin.email,
                company_name=company.name,
                risks=risks,
                training=training,
                background_checks=bgchecks,
                incidents=incidents,
            )
            sent = True
            logger.info(
                "Detection digest sent: company=%s admin=%s total=%d",
                company.name, admin.email, total,
            )
        except Exception:
            logger.exception("Failed to send detection digest to %s", admin.email)

    return sent


async def run_detection_digest_all_companies() -> None:
    """Scheduler entry point."""
    async with AsyncSessionFactory() as db:
        companies_result = await db.execute(select(Company.id))
        company_ids = [row[0] for row in companies_result.all()]

    sent = 0
    for company_id in company_ids:
        async with AsyncSessionFactory() as db:
            if await run_detection_digest_for_company(db, company_id):
                sent += 1

    logger.info("Detection digest complete: sent to %d companies", sent)
