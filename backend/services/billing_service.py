import hashlib
import hmac
import logging
import uuid
from urllib.parse import urlencode

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
    if not settings.ls_api_key or not settings.app_ls_store_id or not settings.ls_growth_variant_id:
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
                    "redirect_url": f"{settings.app_frontend_url}/billing/success",
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": settings.app_ls_store_id}},
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

        prev_plan = company.plan
        company.ls_subscription_id = ls_sub_id
        company.ls_customer_id = ls_customer_id
        company.subscription_status = status
        company.plan = "growth" if status in active_statuses else "free"
        await db.commit()
        logger.info("Billing: company=%s plan=%s status=%s", company_id, company.plan, status)
        if prev_plan != company.plan:
            from services.audit_service import log_action
            action = "plan.upgraded" if company.plan == "growth" else "plan.downgraded"
            await log_action(db, company_id, action, metadata={"status": status})

    elif event_name == "order_created":
        # One-time payment for partner client slot
        if custom.get("event_type") != "partner_client":
            return  # not our event

        payment_id_str = custom.get("payment_id")
        partner_company_id_str = custom.get("partner_company_id")
        client_name = custom.get("client_name", "New Client")
        ls_order_id = str(data.get("id", ""))

        if not payment_id_str or not partner_company_id_str:
            logger.warning("order_created webhook missing payment_id or partner_company_id")
            return

        # Idempotency — skip if already processed
        from models.partner_client_payment import PartnerClientPayment
        dup = await db.execute(
            select(PartnerClientPayment).where(PartnerClientPayment.ls_order_id == ls_order_id)
        )
        if dup.scalar_one_or_none():
            return

        # Find the pending payment record
        payment_result = await db.execute(
            select(PartnerClientPayment).where(PartnerClientPayment.id == payment_id_str)
        )
        payment_row = payment_result.scalar_one_or_none()
        if not payment_row:
            logger.warning("order_created: payment record %s not found", payment_id_str)
            return

        # Provision client company
        import secrets
        from datetime import datetime, timezone
        from models.trust_page import TrustPage, slugify

        partner_company_id = uuid.UUID(partner_company_id_str)
        client_company = Company(
            name=client_name,
            plan="growth",
            is_partner_account=False,
            partner_id=partner_company_id,
            onboarding_completed=True,
        )
        db.add(client_company)
        await db.flush()

        # Auto-create Trust Page for the client
        base_slug = slugify(client_name)
        slug = base_slug
        for _ in range(10):
            existing_slug = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
            if not existing_slug.scalar_one_or_none():
                break
            slug = f"{base_slug}-{secrets.token_hex(3)}"

        trust_page = TrustPage(company_id=client_company.id, slug=slug)
        db.add(trust_page)

        # Update payment record
        payment_row.status = "paid"
        payment_row.client_company_id = client_company.id
        payment_row.ls_order_id = ls_order_id
        payment_row.paid_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(
            "Partner client provisioned: partner=%s client=%s slug=%s",
            partner_company_id, client_company.id, slug,
        )

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
            from services.audit_service import log_action
            await log_action(db, company.id, "plan.downgraded", metadata={"event": event_name})


async def create_partner_client_checkout_url(
    partner_company_id: uuid.UUID,
    client_name: str,
    payment_id: uuid.UUID,
    user_email: str,
) -> str:
    """Create a LemonSqueezy $99 one-time checkout URL for a partner client slot."""
    if not settings.ls_api_key or not settings.app_ls_store_id or not settings.ls_partner_client_variant_id:
        raise ValueError("Partner billing is not configured on this server (LS_PARTNER_CLIENT_VARIANT_ID missing).")

    payload = {
        "data": {
            "type": "checkouts",
            "attributes": {
                "checkout_data": {
                    "email": user_email,
                    "custom": {
                        "partner_company_id": str(partner_company_id),
                        "payment_id": str(payment_id),
                        "client_name": client_name,
                        "event_type": "partner_client",
                    },
                },
                "product_options": {
                    "redirect_url": (
                        f"{settings.app_frontend_url}/partner/clients/success?"
                        + urlencode({"payment_id": str(payment_id), "client_name": client_name})
                    ),
                },
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": settings.app_ls_store_id}},
                "variant": {"data": {"type": "variants", "id": settings.ls_partner_client_variant_id}},
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
