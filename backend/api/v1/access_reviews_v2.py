"""Access review campaigns with per-user item tracking."""
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
from models.access_review_v2 import AccessReviewV2, AccessReviewItem
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/access-reviews-v2", tags=["access-reviews-v2"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    name: str
    framework: str = "soc2"
    review_period: str = "quarterly"
    due_date: Optional[str] = None


class ItemCreate(BaseModel):
    user_email: str
    user_name: Optional[str] = None
    system_name: str
    role_or_permission: Optional[str] = None


class ItemDecision(BaseModel):
    decision: str  # approved | revoked | pending
    notes: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _item_dict(item: AccessReviewItem) -> dict:
    return {
        "id": str(item.id),
        "review_id": str(item.review_id),
        "user_email": item.user_email,
        "user_name": item.user_name,
        "system_name": item.system_name,
        "role_or_permission": item.role_or_permission,
        "decision": item.decision,
        "reviewed_by": item.reviewed_by,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "notes": item.notes,
        "created_at": item.created_at.isoformat(),
    }


def _review_dict(review: AccessReviewV2, items: list, *, include_items: bool = False) -> dict:
    total = len(items)
    reviewed = sum(1 for i in items if i.decision != "pending")
    d = {
        "id": str(review.id),
        "company_id": str(review.company_id),
        "name": review.name,
        "framework": review.framework,
        "review_period": review.review_period,
        "status": review.status,
        "due_date": review.due_date.isoformat() if review.due_date else None,
        "created_by_id": str(review.created_by_id) if review.created_by_id else None,
        "completed_at": review.completed_at.isoformat() if review.completed_at else None,
        "created_at": review.created_at.isoformat(),
        "total_items": total,
        "reviewed_items": reviewed,
    }
    if include_items:
        d["items"] = [_item_dict(i) for i in items]
    return d


async def _get_review_or_404(review_id: uuid.UUID, company_id: uuid.UUID, db: AsyncSession) -> AccessReviewV2:
    result = await db.execute(
        select(AccessReviewV2).where(
            AccessReviewV2.id == review_id,
            AccessReviewV2.company_id == company_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Access review not found")
    return review


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AccessReviewV2)
        .where(AccessReviewV2.company_id == current_user.company_id)
        .order_by(AccessReviewV2.created_at.desc())
    )
    reviews = result.scalars().all()
    out = []
    for review in reviews:
        items_result = await db.execute(
            select(AccessReviewItem).where(AccessReviewItem.review_id == review.id)
        )
        items = items_result.scalars().all()
        out.append(_review_dict(review, items))
    return out


@router.post("", status_code=201)
async def create_review(
    body: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    due_date = None
    if body.due_date:
        try:
            due_date = datetime.fromisoformat(body.due_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid due_date format")

    now = datetime.now(timezone.utc)
    review = AccessReviewV2(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        name=body.name,
        framework=body.framework,
        review_period=body.review_period,
        status="in_progress",
        due_date=due_date,
        created_by_id=current_user.id,
        created_at=now,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return _review_dict(review, [])


@router.get("/{review_id}")
async def get_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review_or_404(review_id, current_user.company_id, db)
    items_result = await db.execute(
        select(AccessReviewItem).where(AccessReviewItem.review_id == review.id)
    )
    items = items_result.scalars().all()
    return _review_dict(review, list(items), include_items=True)


@router.post("/{review_id}/items", status_code=201)
async def add_item(
    review_id: uuid.UUID,
    body: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review_or_404(review_id, current_user.company_id, db)
    now = datetime.now(timezone.utc)
    item = AccessReviewItem(
        id=uuid.uuid4(),
        review_id=review.id,
        user_email=body.user_email,
        user_name=body.user_name,
        system_name=body.system_name,
        role_or_permission=body.role_or_permission,
        decision="pending",
        created_at=now,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _item_dict(item)


@router.patch("/{review_id}/items/{item_id}")
async def update_item_decision(
    review_id: uuid.UUID,
    item_id: uuid.UUID,
    body: ItemDecision,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_review_or_404(review_id, current_user.company_id, db)
    result = await db.execute(
        select(AccessReviewItem).where(
            AccessReviewItem.id == item_id,
            AccessReviewItem.review_id == review_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.decision = body.decision
    if body.notes is not None:
        item.notes = body.notes
    item.reviewed_by = current_user.email
    item.reviewed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(item)
    return _item_dict(item)


@router.delete("/{review_id}/items/{item_id}", status_code=204)
async def delete_item(
    review_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_review_or_404(review_id, current_user.company_id, db)
    result = await db.execute(
        select(AccessReviewItem).where(
            AccessReviewItem.id == item_id,
            AccessReviewItem.review_id == review_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)
    await db.commit()


@router.post("/{review_id}/complete")
async def complete_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review_or_404(review_id, current_user.company_id, db)
    items_result = await db.execute(
        select(AccessReviewItem).where(AccessReviewItem.review_id == review.id)
    )
    items = items_result.scalars().all()

    pending_count = sum(1 for i in items if i.decision == "pending")
    if pending_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete: {pending_count} item(s) still pending decision"
        )

    review.status = "completed"
    review.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(review)
    return _review_dict(review, list(items))


@router.delete("/{review_id}", status_code=204)
async def delete_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    review = await _get_review_or_404(review_id, current_user.company_id, db)
    await db.delete(review)
    await db.commit()
