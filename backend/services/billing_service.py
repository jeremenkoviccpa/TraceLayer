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

FREE_INTEGRATION_LIMIT = 3


def _paddle_base() -> str:
    return "https://sandbox-api.paddle.com" if settings.paddle_sandbox else "https://api.paddle.com"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.paddle_api_key}",
        "Content-Type": "application/json",
    }


async def create_checkout_url(company_id: uuid.UUID, user_email: str) -> str:
    """Create a Paddle hosted checkout URL for the Growth plan subscription."""
    if not settings.paddle_api_key or not settings.paddle_growth_price_id:
        raise ValueError("Paddle is not configured on this server.")

    payload = {
        "items": [{"price_id": settings.paddle_growth_price_id, "quantity": 1}],
        "customer": {"email": user_email},
        "custom_data": {"company_id": str(company_id)},
        "settings": {
            "success_url": f"{settings.app_frontend_url}/billing/success",
            "allow_logout": False,
        },
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_paddle_base()}/transactions",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    url = data.get("data", {}).get("checkout", {}).get("url")
    if not url:
        raise RuntimeError(f"No checkout URL in Paddle response: {data}")
    return url


async def get_customer_portal_url(subscription_id: str) -> str:
    """Return the Paddle customer portal URL for managing/cancelling a subscription.

    Paddle provides per-subscription management URLs. We fetch the subscription
    and return the customer portal URL so they can update payment or cancel.
    """
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{_paddle_base()}/subscriptions/{subscription_id}",
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    sub_data = data.get("data", {})
    customer_id = sub_data.get("customer_id")

    # Prefer the hosted customer portal (requires a one-time auth token)
    if customer_id:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                token_resp = await client.post(
                    f"{_paddle_base()}/customers/{customer_id}/auth-token",
                    headers=_headers(),
                )
                token_resp.raise_for_status()
                token = token_resp.json().get("data", {}).get("token")
            if token:
                base = "https://sandbox-customer.paddle.com" if settings.paddle_sandbox else "https://customer.paddle.com"
                return f"{base}?token={token}"
        except Exception as exc:
            logger.warning("Could not get Paddle customer portal token: %s", exc)

    # Fallback: direct management URLs embedded in the subscription
    mgmt = sub_data.get("management_urls", {})
    url = mgmt.get("update_payment_method") or mgmt.get("cancel")
    if url:
        return url

    raise RuntimeError("Could not retrieve portal URL from Paddle")


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify Paddle webhook signature.

    Paddle sends: Paddle-Signature: ts=1234567890;h1=<hex>
    Signed payload: "{ts}:{raw_body}"
    """
    if not settings.paddle_webhook_secret or not signature:
        return False
    try:
        parts = dict(p.split("=", 1) for p in signature.split(";"))
        ts = parts.get("ts", "")
        h1 = parts.get("h1", "")
        signed = f"{ts}:{payload.decode()}"
        expected = hmac.new(
            settings.paddle_webhook_secret.encode(),
            signed.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, h1)
    except Exception:
        return False


async def handle_webhook(event_type: str, data: dict, db: AsyncSession) -> None:
    """Process a Paddle webhook event.

    Paddle webhook body structure:
      { "event_type": "subscription.created", "data": { ... } }

    Subscription data:  data.id, data.customer_id, data.status, data.custom_data
    Transaction data:   data.id, data.customer_id, data.status, data.custom_data
    """
    sub_id = str(data.get("id", ""))
    customer_id = str(data.get("customer_id", ""))
    status = data.get("status", "")
    custom = data.get("custom_data") or {}

    # ── Subscription lifecycle ───────────────────────────────────────────────
    if event_type in ("subscription.created", "subscription.updated", "subscription.resumed"):
        company_id_str = custom.get("company_id")
        if not company_id_str:
            logger.warning("Paddle webhook %s missing company_id in custom_data", event_type)
            return
        try:
            company_id = uuid.UUID(company_id_str)
        except ValueError:
            logger.warning("Paddle webhook %s invalid company_id: %s", event_type, company_id_str)
            return

        result = await db.execute(select(Company).where(Company.id == company_id))
        company = result.scalar_one_or_none()
        if not company:
            logger.warning("Paddle webhook %s: company %s not found", event_type, company_id)
            return

        active_statuses = {"active", "trialing"}
        prev_plan = company.plan
        company.ls_subscription_id = sub_id      # reusing existing column
        company.ls_customer_id = customer_id      # reusing existing column
        company.subscription_status = status
        company.plan = "growth" if status in active_statuses else "free"
        await db.commit()
        logger.info("Paddle billing: company=%s plan=%s status=%s", company_id, company.plan, status)

        if prev_plan != company.plan:
            from services.audit_service import log_action
            action = "plan.upgraded" if company.plan == "growth" else "plan.downgraded"
            await log_action(db, company_id, action, metadata={"status": status})

    # ── Subscription cancelled / past_due ────────────────────────────────────
    elif event_type in ("subscription.canceled", "subscription.past_due"):
        result = await db.execute(
            select(Company).where(Company.ls_subscription_id == sub_id)
        )
        company = result.scalar_one_or_none()
        if company:
            company.subscription_status = status
            company.plan = "free"
            await db.commit()
            logger.info("Paddle billing: company=%s downgraded (event=%s)", company.id, event_type)
            from services.audit_service import log_action
            await log_action(db, company.id, "plan.downgraded", metadata={"event": event_type})

    # ── One-time transaction: partner client slot ────────────────────────────
    elif event_type == "transaction.completed":
        if custom.get("event_type") != "partner_client":
            return

        payment_id_str = custom.get("payment_id")
        partner_company_id_str = custom.get("partner_company_id")
        client_name = custom.get("client_name", "New Client")
        txn_id = str(data.get("id", ""))

        if not payment_id_str or not partner_company_id_str:
            logger.warning("transaction.completed webhook missing payment_id or partner_company_id")
            return

        # Idempotency
        from models.partner_client_payment import PartnerClientPayment
        dup = await db.execute(
            select(PartnerClientPayment).where(PartnerClientPayment.ls_order_id == txn_id)
        )
        if dup.scalar_one_or_none():
            return

        payment_result = await db.execute(
            select(PartnerClientPayment).where(PartnerClientPayment.id == payment_id_str)
        )
        payment_row = payment_result.scalar_one_or_none()
        if not payment_row:
            logger.warning("transaction.completed: payment record %s not found", payment_id_str)
            return

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

        base_slug = slugify(client_name)
        slug = base_slug
        for _ in range(10):
            existing_slug = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
            if not existing_slug.scalar_one_or_none():
                break
            slug = f"{base_slug}-{secrets.token_hex(3)}"

        trust_page = TrustPage(company_id=client_company.id, slug=slug)
        db.add(trust_page)

        payment_row.status = "paid"
        payment_row.client_company_id = client_company.id
        payment_row.ls_order_id = txn_id
        payment_row.paid_at = datetime.now(timezone.utc)

        await db.commit()
        logger.info(
            "Paddle: partner client provisioned: partner=%s client=%s slug=%s",
            partner_company_id, client_company.id, slug,
        )


async def create_partner_client_checkout_url(
    partner_company_id: uuid.UUID,
    client_name: str,
    payment_id: uuid.UUID,
    user_email: str,
) -> str:
    """Create a Paddle one-time checkout URL for a partner client slot."""
    if not settings.paddle_api_key or not settings.paddle_partner_client_price_id:
        raise ValueError("Partner billing is not configured (PADDLE_PARTNER_CLIENT_PRICE_ID missing).")

    success_url = (
        f"{settings.app_frontend_url}/partner/clients/success?"
        + urlencode({"payment_id": str(payment_id), "client_name": client_name})
    )

    payload = {
        "items": [{"price_id": settings.paddle_partner_client_price_id, "quantity": 1}],
        "customer": {"email": user_email},
        "custom_data": {
            "partner_company_id": str(partner_company_id),
            "payment_id": str(payment_id),
            "client_name": client_name,
            "event_type": "partner_client",
        },
        "settings": {
            "success_url": success_url,
            "allow_logout": False,
        },
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            f"{_paddle_base()}/transactions",
            json=payload,
            headers=_headers(),
        )
        resp.raise_for_status()
        data = resp.json()

    url = data.get("data", {}).get("checkout", {}).get("url")
    if not url:
        raise RuntimeError(f"No checkout URL in Paddle response: {data}")
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
