import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.access_review import AccessReview
from models.evidence import Evidence
from models.user import User
from schemas.access_review import AccessReviewCreate, AccessReviewResponse, AccessReviewUpdate

router = APIRouter(prefix="/access-reviews", tags=["access-reviews"])


async def _build_response(review: AccessReview, db: AsyncSession) -> AccessReviewResponse:
    reviewer_name: str | None = None
    if review.reviewer_user_id:
        res = await db.execute(
            select(User.full_name, User.email).where(User.id == review.reviewer_user_id)
        )
        row = res.one_or_none()
        if row:
            reviewer_name = row.full_name or row.email

    return AccessReviewResponse(
        id=str(review.id),
        company_id=str(review.company_id),
        title=review.title,
        period=review.period,
        reviewer_user_id=str(review.reviewer_user_id) if review.reviewer_user_id else None,
        reviewer_name=reviewer_name,
        status=review.status,
        due_date=review.due_date,
        completed_at=review.completed_at,
        users_reviewed=review.users_reviewed,
        access_changes=review.access_changes,
        scope=review.scope,
        findings=review.findings,
        notes=review.notes,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.get("", response_model=list[AccessReviewResponse])
async def list_access_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AccessReview)
        .where(AccessReview.company_id == current_user.company_id)
        .order_by(AccessReview.created_at.desc())
    )
    reviews = result.scalars().all()
    return [await _build_response(r, db) for r in reviews]


@router.post("", response_model=AccessReviewResponse, status_code=201)
async def create_access_review(
    body: AccessReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reviewer_id: uuid.UUID | None = None
    if body.reviewer_user_id:
        res = await db.execute(
            select(User).where(
                User.id == uuid.UUID(body.reviewer_user_id),
                User.company_id == current_user.company_id,
            )
        )
        reviewer = res.scalar_one_or_none()
        if not reviewer:
            raise HTTPException(status_code=400, detail="reviewer_user_id does not belong to your company")
        reviewer_id = reviewer.id

    review = AccessReview(
        company_id=current_user.company_id,
        title=body.title,
        period=body.period,
        reviewer_user_id=reviewer_id,
        due_date=body.due_date,
        scope=body.scope,
        status="open",
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return await _build_response(review, db)


@router.patch("/{review_id}", response_model=AccessReviewResponse)
async def update_access_review(
    review_id: uuid.UUID,
    body: AccessReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AccessReview).where(
            AccessReview.id == review_id,
            AccessReview.company_id == current_user.company_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Access review not found")

    update_data = body.model_dump(exclude_unset=True)

    if "reviewer_user_id" in update_data:
        raw_id = update_data.pop("reviewer_user_id")
        if raw_id is None:
            review.reviewer_user_id = None
        else:
            res = await db.execute(
                select(User).where(
                    User.id == uuid.UUID(raw_id),
                    User.company_id == current_user.company_id,
                )
            )
            reviewer = res.scalar_one_or_none()
            if not reviewer:
                raise HTTPException(status_code=400, detail="reviewer_user_id does not belong to your company")
            review.reviewer_user_id = reviewer.id

    for field, value in update_data.items():
        setattr(review, field, value)

    await db.commit()
    await db.refresh(review)
    return await _build_response(review, db)


@router.post("/generate", response_model=AccessReviewResponse, status_code=201)
async def generate_access_review(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Auto-generate a pre-populated access review by counting users across all connected integrations."""
    USER_EVIDENCE_TYPES = {
        "iam_users", "github_members", "slack_users",
        "google_users", "google_workspace_users",
        "okta_users", "azure_ad_users", "azure_users", "jira_users",
    }

    evidence_result = await db.execute(
        select(Evidence).where(
            Evidence.company_id == current_user.company_id,
            Evidence.evidence_type.in_(USER_EVIDENCE_TYPES),
        )
    )
    user_evidence = evidence_result.scalars().all()

    by_integration: dict[str, list] = {}
    for ev in user_evidence:
        by_integration.setdefault(ev.integration, []).append(ev)

    total_users = len(user_evidence)

    scope_lines = []
    for integration, evs in sorted(by_integration.items()):
        label = integration.replace("_", " ").title()
        scope_lines.append(f"{label}: {len(evs)} user(s)")

    if scope_lines:
        scope = "\n".join(scope_lines)
    else:
        scope = "No integration user data found. Connect integrations (GitHub, AWS, Okta, etc.) to auto-populate."

    now = datetime.now(timezone.utc)
    q = (now.month - 1) // 3 + 1
    period = f"Q{q} {now.year}"

    review = AccessReview(
        company_id=current_user.company_id,
        title=f"Quarterly Access Review — {period}",
        period=period,
        status="open",
        users_reviewed=total_users,
        scope=scope,
    )
    db.add(review)
    await db.commit()
    await db.refresh(review)
    return await _build_response(review, db)


@router.delete("/{review_id}", status_code=204)
async def delete_access_review(
    review_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AccessReview).where(
            AccessReview.id == review_id,
            AccessReview.company_id == current_user.company_id,
        )
    )
    review = result.scalar_one_or_none()
    if not review:
        raise HTTPException(status_code=404, detail="Access review not found")
    await db.delete(review)
    await db.commit()
