import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.subject_request import SubjectRequest
from models.user import User
from schemas.subject_request import SubjectRequestCreate, SubjectRequestResponse, SubjectRequestUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subject-requests", tags=["subject-requests"])


@router.get("", response_model=list[SubjectRequestResponse])
async def list_subject_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubjectRequest)
        .where(SubjectRequest.company_id == current_user.company_id)
        .order_by(SubjectRequest.received_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=SubjectRequestResponse, status_code=201)
async def create_subject_request(
    body: SubjectRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    request = SubjectRequest(
        company_id=current_user.company_id,
        **body.model_dump(),
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)
    return request


@router.patch("/{request_id}", response_model=SubjectRequestResponse)
async def update_subject_request(
    request_id: uuid.UUID,
    body: SubjectRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubjectRequest).where(
            SubjectRequest.id == request_id,
            SubjectRequest.company_id == current_user.company_id,
        )
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Subject request not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(request, field, value)

    await db.commit()
    await db.refresh(request)
    return request


@router.delete("/{request_id}", status_code=204)
async def delete_subject_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SubjectRequest).where(
            SubjectRequest.id == request_id,
            SubjectRequest.company_id == current_user.company_id,
        )
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=404, detail="Subject request not found")

    await db.delete(request)
    await db.commit()
