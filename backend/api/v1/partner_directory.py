from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models.partner_directory import PartnerDirectoryEntry
from schemas.partner_directory import PartnerDirectoryEntryResponse

router = APIRouter(prefix="/partner-directory", tags=["partner-directory"])


@router.get("", response_model=list[PartnerDirectoryEntryResponse])
async def list_directory(
    partner_type: Optional[str] = Query(None, description="Filter by 'auditor' or 'pen_test'"),
    db: AsyncSession = Depends(get_db),
):
    """Public endpoint — no auth required. Returns the TraceLayer partner directory."""
    query = select(PartnerDirectoryEntry).where(PartnerDirectoryEntry.is_active == True)  # noqa: E712
    if partner_type:
        query = query.where(PartnerDirectoryEntry.partner_type == partner_type)
    query = query.order_by(PartnerDirectoryEntry.is_featured.desc(), PartnerDirectoryEntry.name)

    result = await db.execute(query)
    return result.scalars().all()
