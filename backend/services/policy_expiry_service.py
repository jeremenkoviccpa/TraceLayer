"""Daily job: check for expiring policies and notify company admins.

Notification thresholds (per policy):
  • 30-day warning  — when expires_at is 30 days away and the policy hasn't been
                      notified yet (expiry_notified_at IS NULL).
  • 7-day warning   — when expires_at is ≤ 7 days away and the last notification
                      was sent more than 7 days ago (catches policies that were
                      already past the 30-day warning).
  • Expired notice  — when expires_at passed within the last 2 days and no
                      notification was sent in the past 2 days.

Each company gets one digest email covering all its qualifying policies.
"""
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def _get_admin_emails(company_id, db: AsyncSession) -> list[str]:
    from models.user import User
    result = await db.execute(
        select(User.email).where(
            User.company_id == company_id,
            User.role == "admin",
        )
    )
    return [row[0] for row in result.all()]


async def run_policy_expiry_checks(db: AsyncSession) -> None:
    """Check all companies for expiring policies and send digest emails to admins."""
    from models.company import Company
    from models.policy import Policy
    from services.email_service import send_policy_expiry_email
    from core.config import settings

    now = datetime.now(timezone.utc)

    # Fetch every policy that has expires_at set
    result = await db.execute(
        select(Policy).where(Policy.expires_at.isnot(None))
    )
    all_policies = result.scalars().all()

    # Group qualifying policies by company
    by_company: dict[str, list[dict]] = {}

    for policy in all_policies:
        expires = policy.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)

        days_remaining = (expires.date() - now.date()).days
        last_notified = policy.expiry_notified_at

        # Determine if this policy qualifies for a notification
        qualifies = False

        if days_remaining < 0:
            # Expired: notify if we haven't sent anything in the past 2 days
            if last_notified is None or (now - last_notified).days >= 2:
                qualifies = True

        elif days_remaining <= 7:
            # Critical: notify if no notification sent in the past 7 days
            if last_notified is None or (now - last_notified).days >= 7:
                qualifies = True

        elif days_remaining <= 30:
            # Warning: notify only if we've never sent a notification for this expiry
            if last_notified is None:
                qualifies = True

        if not qualifies:
            continue

        cid = str(policy.company_id)
        if cid not in by_company:
            by_company[cid] = []
        by_company[cid].append({
            "policy_obj": policy,
            "title": policy.slug.replace("-", " ").title(),  # fallback; overwritten below
            "slug": policy.slug,
            "days_remaining": days_remaining,
        })

    if not by_company:
        logger.info("policy_expiry_checks: no qualifying policies found")
        return

    # Enrich titles from DB and send emails
    for company_id_str, items in by_company.items():
        import uuid as _uuid
        company_id = _uuid.UUID(company_id_str)

        # Fetch company name
        company_result = await db.execute(
            select(Company).where(Company.id == company_id)
        )
        company = company_result.scalar_one_or_none()
        company_name = company.name if company else "your organisation"

        # Fetch admin emails
        admin_emails = await _get_admin_emails(company_id, db)
        if not admin_emails:
            logger.warning("policy_expiry_checks: no admins found for company %s", company_id_str)
            continue

        # Map slug → human title using the API's POLICY_TEMPLATES constant
        try:
            from api.v1.policies import POLICY_TEMPLATES
            for item in items:
                tpl = POLICY_TEMPLATES.get(item["slug"])
                if tpl:
                    item["title"] = tpl["title"]
        except Exception:
            pass  # fall back to slug-derived title

        frontend_url = settings.app_frontend_url.rstrip("/")
        payload = [{"title": i["title"], "slug": i["slug"], "days_remaining": i["days_remaining"]} for i in items]

        for admin_email in admin_emails:
            try:
                send_policy_expiry_email(
                    to=admin_email,
                    company_name=company_name,
                    policies=payload,
                    frontend_url=frontend_url,
                )
                logger.info(
                    "policy_expiry_checks: sent notification to %s for %d policies (company=%s)",
                    admin_email, len(payload), company_id_str,
                )
            except Exception:
                logger.exception(
                    "policy_expiry_checks: failed to send to %s (company=%s)",
                    admin_email, company_id_str,
                )

        # Update expiry_notified_at for all qualifying policies
        for item in items:
            item["policy_obj"].expiry_notified_at = now

    await db.commit()
    logger.info("policy_expiry_checks: done — processed %d companies", len(by_company))


async def run_policy_expiry_all_companies() -> None:
    """Entry point called by APScheduler (creates its own DB session)."""
    from core.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await run_policy_expiry_checks(db)
