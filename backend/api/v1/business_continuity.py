import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.bcp_record import BcpRecord
from models.user import User
from schemas.bcp_record import BcpRecordCreate, BcpRecordResponse, BcpRecordUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-continuity", tags=["business-continuity"])


def _to_response(record: BcpRecord, owner_map: dict) -> BcpRecordResponse:
    owner_id = record.owner_user_id
    return BcpRecordResponse(
        id=str(record.id),
        company_id=str(record.company_id),
        title=record.title,
        record_type=record.record_type,
        status=record.status,
        last_tested_at=record.last_tested_at,
        next_test_due=record.next_test_due,
        rto_minutes=record.rto_minutes,
        rpo_minutes=record.rpo_minutes,
        test_results=record.test_results,
        scope=record.scope,
        notes=record.notes,
        owner_user_id=str(owner_id) if owner_id else None,
        owner_name=owner_map.get(owner_id) if owner_id else None,
        file_url=record.file_url,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.get("", response_model=list[BcpRecordResponse])
async def list_bcp_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BcpRecord).where(BcpRecord.company_id == current_user.company_id).order_by(BcpRecord.created_at.desc())
    )
    records = result.scalars().all()

    owner_ids = {r.owner_user_id for r in records if r.owner_user_id is not None}
    owner_map: dict = {}
    if owner_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(owner_ids))
        )
        for row in users_result.all():
            owner_map[row.id] = row.full_name or row.email

    return [_to_response(r, owner_map) for r in records]


@router.post("", response_model=BcpRecordResponse, status_code=201)
async def create_bcp_record(
    body: BcpRecordCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_user_id: Optional[uuid.UUID] = None
    if body.owner_user_id:
        res = await db.execute(
            select(User).where(User.id == uuid.UUID(body.owner_user_id), User.company_id == current_user.company_id)
        )
        owner = res.scalar_one_or_none()
        if not owner:
            raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
        owner_user_id = owner.id

    record = BcpRecord(
        company_id=current_user.company_id,
        title=body.title,
        record_type=body.record_type,
        status=body.status,
        last_tested_at=body.last_tested_at,
        next_test_due=body.next_test_due,
        rto_minutes=body.rto_minutes,
        rpo_minutes=body.rpo_minutes,
        test_results=body.test_results,
        scope=body.scope,
        notes=body.notes,
        owner_user_id=owner_user_id,
        file_url=body.file_url,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    owner_map: dict = {}
    if owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(record, owner_map)


@router.patch("/{record_id}", response_model=BcpRecordResponse)
async def update_bcp_record(
    record_id: uuid.UUID,
    body: BcpRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BcpRecord).where(BcpRecord.id == record_id, BcpRecord.company_id == current_user.company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="BCP record not found")

    update_data = body.model_dump(exclude_unset=True)

    if "owner_user_id" in update_data:
        raw_id = update_data.pop("owner_user_id")
        if raw_id is None:
            record.owner_user_id = None
        else:
            res = await db.execute(
                select(User).where(User.id == uuid.UUID(raw_id), User.company_id == current_user.company_id)
            )
            owner = res.scalar_one_or_none()
            if not owner:
                raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
            record.owner_user_id = owner.id

    for field, value in update_data.items():
        setattr(record, field, value)

    await db.commit()
    await db.refresh(record)

    owner_map: dict = {}
    if record.owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == record.owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(record, owner_map)


@router.delete("/{record_id}", status_code=204)
async def delete_bcp_record(
    record_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BcpRecord).where(BcpRecord.id == record_id, BcpRecord.company_id == current_user.company_id)
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="BCP record not found")

    await db.delete(record)
    await db.commit()
