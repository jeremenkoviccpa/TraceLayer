import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.offboarding import Offboarding
from models.user import User
from schemas.offboarding import OffboardingCreate, OffboardingResponse, OffboardingUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offboarding", tags=["offboarding"])


def _to_response(record: Offboarding) -> OffboardingResponse:
    return OffboardingResponse(
        id=str(record.id),
        company_id=str(record.company_id),
        employee_name=record.employee_name,
        employee_email=record.employee_email,
        last_day=record.last_day,
        department=record.department,
        status=record.status,
        checklist=record.checklist or [],
        completed_by_user_id=str(record.completed_by_user_id) if record.completed_by_user_id else None,
        completed_at=record.completed_at,
        notes=record.notes,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("", response_model=list[OffboardingResponse])
async def list_offboardings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Offboarding)
        .where(Offboarding.company_id == current_user.company_id)
        .order_by(Offboarding.created_at.desc())
    )
    records = result.scalars().all()
    return [_to_response(r) for r in records]


@router.post("", response_model=OffboardingResponse, status_code=201)
async def create_offboarding(
    body: OffboardingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = Offboarding(
        company_id=current_user.company_id,
        employee_name=body.employee_name,
        employee_email=body.employee_email,
        last_day=body.last_day,
        department=body.department,
        status=body.status,
        checklist=body.checklist,
        notes=body.notes,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.patch("/{record_id}", response_model=OffboardingResponse)
async def update_offboarding(
    record_id: uuid.UUID,
    body: OffboardingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Offboarding).where(Offboarding.id == record_id, Offboarding.company_id == current_user.company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Offboarding record not found")

    update_data = body.model_dump(exclude_unset=True)

    # Auto-set completed_by when status changes to completed
    if update_data.get("status") == "completed" and not record.completed_at:
        from datetime import datetime, timezone
        update_data.setdefault("completed_at", datetime.now(timezone.utc))
        update_data.setdefault("completed_by_user_id", current_user.id)

    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)
    return _to_response(record)


@router.delete("/{record_id}", status_code=204)
async def delete_offboarding(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Offboarding).where(Offboarding.id == record_id, Offboarding.company_id == current_user.company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Offboarding record not found")

    await db.delete(record)
    await db.commit()
