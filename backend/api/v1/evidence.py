import math
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.evidence import EvidenceResponse
from services.evidence_service import list_evidence
from utils.pagination import Page

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("", response_model=Page[EvidenceResponse])
async def get_evidence(
    control: Optional[str] = Query(None),
    integration: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await list_evidence(
        company_id=current_user.company_id,
        db=db,
        control=control,
        integration=integration,
        page=page,
        page_size=page_size,
    )
    return Page(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )
