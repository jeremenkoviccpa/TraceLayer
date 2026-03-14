import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.control import Control
from models.evidence import Evidence

# Expected evidence types per control category.
# Coverage score is based on how many of these are present.
EXPECTED_TYPES: dict[str, set[str]] = {
    "access_control": {
        "iam_users",
        "iam_policies",
        "github_members",
        "github_admin_members",
        "slack_users",
        "slack_workspace",
    },
    "logging_monitoring": {"cloudtrail_logs"},
    "change_management": {"repositories"},
}


def _compute_score(
    covered: set[str],
    expected: set[str],
    latest: Optional[datetime],
    total_count: int,
) -> int:
    if not expected:
        return 0

    coverage_ratio = len(covered) / len(expected)
    score = coverage_ratio * 70  # up to 70 from coverage

    # Recency bonus (up to 20)
    if latest:
        age_days = (datetime.now(timezone.utc) - latest.replace(tzinfo=timezone.utc) if latest.tzinfo is None else datetime.now(timezone.utc) - latest).days
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
        expected = EXPECTED_TYPES.get(control.category, set())

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

    return {
        "framework": framework,
        "overall_score": overall,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "controls": control_scores,
    }
