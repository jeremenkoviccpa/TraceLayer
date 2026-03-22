import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.data_flow import DataFlow
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


@router.post("/generate", status_code=200)
async def generate_ropa_from_data_flows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate RoPA records from the Data Flow Map. Each tool+data_type pair becomes one processing activity."""
    flows_result = await db.execute(
        select(DataFlow).where(DataFlow.company_id == current_user.company_id)
    )
    flows = flows_result.scalars().all()

    existing_result = await db.execute(
        select(RopaRecord.name).where(RopaRecord.company_id == current_user.company_id)
    )
    existing_names = {row[0].lower() for row in existing_result.all()}

    created = 0
    skipped = 0

    for flow in flows:
        name = f"{flow.tool_label} — {flow.data_type.replace('_', ' ').title()}"
        if name.lower() in existing_names:
            skipped += 1
            continue

        regs = ", ".join(flow.regulations) if flow.regulations else "N/A"
        cross_border_note = "Yes — cross-border transfer detected. SCCs or BCRs may be required." if flow.is_cross_border else "No"

        record = RopaRecord(
            company_id=current_user.company_id,
            name=name,
            role="controller",
            purpose=flow.purpose or f"Processing of {flow.data_type.replace('_', ' ')} via {flow.tool_label}",
            legal_basis=flow.legal_basis or "legitimate_interests",
            data_categories=flow.data_category,
            data_subjects="End users, customers, and employees as applicable",
            recipients=flow.tool_label,
            third_country_transfers=cross_border_note,
            retention_period="As defined in data retention policy",
            security_measures=f"Access controlled and audited via {flow.tool_label}. Risk level: {flow.risk_level}.",
            notes=f"Auto-generated from Data Flow Map. Applicable regulations: {regs}.",
        )
        db.add(record)
        existing_names.add(name.lower())
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}


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
