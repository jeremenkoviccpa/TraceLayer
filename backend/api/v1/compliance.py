import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.manual_control import ManualControl
from models.user import User
from schemas.compliance import (
    ComplianceScoreResponse,
    EvidenceActivityPoint,
    ManualControlItem,
    ScoreHistoryPoint,
    UpdateManualControlRequest,
)
from services.compliance_service import get_compliance_score, get_evidence_activity, get_score_history

router = APIRouter(prefix="/compliance", tags=["compliance"])

# ── Manual control definitions ───────────────────────────────────────────────

_MANUAL_CONTROLS: dict[str, list[dict]] = {
    "soc2": [
        {"control_id": "security_policy", "name": "Information Security Policy",
         "description": "Written security policy documented, approved by management, and reviewed in the last 12 months."},
        {"control_id": "incident_response", "name": "Incident Response Plan",
         "description": "Incident response plan documented, communicated to staff, and tested at least annually."},
        {"control_id": "security_training", "name": "Security Awareness Training",
         "description": "Annual security awareness training completed by all employees."},
        {"control_id": "vendor_risk", "name": "Vendor Risk Management",
         "description": "Third-party vendor risk assessments performed before onboarding and annually thereafter."},
        {"control_id": "background_checks", "name": "Background Checks",
         "description": "Background verification performed for all employees with access to production systems."},
        {"control_id": "bcp", "name": "Business Continuity Plan",
         "description": "Business continuity and disaster recovery plan documented and tested."},
    ],
    "iso27001": [
        {"control_id": "isms_policy", "name": "ISMS Policy",
         "description": "Information Security Management System policy documented and approved by top management."},
        {"control_id": "risk_assessment", "name": "Risk Assessment",
         "description": "Formal risk assessment completed covering all in-scope assets."},
        {"control_id": "statement_of_applicability", "name": "Statement of Applicability",
         "description": "Statement of Applicability (SoA) completed and signed off."},
        {"control_id": "management_review", "name": "Management Review",
         "description": "ISMS management review conducted at planned intervals (at least annually)."},
        {"control_id": "internal_audit", "name": "Internal Audit",
         "description": "Internal audit of the ISMS completed covering all controls."},
        {"control_id": "asset_inventory", "name": "Asset Inventory",
         "description": "Inventory of all information assets documented and maintained."},
    ],
    "hipaa": [
        {"control_id": "privacy_officer", "name": "Privacy Officer Designated",
         "description": "Privacy officer (and Security officer if separate) formally designated."},
        {"control_id": "hipaa_training", "name": "HIPAA Training",
         "description": "HIPAA privacy and security training completed by all workforce members who handle PHI."},
        {"control_id": "baa", "name": "Business Associate Agreements",
         "description": "Business Associate Agreements (BAAs) in place with all vendors who handle PHI."},
        {"control_id": "phi_inventory", "name": "PHI Inventory",
         "description": "Inventory of all PHI data flows and storage locations documented."},
        {"control_id": "breach_response", "name": "Breach Response Procedure",
         "description": "Breach notification procedure documented meeting HIPAA 60-day notification requirement."},
        {"control_id": "risk_analysis", "name": "Security Risk Analysis",
         "description": "Formal security risk analysis of PHI completed as required by the HIPAA Security Rule."},
    ],
}

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/score", response_model=ComplianceScoreResponse)
async def compliance_score(
    framework: str = Query("soc2", description="Compliance framework"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_compliance_score(current_user.company_id, framework, db)


@router.get("/score-history", response_model=list[ScoreHistoryPoint])
async def score_history(
    framework: str = Query("soc2"),
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_score_history(current_user.company_id, framework, days, db)


@router.get("/evidence-activity", response_model=list[EvidenceActivityPoint])
async def evidence_activity(
    days: int = Query(14, ge=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_evidence_activity(current_user.company_id, days, db)


@router.get("/manual-controls", response_model=list[ManualControlItem])
async def get_manual_controls(
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    definitions = _MANUAL_CONTROLS.get(framework, [])
    if not definitions:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")

    # Load saved records for this company+framework
    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
        )
    )
    saved = {r.control_id: r for r in result.scalars().all()}

    items = []
    for defn in definitions:
        cid = defn["control_id"]
        rec = saved.get(cid)
        items.append(ManualControlItem(
            control_id=cid,
            name=defn["name"],
            description=defn["description"],
            status=rec.status if rec else "pending",
            notes=rec.notes if rec else None,
            updated_at=rec.updated_at.isoformat() if rec else None,
        ))
    return items


@router.put("/manual-controls/{control_id}", response_model=ManualControlItem)
async def update_manual_control(
    control_id: str,
    body: UpdateManualControlRequest,
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    definitions = _MANUAL_CONTROLS.get(framework, [])
    defn = next((d for d in definitions if d["control_id"] == control_id), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Control not found")

    valid_statuses = {"pending", "compliant", "not_applicable"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")

    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
            ManualControl.control_id == control_id,
        )
    )
    rec = result.scalar_one_or_none()

    if rec:
        rec.status = body.status
        rec.notes = body.notes
        rec.updated_by_id = current_user.id
    else:
        rec = ManualControl(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            framework=framework,
            control_id=control_id,
            status=body.status,
            notes=body.notes,
            updated_by_id=current_user.id,
        )
        db.add(rec)

    await db.commit()
    await db.refresh(rec)

    return ManualControlItem(
        control_id=control_id,
        name=defn["name"],
        description=defn["description"],
        status=rec.status,
        notes=rec.notes,
        updated_at=rec.updated_at.isoformat(),
    )
