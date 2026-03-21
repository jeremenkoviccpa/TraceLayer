"""
Opsgenie integration via Opsgenie REST API v2.

Credentials:
  api_key — Opsgenie API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.opsgenie.com/v2"


class OpsgenieIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"GenieKey {self._api_key}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/users",
                headers={"Authorization": f"GenieKey {api_key}"},
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Opsgenie API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Opsgenie connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_teams,
                self._collect_schedules,
                self._collect_alerts,
                self._collect_escalations,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Opsgenie collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users: list[dict] = []
        url = f"{_BASE}/users"
        params: dict = {"limit": 100}

        while True:
            r = await client.get(url, headers=self._headers(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"Opsgenie users HTTP {r.status_code}")
            body = r.json()
            users.extend(body.get("data", []))
            next_url = body.get("paging", {}).get("next")
            if not next_url:
                break
            # Use the full next URL directly; clear params so they aren't duplicated
            url = next_url
            params = {}

        return [{"_type": "user", **item} for item in users]

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/teams", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Opsgenie teams HTTP {r.status_code}")
        return [{"_type": "team", **item} for item in r.json().get("data", [])]

    async def _collect_schedules(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/schedules", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Opsgenie schedules HTTP {r.status_code}")
        return [{"_type": "schedule", **item} for item in r.json().get("data", [])]

    async def _collect_alerts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/alerts",
            headers=self._headers(),
            params={"limit": 50, "status": "open"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Opsgenie alerts HTTP {r.status_code}")
        return [{"_type": "alert", **item} for item in r.json().get("data", [])]

    async def _collect_escalations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/escalations", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Opsgenie escalations HTTP {r.status_code}")
        return [{"_type": "escalation", **item} for item in r.json().get("data", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "team":
                result.append(self._norm_team(item))
            elif t == "schedule":
                result.append(self._norm_schedule(item))
            elif t == "alert":
                result.append(self._norm_alert(item))
            elif t == "escalation":
                result.append(self._norm_escalation(item))
        return result

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "opsgenie",
            "control": "access_control",
            "evidence_type": "opsgenie_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "username": raw.get("username"),
                "fullName": raw.get("fullName"),
                "role": raw.get("role", {}).get("name"),
                "blocked": raw.get("blocked"),
                "verified": raw.get("verified"),
            },
        }

    def _norm_team(self, raw: dict) -> dict:
        return {
            "integration": "opsgenie",
            "control": "access_control",
            "evidence_type": "opsgenie_teams",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
            },
        }

    def _norm_schedule(self, raw: dict) -> dict:
        return {
            "integration": "opsgenie",
            "control": "logging_monitoring",
            "evidence_type": "opsgenie_schedules",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "timezone": raw.get("timezone"),
                "enabled": raw.get("enabled"),
            },
        }

    def _norm_alert(self, raw: dict) -> dict:
        return {
            "integration": "opsgenie",
            "control": "logging_monitoring",
            "evidence_type": "opsgenie_alerts",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "message": raw.get("message"),
                "status": raw.get("status"),
                "priority": raw.get("priority"),
                "source": raw.get("source"),
            },
        }

    def _norm_escalation(self, raw: dict) -> dict:
        return {
            "integration": "opsgenie",
            "control": "logging_monitoring",
            "evidence_type": "opsgenie_escalations",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "rules": raw.get("rules", []),
            },
        }
