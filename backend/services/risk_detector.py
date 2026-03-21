"""Automated risk detection service.

Reads existing data (training, vendors, pen tests, vulnerabilities, integrations,
policies, incidents) and creates Risk entries automatically.  Each detector is
idempotent: it identifies itself with a ``detection_key`` that is unique per
company.  If the risk already exists it is skipped; if the underlying condition
is resolved the risk is NOT automatically deleted (stays for audit trail) but
the detector simply won't re-create it.
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.incident import Incident
from models.integration import Integration
from models.pen_test import PenTest
from models.policy import Policy
from models.risk import Risk
from models.training import TrainingRecord
from models.vendor import Vendor
from models.vulnerability import Vulnerability

logger = logging.getLogger(__name__)

_CLOUD_TYPES = {"aws", "gcp", "azure"}
_IDENTITY_TYPES = {"okta", "google_workspace", "azure_ad"}
_CODE_TYPES = {"github", "gitlab"}


@dataclass
class DetectedRisk:
    detection_key: str
    title: str
    description: str
    category: str
    likelihood: int
    impact: int


# ---------------------------------------------------------------------------
# Individual detectors — each returns a list of DetectedRisk (usually 0 or 1)
# ---------------------------------------------------------------------------

async def _detect_training_overdue(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count()).where(
            TrainingRecord.company_id == company_id,
            TrainingRecord.status != "completed",
            TrainingRecord.due_date < now,
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:training:overdue",
        title="Security training overdue for team members",
        description=f"{count} training assignment(s) are past their due date and not yet completed. Incomplete security awareness training increases the risk of phishing and insider threats.",
        category="Incident Response",
        likelihood=3,
        impact=3,
    )]


async def _detect_training_no_program(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(TrainingRecord.company_id == company_id)
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:training:no_program",
        title="No security awareness training program",
        description="No training records found. SOC 2 and ISO 27001 require annual security awareness training for all personnel.",
        category="Incident Response",
        likelihood=4,
        impact=3,
    )]


async def _detect_vendor_overdue_review(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    result = await db.execute(
        select(func.count()).where(
            Vendor.company_id == company_id,
            (Vendor.review_date == None) | (Vendor.review_date < cutoff),  # noqa: E711
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:vendor:overdue_review",
        title=f"Vendor security reviews overdue ({count} vendor{'s' if count > 1 else ''})",
        description=f"{count} vendor(s) have not been reviewed in over 12 months or have never been reviewed. Annual vendor risk assessments are required for SOC 2 CC9.2.",
        category="Vendor Management",
        likelihood=3,
        impact=3,
    )]


async def _detect_vendor_high_risk_no_cert(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            Vendor.company_id == company_id,
            Vendor.risk_level.in_(["high", "critical"]),
            Vendor.soc2_certified == False,  # noqa: E712
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:vendor:high_risk_no_soc2",
        title=f"High-risk vendor(s) without SOC 2 certification ({count})",
        description=f"{count} vendor(s) rated high or critical risk do not have a SOC 2 certificate on file. This increases supply chain risk.",
        category="Vendor Management",
        likelihood=3,
        impact=4,
    )]


async def _detect_pentest_no_recent(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=365)
    result = await db.execute(
        select(func.count()).where(
            PenTest.company_id == company_id,
            PenTest.status == "completed",
            PenTest.conducted_at >= cutoff,
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:pentest:no_recent",
        title="No penetration test completed in the last 12 months",
        description="SOC 2, ISO 27001, and most enterprise procurement checklists require an annual penetration test. No completed pen test found within the past year.",
        category="Availability",
        likelihood=3,
        impact=4,
    )]


async def _detect_pentest_open_findings(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            PenTest.company_id == company_id,
            PenTest.status == "completed",
            (PenTest.critical_count + PenTest.high_count) > 0,
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:pentest:open_findings",
        title="Unresolved critical/high findings from penetration test",
        description=f"{count} completed pen test(s) have open critical or high severity findings that have not been marked as remediated.",
        category="Availability",
        likelihood=4,
        impact=5,
    )]


async def _detect_vuln_open_critical(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(func.count()).where(
            Vulnerability.company_id == company_id,
            Vulnerability.severity == "critical",
            Vulnerability.status == "open",
            Vulnerability.created_at <= cutoff,
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:vuln:open_critical",
        title=f"Critical vulnerabilities open for over 30 days ({count})",
        description=f"{count} critical severity vulnerability/ies have been open for more than 30 days. Critical vulnerabilities should be remediated within 30 days per most compliance frameworks.",
        category="Data Protection",
        likelihood=4,
        impact=5,
    )]


async def _detect_vuln_open_high(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    result = await db.execute(
        select(func.count()).where(
            Vulnerability.company_id == company_id,
            Vulnerability.severity == "high",
            Vulnerability.status == "open",
            Vulnerability.created_at <= cutoff,
        )
    )
    count = result.scalar() or 0
    if count == 0:
        return []
    return [DetectedRisk(
        detection_key="auto:vuln:open_high",
        title=f"High vulnerabilities open for over 90 days ({count})",
        description=f"{count} high severity vulnerability/ies have been open for more than 90 days without remediation.",
        category="Data Protection",
        likelihood=3,
        impact=4,
    )]


async def _detect_no_cloud_integration(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            Integration.company_id == company_id,
            Integration.integration_type.in_(_CLOUD_TYPES),
            Integration.status == "active",
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:integration:no_cloud",
        title="No cloud provider integration connected",
        description="No active AWS, GCP, or Azure integration found. Without cloud monitoring, configuration drift and misconfigurations cannot be automatically detected.",
        category="Logging & Monitoring",
        likelihood=3,
        impact=3,
    )]


async def _detect_no_identity_integration(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            Integration.company_id == company_id,
            Integration.integration_type.in_(_IDENTITY_TYPES),
            Integration.status == "active",
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:integration:no_identity",
        title="No identity provider integration connected",
        description="No active Okta, Google Workspace, or Azure AD integration found. User access cannot be monitored automatically — offboarding gaps and privilege creep may go undetected.",
        category="Access Control",
        likelihood=3,
        impact=4,
    )]


async def _detect_no_code_integration(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            Integration.company_id == company_id,
            Integration.integration_type.in_(_CODE_TYPES),
            Integration.status == "active",
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:integration:no_code",
        title="No source code repository integration connected",
        description="No active GitHub or GitLab integration found. Code change monitoring and branch protection evidence cannot be collected automatically.",
        category="Change Management",
        likelihood=2,
        impact=3,
    )]


async def _detect_no_incident_policy(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    result = await db.execute(
        select(func.count()).where(
            Policy.company_id == company_id,
            Policy.slug.ilike("%incident%"),
        )
    )
    count = result.scalar() or 0
    if count > 0:
        return []
    return [DetectedRisk(
        detection_key="auto:policy:no_incident_response",
        title="No incident response policy found",
        description="An incident response policy is required for SOC 2 (CC7.3–CC7.5) and ISO 27001. No policy with 'incident' in the name was found.",
        category="Incident Response",
        likelihood=3,
        impact=4,
    )]


async def _detect_recurring_incidents(db: AsyncSession, company_id: uuid.UUID) -> list[DetectedRisk]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    result = await db.execute(
        select(func.count()).where(
            Incident.company_id == company_id,
            Incident.created_at >= cutoff,
        )
    )
    count = result.scalar() or 0
    if count < 3:
        return []
    return [DetectedRisk(
        detection_key="auto:incident:recurring",
        title=f"High incident frequency — {count} incidents in 90 days",
        description=f"{count} incidents recorded in the last 90 days. Recurring incidents may indicate systemic control failures requiring a root-cause review.",
        category="Incident Response",
        likelihood=4,
        impact=4,
    )]


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

_DETECTORS = [
    _detect_training_overdue,
    _detect_training_no_program,
    _detect_vendor_overdue_review,
    _detect_vendor_high_risk_no_cert,
    _detect_pentest_no_recent,
    _detect_pentest_open_findings,
    _detect_vuln_open_critical,
    _detect_vuln_open_high,
    _detect_no_cloud_integration,
    _detect_no_identity_integration,
    _detect_no_code_integration,
    _detect_no_incident_policy,
    _detect_recurring_incidents,
]


async def run_risk_detection_for_company(db: AsyncSession, company_id: uuid.UUID) -> int:
    """Run all detectors for a single company. Returns the number of new risks created."""
    created = 0

    # Fetch existing detection keys for this company to avoid N+1 lookups
    result = await db.execute(
        select(Risk.detection_key).where(
            Risk.company_id == company_id,
            Risk.detection_key != None,  # noqa: E711
        )
    )
    existing_keys = {row[0] for row in result.all()}

    for detector in _DETECTORS:
        try:
            findings = await detector(db, company_id)
        except Exception as exc:
            logger.warning("Detector %s failed for company %s: %s", detector.__name__, company_id, exc)
            continue

        for finding in findings:
            if finding.detection_key in existing_keys:
                continue  # already created

            risk = Risk(
                company_id=company_id,
                title=finding.title,
                description=finding.description,
                category=finding.category,
                likelihood=finding.likelihood,
                impact=finding.impact,
                status="open",
                auto_detected=True,
                detection_key=finding.detection_key,
            )
            db.add(risk)
            existing_keys.add(finding.detection_key)
            created += 1
            logger.info("Auto-detected risk '%s' for company %s", finding.detection_key, company_id)

    if created:
        await db.commit()

    return created


async def run_risk_detection_all_companies() -> None:
    """Entry point for the scheduler — runs detection across all companies."""
    from models.company import Company

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Company.id))
        company_ids = [row[0] for row in result.all()]

    total = 0
    for company_id in company_ids:
        async with AsyncSessionLocal() as db:
            try:
                n = await run_risk_detection_for_company(db, company_id)
                total += n
            except Exception as exc:
                logger.error("Risk detection failed for company %s: %s", company_id, exc)

    logger.info("Risk detection complete — %d new risk(s) across %d company/ies", total, len(company_ids))
