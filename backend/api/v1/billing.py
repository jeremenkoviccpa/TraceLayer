import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.company import Company
from models.user import User
from services.billing_service import (
    check_integration_limit,
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
    """Return a hosted LemonSqueezy checkout URL for upgrading to Growth."""
    try:
        url = await create_checkout_url(current_user.company_id, current_user.email)
    except ValueError as exc:
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
    return {
        "plan": company.plan,
        "subscription_status": company.subscription_status,
        "ls_subscription_id": company.ls_subscription_id,
    }


@router.post("/portal")
async def customer_portal(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return the LemonSqueezy customer portal URL to manage or cancel a subscription."""
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
async def lemonsqueezy_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive and process LemonSqueezy subscription webhooks."""
    payload = await request.body()
    signature = request.headers.get("X-Signature", "")

    if not verify_webhook_signature(payload, signature):
        logger.warning("LemonSqueezy webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    body = await request.json() if not payload else __import__("json").loads(payload)
    event_name = body.get("meta", {}).get("event_name", "")
    data = body.get("data", {})
    meta = body.get("meta", {})

    logger.info("LemonSqueezy webhook: event=%s", event_name)

    try:
        await handle_webhook(event_name, data, meta, db)
    except Exception:
        logger.exception("Error handling webhook event=%s", event_name)
        # Return 200 anyway so LemonSqueezy doesn't retry indefinitely
    return {"received": True}
