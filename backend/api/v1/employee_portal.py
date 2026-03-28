from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.device import Device
from models.policy import Policy
from models.policy_signature import PolicySignature
from models.training import TrainingRecord
from models.user import User

router = APIRouter(prefix="/portal", tags=["portal"])


# ── Schemas ────────────────────────────────────────────────────────────────────

def _fmt_slug(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ").title()


class PolicyTaskItem(BaseModel):
    policy_id: str
    slug: str
    title: str
    signed: bool
    signed_at: Optional[str] = None


class DeviceTaskItem(BaseModel):
    attested: bool
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    last_attested_at: Optional[str] = None
    disk_encrypted: Optional[bool] = None
    lockscreen_enabled: Optional[bool] = None
    antivirus_installed: Optional[bool] = None


class TrainingTaskItem(BaseModel):
    id: str
    title: str
    status: str
    due_date: Optional[str]
    completed_at: Optional[str]
    quiz_passed: bool
    quiz_score: Optional[int]
    quiz_attempts: int
    completion_token: Optional[str]


class PortalTasksResponse(BaseModel):
    user_email: str
    user_name: Optional[str]
    pending_count: int
    total_count: int
    policies: list[PolicyTaskItem]
    device: DeviceTaskItem
    training: list[TrainingTaskItem]


class PolicyContentResponse(BaseModel):
    slug: str
    title: str
    content: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=PortalTasksResponse)
async def get_portal_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's pending compliance tasks."""
    # Policies with non-empty content
    policies_result = await db.execute(
        select(Policy).where(
            Policy.company_id == current_user.company_id,
            Policy.content != "",
        )
    )
    policies = policies_result.scalars().all()

    # Which ones has this user signed?
    sigs_result = await db.execute(
        select(PolicySignature).where(PolicySignature.user_id == current_user.id)
    )
    signed_map = {str(s.policy_id): s for s in sigs_result.scalars().all()}

    policy_tasks: list[PolicyTaskItem] = []
    for p in policies:
        sig = signed_map.get(str(p.id))
        policy_tasks.append(PolicyTaskItem(
            policy_id=str(p.id),
            slug=p.slug,
            title=_fmt_slug(p.slug),
            signed=sig is not None,
            signed_at=sig.signed_at.isoformat() if sig else None,
        ))

    # Device attestation
    device_result = await db.execute(
        select(Device).where(Device.user_id == current_user.id)
    )
    device = device_result.scalar_one_or_none()
    device_task = DeviceTaskItem(
        attested=device is not None,
        device_id=str(device.id) if device else None,
        device_name=device.device_name if device else None,
        last_attested_at=device.last_attested_at.isoformat() if device and device.last_attested_at else None,
        disk_encrypted=device.disk_encrypted if device else None,
        lockscreen_enabled=device.lockscreen_enabled if device else None,
        antivirus_installed=device.antivirus_installed if device else None,
    )

    # Training records assigned to this user's email
    training_result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.company_id == current_user.company_id,
            TrainingRecord.assignee_email == current_user.email,
        ).order_by(TrainingRecord.created_at.desc())
    )
    training_records = training_result.scalars().all()
    training_tasks = [
        TrainingTaskItem(
            id=str(t.id),
            title=t.title,
            status=t.status,
            due_date=t.due_date.isoformat() if t.due_date else None,
            completed_at=t.completed_at.isoformat() if t.completed_at else None,
            quiz_passed=t.quiz_passed,
            quiz_score=t.quiz_score,
            quiz_attempts=t.quiz_attempts,
            completion_token=t.completion_token,
        )
        for t in training_records
    ]

    unsigned_policies = sum(1 for p in policy_tasks if not p.signed)
    device_pending = 0 if device_task.attested else 1
    training_pending = sum(1 for t in training_tasks if not t.quiz_passed)
    pending = unsigned_policies + device_pending + training_pending
    total = len(policy_tasks) + 1 + len(training_tasks)

    return PortalTasksResponse(
        user_email=current_user.email,
        user_name=current_user.full_name,
        pending_count=pending,
        total_count=total,
        policies=policy_tasks,
        device=device_task,
        training=training_tasks,
    )


@router.get("/policies/{slug}", response_model=PolicyContentResponse)
async def get_portal_policy(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(
            Policy.company_id == current_user.company_id,
            Policy.slug == slug,
        )
    )
    policy = result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return PolicyContentResponse(slug=policy.slug, title=_fmt_slug(policy.slug), content=policy.content)


@router.post("/policies/{slug}/sign", response_model=PolicyTaskItem)
async def sign_policy(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy_result = await db.execute(
        select(Policy).where(
            Policy.company_id == current_user.company_id,
            Policy.slug == slug,
        )
    )
    policy = policy_result.scalar_one_or_none()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Idempotent — already signed?
    existing = await db.execute(
        select(PolicySignature).where(
            PolicySignature.policy_id == policy.id,
            PolicySignature.user_id == current_user.id,
        )
    )
    sig = existing.scalar_one_or_none()
    if not sig:
        sig = PolicySignature(
            policy_id=policy.id,
            user_id=current_user.id,
            company_id=current_user.company_id,
        )
        db.add(sig)
        await db.commit()
        await db.refresh(sig)

    return PolicyTaskItem(
        policy_id=str(policy.id),
        slug=policy.slug,
        title=_fmt_slug(policy.slug),
        signed=True,
        signed_at=sig.signed_at.isoformat(),
    )
