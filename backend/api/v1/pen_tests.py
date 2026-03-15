import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.pen_test import PenTest
from models.user import User
from schemas.pen_test import PenTestCreate, PenTestResponse, PenTestUpdate

router = APIRouter(prefix="/pen-tests", tags=["pen-tests"])


def _to_response(pt: PenTest) -> PenTestResponse:
    return PenTestResponse(
        id=str(pt.id),
        company_id=str(pt.company_id),
        vendor_name=pt.vendor_name,
        status=pt.status,
        scope=pt.scope,
        conducted_at=pt.conducted_at,
        next_scheduled_at=pt.next_scheduled_at,
        critical_count=pt.critical_count,
        high_count=pt.high_count,
        medium_count=pt.medium_count,
        low_count=pt.low_count,
        summary=pt.summary,
        file_url=pt.file_url,
        remediation_notes=pt.remediation_notes,
        created_at=pt.created_at,
        updated_at=pt.updated_at,
    )


@router.get("", response_model=list[PenTestResponse])
async def list_pen_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PenTest)
        .where(PenTest.company_id == current_user.company_id)
        .order_by(PenTest.created_at.desc())
    )
    return [_to_response(pt) for pt in result.scalars().all()]


@router.post("", response_model=PenTestResponse, status_code=201)
async def create_pen_test(
    body: PenTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = PenTest(
        company_id=current_user.company_id,
        vendor_name=body.vendor_name,
        status=body.status,
        scope=body.scope,
        conducted_at=body.conducted_at,
        next_scheduled_at=body.next_scheduled_at,
        critical_count=body.critical_count,
        high_count=body.high_count,
        medium_count=body.medium_count,
        low_count=body.low_count,
        summary=body.summary,
        remediation_notes=body.remediation_notes,
    )
    db.add(pt)
    await db.commit()
    await db.refresh(pt)
    return _to_response(pt)


@router.patch("/{pen_test_id}", response_model=PenTestResponse)
async def update_pen_test(
    pen_test_id: uuid.UUID,
    body: PenTestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PenTest).where(
            PenTest.id == pen_test_id,
            PenTest.company_id == current_user.company_id,
        )
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Pen test not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(pt, field, value)

    await db.commit()
    await db.refresh(pt)
    return _to_response(pt)


@router.delete("/{pen_test_id}", status_code=204)
async def delete_pen_test(
    pen_test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PenTest).where(
            PenTest.id == pen_test_id,
            PenTest.company_id == current_user.company_id,
        )
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Pen test not found")
    await db.delete(pt)
    await db.commit()
