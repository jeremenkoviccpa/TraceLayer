"""GDPR/privacy subprocessor management."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.subprocessor import Subprocessor
from models.user import User
from services.audit_service import log_action

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/subprocessors", tags=["subprocessors"])

DATA_CATEGORIES = [
    "personal_identifiers", "contact_data", "financial_data", "health_data",
    "usage_data", "device_data", "location_data", "behavioral_data",
    "credentials", "communications", "employee_data", "biometric_data",
]

LEGAL_BASES = ["consent", "contract", "legal_obligation", "vital_interests", "public_task", "legitimate_interests"]
TRANSFER_MECHANISMS = ["adequacy_decision", "standard_contractual_clauses", "binding_corporate_rules", "derogation", "not_applicable"]


class SubprocessorCreate(BaseModel):
    name: str
    country: Optional[str] = None
    purpose: Optional[str] = None
    data_categories: list[str] = []
    legal_basis: Optional[str] = None
    transfer_mechanism: Optional[str] = None
    dpa_signed: bool = False
    dpa_signed_at: Optional[datetime] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None


class SubprocessorUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    purpose: Optional[str] = None
    data_categories: Optional[list[str]] = None
    legal_basis: Optional[str] = None
    transfer_mechanism: Optional[str] = None
    dpa_signed: Optional[bool] = None
    dpa_signed_at: Optional[datetime] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None


def _to_response(s: Subprocessor) -> dict:
    return {
        "id": str(s.id),
        "name": s.name,
        "country": s.country,
        "purpose": s.purpose,
        "data_categories": s.data_categories or [],
        "legal_basis": s.legal_basis,
        "transfer_mechanism": s.transfer_mechanism,
        "dpa_signed": s.dpa_signed,
        "dpa_signed_at": s.dpa_signed_at,
        "website": s.website,
        "contact_email": s.contact_email,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }


@router.get("")
async def list_subprocessors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subprocessor)
        .where(Subprocessor.company_id == current_user.company_id)
        .order_by(Subprocessor.name)
    )
    return [_to_response(s) for s in result.scalars().all()]


@router.post("", status_code=201)
async def create_subprocessor(
    body: SubprocessorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    sp = Subprocessor(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        name=body.name,
        country=body.country,
        purpose=body.purpose,
        data_categories=body.data_categories,
        legal_basis=body.legal_basis,
        transfer_mechanism=body.transfer_mechanism,
        dpa_signed=body.dpa_signed,
        dpa_signed_at=body.dpa_signed_at,
        website=body.website,
        contact_email=body.contact_email,
        created_at=now,
        updated_at=now,
    )
    db.add(sp)
    await db.commit()
    await db.refresh(sp)
    await log_action(db, current_user.company_id, "subprocessor.created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="subprocessor", resource_id=str(sp.id),
                     metadata={"name": body.name})
    return _to_response(sp)


@router.patch("/{sp_id}")
async def update_subprocessor(
    sp_id: uuid.UUID,
    body: SubprocessorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sp = (await db.execute(
        select(Subprocessor).where(
            Subprocessor.id == sp_id,
            Subprocessor.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not sp:
        raise HTTPException(status_code=404, detail="Subprocessor not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sp, field, value)
    sp.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sp)
    return _to_response(sp)


@router.delete("/{sp_id}", status_code=204)
async def delete_subprocessor(
    sp_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sp = (await db.execute(
        select(Subprocessor).where(
            Subprocessor.id == sp_id,
            Subprocessor.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not sp:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(sp)
    await db.commit()


@router.get("/meta")
async def get_subprocessor_meta(current_user: User = Depends(get_current_user)):
    """Return available data categories, legal bases, and transfer mechanisms."""
    return {
        "data_categories": DATA_CATEGORIES,
        "legal_bases": LEGAL_BASES,
        "transfer_mechanisms": TRANSFER_MECHANISMS,
    }
