"""Auto-detection service for training assignments and background checks.

Scans the company's user list and creates pending records for team members
who are missing required compliance entries.  All records are idempotent
via ``detection_key`` (unique per company + user).
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.background_check import BackgroundCheck
from models.training import TrainingRecord
from models.user import User

logger = logging.getLogger(__name__)

_TRAINING_TITLE = "Annual Security Awareness Training"


async def run_training_detection_for_company(db: AsyncSession, company_id: uuid.UUID) -> int:
    """Create pending training assignments for users with no training record at all."""
    # Get all users in the company
    users_result = await db.execute(
        select(User.id, User.email, User.full_name).where(User.company_id == company_id)
    )
    users = users_result.all()
    if not users:
        return 0

    # Get existing detection keys for this company
    existing_result = await db.execute(
        select(TrainingRecord.detection_key).where(
            TrainingRecord.company_id == company_id,
            TrainingRecord.detection_key != None,  # noqa: E711
        )
    )
    existing_keys = {row[0] for row in existing_result.all()}

    # Also check emails already covered by ANY training (manual or auto)
    covered_result = await db.execute(
        select(TrainingRecord.assignee_email).where(TrainingRecord.company_id == company_id)
    )
    covered_emails = {row[0] for row in covered_result.all()}

    created = 0
    due = datetime.now(timezone.utc) + timedelta(days=30)

    for user_id, email, full_name in users:
        detection_key = f"auto:training:assign:{user_id}"
        if detection_key in existing_keys:
            continue
        if email in covered_emails:
            existing_keys.add(detection_key)  # mark as handled
            continue

        record = TrainingRecord(
            company_id=company_id,
            assignee_email=email,
            assignee_name=full_name or email,
            title=_TRAINING_TITLE,
            description="Annual security awareness training required for SOC 2 CC1.4 compliance.",
            due_date=due,
            annual=True,
            status="pending",
            auto_detected=True,
            detection_key=detection_key,
        )
        db.add(record)
        existing_keys.add(detection_key)
        covered_emails.add(email)
        created += 1
        logger.info("Auto-created training assignment for %s (company %s)", email, company_id)

    if created:
        await db.commit()

    return created


async def run_background_check_detection_for_company(db: AsyncSession, company_id: uuid.UUID) -> int:
    """Create pending background check records for users with no background check on file."""
    users_result = await db.execute(
        select(User.id, User.email, User.full_name).where(User.company_id == company_id)
    )
    users = users_result.all()
    if not users:
        return 0

    # Existing detection keys
    existing_result = await db.execute(
        select(BackgroundCheck.detection_key).where(
            BackgroundCheck.company_id == company_id,
            BackgroundCheck.detection_key != None,  # noqa: E711
        )
    )
    existing_keys = {row[0] for row in existing_result.all()}

    # Emails already covered by ANY background check
    covered_result = await db.execute(
        select(BackgroundCheck.employee_email).where(
            BackgroundCheck.company_id == company_id,
            BackgroundCheck.employee_email != None,  # noqa: E711
        )
    )
    covered_emails = {row[0] for row in covered_result.all()}

    created = 0

    for user_id, email, full_name in users:
        detection_key = f"auto:bgcheck:assign:{user_id}"
        if detection_key in existing_keys:
            continue
        if email in covered_emails:
            existing_keys.add(detection_key)
            continue

        check = BackgroundCheck(
            company_id=company_id,
            employee_name=full_name or email,
            employee_email=email,
            check_type="standard",
            status="pending",
            notes="Auto-flagged: no background check on file for this team member.",
            auto_detected=True,
            detection_key=detection_key,
        )
        db.add(check)
        existing_keys.add(detection_key)
        covered_emails.add(email)
        created += 1
        logger.info("Auto-created background check record for %s (company %s)", email, company_id)

    if created:
        await db.commit()

    return created


async def run_auto_detection_all_companies() -> None:
    """Nightly scheduler entry point — runs training + background check detection for all companies."""
    from models.company import Company

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Company.id))
        company_ids = [row[0] for row in result.all()]

    training_total = 0
    bgcheck_total = 0

    for company_id in company_ids:
        async with AsyncSessionLocal() as db:
            try:
                training_total += await run_training_detection_for_company(db, company_id)
                bgcheck_total += await run_background_check_detection_for_company(db, company_id)
            except Exception as exc:
                logger.error("Auto-detection failed for company %s: %s", company_id, exc)

    logger.info(
        "Auto-detection complete — %d training + %d background check record(s) across %d company/ies",
        training_total, bgcheck_total, len(company_ids),
    )
