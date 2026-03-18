import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.data_breach import DataBreach
from models.user import User
from schemas.data_breach import DataBreachCreate, DataBreachResponse, DataBreachUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/data-breaches", tags=["data-breaches"])


@router.get("", response_model=list[DataBreachResponse])
async def list_data_breaches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataBreach)
        .where(DataBreach.company_id == current_user.company_id)
        .order_by(DataBreach.discovered_at.desc().nulls_last())
    )
    return result.scalars().all()


@router.post("", response_model=DataBreachResponse, status_code=201)
async def create_data_breach(
    body: DataBreachCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    breach = DataBreach(
        company_id=current_user.company_id,
        **body.model_dump(),
    )
    db.add(breach)
    await db.commit()
    await db.refresh(breach)
    return breach


@router.patch("/{breach_id}", response_model=DataBreachResponse)
async def update_data_breach(
    breach_id: uuid.UUID,
    body: DataBreachUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataBreach).where(
            DataBreach.id == breach_id,
            DataBreach.company_id == current_user.company_id,
        )
    )
    breach = result.scalar_one_or_none()
    if not breach:
        raise HTTPException(status_code=404, detail="Data breach not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(breach, field, value)

    await db.commit()
    await db.refresh(breach)
    return breach


@router.delete("/{breach_id}", status_code=204)
async def delete_data_breach(
    breach_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataBreach).where(
            DataBreach.id == breach_id,
            DataBreach.company_id == current_user.company_id,
        )
    )
    breach = result.scalar_one_or_none()
    if not breach:
        raise HTTPException(status_code=404, detail="Data breach not found")

    await db.delete(breach)
    await db.commit()
