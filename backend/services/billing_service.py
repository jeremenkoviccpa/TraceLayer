import hashlib
import hmac
import logging
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.company import Company

logger = logging.getLogger(__name__)

LS_API = "https://api.lemonsqueezy.com/v1"

FREE_INTEGRATION_LIMIT = 3


def _headers() -> dict:
    return {"Authorization": f"Bearer {settings.ls_api_key}", "Accept": "application/vnd.api+json"}


async def create_checkout_url(company_id: uuid.UUID, user_email: str) -> str:
    """Create a LemonSqueezy hosted checkout URL for the Growth plan."""
    if not settings.ls_api_key or not settings.ls_store_id or not settings.ls_growth_variant_id:
        raise ValueError("LemonSqueezy is not configured on this server.")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {"company_id": str(company_id)},
                },
                "product_options": {
                    "redirect_url": f"{settings.frontend_url}/billing/success",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": settings.ls_store_id}},
                "variant": {"data": {"type": "variants", "id": settings.ls_growth_variant_id}},
            },
        }
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{LS_API}/checkouts", json=payload, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    url = data["data"]["attributes"].get("url")
    if not url:
        raise RuntimeError(f"No checkout URL in LemonSqueezy response: {data}")
    return url


async def get_customer_portal_url(ls_subscription_id: str) -> str:
    """Return the LemonSqueezy customer portal URL for managing/cancelling a subscription."""
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{LS_API}/subscriptions/{ls_subscription_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    urls = data["data"]["attributes"].get("urls", {})
    portal = urls.get("customer_portal") or urls.get("update_payment_method")
    if not portal:
        raise RuntimeError("Could not retrieve portal URL from LemonSqueezy")
    return portal


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from X-Signature header."""
    if not settings.ls_webhook_secret:
        return False
    expected = hmac.new(
        settings.ls_webhook_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_webhook(event_name: str, data: dict, meta: dict, db: AsyncSession) -> None:
    """Process a LemonSqueezy subscription webhook event."""
    custom = meta.get("custom_data") or {}
    company_id_str = custom.get("company_id")

    attrs = data.get("attributes", {})
    ls_sub_id = str(data.get("id", ""))
    ls_customer_id = str(attrs.get("customer_id", ""))
    status = attrs.get("status", "")

    # Map LemonSqueezy status → our plan
    active_statuses = {"active", "on_trial"}
    cancelled_statuses = {"cancelled", "expired", "past_due", "unpaid"}

    if event_name in ("subscription_created", "subscription_updated", "subscription_resumed"):
        if not company_id_str:
            logger.warning("Webhook %s missing company_id in custom_data", event_name)
            return
        try:
            company_id = uuid.UUID(company_id_str)
        except ValueError:
            logger.warning("Webhook %s invalid company_id: %s", event_name, company_id_str)
            return

        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            logger.warning("Webhook %s: company %s not found", event_name, company_id)
            return

        company.ls_subscription_id = ls_sub_id
        company.ls_customer_id = ls_customer_id
        company.subscription_status = status
        company.plan = "growth" if status in active_statuses else "free"
        await db.commit()
        logger.info("Billing: company=%s plan=%s status=%s", company_id, company.plan, status)

    elif event_name in ("subscription_cancelled", "subscription_expired"):
        # Find company by subscription ID
        result = await db.execute(
            select(Company).where(Company.ls_subscription_id == ls_sub_id)
        )
        company = result.scalar_one_or_none()
        if company:
            company.subscription_status = status
            company.plan = "free"
            await db.commit()
            logger.info("Billing: company=%s downgraded to free (event=%s)", company.id, event_name)


async def check_integration_limit(company_id: uuid.UUID, db: AsyncSession) -> None:
    """Raise ValueError if free plan has hit the integration limit."""
    from models.integration import Integration
    from sqlalchemy import func

    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company or company.plan != "free":
        return

    count_result = await db.execute(
        select(func.count()).where(Integration.company_id == company_id)
    )
    count = count_result.scalar_one()
    if count >= FREE_INTEGRATION_LIMIT:
        raise ValueError(
            f"Free plan is limited to {FREE_INTEGRATION_LIMIT} integrations. "
            "Upgrade to Growth to connect unlimited integrations."
        )
