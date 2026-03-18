import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.management_review import ManagementReview
from models.user import User
from schemas.management_review import ManagementReviewCreate, ManagementReviewResponse, ManagementReviewUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/management-reviews", tags=["management-reviews"])


@router.get("", response_model=list[ManagementReviewResponse])
async def list_management_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManagementReview)
        .where(ManagementReview.company_id == current_user.company_id)
        .order_by(ManagementReview.review_date.desc())
    )
    return result.scalars().all()


@router.post("", response_model=ManagementReviewResponse, status_code=201)
async def create_management_review(
    body: ManagementReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = ManagementReview(
        company_id=current_user.company_id,
        **body.model_dump(),
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return review


@router.patch("/{review_id}", response_model=ManagementReviewResponse)
async def update_management_review(
    review_id: uuid.UUID,
    body: ManagementReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManagementReview).where(
            ManagementReview.id == review_id,
            ManagementReview.company_id == current_user.company_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Management review not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return review


@router.delete("/{review_id}", status_code=204)
async def delete_management_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ManagementReview).where(
            ManagementReview.id == review_id,
            ManagementReview.company_id == current_user.company_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Management review not found")

    await db.delete(review)
    await db.commit()
