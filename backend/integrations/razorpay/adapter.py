"""
Razorpay integration adapter.

Collects payments, refunds, and settlements from the Razorpay API
(https://api.razorpay.com/v1) using HTTP Basic authentication.

Credentials:
  key_id     — Razorpay API key ID
  key_secret — Razorpay API key secret
"""

import logging
from datetime import datetime, timedelta, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.razorpay.com/v1"


class RazorpayIntegration(IntegrationAdapter):
    """Collects financial-controls evidence from Razorpay."""

    def __init__(self) -> None:
        self._key_id: str | None = None
        self._key_secret: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by fetching a single payment record."""
        key_id = (credentials.get("key_id") or "").strip()
        key_secret = (credentials.get("key_secret") or "").strip()

        if not key_id or not key_secret:
            raise IntegrationAuthError("key_id and key_secret are required.")

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{_BASE}/payments",
                params={"count": 1},
                auth=(key_id, key_secret),
            )
            if r.status_code == 401:
                raise IntegrationAuthError(
                    "Invalid Razorpay key_id or key_secret."
                )
            if r.status_code not in (200, 204):
                raise RuntimeError(f"Razorpay connect failed HTTP {r.status_code}")

        self._key_id = key_id
        self._key_secret = key_secret
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_payments,
                self._collect_refunds,
                self._collect_settlements,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Razorpay collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "payment":
                result.append(self._norm_payment(item, now))
            elif t == "refund":
                result.append(self._norm_refund(item, now))
            elif t == "settlement":
                result.append(self._norm_settlement(item, now))

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    def _auth(self) -> tuple[str, str]:
        return (self._key_id, self._key_secret)

    async def _collect_payments(self, client: httpx.AsyncClient) -> list[dict]:
        from_epoch = int(
            (datetime.now(timezone.utc) - timedelta(days=30)).timestamp()
        )
        r = await client.get(
            f"{_BASE}/payments",
            params={"count": 100, "from": from_epoch},
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Razorpay payments HTTP {r.status_code}")
        return [
            {"_type": "payment", **item}
            for item in r.json().get("items", [])
        ]

    async def _collect_refunds(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/refunds",
            params={"count": 100},
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Razorpay refunds HTTP {r.status_code}")
        return [
            {"_type": "refund", **item}
            for item in r.json().get("items", [])
        ]

    async def _collect_settlements(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/settlements",
            params={"count": 50},
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Razorpay settlements HTTP {r.status_code}")
        return [
            {"_type": "settlement", **item}
            for item in r.json().get("items", [])
        ]

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _epoch_to_iso(self, value, fallback: str) -> str:
        if value is not None:
            try:
                return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
            except (ValueError, OSError):
                pass
        return fallback

    def _norm_payment(self, raw: dict, now: str) -> dict:
        return {
            "integration": "razorpay",
            "control": "financial_controls",
            "evidence_type": "razorpay_payment",
            "source_id": raw.get("id", ""),
            "timestamp": self._epoch_to_iso(raw.get("created_at"), now),
            "data": {
                "id": raw.get("id"),
                "entity": raw.get("entity"),
                "amount": raw.get("amount"),
                "currency": raw.get("currency"),
                "status": raw.get("status"),
                "method": raw.get("method"),
                "description": raw.get("description"),
                "email": raw.get("email"),
                "contact": raw.get("contact"),
                "captured": raw.get("captured"),
            },
        }

    def _norm_refund(self, raw: dict, now: str) -> dict:
        return {
            "integration": "razorpay",
            "control": "financial_controls",
            "evidence_type": "razorpay_refund",
            "source_id": raw.get("id", ""),
            "timestamp": self._epoch_to_iso(raw.get("created_at"), now),
            "data": {
                "id": raw.get("id"),
                "entity": raw.get("entity"),
                "amount": raw.get("amount"),
                "currency": raw.get("currency"),
                "payment_id": raw.get("payment_id"),
                "status": raw.get("status"),
                "speed_processed": raw.get("speed_processed"),
            },
        }

    def _norm_settlement(self, raw: dict, now: str) -> dict:
        return {
            "integration": "razorpay",
            "control": "financial_controls",
            "evidence_type": "razorpay_settlement",
            "source_id": raw.get("id", ""),
            "timestamp": now,
            "data": {
                "id": raw.get("id"),
                "entity": raw.get("entity"),
                "amount": raw.get("amount"),
                "fees": raw.get("fees"),
                "tax": raw.get("tax"),
                "utr": raw.get("utr"),
                "created_at": raw.get("created_at"),
                "settled": raw.get("settled"),
            },
        }
