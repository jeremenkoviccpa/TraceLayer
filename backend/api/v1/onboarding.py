"""Automated new-hire onboarding task management."""
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from core.database import get_db
from core.deps import get_current_user
from models.onboarding_task import OnboardingTask
from models.user import User
from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/onboarding", tags=["onboarding"])

TASK_FIELDS = ["policy_ack_status", "training_status", "device_status", "background_check_status", "access_provisioned_status"]
TASK_LABELS = {
    "policy_ack_status": "Policy Acknowledgment",
    "training_status": "Security Training",
    "device_status": "Device Enrollment",
    "background_check_status": "Background Check",
    "access_provisioned_status": "Access Provisioning",
}


class OnboardingCreateRequest(BaseModel):
    employee_email: str
    employee_name: Optional[str] = None
    hired_at: Optional[datetime] = None
    department: Optional[str] = None
    role_title: Optional[str] = None
    notes: Optional[str] = None


class OnboardingTaskStatusUpdate(BaseModel):
    field: str  # one of TASK_FIELDS
    status: str  # pending | completed | skipped


class OnboardingResponse(BaseModel):
    id: str
    employee_email: str
    employee_name: Optional[str]
    source: str
    hired_at: Optional[datetime]
    department: Optional[str]
    role_title: Optional[str]
    policy_ack_status: str
    training_status: str
    device_status: str
    background_check_status: str
    access_provisioned_status: str
    overall_status: str
    completed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


def _compute_overall(task: OnboardingTask) -> str:
    statuses = [
        task.policy_ack_status, task.training_status, task.device_status,
        task.background_check_status, task.access_provisioned_status,
    ]
    if all(s in ("completed", "skipped") for s in statuses):
        return "completed"
    if any(s == "completed" for s in statuses):
        return "in_progress"
    return "in_progress"


def _to_response(t: OnboardingTask) -> dict:
    return {
        "id": str(t.id),
        "employee_email": t.employee_email,
        "employee_name": t.employee_name,
        "source": t.source,
        "hired_at": t.hired_at,
        "department": t.department,
        "role_title": t.role_title,
        "policy_ack_status": t.policy_ack_status,
        "training_status": t.training_status,
        "device_status": t.device_status,
        "background_check_status": t.background_check_status,
        "access_provisioned_status": t.access_provisioned_status,
        "overall_status": t.overall_status,
        "completed_at": t.completed_at,
        "notes": t.notes,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
    }


@router.get("")
async def list_onboarding(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(OnboardingTask)
        .where(OnboardingTask.company_id == current_user.company_id)
        .order_by(OnboardingTask.created_at.desc())
    )
    return [_to_response(t) for t in result.scalars().all()]


@router.post("", status_code=201)
async def create_onboarding(
    body: OnboardingCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(OnboardingTask).where(
            OnboardingTask.company_id == current_user.company_id,
            OnboardingTask.employee_email == body.employee_email,
        )
    )).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="Onboarding record already exists for this employee.")

    now = datetime.now(timezone.utc)
    task = OnboardingTask(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        employee_email=body.employee_email,
        employee_name=body.employee_name,
        source="manual",
        hired_at=body.hired_at,
        department=body.department,
        role_title=body.role_title,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await log_action(db, current_user.company_id, "onboarding.created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="onboarding_task", resource_id=str(task.id),
                     metadata={"employee_email": body.employee_email})
    return _to_response(task)


@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: uuid.UUID,
    body: OnboardingTaskStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.field not in TASK_FIELDS:
        raise HTTPException(status_code=422, detail=f"Invalid field. Must be one of: {', '.join(TASK_FIELDS)}")
    if body.status not in ("pending", "completed", "skipped"):
        raise HTTPException(status_code=422, detail="Status must be: pending, completed, or skipped")

    task = (await db.execute(
        select(OnboardingTask).where(
            OnboardingTask.id == task_id,
            OnboardingTask.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Onboarding task not found")

    setattr(task, body.field, body.status)
    now = datetime.now(timezone.utc)
    task.overall_status = _compute_overall(task)
    if task.overall_status == "completed" and not task.completed_at:
        task.completed_at = now
    elif task.overall_status != "completed":
        task.completed_at = None
    task.updated_at = now

    await db.commit()
    await db.refresh(task)
    return _to_response(task)


@router.delete("/{task_id}", status_code=204)
async def delete_onboarding(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = (await db.execute(
        select(OnboardingTask).where(
            OnboardingTask.id == task_id,
            OnboardingTask.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(task)
    await db.commit()
