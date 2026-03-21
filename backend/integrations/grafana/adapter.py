from __future__ import annotations

"""
Grafana integration via Grafana HTTP API.

Credentials:
  url     — Grafana base URL (e.g. "https://mycompany.grafana.net")
  api_key — Grafana service account token or API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class GrafanaIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._url: str | None = None
        self._api_key: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        url = credentials.get("url", "").strip().rstrip("/")
        api_key = credentials.get("api_key", "").strip()
        if not url or not api_key:
            raise IntegrationAuthError("url and api_key are required.")

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{url}/api/health", headers=headers)
            if r.status_code == 200:
                self._url = url
                self._api_key = api_key
                return True

            # /api/health may not require auth on some setups — fall back to /api/user
            r2 = await client.get(f"{url}/api/user", headers=headers)
            if r2.status_code == 401:
                raise IntegrationAuthError("Invalid Grafana credentials.")
            if r2.status_code != 200:
                raise RuntimeError(
                    f"Grafana connect failed HTTP {r2.status_code}"
                )

        self._url = url
        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_org,
                self._collect_users,
                self._collect_dashboards,
                self._collect_datasources,
                self._collect_alert_rules,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Grafana collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_org(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{self._url}/api/org", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Grafana org HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "org", **body}]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{self._url}/api/org/users", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Grafana org/users HTTP {r.status_code}")
        return [{"_type": "user", **u} for u in r.json()]

    async def _collect_dashboards(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._url}/api/search",
            headers=self._headers(),
            params={"type": "dash-db", "limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Grafana search HTTP {r.status_code}")
        return [{"_type": "dashboard", **d} for d in r.json()]

    async def _collect_datasources(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._url}/api/datasources", headers=self._headers()
        )
        if r.status_code != 200:
            raise RuntimeError(f"Grafana datasources HTTP {r.status_code}")
        return [{"_type": "datasource", **ds} for ds in r.json()]

    async def _collect_alert_rules(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._url}/api/v1/provisioning/alert-rules",
            headers=self._headers(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Grafana alert-rules HTTP {r.status_code}")

        body = r.json()

        # Body may be a flat list or {"groups": [...]} structure
        if isinstance(body, list):
            rules = body
        elif isinstance(body, dict) and "groups" in body:
            rules = []
            for group in body.get("groups", []):
                rules.extend(group.get("rules", []))
        else:
            rules = []

        return [{"_type": "alert_rule", **rule} for rule in rules]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "org":
                result.append(self._norm_org(item, now))
            elif t == "user":
                result.append(self._norm_user(item, now))
            elif t == "dashboard":
                result.append(self._norm_dashboard(item, now))
            elif t == "datasource":
                result.append(self._norm_datasource(item, now))
            elif t == "alert_rule":
                result.append(self._norm_alert_rule(item, now))
        return result

    def _norm_org(self, item: dict, now: str) -> dict:
        return {
            "integration": "grafana",
            "control": "access_control",
            "evidence_type": "grafana_org",
            "source_id": str(item.get("id", "org")),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "address": item.get("address", {}),
            },
        }

    def _norm_user(self, item: dict, now: str) -> dict:
        source_id = str(item.get("userId", "") or item.get("id", ""))
        return {
            "integration": "grafana",
            "control": "access_control",
            "evidence_type": "grafana_users",
            "source_id": source_id,
            "timestamp": now,
            "data": {
                "login": item.get("login"),
                "email": item.get("email"),
                "name": item.get("name"),
                "role": item.get("role"),
                "isGrafanaAdmin": item.get("isGrafanaAdmin"),
                "lastSeenAt": item.get("lastSeenAt"),
            },
        }

    def _norm_dashboard(self, item: dict, now: str) -> dict:
        return {
            "integration": "grafana",
            "control": "logging_monitoring",
            "evidence_type": "grafana_dashboards",
            "source_id": str(item.get("id", "")),
            "timestamp": item.get("created") or now,
            "data": {
                "title": item.get("title"),
                "uid": item.get("uid"),
                "folderTitle": item.get("folderTitle"),
                "tags": item.get("tags", []),
            },
        }

    def _norm_datasource(self, item: dict, now: str) -> dict:
        return {
            "integration": "grafana",
            "control": "logging_monitoring",
            "evidence_type": "grafana_datasources",
            "source_id": str(item.get("id", "")),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "type": item.get("type"),
                "url": item.get("url"),
                "access": item.get("access"),
                "isDefault": item.get("isDefault"),
            },
        }

    def _norm_alert_rule(self, item: dict, now: str) -> dict:
        return {
            "integration": "grafana",
            "control": "logging_monitoring",
            "evidence_type": "grafana_alert_rules",
            "source_id": item.get("uid", ""),
            "timestamp": item.get("updated") or now,
            "data": {
                "title": item.get("title"),
                "condition": item.get("condition"),
                "folderUID": item.get("folderUID"),
                "noDataState": item.get("noDataState"),
                "execErrState": item.get("execErrState"),
            },
        }
