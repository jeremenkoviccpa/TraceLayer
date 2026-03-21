import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.data_flow import DataFlow
from models.user import User
from schemas.data_flow import DataFlowCreate, DataFlowResponse, DataFlowUpdate
from services.data_flow_service import scan_and_populate

router = APIRouter(prefix="/data-flows", tags=["data-flows"])


def _to_response(df: DataFlow) -> DataFlowResponse:
    return DataFlowResponse(
        id=str(df.id),
        company_id=str(df.company_id),
        data_type=df.data_type,
        data_category=df.data_category,
        tool=df.tool,
        tool_label=df.tool_label,
        region=df.region,
        risk_level=df.risk_level,
        regulations=df.regulations or [],
        purpose=df.purpose,
        legal_basis=df.legal_basis,
        is_auto_detected=df.is_auto_detected,
        is_cross_border=df.is_cross_border,
        notes=df.notes,
        created_at=df.created_at,
        updated_at=df.updated_at,
    )


@router.get("", response_model=list[DataFlowResponse])
async def list_data_flows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataFlow)
        .where(DataFlow.company_id == current_user.company_id)
        .order_by(DataFlow.risk_level, DataFlow.tool, DataFlow.data_type)
    )
    return [_to_response(df) for df in result.scalars().all()]


@router.post("", response_model=DataFlowResponse, status_code=201)
async def create_data_flow(
    body: DataFlowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    df = DataFlow(
        company_id=current_user.company_id,
        data_type=body.data_type,
        data_category=body.data_category,
        tool=body.tool,
        tool_label=body.tool_label,
        region=body.region,
        risk_level=body.risk_level,
        regulations=body.regulations,
        purpose=body.purpose,
        legal_basis=body.legal_basis,
        is_auto_detected=False,
        is_cross_border=body.is_cross_border,
        notes=body.notes,
    )
    db.add(df)
    await db.commit()
    await db.refresh(df)
    return _to_response(df)


@router.patch("/{flow_id}", response_model=DataFlowResponse)
async def update_data_flow(
    flow_id: uuid.UUID,
    body: DataFlowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataFlow).where(
            DataFlow.id == flow_id,
            DataFlow.company_id == current_user.company_id,
        )
    )
    df = result.scalar_one_or_none()
    if not df:
        raise HTTPException(status_code=404, detail="Data flow not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(df, field, value)

    await db.commit()
    await db.refresh(df)
    return _to_response(df)


@router.delete("/{flow_id}", status_code=204)
async def delete_data_flow(
    flow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataFlow).where(
            DataFlow.id == flow_id,
            DataFlow.company_id == current_user.company_id,
        )
    )
    df = result.scalar_one_or_none()
    if not df:
        raise HTTPException(status_code=404, detail="Data flow not found")
    await db.delete(df)
    await db.commit()


@router.post("/scan", response_model=list[DataFlowResponse])
async def scan_data_flows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-scan all active integrations and rebuild auto-detected data flows."""
    await scan_and_populate(current_user.company_id, db)
    result = await db.execute(
        select(DataFlow)
        .where(DataFlow.company_id == current_user.company_id)
        .order_by(DataFlow.risk_level, DataFlow.tool, DataFlow.data_type)
    )
    return [_to_response(df) for df in result.scalars().all()]
