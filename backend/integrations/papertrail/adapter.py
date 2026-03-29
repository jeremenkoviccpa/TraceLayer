"""
Papertrail integration adapter.

Collects systems, groups, saved searches, log events, and account info
from the Papertrail REST API (https://papertrailapp.com/api/v1/).
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

PAPERTRAIL_API_BASE = "https://papertrailapp.com/api/v1"


class PapertrailIntegration(IntegrationAdapter):
    """Collects logging and monitoring evidence from Papertrail."""

    def __init__(self) -> None:
        self._api_token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by fetching the systems list."""
        api_token = (credentials.get("api_token") or "").strip()
        if not api_token:
            raise IntegrationAuthError("Papertrail api_token is required.")

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{PAPERTRAIL_API_BASE}/systems.json",
                headers={"X-Papertrail-Token": api_token},
            )
            if r.status_code == 403:
                raise IntegrationAuthError("Invalid Papertrail API token.")
            r.raise_for_status()

        self._api_token = api_token
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                systems = await self._collect_systems(client)
                raw.extend(systems)
            except Exception as e:
                logger.exception("Papertrail: failed to collect systems")
                raw.append({"_type": "error", "_source": "_collect_systems", "_error": str(e)})

            try:
                groups = await self._collect_groups(client)
                raw.extend(groups)
            except Exception as e:
                logger.exception("Papertrail: failed to collect groups")
                raw.append({"_type": "error", "_source": "_collect_groups", "_error": str(e)})

            try:
                saved_searches = await self._collect_saved_searches(client)
                raw.extend(saved_searches)
            except Exception as e:
                logger.exception("Papertrail: failed to collect saved searches")
                raw.append({"_type": "error", "_source": "_collect_saved_searches", "_error": str(e)})

            try:
                log_events = await self._collect_log_events(client)
                raw.extend(log_events)
            except Exception as e:
                logger.exception("Papertrail: failed to collect log events")
                raw.append({"_type": "error", "_source": "_collect_log_events", "_error": str(e)})

            try:
                account = await self._collect_account(client)
                raw.append(account)
            except Exception as e:
                logger.exception("Papertrail: failed to collect account info")
                raw.append({"_type": "error", "_source": "_collect_account", "_error": str(e)})

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "system":
                result.append(self._norm_system(item, now))
            elif t == "group":
                result.append(self._norm_group(item, now))
            elif t == "saved_search":
                result.append(self._norm_saved_search(item, now))
            elif t == "log_event":
                result.append(self._norm_log_event(item, now))
            elif t == "account_info":
                result.append(self._norm_account_info(item, now))
            # skip error records

        return result

    # ------------------------------------------------------------------
    # Private helpers — headers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict:
        return {"X-Papertrail-Token": self._api_token}

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_systems(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{PAPERTRAIL_API_BASE}/systems.json",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        items = r.json()
        if not isinstance(items, list):
            items = items.get("systems", []) if isinstance(items, dict) else []
        for item in items:
            item["_type"] = "system"
        return items

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{PAPERTRAIL_API_BASE}/groups.json",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        items = r.json()
        if not isinstance(items, list):
            items = items.get("groups", []) if isinstance(items, dict) else []
        for item in items:
            item["_type"] = "group"
        return items

    async def _collect_saved_searches(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{PAPERTRAIL_API_BASE}/searches.json",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        items = r.json()
        if not isinstance(items, list):
            items = items.get("searches", []) if isinstance(items, dict) else []
        for item in items:
            item["_type"] = "saved_search"
        return items

    async def _collect_log_events(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{PAPERTRAIL_API_BASE}/events/search.json",
            headers=self._auth_headers(),
            params={"q": "", "limit": 100},
        )
        r.raise_for_status()
        body = r.json()
        items = body.get("events", [])
        for item in items:
            item["_type"] = "log_event"
        return items

    async def _collect_account(self, client: httpx.AsyncClient) -> dict:
        r = await client.get(
            f"{PAPERTRAIL_API_BASE}/accounts.json",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        body = r.json()
        # The API returns a single object or a list; normalise to dict.
        account = body[0] if isinstance(body, list) and body else body
        account["_type"] = "account_info"
        return account

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_system(self, item: dict, now: str) -> dict:
        return {
            "integration": "papertrail",
            "control": "logging_monitoring",
            "evidence_type": "papertrail_system",
            "source_id": str(item.get("id", "")),
            "timestamp": item.get("last_event_at") or now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "hostname": item.get("hostname"),
                "ip_address": item.get("ip_address"),
                "last_event_at": item.get("last_event_at"),
                "syslog_hostname": item.get("syslog_hostname"),
                "syslog_port": item.get("syslog_port"),
            },
        }

    def _norm_group(self, item: dict, now: str) -> dict:
        return {
            "integration": "papertrail",
            "control": "logging_monitoring",
            "evidence_type": "papertrail_group",
            "source_id": str(item.get("id", "")),
            "timestamp": now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "system_wildcard": item.get("system_wildcard"),
                "system_ids": item.get("system_ids"),
                "_links": item.get("_links"),
            },
        }

    def _norm_saved_search(self, item: dict, now: str) -> dict:
        return {
            "integration": "papertrail",
            "control": "logging_monitoring",
            "evidence_type": "papertrail_saved_search",
            "source_id": str(item.get("id", "")),
            "timestamp": item.get("last_occurred_at") or now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "query": item.get("query"),
                "last_occurred_at": item.get("last_occurred_at"),
                "count": item.get("count"),
            },
        }

    def _norm_log_event(self, item: dict, now: str) -> dict:
        return {
            "integration": "papertrail",
            "control": "logging_monitoring",
            "evidence_type": "papertrail_log_event",
            "source_id": str(item.get("id", "")),
            "timestamp": item.get("received_at") or now,
            "data": {
                "id": item.get("id"),
                "source_name": item.get("source_name"),
                "source_ip": item.get("source_ip"),
                "program": item.get("program"),
                "message": item.get("message"),
                "severity": item.get("severity"),
                "facility": item.get("facility"),
                "received_at": item.get("received_at"),
                "hostname": item.get("hostname"),
            },
        }

    def _norm_account_info(self, item: dict, now: str) -> dict:
        return {
            "integration": "papertrail",
            "control": "logging_monitoring",
            "evidence_type": "papertrail_account",
            "source_id": "account",
            "timestamp": now,
            "data": item,
        }
