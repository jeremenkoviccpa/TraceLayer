"""
Daily compliance alert service.

Checks all companies for overdue training, access reviews, vendor reviews,
and stale evidence — then sends a digest email (and optional Slack message)
to each admin.
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.access_review import AccessReview
from models.company import Company
from models.integration import Integration
from models.training import TrainingRecord
from models.user import User
from models.vendor import Vendor

logger = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "training_overdue": True,
    "access_review_overdue": True,
    "vendor_needs_review": True,
    "evidence_stale": True,
    "weekly_digest": True,
    "control_failing": True,
}

ALERT_LABELS = {
    "training_overdue": "Overdue Training",
    "access_review_overdue": "Overdue Access Reviews",
    "vendor_needs_review": "Vendors Needing Review",
    "evidence_stale": "Stale Evidence Collection",
    "control_failing": "Failing Compliance Controls",
}

MONITORED_FRAMEWORKS = ["soc2", "iso27001", "hipaa", "gdpr", "pci_dss", "ccpa", "nist_csf", "dpdp", "cert_in", "lpdp", "nis2"]


async def _check_training_overdue(db: AsyncSession, company_id) -> list[str]:
    result = await db.execute(
        select(TrainingRecord).where(
            and_(
                TrainingRecord.company_id == company_id,
                TrainingRecord.status == "overdue",
            )
        )
    )
    records = result.scalars().all()
    return [
        f"{r.assignee_name or r.assignee_email} — {r.title}"
        for r in records
    ]


async def _check_access_review_overdue(db: AsyncSession, company_id) -> list[str]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(AccessReview).where(
            and_(
                AccessReview.company_id == company_id,
                AccessReview.status != "completed",
                AccessReview.due_date < now,
            )
        )
    )
    records = result.scalars().all()
    return [
        f"{r.title} ({r.period})"
        for r in records
    ]


async def _check_vendor_needs_review(db: AsyncSession, company_id) -> list[str]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=365)
    result = await db.execute(
        select(Vendor).where(
            and_(
                Vendor.company_id == company_id,
                (Vendor.review_date.is_(None)) | (Vendor.review_date < cutoff),
            )
        )
    )
    records = result.scalars().all()
    return [r.name for r in records]


async def _check_evidence_stale(db: AsyncSession, company_id) -> list[str]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=48)
    result = await db.execute(
        select(Integration).where(
            and_(
                Integration.company_id == company_id,
                Integration.status == "active",
                (Integration.last_collected_at.is_(None)) | (Integration.last_collected_at < cutoff),
            )
        )
    )
    records = result.scalars().all()
    return [r.integration_type for r in records]


async def _check_failing_controls(db: AsyncSession, company_id) -> list[dict]:
    """Return failing controls across all frameworks for this company."""
    from services.compliance_service import get_compliance_score
    from services.audit_package_service import FRAMEWORK_LABELS

    failing = []
    for fw in MONITORED_FRAMEWORKS:
        try:
            score_data = await get_compliance_score(company_id, fw, db)
            for c in score_data.get("controls", []):
                if c["status"] == "failing":
                    failing.append({
                        "name": c["name"],
                        "score": c["score"],
                        "missing_types": c.get("missing_types", []),
                        "framework": fw,
                        "framework_label": FRAMEWORK_LABELS.get(fw, fw.upper()),
                    })
        except Exception:
            pass
    return failing


async def send_slack_alert(webhook_url: str, company_name: str, alerts: list[dict]) -> None:
    """Send a Slack message via incoming webhook."""
    lines = [f"*TraceLayer Alert — {company_name}*"]
    for alert in alerts:
        lines.append(f"• {alert['label']}: {alert['count']} item(s)")
    text = "\n".join(lines)
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json={"text": text}, timeout=10)


async def send_teams_alert(webhook_url: str, company_name: str, alerts: list[dict]) -> None:
    """Send a Microsoft Teams message via incoming webhook (Adaptive Card)."""
    facts = [{"title": a["label"], "value": f"{a['count']} item(s)"} for a in alerts]
    payload = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": f"TraceLayer Alert — {company_name}", "weight": "bolder", "size": "medium"},
                    {"type": "FactSet", "facts": facts},
                ],
            },
        }],
    }
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=payload, timeout=10)


async def run_daily_alerts(db: AsyncSession) -> None:
    """Check all companies for alert conditions and send notifications."""
    from services.email_service import send_alert_digest

    # Fetch all companies
    companies_result = await db.execute(select(Company))
    companies = companies_result.scalars().all()

    for company in companies:
        try:
            # Get admin users for this company
            admins_result = await db.execute(
                select(User).where(
                    and_(
                        User.company_id == company.id,
                        User.role == "admin",
                    )
                )
            )
            admins = admins_result.scalars().all()
            if not admins:
                continue

            prefs = {**DEFAULT_PREFS, **(company.notification_prefs or {})}
            alerts: list[dict] = []

            if prefs.get("training_overdue"):
                items = await _check_training_overdue(db, company.id)
                if items:
                    alerts.append({
                        "type": "training_overdue",
                        "label": ALERT_LABELS["training_overdue"],
                        "count": len(items),
                        "items": items,
                    })

            if prefs.get("access_review_overdue"):
                items = await _check_access_review_overdue(db, company.id)
                if items:
                    alerts.append({
                        "type": "access_review_overdue",
                        "label": ALERT_LABELS["access_review_overdue"],
                        "count": len(items),
                        "items": items,
                    })

            if prefs.get("vendor_needs_review"):
                items = await _check_vendor_needs_review(db, company.id)
                if items:
                    alerts.append({
                        "type": "vendor_needs_review",
                        "label": ALERT_LABELS["vendor_needs_review"],
                        "count": len(items),
                        "items": items,
                    })

            if prefs.get("evidence_stale"):
                items = await _check_evidence_stale(db, company.id)
                if items:
                    alerts.append({
                        "type": "evidence_stale",
                        "label": ALERT_LABELS["evidence_stale"],
                        "count": len(items),
                        "items": items,
                    })

            # Check failing controls and send dedicated alerts (not bundled in digest)
            if prefs.get("control_failing"):
                failing_controls = await _check_failing_controls(db, company.id)
                if failing_controls:
                    from services.email_service import send_control_break_alert
                    from services.audit_package_service import FRAMEWORK_LABELS
                    # Group by framework
                    by_fw: dict[str, list] = {}
                    for c in failing_controls:
                        by_fw.setdefault(c["framework"], []).append(c)
                    for fw, fw_controls in by_fw.items():
                        fw_label = FRAMEWORK_LABELS.get(fw, fw.upper())
                        for admin in admins:
                            try:
                                send_control_break_alert(
                                    to=admin.email,
                                    company_name=company.name,
                                    framework_label=fw_label,
                                    failing_controls=fw_controls,
                                    frontend_url=settings.app_frontend_url,
                                )
                            except Exception as exc:
                                logger.warning("Failed to send control break alert to %s: %s", admin.email, exc)

            if not alerts:
                continue

            # Send digest email to each admin
            for admin in admins:
                try:
                    send_alert_digest(
                        to=admin.email,
                        company_name=company.name,
                        alerts=alerts,
                        frontend_url=settings.app_frontend_url,
                    )
                except Exception as exc:
                    logger.warning(
                        "Failed to send alert digest to %s: %s", admin.email, exc
                    )

            # Send Slack notification if configured
            if company.slack_webhook_url:
                try:
                    await send_slack_alert(
                        webhook_url=company.slack_webhook_url,
                        company_name=company.name,
                        alerts=alerts,
                    )
                except Exception as exc:
                    logger.warning("Failed to send Slack alert for company %s: %s", company.id, exc)

            # Send Teams notification if configured
            if company.teams_webhook_url:
                try:
                    await send_teams_alert(
                        webhook_url=company.teams_webhook_url,
                        company_name=company.name,
                        alerts=alerts,
                    )
                except Exception as exc:
                    logger.warning("Failed to send Teams alert for company %s: %s", company.id, exc)

        except Exception as exc:
            logger.error(
                "Error processing daily alerts for company %s: %s", company.id, exc,
                exc_info=True,
            )


async def run_daily_alerts_job() -> None:
    """Entry point for the APScheduler cron job."""
    from core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        await run_daily_alerts(db)
