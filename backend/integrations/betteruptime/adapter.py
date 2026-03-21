from __future__ import annotations

"""
Better Uptime integration via Better Stack Uptime REST API v2.

Credentials:
  api_token — Better Uptime API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://uptime.betterstack.com/api/v2"
_MAX_PAGES = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class BetterUptimeIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_token: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()

        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/monitors",
                headers={"Authorization": f"Bearer {api_token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Better Uptime API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Better Uptime connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Pagination helper ──────────────────────────────────────────────────────

    async def _paginate(self, client: httpx.AsyncClient, path: str) -> list[dict]:
        """Follow pagination.next links up to _MAX_PAGES pages."""
        items: list[dict] = []
        url: str | None = f"{_BASE}/{path}"
        pages_fetched = 0

        while url and pages_fetched < _MAX_PAGES:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            body = r.json()
            items.extend(body.get("data", []))
            url = body.get("pagination", {}).get("next")
            pages_fetched += 1

        return items

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_monitors,
                self._collect_incidents,
                self._collect_status_pages,
                self._collect_on_call_calendars,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Better Uptime collection error in %s: %s",
                        fetch_fn.__name__,
                        exc,
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_monitors(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._paginate(client, "monitors")
        return [{"_type": "monitor", **m} for m in items]

    async def _collect_incidents(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._paginate(client, "incidents")
        return [{"_type": "incident", **i} for i in items]

    async def _collect_status_pages(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/status-pages", headers=self._headers())
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return [{"_type": "status_page", **p} for p in r.json().get("data", [])]

    async def _collect_on_call_calendars(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/on-call-calendars", headers=self._headers())
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return [{"_type": "on_call_calendar", **c} for c in r.json().get("data", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "monitor":
                result.append(self._norm_monitor(item))
            elif t == "incident":
                result.append(self._norm_incident(item))
            elif t == "status_page":
                result.append(self._norm_status_page(item))
            elif t == "on_call_calendar":
                result.append(self._norm_on_call_calendar(item))
            # skip error sentinels silently
        return result

    def _norm_monitor(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "betteruptime",
            "control": "infrastructure_security",
            "evidence_type": "betteruptime_monitors",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("created_at") or _now(),
            "data": {
                "url": attrs.get("url"),
                "monitor_type": attrs.get("monitor_type"),
                "status": attrs.get("status"),
                "availability": attrs.get("availability"),
                "paused": attrs.get("paused"),
                "check_frequency": attrs.get("check_frequency"),
            },
        }

    def _norm_incident(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "betteruptime",
            "control": "incident_management",
            "evidence_type": "betteruptime_incidents",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("started_at") or _now(),
            "data": {
                "cause": attrs.get("cause"),
                "started_at": attrs.get("started_at"),
                "resolved_at": attrs.get("resolved_at"),
                "acknowledged_at": attrs.get("acknowledged_at"),
                "response_content": attrs.get("response_content"),
            },
        }

    def _norm_status_page(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "betteruptime",
            "control": "infrastructure_security",
            "evidence_type": "betteruptime_status_pages",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("created_at") or _now(),
            "data": {
                "subdomain": attrs.get("subdomain"),
                "custom_domain": attrs.get("custom_domain"),
                "aggregate_state": attrs.get("aggregate_state"),
                "company_name": attrs.get("company_name"),
            },
        }

    def _norm_on_call_calendar(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "betteruptime",
            "control": "incident_management",
            "evidence_type": "betteruptime_on_call_calendars",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("created_at") or _now(),
            "data": {
                "name": attrs.get("name"),
                "color": attrs.get("color"),
                "default_calendar": attrs.get("default_calendar"),
            },
        }
