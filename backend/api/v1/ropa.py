import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.ropa_record import RopaRecord
from models.user import User
from schemas.ropa_record import RopaRecordCreate, RopaRecordResponse, RopaRecordUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ropa", tags=["ropa"])


@router.get("", response_model=list[RopaRecordResponse])
async def list_ropa_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RopaRecord)
        .where(RopaRecord.company_id == current_user.company_id)
        .order_by(RopaRecord.name)
    )
    return result.scalars().all()


@router.post("", response_model=RopaRecordResponse, status_code=201)
async def create_ropa_record(
    body: RopaRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = RopaRecord(
        company_id=current_user.company_id,
        **body.model_dump(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.patch("/{record_id}", response_model=RopaRecordResponse)
async def update_ropa_record(
    record_id: uuid.UUID,
    body: RopaRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RopaRecord).where(
            RopaRecord.id == record_id,
            RopaRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="RoPA record not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
async def delete_ropa_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(RopaRecord).where(
            RopaRecord.id == record_id,
            RopaRecord.company_id == current_user.company_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="RoPA record not found")

    await db.delete(record)
    await db.commit()
