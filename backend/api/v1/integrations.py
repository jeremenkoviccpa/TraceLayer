from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.runner import run_collector_job
from collectors.scheduler import schedule_integration, unschedule_integration
from core.database import get_db
from core.deps import get_current_user
from integrations.simulation_meta import DATA_CATEGORY_META, SIMULATION_META
from models.evidence import Evidence
from models.integration import Integration
from models.user import User
from schemas.integrations import ConnectRequest, IntegrationResponse
from services.audit_service import log_action
from services.billing_service import check_integration_limit
from services.compliance_service import EXPECTED_TYPES, _compute_score
from services.integration_service import (
    connect_integration,
    disconnect_integration,
    list_integrations,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_integrations(current_user.company_id, db)


@router.post("/connect", response_model=IntegrationResponse, status_code=201)
async def connect(
    body: ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        body.validate_type()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await check_integration_limit(current_user.company_id, db)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))

    try:
        integration = await connect_integration(
            current_user.company_id,
            body.integration_type,
            body.credentials,
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Schedule recurring collection — run_now fires first collection in 30s
    schedule_integration(
        str(current_user.company_id),
        body.integration_type,
        run_now=True,
    )

    await log_action(
        db, current_user.company_id, "integration.connected",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="integration", resource_id=body.integration_type,
    )
    return integration


@router.delete("/{integration_type}", status_code=204)
async def disconnect(
    integration_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await disconnect_integration(current_user.company_id, integration_type, db)
    if not removed:
        raise HTTPException(status_code=404, detail="Integration not found")

    unschedule_integration(str(current_user.company_id), integration_type)
    await log_action(
        db, current_user.company_id, "integration.disconnected",
        user_id=current_user.id, user_email=current_user.email,
        resource_type="integration", resource_id=integration_type,
    )


@router.post("/{integration_type}/collect", status_code=202)
async def trigger_collect(
    integration_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(
        run_collector_job,
        str(current_user.company_id),
        integration_type,
    )
    return {"message": "Collection job queued"}


@router.get("/simulate/{integration_type}")
async def simulate_integration(
    integration_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return a score-impact preview for connecting an integration without
    making any real API calls to the third-party service.
    """
    meta = SIMULATION_META.get(integration_type)
    if not meta:
        raise HTTPException(
            status_code=404,
            detail=f"No simulation data available for '{integration_type}'.",
        )

    # ── Already connected? ────────────────────────────────────────────────────
    existing_row = await db.execute(
        select(Integration.id).where(
            Integration.company_id == current_user.company_id,
            Integration.integration_type == integration_type,
        ).limit(1)
    )
    already_connected = existing_row.scalar() is not None

    # ── Current evidence coverage per control category ────────────────────────
    rows = await db.execute(
        select(
            Evidence.control,
            Evidence.evidence_type,
            func.count().label("cnt"),
            func.max(Evidence.timestamp).label("latest"),
        )
        .where(Evidence.company_id == current_user.company_id)
        .group_by(Evidence.control, Evidence.evidence_type)
    )

    by_control: dict[str, dict] = {}
    for row in rows:
        entry = by_control.setdefault(
            row.control, {"types": set(), "count": 0, "latest": None}
        )
        entry["types"].add(row.evidence_type)
        entry["count"] += row.cnt
        if row.latest and (entry["latest"] is None or row.latest > entry["latest"]):
            entry["latest"] = row.latest

    # ── New types per control this integration would add ──────────────────────
    new_by_control: dict[str, set[str]] = {}
    new_type_counts: dict[str, int] = {}
    for ev in meta["evidence_types"]:
        new_by_control.setdefault(ev["control"], set()).add(ev["type"])
        new_type_counts[ev["type"]] = ev.get("typical_count", 10)

    # ── Compute per-framework score delta ─────────────────────────────────────
    framework_labels = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}
    framework_deltas = []

    for framework, controls in EXPECTED_TYPES.items():
        current_total = 0
        sim_total = 0
        all_new_covered: list[str] = []

        for control_cat, expected in controls.items():
            ev = by_control.get(control_cat, {"types": set(), "count": 0, "latest": None})
            current_covered: set[str] = ev["types"]
            current_score = _compute_score(current_covered, expected, ev["latest"], ev["count"])

            added_types = new_by_control.get(control_cat, set()) - current_covered
            sim_covered = current_covered | added_types
            added_count = sum(new_type_counts.get(t, 10) for t in added_types)
            sim_score = _compute_score(
                sim_covered,
                expected,
                ev["latest"] or datetime.now(timezone.utc),
                ev["count"] + added_count,
            )

            current_total += current_score
            sim_total += sim_score
            all_new_covered.extend(sorted(added_types))

        n = len(controls)
        current_avg = int(current_total / n) if n else 0
        sim_avg = int(sim_total / n) if n else 0
        delta = sim_avg - current_avg

        framework_deltas.append({
            "framework": framework,
            "label": framework_labels.get(framework, framework),
            "current_score": current_avg,
            "simulated_score": sim_avg,
            "delta": delta,
            "new_types_covered": all_new_covered,
        })

    # Sort: highest delta first
    framework_deltas.sort(key=lambda x: x["delta"], reverse=True)

    # ── Assemble data category info ───────────────────────────────────────────
    data_categories = [
        {"key": cat, **DATA_CATEGORY_META[cat]}
        for cat in meta.get("data_categories", [])
        if cat in DATA_CATEGORY_META
    ]

    return {
        "integration_type": integration_type,
        "label": meta["label"],
        "description": meta.get("description", ""),
        "evidence_types": meta["evidence_types"],
        "data_categories": data_categories,
        "framework_deltas": framework_deltas,
        "already_connected": already_connected,
    }
