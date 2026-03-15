import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.training import TrainingRecord
from models.user import User
from schemas.training import TrainingCreate, TrainingResponse, TrainingUpdate

router = APIRouter(prefix="/training", tags=["training"])


def _to_response(t: TrainingRecord) -> TrainingResponse:
    return TrainingResponse(
        id=str(t.id),
        company_id=str(t.company_id),
        assignee_email=t.assignee_email,
        assignee_name=t.assignee_name,
        title=t.title,
        description=t.description,
        due_date=t.due_date,
        completed_at=t.completed_at,
        status=t.status,
        annual=t.annual,
        notes=t.notes,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _compute_status(record: TrainingRecord) -> str:
    if record.completed_at:
        return "completed"
    if record.due_date and record.due_date < datetime.now(timezone.utc):
        return "overdue"
    return "pending"


@router.get("", response_model=list[TrainingResponse])
async def list_training(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord)
        .where(TrainingRecord.company_id == current_user.company_id)
        .order_by(TrainingRecord.created_at.desc())
    )
    records = result.scalars().all()
    # Refresh computed status
    for r in records:
        computed = _compute_status(r)
        if r.status != computed and r.status != "completed":
            r.status = computed
    if any(r.status == "overdue" for r in records):
        await db.commit()
    return [_to_response(r) for r in records]


@router.post("", response_model=TrainingResponse, status_code=201)
async def create_training(
    body: TrainingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = TrainingRecord(
        company_id=current_user.company_id,
        assignee_email=body.assignee_email,
        assignee_name=body.assignee_name,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        annual=body.annual,
        notes=body.notes,
        status="pending",
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.patch("/{record_id}", response_model=TrainingResponse)
async def update_training(
    record_id: uuid.UUID,
    body: TrainingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.id == record_id,
            TrainingRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    # Recompute status unless explicitly set
    if "status" not in body.model_dump(exclude_unset=True):
        record.status = _compute_status(record)

    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.delete("/{record_id}", status_code=204)
async def delete_training(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.id == record_id,
            TrainingRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Training record not found")
    await db.delete(record)
    await db.commit()
