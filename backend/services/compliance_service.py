import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from models.control import Control
from models.evidence import Evidence
from models.score_snapshot import ScoreSnapshot

# Expected evidence types per framework per control category.
# Coverage score = how many expected types are present in collected evidence.
EXPECTED_TYPES: dict[str, dict[str, set[str]]] = {
    "soc2": {
        "access_control": {
            "iam_users", "iam_policies",
            "github_members", "github_admin_members",
            "slack_users", "slack_workspace",
            "workspace_users", "workspace_admin_members",
            "okta_users", "okta_groups",
            "azure_users", "azure_roles",
            "jira_users",
        },
        "logging_monitoring": {"cloudtrail_logs"},
        "change_management": {"repositories", "jira_projects"},
    },
    "iso27001": {
        "access_control": {
            "iam_users", "iam_policies",
            "github_members", "github_admin_members",
            "slack_users",
            "workspace_users", "workspace_admin_members",
            "okta_users", "okta_groups",
            "azure_users", "azure_roles",
        },
        "operations_security": {"cloudtrail_logs"},
        "communications_security": {"slack_workspace", "slack_users", "workspace_groups"},
        "change_management": {"repositories", "jira_projects"},
    },
    "hipaa": {
        "access_control": {
            "iam_users", "iam_policies",
            "workspace_users", "okta_users", "azure_users",
        },
        "audit_controls": {"cloudtrail_logs"},
        "workforce_security": {
            "github_members", "slack_users",
            "workspace_users", "okta_users", "jira_users",
        },
    },
    "dpdp": {
        # Sec.4-7: Lawful basis, consent records, notice — India-specific consent
        # management tools are primary evidence; DLP + IAM as supporting evidence
        "lawful_processing": {
            "leegality_documents", "leegality_templates",
            "digilocker_documents", "digilocker_issued_documents",
            "signzy_verifications",
            "nightfall_policies", "nightfall_detectors",
            "okta_users", "azure_users", "workspace_users",
            "iam_policies",
        },
        # Sec.8, 8.3, 10: Security safeguards, data erasure, processor agreements
        "data_fiduciary_obligations": {
            "cloudtrail_logs",
            "iam_policies", "iam_users",
            "nightfall_policies", "nightfall_detectors",
            "wiz_issues",
            "crowdstrike_policies", "sentinelone_agents",
            "github_repositories",
        },
        # Sec.9: Children's data — DLP + identity/age-verification integrations
        "special_categories": {
            "nightfall_policies", "nightfall_detectors",
            "iam_policies", "okta_policies",
            "signzy_verifications",
        },
        # Sec.11-14, 17: DSR records are primary evidence — auto-generated
        # from Subject Requests module completions; supplemented by ticketing
        "data_principal_rights": {
            "dsr_records",
            "jira_projects", "servicenow_incidents",
            "okta_users", "workspace_users", "azure_users",
        },
        # Sec.8.6: DPBI breach notification records + detection capabilities
        "breach_notification": {
            "dpbi_notifications",
            "pagerduty_incidents", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_escalations",
            "sentinelone_threats", "wiz_issues",
            "cloudtrail_logs",
        },
        # Sec.16: Cross-border transfer controls — network policies + cloud region
        "cross_border_transfers": {
            "cloudflare_security_settings", "cloudflare_zones",
            "tailscale_acl",
            "iam_policies",
            "cloudtrail_logs",
        },
    },
    "cert_in": {
        # Dir.1, 5: 6-hour incident reporting — ticketing and on-call platforms
        # are primary evidence; certin_incidents is a native evidence type
        # generated when incidents are filed with CERT-In from the Incidents module
        "incident_reporting": {
            "certin_incidents",
            "pagerduty_services", "pagerduty_incidents",
            "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_escalations", "opsgenie_schedules",
        },
        # Dir.2, 12: NTP sync evidenced through timestamped audit logs;
        # cloud posture + hardening evidenced through security tools
        "it_infrastructure": {
            "cloudtrail_logs",
            "iam_policies",
            "network_policies", "pods",
            "wiz_issues",
            "crowdstrike_policies",
            "github_repositories",
        },
        # Dir.3: 180-day log retention — SIEM + CloudTrail are primary evidence;
        # Indian jurisdiction confirmed through storage region configuration
        "log_management": {
            "cloudtrail_logs",
            "splunk_saved_searches", "splunk_alerts",
            "datadog_monitors",
            "datadog_logs",
        },
        # Dir.4: KYC for VPS/VPN/cloud/DC providers — India-specific identity
        # verification tools are primary; IAM user records as supporting evidence
        "identity_verification": {
            "signzy_verifications",
            "okta_users", "azure_users",
            "workspace_users", "jira_users",
            "iam_users",
        },
        # Dir.6: Incident response plan — escalation policies, schedules, and
        # change records demonstrate a documented and tested IRP
        "incident_response": {
            "pagerduty_escalation_policies", "pagerduty_schedules", "pagerduty_services",
            "servicenow_incidents", "servicenow_changes",
            "opsgenie_schedules", "opsgenie_escalations",
        },
        # Dir.7: VA/PT + advisory response — scan results and exploit management
        "vulnerability_management": {
            "snyk_projects",
            "vulnerability_scans", "assets",
            "wiz_issues",
            "hackerone_reports", "hackerone_programs",
            "detectify_findings", "detectify_scan_profiles",
            "crowdstrike_detections",
            "github_repositories",
        },
        # Dir.8: MFA + PAM — all identity platforms with MFA/policy evidence;
        # vault for privileged access session logging
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "workspace_users",
            "mfa_policies", "mfa_enrollments",
            "vault_auth_method", "vault_policy",
        },
        # Dir.9: Backups + BCP/DR — uptime monitoring and change records
        # demonstrate backup and continuity posture
        "resilience": {
            "pagerduty_services",
            "servicenow_changes",
            "vault_secrets_engine",
            "datadog_monitors",
            "datadog_slos",
        },
        # Dir.10: Continuous monitoring — SIEM, EDR, and cloud posture tools
        "monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_alerts",
            "crowdstrike_detections",
            "sentinelone_threats",
            "wiz_issues",
            "network_policies",
        },
        # Dir.11: Endpoint protection + MDM + encryption enforcement
        "endpoint_security": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers", "jamf_policies",
            "kandji_devices", "kandji_blueprints",
            "tailscale_devices",
        },
    },
}


def _compute_score(
    covered: set[str],
    expected: set[str],
    latest: Optional[datetime],
    total_count: int,
    reference: Optional[datetime] = None,
) -> int:
    if not expected:
        return 0

    coverage_ratio = len(covered) / len(expected)
    score = coverage_ratio * 70  # up to 70 from coverage

    # Recency bonus (up to 20) — relative to `reference` (defaults to now)
    if latest:
        ref = reference or datetime.now(timezone.utc)
        latest_tz = latest.replace(tzinfo=timezone.utc) if latest.tzinfo is None else latest
        age_days = (ref - latest_tz).days
        if age_days <= 7:
            score += 20
        elif age_days <= 30:
            score += 10

    # Volume bonus (up to 10)
    if total_count >= 10:
        score += 10
    elif total_count >= 3:
        score += 5

    return min(100, int(score))


async def get_compliance_score(
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
) -> dict:
    controls_result = await db.execute(
        select(Control).where(Control.framework == framework)
    )
    controls = list(controls_result.scalars().all())

    # Aggregate evidence by control + evidence_type
    rows = await db.execute(
        select(
            Evidence.control,
            Evidence.evidence_type,
            func.count().label("cnt"),
            func.max(Evidence.timestamp).label("latest"),
        )
        .where(Evidence.company_id == company_id)
        .group_by(Evidence.control, Evidence.evidence_type)
    )

    # Build lookup: control_category -> {types, count, latest}
    by_control: dict[str, dict] = {}
    for row in rows:
        entry = by_control.setdefault(row.control, {"types": set(), "count": 0, "latest": None})
        entry["types"].add(row.evidence_type)
        entry["count"] += row.cnt
        if row.latest and (entry["latest"] is None or row.latest > entry["latest"]):
            entry["latest"] = row.latest

    control_scores = []
    total = 0

    for control in controls:
        ev = by_control.get(control.category, {"types": set(), "count": 0, "latest": None})
        covered = ev["types"]
        count = ev["count"]
        latest = ev["latest"]
        expected = EXPECTED_TYPES.get(framework, {}).get(control.category, set())

        score = _compute_score(covered, expected, latest, count)

        if count == 0:
            status = "no_evidence"
        elif score >= 80:
            status = "passing"
        elif score >= 50:
            status = "warning"
        else:
            status = "failing"

        control_scores.append({
            "category": control.category,
            "name": control.name,
            "score": score,
            "status": status,
            "evidence_count": count,
            "covered_types": sorted(covered),
            "missing_types": sorted(expected - covered),
            "last_collected": latest.isoformat() if latest else None,
        })
        total += score

    overall = int(total / len(control_scores)) if control_scores else 0

    # Snapshot at most once per hour per company+framework
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    existing = await db.execute(
        select(ScoreSnapshot.id)
        .where(
            ScoreSnapshot.company_id == company_id,
            ScoreSnapshot.framework == framework,
            ScoreSnapshot.snapshot_at >= cutoff,
        )
        .limit(1)
    )
    if not existing.scalar():
        db.add(ScoreSnapshot(
            company_id=company_id,
            framework=framework,
            overall_score=overall,
            snapshot_at=datetime.now(timezone.utc),
        ))
        await db.commit()

    return {
        "framework": framework,
        "overall_score": overall,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "controls": control_scores,
    }


async def get_score_history(
    company_id: uuid.UUID,
    framework: str,
    days: int,
    db: AsyncSession,
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await db.execute(
        select(ScoreSnapshot.overall_score, ScoreSnapshot.snapshot_at)
        .where(
            ScoreSnapshot.company_id == company_id,
            ScoreSnapshot.framework == framework,
            ScoreSnapshot.snapshot_at >= since,
        )
        .order_by(ScoreSnapshot.snapshot_at)
    )
    return [
        {"score": row.overall_score, "ts": row.snapshot_at.isoformat()}
        for row in rows
    ]


async def get_compliance_score_at(
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
    as_of: datetime,
) -> dict:
    """
    Point-in-time compliance score. Filters evidence to records that existed
    at `as_of` (Evidence.created_at <= as_of) and computes the score using
    `as_of` as the recency reference, so the result reflects compliance state
    on that exact date rather than today.
    """
    controls_result = await db.execute(
        select(Control).where(Control.framework == framework)
    )
    controls = list(controls_result.scalars().all())

    # Ensure as_of is timezone-aware
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    rows = await db.execute(
        select(
            Evidence.control,
            Evidence.evidence_type,
            func.count().label("cnt"),
            func.max(Evidence.timestamp).label("latest"),
        )
        .where(
            Evidence.company_id == company_id,
            Evidence.created_at <= as_of,
        )
        .group_by(Evidence.control, Evidence.evidence_type)
    )

    by_control: dict[str, dict] = {}
    for row in rows:
        entry = by_control.setdefault(row.control, {"types": set(), "count": 0, "latest": None})
        entry["types"].add(row.evidence_type)
        entry["count"] += row.cnt
        if row.latest and (entry["latest"] is None or row.latest > entry["latest"]):
            entry["latest"] = row.latest

    control_scores = []
    total = 0

    for control in controls:
        ev = by_control.get(control.category, {"types": set(), "count": 0, "latest": None})
        covered = ev["types"]
        count = ev["count"]
        latest = ev["latest"]
        expected = EXPECTED_TYPES.get(framework, {}).get(control.category, set())

        score = _compute_score(covered, expected, latest, count, reference=as_of)

        if count == 0:
            status = "no_evidence"
        elif score >= 80:
            status = "passing"
        elif score >= 50:
            status = "warning"
        else:
            status = "failing"

        control_scores.append({
            "category": control.category,
            "name": control.name,
            "score": score,
            "status": status,
            "evidence_count": count,
            "covered_types": sorted(covered),
            "missing_types": sorted(expected - covered),
            "last_collected": latest.isoformat() if latest else None,
        })
        total += score

    overall = int(total / len(control_scores)) if control_scores else 0

    return {
        "framework": framework,
        "overall_score": overall,
        "evaluated_at": as_of.isoformat(),
        "controls": control_scores,
    }


async def take_daily_snapshots_all_companies() -> None:
    """
    Nightly job: persist one ScoreSnapshot per company per framework so the
    time-machine endpoint always has dense historical data even for companies
    that haven't opened the dashboard recently.
    """
    import logging
    from models.company import Company
    from core.database import AsyncSessionLocal

    logger = logging.getLogger(__name__)
    frameworks = list(EXPECTED_TYPES.keys())
    now = datetime.now(timezone.utc)
    # Use midnight (start of day) as the canonical snapshot time
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        async with AsyncSessionLocal() as db:
            company_ids_result = await db.execute(select(Company.id))
            company_ids = [row[0] for row in company_ids_result.all()]

        for company_id in company_ids:
            for fw in frameworks:
                try:
                    async with AsyncSessionLocal() as db:
                        # Skip if a snapshot already exists for today
                        existing = await db.execute(
                            select(ScoreSnapshot.id)
                            .where(
                                ScoreSnapshot.company_id == company_id,
                                ScoreSnapshot.framework == fw,
                                ScoreSnapshot.snapshot_at >= today_midnight,
                            )
                            .limit(1)
                        )
                        if existing.scalar():
                            continue

                        result = await get_compliance_score_at(
                            company_id, fw, db, as_of=now
                        )
                        db.add(ScoreSnapshot(
                            company_id=company_id,
                            framework=fw,
                            overall_score=result["overall_score"],
                            snapshot_at=now,
                        ))
                        await db.commit()
                except Exception as exc:
                    logger.warning(
                        "Daily snapshot failed for company=%s fw=%s: %s",
                        company_id, fw, exc,
                    )
    except Exception as exc:
        logger.error("Daily snapshot job failed: %s", exc)


async def get_evidence_activity(
    company_id: uuid.UUID,
    days: int,
    db: AsyncSession,
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await db.execute(
        select(
            cast(Evidence.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(Evidence.company_id == company_id, Evidence.created_at >= since)
        .group_by(cast(Evidence.created_at, Date))
        .order_by(cast(Evidence.created_at, Date))
    )
    return [{"day": str(row.day), "count": row.cnt} for row in rows]
