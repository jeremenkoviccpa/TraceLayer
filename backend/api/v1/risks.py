import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.risk import Risk
from models.user import User
from schemas.risk import RiskCreate, RiskResponse, RiskUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risks", tags=["risks"])


def _to_response(risk: Risk, owner_map: dict[uuid.UUID, str]) -> RiskResponse:
    owner_id = risk.owner_user_id
    owner_name = owner_map.get(owner_id) if owner_id else None
    return RiskResponse(
        id=str(risk.id),
        company_id=str(risk.company_id),
        title=risk.title,
        description=risk.description,
        category=risk.category,
        likelihood=risk.likelihood,
        impact=risk.impact,
        status=risk.status,
        owner_user_id=str(owner_id) if owner_id else None,
        owner_name=owner_name,
        notes=risk.notes,
        created_at=risk.created_at,
        updated_at=risk.updated_at,
    )


@router.get("", response_model=list[RiskResponse])
async def list_risks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Risk)
        .where(Risk.company_id == current_user.company_id)
        .order_by(Risk.created_at.desc())
    )
    risks = result.scalars().all()

    # Collect all distinct owner_user_ids and build a name map in a single query
    owner_ids = {r.owner_user_id for r in risks if r.owner_user_id is not None}
    owner_map: dict[uuid.UUID, str] = {}
    if owner_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(owner_ids))
        )
        for row in users_result.all():
            owner_map[row.id] = row.full_name or row.email

    return [_to_response(r, owner_map) for r in risks]


@router.post("", response_model=RiskResponse, status_code=201)
async def create_risk(
    body: RiskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_user_id: Optional[uuid.UUID] = None
    if body.owner_user_id:
        # Validate owner belongs to same company
        owner_result = await db.execute(
            select(User).where(
                User.id == uuid.UUID(body.owner_user_id),
                User.company_id == current_user.company_id,
            )
        )
        owner = owner_result.scalar_one_or_none()
        if not owner:
            raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
        owner_user_id = owner.id

    risk = Risk(
        company_id=current_user.company_id,
        title=body.title,
        description=body.description,
        category=body.category,
        likelihood=body.likelihood,
        impact=body.impact,
        status=body.status,
        owner_user_id=owner_user_id,
        notes=body.notes,
    )
    db.add(risk)
    await db.commit()
    await db.refresh(risk)

    owner_map: dict[uuid.UUID, str] = {}
    if owner_user_id:
        owner_res = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id == owner_user_id)
        )
        row = owner_res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(risk, owner_map)


@router.patch("/{risk_id}", response_model=RiskResponse)
async def update_risk(
    risk_id: uuid.UUID,
    body: RiskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Risk).where(Risk.id == risk_id, Risk.company_id == current_user.company_id)
    )
    risk = result.scalar_one_or_none()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    update_data = body.model_dump(exclude_unset=True)

    if "owner_user_id" in update_data:
        raw_owner_id = update_data.pop("owner_user_id")
        if raw_owner_id is None:
            risk.owner_user_id = None
        else:
            owner_result = await db.execute(
                select(User).where(
                    User.id == uuid.UUID(raw_owner_id),
                    User.company_id == current_user.company_id,
                )
            )
            owner = owner_result.scalar_one_or_none()
            if not owner:
                raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
            risk.owner_user_id = owner.id

    for field, value in update_data.items():
        setattr(risk, field, value)

    await db.commit()
    await db.refresh(risk)

    owner_map: dict[uuid.UUID, str] = {}
    if risk.owner_user_id:
        owner_res = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id == risk.owner_user_id)
        )
        row = owner_res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(risk, owner_map)


@router.delete("/{risk_id}", status_code=204)
async def delete_risk(
    risk_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Risk).where(Risk.id == risk_id, Risk.company_id == current_user.company_id)
    )
    risk = result.scalar_one_or_none()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk not found")

    await db.delete(risk)
    await db.commit()
