import logging
import uuid
from datetime import datetime, timezone

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


@router.post("/schedule-next", response_model=ManagementReviewResponse, status_code=201)
async def schedule_next_management_review(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a pre-filled management review for the current quarter if one does not already exist."""
    now = datetime.now(timezone.utc)
    q = (now.month - 1) // 3 + 1
    year = now.year

    # Quarter boundaries
    q_starts = {1: (year, 1, 1), 2: (year, 4, 1), 3: (year, 7, 1), 4: (year, 10, 1)}
    q_ends   = {1: (year, 3, 31), 2: (year, 6, 30), 3: (year, 9, 30), 4: (year, 12, 31)}
    qs_y, qs_m, qs_d = q_starts[q]
    qe_y, qe_m, qe_d = q_ends[q]
    quarter_start = datetime(qs_y, qs_m, qs_d, tzinfo=timezone.utc)
    quarter_end   = datetime(qe_y, qe_m, qe_d, 23, 59, 59, tzinfo=timezone.utc)

    existing = await db.execute(
        select(ManagementReview).where(
            ManagementReview.company_id == current_user.company_id,
            ManagementReview.review_date >= quarter_start,
            ManagementReview.review_date <= quarter_end,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"A management review for Q{q} {year} already exists.")

    # Next quarter
    nq = (q % 4) + 1
    ny = year + 1 if q == 4 else year
    nq_ends = {1: (ny, 3, 31), 2: (ny, 6, 30), 3: (ny, 9, 30), 4: (ny, 12, 31)}
    nqe_y, nqe_m, nqe_d = nq_ends[nq]

    review_date = datetime(qe_y, qe_m, qe_d, tzinfo=timezone.utc)
    next_review_date = datetime(nqe_y, nqe_m, nqe_d, tzinfo=timezone.utc)

    review = ManagementReview(
        company_id=current_user.company_id,
        review_date=review_date,
        outcome="satisfactory",
        inputs_summary=(
            f"Q{q} {year} management review covering: compliance posture and score trend, "
            "risk register status and open items, audit findings and corrective actions, "
            "incident summary, vulnerability status, training completion, and vendor risk."
        ),
        action_items=[],
        next_review_date=next_review_date,
        notes=f"Auto-scheduled for Q{q} {year}. Update with attendees, decisions, and action items after the review meeting.",
    )
    db.add(review)
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
