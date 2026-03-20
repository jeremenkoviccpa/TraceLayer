"""
1Password Events API integration adapter.

Collects sign-in attempts, item usage events, and audit events from the
1Password Events API (https://events.1password.com).

All three endpoints use POST with a JSON body to filter/paginate results.
The cursor-based pagination scheme is: if the response contains a
"cursor" field, pass it as { "cursor": <cursor> } in the next request body.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

OP_EVENTS_API = "https://events.1password.com"


class OnePasswordIntegration(IntegrationAdapter):
    """Collects access-control evidence from 1Password Events API."""

    def __init__(self) -> None:
        self._token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate the service account token by posting to /api/v1/signinattempts."""
        token = (credentials.get("service_account_token") or "").strip()
        if not token:
            raise IntegrationAuthError("1Password service_account_token is required.")

        headers = self._auth_headers(token)
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{OP_EVENTS_API}/api/v1/signinattempts",
                headers=headers,
                json={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid 1Password service account token.")
            r.raise_for_status()

        self._token = token
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        headers = self._auth_headers(self._token)
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # ── Sign-in attempts ───────────────────────────────────────
            try:
                sign_ins = await self._collect_sign_in_attempts(client, headers)
                raw.extend(sign_ins)
            except Exception:
                logger.exception("1Password: failed to collect sign-in attempts")

            # ── Item usages ────────────────────────────────────────────
            try:
                item_usages = await self._collect_item_usages(client, headers)
                raw.extend(item_usages)
            except Exception:
                logger.exception("1Password: failed to collect item usages")

            # ── Audit events ───────────────────────────────────────────
            try:
                audit_events = await self._collect_audit_events(client, headers)
                raw.extend(audit_events)
            except Exception:
                logger.exception("1Password: failed to collect audit events")

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "sign_in":
                result.append(self._norm_sign_in(item, now))
            elif t == "item_usage":
                result.append(self._norm_item_usage(item, now))
            elif t == "audit_event":
                result.append(self._norm_audit_event(item, now))

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    def _auth_headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _paginate_events(
        self,
        client: httpx.AsyncClient,
        headers: dict,
        endpoint: str,
        event_type: str,
        limit: int = 100,
    ) -> list[dict]:
        """
        Generic paginator for 1Password Events API endpoints.

        The API returns a top-level "items" list and, when more pages exist,
        a "cursor" string.  Pass the cursor back in the next request body.
        """
        results: list[dict] = []
        body: dict[str, Any] = {"limit": limit}

        while True:
            r = await client.post(f"{OP_EVENTS_API}{endpoint}", headers=headers, json=body)
            r.raise_for_status()
            data = r.json()

            items = data.get("items") or []
            for item in items:
                results.append({"_type": event_type, **item})

            cursor = data.get("cursor")
            has_more = data.get("has_more", False)
            if not has_more or not cursor:
                break

            body = {"cursor": cursor}

        return results

    async def _collect_sign_in_attempts(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        return await self._paginate_events(
            client, headers, "/api/v1/signinattempts", "sign_in"
        )

    async def _collect_item_usages(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        return await self._paginate_events(
            client, headers, "/api/v1/itemusages", "item_usage"
        )

    async def _collect_audit_events(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        return await self._paginate_events(
            client, headers, "/api/v1/auditevents", "audit_event"
        )

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_sign_in(self, raw: dict, now: str) -> dict:
        target_user = raw.get("target_user") or {}
        return {
            "integration": "1password",
            "control": "access_control",
            "evidence_type": "1password_sign_ins",
            "source_id": raw.get("uuid") or raw.get("session_uuid") or now,
            "timestamp": raw.get("timestamp") or now,
            "data": {
                "email": target_user.get("email"),
                "type": raw.get("type"),
                "result": raw.get("result"),
                "timestamp": raw.get("timestamp"),
                "country": raw.get("country"),
            },
        }

    def _norm_item_usage(self, raw: dict, now: str) -> dict:
        user = raw.get("user") or {}
        return {
            "integration": "1password",
            "control": "access_control",
            "evidence_type": "1password_item_usage",
            "source_id": raw.get("uuid") or now,
            "timestamp": raw.get("timestamp") or now,
            "data": {
                "email": user.get("email"),
                "vault_id": raw.get("vault_uuid") or raw.get("vault_id"),
                "action": raw.get("action"),
                "timestamp": raw.get("timestamp"),
            },
        }

    def _norm_audit_event(self, raw: dict, now: str) -> dict:
        return {
            "integration": "1password",
            "control": "access_control",
            "evidence_type": "1password_audit_events",
            "source_id": raw.get("uuid") or now,
            "timestamp": raw.get("timestamp") or now,
            "data": {
                "actor_uuid": raw.get("actor_uuid"),
                "action": raw.get("action"),
                "timestamp": raw.get("timestamp"),
                "object_type": raw.get("object_type"),
            },
        }
