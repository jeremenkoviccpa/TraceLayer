import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.background_check import BackgroundCheck
from models.user import User
from schemas.background_check import BackgroundCheckCreate, BackgroundCheckResponse, BackgroundCheckUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/background-checks", tags=["background-checks"])


def _to_response(check: BackgroundCheck) -> BackgroundCheckResponse:
    return BackgroundCheckResponse(
        id=str(check.id),
        company_id=str(check.company_id),
        employee_name=check.employee_name,
        employee_email=check.employee_email,
        check_type=check.check_type,
        vendor=check.vendor,
        status=check.status,
        initiated_at=check.initiated_at,
        completed_at=check.completed_at,
        valid_until=check.valid_until,
        notes=check.notes,
        created_at=check.created_at,
        updated_at=check.updated_at,
    )


@router.get("", response_model=list[BackgroundCheckResponse])
async def list_background_checks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BackgroundCheck)
        .where(BackgroundCheck.company_id == current_user.company_id)
        .order_by(BackgroundCheck.created_at.desc())
    )
    checks = result.scalars().all()
    return [_to_response(c) for c in checks]


@router.post("", response_model=BackgroundCheckResponse, status_code=201)
async def create_background_check(
    body: BackgroundCheckCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    check = BackgroundCheck(
        company_id=current_user.company_id,
        employee_name=body.employee_name,
        employee_email=body.employee_email,
        check_type=body.check_type,
        vendor=body.vendor,
        status=body.status,
        initiated_at=body.initiated_at,
        completed_at=body.completed_at,
        valid_until=body.valid_until,
        notes=body.notes,
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return _to_response(check)


@router.patch("/{check_id}", response_model=BackgroundCheckResponse)
async def update_background_check(
    check_id: uuid.UUID,
    body: BackgroundCheckUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BackgroundCheck).where(
            BackgroundCheck.id == check_id,
            BackgroundCheck.company_id == current_user.company_id,
        )
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Background check not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(check, field, value)

    await db.commit()
    await db.refresh(check)
    return _to_response(check)


@router.delete("/{check_id}", status_code=204)
async def delete_background_check(
    check_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BackgroundCheck).where(
            BackgroundCheck.id == check_id,
            BackgroundCheck.company_id == current_user.company_id,
        )
    )
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Background check not found")

    await db.delete(check)
    await db.commit()
