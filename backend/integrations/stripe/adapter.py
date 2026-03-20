"""
Stripe integration adapter.

Collects webhook endpoints, Radar value lists, recent subscription events,
and account configuration from the Stripe API (https://api.stripe.com/v1).
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

STRIPE_API = "https://api.stripe.com/v1"


class StripeIntegration(IntegrationAdapter):
    """Collects access-control evidence from Stripe."""

    def __init__(self) -> None:
        self._api_key: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate the API key by fetching /account."""
        api_key = (credentials.get("api_key") or "").strip()
        if not api_key:
            raise IntegrationAuthError("Stripe api_key is required.")

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{STRIPE_API}/account",
                auth=httpx.BasicAuth(api_key, ""),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid or unauthorized Stripe API key.")
            r.raise_for_status()

        self._api_key = api_key
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        auth = httpx.BasicAuth(self._api_key, "")
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # ── Account ────────────────────────────────────────────────
            try:
                account = await self._collect_account(client, auth)
                raw.extend(account)
            except Exception:
                logger.exception("Stripe: failed to collect account")

            # ── Webhook endpoints ──────────────────────────────────────
            try:
                webhooks = await self._collect_webhooks(client, auth)
                raw.extend(webhooks)
            except Exception:
                logger.exception("Stripe: failed to collect webhook endpoints")

            # ── Radar value lists ──────────────────────────────────────
            try:
                radar_lists = await self._collect_radar_lists(client, auth)
                raw.extend(radar_lists)
            except Exception:
                logger.exception("Stripe: failed to collect Radar value lists")

            # ── Subscription events ────────────────────────────────────
            try:
                events = await self._collect_events(client, auth)
                raw.extend(events)
            except Exception:
                logger.exception("Stripe: failed to collect subscription events")

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "account":
                result.append(self._norm_account(item, now))
            elif t == "webhook":
                result.append(self._norm_webhook(item, now))
            elif t == "radar_list":
                result.append(self._norm_radar_list(item, now))
            # "event" items are informational; skip separate normalization
            # unless a caller explicitly wants them — they don't have a
            # defined control mapping in the spec.

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_account(
        self, client: httpx.AsyncClient, auth: httpx.BasicAuth
    ) -> list[dict]:
        r = await client.get(f"{STRIPE_API}/account", auth=auth)
        r.raise_for_status()
        data = r.json()
        settings = data.get("settings", {})
        dashboard = settings.get("dashboard", {})
        return [{
            "_type": "account",
            "id": data.get("id"),
            "business_type": data.get("business_type"),
            "charges_enabled": data.get("charges_enabled"),
            "payouts_enabled": data.get("payouts_enabled"),
            "country": data.get("country"),
            "timezone": dashboard.get("timezone"),
        }]

    async def _collect_webhooks(
        self, client: httpx.AsyncClient, auth: httpx.BasicAuth
    ) -> list[dict]:
        webhooks: list[dict] = []
        starting_after: str | None = None

        while True:
            params: dict = {"limit": 100}
            if starting_after:
                params["starting_after"] = starting_after

            r = await client.get(f"{STRIPE_API}/webhook_endpoints", auth=auth, params=params)
            r.raise_for_status()
            body = r.json()
            items = body.get("data", [])
            if not items:
                break
            for wh in items:
                webhooks.append({
                    "_type": "webhook",
                    "id": wh.get("id"),
                    "url": wh.get("url"),
                    "enabled_events": wh.get("enabled_events", []),
                    "status": wh.get("status"),
                    "created": wh.get("created"),
                })
            if not body.get("has_more"):
                break
            starting_after = items[-1]["id"]

        return webhooks

    async def _collect_radar_lists(
        self, client: httpx.AsyncClient, auth: httpx.BasicAuth
    ) -> list[dict]:
        radar_lists: list[dict] = []
        starting_after: str | None = None

        while True:
            params: dict = {"limit": 100}
            if starting_after:
                params["starting_after"] = starting_after

            r = await client.get(f"{STRIPE_API}/radar/value_lists", auth=auth, params=params)
            r.raise_for_status()
            body = r.json()
            items = body.get("data", [])
            if not items:
                break
            for rl in items:
                radar_lists.append({
                    "_type": "radar_list",
                    "id": rl.get("id"),
                    "name": rl.get("name"),
                    "item_type": rl.get("item_type"),
                    "created": rl.get("created"),
                })
            if not body.get("has_more"):
                break
            starting_after = items[-1]["id"]

        return radar_lists

    async def _collect_events(
        self, client: httpx.AsyncClient, auth: httpx.BasicAuth
    ) -> list[dict]:
        events: list[dict] = []
        starting_after: str | None = None

        while True:
            params: dict = {"limit": 100, "type": "customer.subscription.created"}
            if starting_after:
                params["starting_after"] = starting_after

            r = await client.get(f"{STRIPE_API}/events", auth=auth, params=params)
            r.raise_for_status()
            body = r.json()
            items = body.get("data", [])
            if not items:
                break
            for ev in items:
                events.append({
                    "_type": "event",
                    "id": ev.get("id"),
                    "type": ev.get("type"),
                    "created": ev.get("created"),
                    "livemode": ev.get("livemode"),
                })
            if not body.get("has_more"):
                break
            starting_after = items[-1]["id"]

        return events

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_account(self, raw: dict, now: str) -> dict:
        return {
            "integration": "stripe",
            "control": "access_control",
            "evidence_type": "stripe_account",
            "source_id": raw.get("id", "account"),
            "timestamp": now,
            "data": {
                "business_type": raw.get("business_type"),
                "charges_enabled": raw.get("charges_enabled"),
                "payouts_enabled": raw.get("payouts_enabled"),
                "country": raw.get("country"),
                "timezone": raw.get("timezone"),
            },
        }

    def _norm_webhook(self, raw: dict, now: str) -> dict:
        created = raw.get("created")
        timestamp = (
            datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
            if isinstance(created, (int, float))
            else now
        )
        return {
            "integration": "stripe",
            "control": "access_control",
            "evidence_type": "stripe_webhooks",
            "source_id": raw.get("id", "unknown"),
            "timestamp": timestamp,
            "data": {
                "url": raw.get("url"),
                "enabled_events": raw.get("enabled_events", []),
                "status": raw.get("status"),
            },
        }

    def _norm_radar_list(self, raw: dict, now: str) -> dict:
        created = raw.get("created")
        timestamp = (
            datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
            if isinstance(created, (int, float))
            else now
        )
        return {
            "integration": "stripe",
            "control": "access_control",
            "evidence_type": "stripe_radar_lists",
            "source_id": raw.get("id", "unknown"),
            "timestamp": timestamp,
            "data": {
                "name": raw.get("name"),
                "item_type": raw.get("item_type"),
            },
        }
