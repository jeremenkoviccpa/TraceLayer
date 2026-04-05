"""
Public endpoints — no authentication required.
Used by the free tools on the marketing site.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from integrations.simulation_meta import DATA_CATEGORY_META, SIMULATION_META
from models.tool_lead import ToolLead
from services.compliance_service import EXPECTED_TYPES, _compute_score

router = APIRouter(prefix="/public", tags=["public"])

FRAMEWORK_LABELS = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}

CONTROL_LABELS = {
    "access_control": "Access Control",
    "logging_monitoring": "Logging & Monitoring",
    "change_management": "Change Management",
    "operations_security": "Operations Security",
    "communications_security": "Communications Security",
    "audit_controls": "Audit Controls",
    "workforce_security": "Workforce Security",
}


class ToolLeadRequest(BaseModel):
    email: EmailStr
    tool: str


@router.post("/capture-lead", status_code=201)
async def capture_lead(body: ToolLeadRequest, db: AsyncSession = Depends(get_db)) -> dict:
    """Store a free tool lead email in the database."""
    lead = ToolLead(email=body.email.lower().strip(), tool=body.tool)
    db.add(lead)
    await db.commit()
    return {"ok": True}


class StackSimulateRequest(BaseModel):
    integration_types: list[str]


@router.post("/simulate")
async def public_simulate(body: StackSimulateRequest) -> dict:
    """
    Given a list of integration types, compute a projected compliance score
    starting from zero evidence (no existing data). Used by the free
    'Compliance Stack Scorer' tool — no auth required.
    """
    # Resolve known integrations only
    known = [t for t in body.integration_types if t in SIMULATION_META]

    # Build combined coverage: control → set of evidence types
    coverage_by_control: dict[str, set[str]] = {}
    type_counts: dict[str, int] = {}
    all_evidence: list[dict] = []
    data_categories_seen: set[str] = set()

    for integration_type in known:
        meta = SIMULATION_META[integration_type]
        for ev in meta["evidence_types"]:
            coverage_by_control.setdefault(ev["control"], set()).add(ev["type"])
            type_counts[ev["type"]] = ev.get("typical_count", 10)
            all_evidence.append({
                "type": ev["type"],
                "label": ev["label"],
                "control": ev["control"],
                "typical_count": ev.get("typical_count", 10),
                "integration": meta["label"],
                "integration_type": integration_type,
            })
        for cat in meta.get("data_categories", []):
            data_categories_seen.add(cat)

    # Total simulated evidence records
    total_records = sum(type_counts.values())

    # Simulate from zero: compute per-framework projected scores
    now = datetime.now(timezone.utc)
    framework_results = []

    for framework, controls in EXPECTED_TYPES.items():
        covered_controls = []
        partial_controls = []
        missing_controls = []
        fw_score_total = 0

        for control_cat, expected in controls.items():
            covered = coverage_by_control.get(control_cat, set())
            count = sum(type_counts.get(t, 10) for t in covered)

            score = _compute_score(
                covered,
                expected,
                now if covered else None,
                count,
            )
            fw_score_total += score

            covered_here = covered & expected
            missing_here = expected - covered

            control_label = CONTROL_LABELS.get(control_cat, control_cat.replace("_", " ").title())

            if not missing_here:
                covered_controls.append(control_label)
            elif covered_here:
                partial_controls.append({
                    "label": control_label,
                    "covered": sorted(covered_here),
                    "missing": sorted(missing_here),
                })
            else:
                missing_controls.append({
                    "label": control_label,
                    "missing": sorted(missing_here),
                })

        n = len(controls)
        projected_score = int(fw_score_total / n) if n else 0

        framework_results.append({
            "framework": framework,
            "label": FRAMEWORK_LABELS.get(framework, framework),
            "projected_score": projected_score,
            "covered_controls": covered_controls,
            "partial_controls": partial_controls,
            "missing_controls": missing_controls,
        })

    # Sort by score descending
    framework_results.sort(key=lambda x: x["projected_score"], reverse=True)

    # Data categories
    data_categories = [
        {"key": cat, **DATA_CATEGORY_META[cat]}
        for cat in data_categories_seen
        if cat in DATA_CATEGORY_META
    ]

    # Sort evidence preview by typical_count desc, deduplicated by type
    seen_types: set[str] = set()
    evidence_preview = []
    for ev in sorted(all_evidence, key=lambda x: x["typical_count"], reverse=True):
        if ev["type"] not in seen_types:
            seen_types.add(ev["type"])
            evidence_preview.append(ev)

    return {
        "framework_results": framework_results,
        "total_records": total_records,
        "evidence_preview": evidence_preview[:20],
        "data_categories": data_categories,
        "integration_count": len(known),
        "unknown_types": [t for t in body.integration_types if t not in SIMULATION_META],
    }
