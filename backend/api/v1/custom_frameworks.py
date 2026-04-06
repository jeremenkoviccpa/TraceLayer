"""Custom framework builder — define internal control frameworks and map your own policies."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.custom_framework import CustomControl, CustomFramework
from models.user import User
from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/custom-frameworks", tags=["custom-frameworks"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class FrameworkCreate(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0"


class FrameworkUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    version: Optional[str] = None
    is_active: Optional[bool] = None


class ControlCreate(BaseModel):
    name: str
    category: str = "general"
    description: Optional[str] = None
    external_id: Optional[str] = None
    evidence_types: list[str] = []
    sort_order: int = 0


class ControlUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    external_id: Optional[str] = None
    evidence_types: Optional[list[str]] = None
    sort_order: Optional[int] = None


# ── Serializers ───────────────────────────────────────────────────────────────

def _fw_to_dict(fw: CustomFramework, control_count: int = 0) -> dict:
    return {
        "id": str(fw.id),
        "company_id": str(fw.company_id),
        "name": fw.name,
        "description": fw.description,
        "version": fw.version,
        "is_active": fw.is_active,
        "created_by_id": str(fw.created_by_id) if fw.created_by_id else None,
        "created_at": fw.created_at,
        "updated_at": fw.updated_at,
        "control_count": control_count,
    }


def _ctrl_to_dict(c: CustomControl) -> dict:
    return {
        "id": str(c.id),
        "framework_id": str(c.framework_id),
        "company_id": str(c.company_id),
        "name": c.name,
        "category": c.category,
        "description": c.description,
        "external_id": c.external_id,
        "evidence_types": c.evidence_types or [],
        "sort_order": c.sort_order,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_framework(
    framework_id: uuid.UUID,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> CustomFramework:
    fw = (await db.execute(
        select(CustomFramework).where(
            CustomFramework.id == framework_id,
            CustomFramework.company_id == company_id,
        )
    )).scalar_one_or_none()
    if not fw:
        raise HTTPException(status_code=404, detail="Framework not found")
    return fw


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def list_frameworks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active custom frameworks for the company with control counts."""
    # Subquery: count controls per framework
    count_sq = (
        select(
            CustomControl.framework_id,
            func.count().label("cnt"),
        )
        .where(CustomControl.company_id == current_user.company_id)
        .group_by(CustomControl.framework_id)
        .subquery()
    )

    rows = await db.execute(
        select(CustomFramework, func.coalesce(count_sq.c.cnt, 0).label("control_count"))
        .outerjoin(count_sq, CustomFramework.id == count_sq.c.framework_id)
        .where(CustomFramework.company_id == current_user.company_id)
        .order_by(CustomFramework.created_at.desc())
    )

    result = []
    for fw, ctrl_count in rows:
        result.append(_fw_to_dict(fw, int(ctrl_count)))
    return result


@router.post("", status_code=201)
async def create_framework(
    body: FrameworkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    fw = CustomFramework(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        name=body.name,
        description=body.description,
        version=body.version,
        is_active=True,
        created_by_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(fw)
    await db.commit()
    await db.refresh(fw)
    await log_action(db, current_user.company_id, "custom_framework.created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="custom_framework", resource_id=str(fw.id),
                     metadata={"name": body.name})
    return _fw_to_dict(fw, 0)


@router.get("/{framework_id}")
async def get_framework(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a framework with all its controls ordered by sort_order."""
    fw = await _get_framework(framework_id, current_user.company_id, db)

    controls_result = await db.execute(
        select(CustomControl)
        .where(
            CustomControl.framework_id == framework_id,
            CustomControl.company_id == current_user.company_id,
        )
        .order_by(CustomControl.sort_order, CustomControl.created_at)
    )
    controls = [_ctrl_to_dict(c) for c in controls_result.scalars().all()]

    data = _fw_to_dict(fw, len(controls))
    data["controls"] = controls
    return data


@router.patch("/{framework_id}")
async def update_framework(
    framework_id: uuid.UUID,
    body: FrameworkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fw = await _get_framework(framework_id, current_user.company_id, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(fw, field, value)
    fw.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(fw)
    return _fw_to_dict(fw)


@router.delete("/{framework_id}", status_code=204)
async def delete_framework(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    fw = await _get_framework(framework_id, current_user.company_id, db)
    await db.delete(fw)
    await db.commit()


@router.post("/{framework_id}/controls", status_code=201)
async def add_control(
    framework_id: uuid.UUID,
    body: ControlCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify framework belongs to company
    await _get_framework(framework_id, current_user.company_id, db)

    now = datetime.now(timezone.utc)
    ctrl = CustomControl(
        id=uuid.uuid4(),
        framework_id=framework_id,
        company_id=current_user.company_id,
        name=body.name,
        category=body.category,
        description=body.description,
        external_id=body.external_id,
        evidence_types=body.evidence_types,
        sort_order=body.sort_order,
        created_at=now,
        updated_at=now,
    )
    db.add(ctrl)
    await db.commit()
    await db.refresh(ctrl)
    return _ctrl_to_dict(ctrl)


@router.patch("/{framework_id}/controls/{control_id}")
async def update_control(
    framework_id: uuid.UUID,
    control_id: uuid.UUID,
    body: ControlUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = (await db.execute(
        select(CustomControl).where(
            CustomControl.id == control_id,
            CustomControl.framework_id == framework_id,
            CustomControl.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ctrl, field, value)
    ctrl.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(ctrl)
    return _ctrl_to_dict(ctrl)


@router.delete("/{framework_id}/controls/{control_id}", status_code=204)
async def delete_control(
    framework_id: uuid.UUID,
    control_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ctrl = (await db.execute(
        select(CustomControl).where(
            CustomControl.id == control_id,
            CustomControl.framework_id == framework_id,
            CustomControl.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not ctrl:
        raise HTTPException(status_code=404, detail="Control not found")
    await db.delete(ctrl)
    await db.commit()


@router.get("/{framework_id}/score")
async def get_framework_score(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compute compliance score for a custom framework based on recent evidence."""
    fw = await _get_framework(framework_id, current_user.company_id, db)

    controls_result = await db.execute(
        select(CustomControl)
        .where(
            CustomControl.framework_id == framework_id,
            CustomControl.company_id == current_user.company_id,
        )
        .order_by(CustomControl.sort_order, CustomControl.created_at)
    )
    controls = controls_result.scalars().all()

    if not controls:
        return {
            "framework_id": str(fw.id),
            "framework_name": fw.name,
            "overall_score": 0,
            "total_controls": 0,
            "passing_controls": 0,
            "controls": [],
        }

    control_results = []
    passing_count = 0

    for ctrl in controls:
        evidence_types = ctrl.evidence_types or []

        # A control with no evidence_types is treated as manual/passing
        if not evidence_types:
            control_results.append({
                "id": str(ctrl.id),
                "name": ctrl.name,
                "category": ctrl.category,
                "status": "passing",
                "evidence_count": 0,
            })
            passing_count += 1
            continue

        # Query evidence collected in the last 30 days matching any of the types
        row = await db.execute(
            text("""
                SELECT COUNT(*)
                FROM evidence
                WHERE company_id = :company_id
                  AND data_type = ANY(ARRAY(SELECT jsonb_array_elements_text(:types)))
                  AND collected_at > NOW() - INTERVAL '30 days'
            """),
            {"company_id": str(current_user.company_id), "types": evidence_types},
        )
        evidence_count = row.scalar() or 0

        status = "passing" if evidence_count > 0 else "no_evidence"
        if status == "passing":
            passing_count += 1

        control_results.append({
            "id": str(ctrl.id),
            "name": ctrl.name,
            "category": ctrl.category,
            "status": status,
            "evidence_count": int(evidence_count),
        })

    total = len(controls)
    overall_score = int((passing_count / total) * 100) if total > 0 else 0

    return {
        "framework_id": str(fw.id),
        "framework_name": fw.name,
        "overall_score": overall_score,
        "total_controls": total,
        "passing_controls": passing_count,
        "controls": control_results,
    }
