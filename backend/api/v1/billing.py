import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.company import Company
from models.user import User
from services.billing_service import (
    create_checkout_url,
    get_customer_portal_url,
    handle_webhook,
    verify_webhook_signature,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
async def create_checkout(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return a hosted Paddle checkout URL for upgrading to Growth."""
    import os
    from core.config import settings as _s
    logger.info("PADDLE DEBUG key=%s price=%s sandbox=%s | RAW_KEY=%s RAW_PRICE=%s",
                _s.paddle_sk[:12] if _s.paddle_sk else "EMPTY",
                _s.paddle_growth_price_id or "EMPTY",
                _s.paddle_sandbox,
                os.environ.get("PADDLE_SK", "NOT_IN_ENV")[:12],
                os.environ.get("PADDLE_GROWTH_PRICE_ID", "NOT_IN_ENV"))
    try:
        url = await create_checkout_url(current_user.company_id, current_user.email)
    except ValueError as exc:
        logger.error("PADDLE CONFIG ERROR: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Failed to create checkout for company=%s", current_user.company_id)
        raise HTTPException(status_code=503, detail="Could not create checkout. Try again shortly.")
    return {"checkout_url": url}


@router.get("/subscription")
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return current plan and subscription status for the company."""
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    # Internal accounts always get Growth (frontend also short-circuits for these emails)
    INTERNAL_ADMINS = {"admin@tracelayer.it.com", "jeremenkovic23@gmail.com"}
    effective_plan = "growth" if current_user.email in INTERNAL_ADMINS else company.plan
    return {
        "plan": effective_plan,
        "subscription_status": company.subscription_status,
        "ls_subscription_id": company.ls_subscription_id,
    }


@router.post("/portal")
async def customer_portal(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return the Paddle customer portal URL to manage or cancel a subscription."""
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company or not company.ls_subscription_id:
        raise HTTPException(status_code=404, detail="No active subscription found")
    try:
        url = await get_customer_portal_url(company.ls_subscription_id)
    except Exception:
        logger.exception("Failed to get portal URL for company=%s", current_user.company_id)
        raise HTTPException(status_code=503, detail="Could not retrieve billing portal. Try again shortly.")
    return {"portal_url": url}


@router.post("/webhook", include_in_schema=False)
async def paddle_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive and process Paddle subscription webhooks."""
    payload = await request.body()
    signature = request.headers.get("Paddle-Signature", "")

    if not verify_webhook_signature(payload, signature):
        logger.warning("Paddle webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    body = __import__("json").loads(payload)
    event_type = body.get("event_type", "")
    data = body.get("data", {})

    logger.info("Paddle webhook: event=%s", event_type)

    try:
        await handle_webhook(event_type, data, db)
    except Exception:
        logger.exception("Error handling Paddle webhook event=%s", event_type)
        # Return 200 anyway so Paddle doesn't retry indefinitely
    return {"received": True}
