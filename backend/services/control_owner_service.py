"""
Weekly reminder emails to control owners with pending manual controls.
Runs every Monday at 09:30 UTC (after the weekly compliance digest at 09:00).
"""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.company import Company
from models.manual_control import ManualControl
from models.user import User

logger = logging.getLogger(__name__)


async def run_control_owner_reminders_for_company(
    db: AsyncSession, company_id
) -> int:
    """Send reminder emails to each owner with pending controls. Returns emails sent."""
    company_result = await db.execute(select(Company).where(Company.id == company_id))
    company = company_result.scalar_one_or_none()
    if not company:
        return 0

    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == company_id,
            ManualControl.status == "pending",
            ManualControl.owner_user_id.isnot(None),
        )
    )
    pending = result.scalars().all()
    if not pending:
        return 0

    by_owner: dict[str, list[dict]] = defaultdict(list)
    for ctrl in pending:
        by_owner[str(ctrl.owner_user_id)].append({
            "name": ctrl.control_id,
            "framework": ctrl.framework.upper().replace("_", " "),
        })

    owner_ids = list(by_owner.keys())
    users_result = await db.execute(
        select(User.id, User.email, User.full_name).where(User.id.in_(owner_ids))
    )

    sent = 0
    for row in users_result.all():
        controls = by_owner[str(row.id)]
        try:
            from services.email_service import send_control_owner_reminder
            send_control_owner_reminder(
                to=row.email,
                owner_name=row.full_name or row.email.split("@")[0],
                company_name=company.name,
                controls=controls,
            )
            sent += 1
            logger.info(
                "Control owner reminder sent: user=%s controls=%d company=%s",
                row.email, len(controls), company.name,
            )
        except Exception:
            logger.exception("Failed to send control owner reminder to %s", row.email)

    return sent


async def run_control_owner_reminders() -> None:
    """Scheduler entry point — runs weekly across all companies."""
    async with AsyncSessionLocal() as db:
        companies_result = await db.execute(select(Company.id))
        company_ids = [row[0] for row in companies_result.all()]

    total_sent = 0
    for company_id in company_ids:
        async with AsyncSessionLocal() as db:
            sent = await run_control_owner_reminders_for_company(db, company_id)
            total_sent += sent

    logger.info(
        "Control owner reminders complete: %d emails sent across %d companies",
        total_sent, len(company_ids),
    )
