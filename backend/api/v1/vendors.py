import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from models.vendor import Vendor
from schemas.vendor import VendorCreate, VendorResponse, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["vendors"])


def _to_response(v: Vendor) -> VendorResponse:
    return VendorResponse(
        id=str(v.id),
        company_id=str(v.company_id),
        name=v.name,
        category=v.category,
        risk_level=v.risk_level,
        website=v.website,
        contact_email=v.contact_email,
        soc2_certified=v.soc2_certified,
        iso27001_certified=v.iso27001_certified,
        hipaa_certified=v.hipaa_certified,
        review_date=v.review_date,
        notes=v.notes,
        report_file_url=v.report_file_url,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor)
        .where(Vendor.company_id == current_user.company_id)
        .order_by(Vendor.name)
    )
    return [_to_response(v) for v in result.scalars().all()]


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(
    body: VendorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    v = Vendor(
        company_id=current_user.company_id,
        name=body.name,
        category=body.category,
        risk_level=body.risk_level,
        website=body.website,
        contact_email=body.contact_email,
        soc2_certified=body.soc2_certified,
        iso27001_certified=body.iso27001_certified,
        hipaa_certified=body.hipaa_certified,
        review_date=body.review_date,
        notes=body.notes,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return _to_response(v)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    body: VendorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.company_id == current_user.company_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(v, field, value)

    await db.commit()
    await db.refresh(v)
    return _to_response(v)


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(
    vendor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.company_id == current_user.company_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.delete(v)
    await db.commit()
