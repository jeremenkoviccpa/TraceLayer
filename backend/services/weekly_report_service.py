"""
Weekly compliance digest emails.
Runs every Monday at 09:00 UTC via APScheduler.
"""
import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from core.database import AsyncSessionLocal
from models.company import Company
from models.user import User
from services.compliance_service import get_compliance_score
from services.email_service import send_weekly_compliance_report
from core.config import settings

logger = logging.getLogger(__name__)

FRAMEWORKS = [
    {"value": "soc2",      "label": "SOC 2"},
    {"value": "iso27001",  "label": "ISO 27001"},
    {"value": "hipaa",     "label": "HIPAA"},
    {"value": "gdpr",      "label": "GDPR"},
    {"value": "pci_dss",   "label": "PCI DSS"},
    {"value": "ccpa",      "label": "CCPA"},
    {"value": "nist_csf",  "label": "NIST CSF"},
    {"value": "dpdp",      "label": "DPDP Act"},
    {"value": "cert_in",   "label": "CERT-In"},
    {"value": "lpdp",      "label": "Serbian LPDP"},
    {"value": "nis2",      "label": "NIS2"},
    {"value": "iso42001",  "label": "ISO 42001"},
]


def _week_label() -> str:
    today = datetime.now(timezone.utc)
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    fmt = "%b %-d"
    return f"{monday.strftime(fmt)} – {sunday.strftime(fmt)}, {sunday.year}"


async def send_weekly_reports() -> None:
    """Fetch all companies, compute scores, send digest emails to admin users."""
    logger.info("Starting weekly compliance report job")
    week = _week_label()

    async with AsyncSessionLocal() as db:
        companies = (await db.execute(select(Company))).scalars().all()
        for company in companies:
            try:
                # Fetch admin users
                admins = (await db.execute(
                    select(User).where(
                        User.company_id == company.id,
                        User.role == "admin",
                        User.email_verified == True,
                    )
                )).scalars().all()

                if not admins:
                    continue

                # Compute scores for all frameworks
                framework_scores = []
                for fw in FRAMEWORKS:
                    score_data = await get_compliance_score(company.id, fw["value"], db)
                    framework_scores.append({
                        "framework": fw["value"],
                        "label": fw["label"],
                        "score": score_data["overall_score"],
                        "controls": score_data["controls"],
                    })

                # Send to each admin
                for admin in admins:
                    send_weekly_compliance_report(
                        to=admin.email,
                        company_name=company.name,
                        framework_scores=framework_scores,
                        week_label=week,
                        frontend_url=settings.app_frontend_url,
                    )
                    logger.info("Sent weekly report to %s (company: %s)", admin.email, company.name)

            except Exception as exc:
                logger.error("Weekly report failed for company %s: %s", company.id, exc)

    logger.info("Weekly compliance report job complete")
