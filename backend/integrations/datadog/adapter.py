"""
Datadog integration via Datadog API v1/v2.

Credentials:
  api_key — Datadog API key (DD-API-KEY header)
  app_key — Datadog Application key (DD-APPLICATION-KEY header)
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

DD_API_V1 = "https://api.datadoghq.com/api/v1"
DD_API_V2 = "https://api.datadoghq.com/api/v2"


class DatadogIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None
        self._app_key: str | None = None

    def _headers(self) -> dict:
        return {
            "DD-API-KEY": self._api_key,
            "DD-APPLICATION-KEY": self._app_key,
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        app_key = credentials.get("app_key", "").strip()

        if not api_key or not app_key:
            raise IntegrationAuthError("api_key and app_key are required.")

        headers = {
            "DD-API-KEY": api_key,
            "DD-APPLICATION-KEY": app_key,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{DD_API_V1}/validate", headers=headers)
            if r.status_code == 403:
                raise IntegrationAuthError("Invalid Datadog API key or Application key.")
            if r.status_code == 401:
                raise IntegrationAuthError("Datadog credentials are unauthorized.")
            r.raise_for_status()
            body = r.json()
            if not body.get("valid", False):
                raise IntegrationAuthError("Datadog credentials are not valid.")

        self._api_key = api_key
        self._app_key = app_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            results: list[dict] = []

            try:
                monitors = await self._collect_monitors(client)
                results.extend(monitors)
            except Exception as exc:
                results.append({"_type": "error", "_source": "monitors", "_error": str(exc)})

            try:
                users = await self._collect_users(client)
                results.extend(users)
            except Exception as exc:
                results.append({"_type": "error", "_source": "users", "_error": str(exc)})

            try:
                dashboards = await self._collect_dashboards(client)
                results.extend(dashboards)
            except Exception as exc:
                results.append({"_type": "error", "_source": "dashboards", "_error": str(exc)})

            try:
                slos = await self._collect_slos(client)
                results.extend(slos)
            except Exception as exc:
                results.append({"_type": "error", "_source": "slos", "_error": str(exc)})

        return results

    async def _collect_monitors(self, client: httpx.AsyncClient) -> list[dict]:
        monitors = []
        page = 0
        page_size = 100
        while True:
            r = await client.get(
                f"{DD_API_V1}/monitor",
                headers=self._headers(),
                params={"page": page, "page_size": page_size},
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            for m in data:
                monitors.append({
                    "_type": "monitor",
                    "id": m.get("id"),
                    "name": m.get("name"),
                    "type": m.get("type"),
                    "status": m.get("overall_state"),
                    "tags": m.get("tags", []),
                    "message": m.get("message"),
                    "created": m.get("created"),
                    "modified": m.get("modified"),
                })
            if len(data) < page_size:
                break
            page += 1
        return monitors

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users = []
        page_number = 0
        page_size = 100
        while True:
            r = await client.get(
                f"{DD_API_V2}/users",
                headers=self._headers(),
                params={"page[number]": page_number, "page[size]": page_size},
            )
            r.raise_for_status()
            body = r.json()
            data = body.get("data", [])
            if not data:
                break
            for u in data:
                attrs = u.get("attributes", {})
                users.append({
                    "_type": "user",
                    "id": u.get("id"),
                    "email": attrs.get("email"),
                    "name": attrs.get("name"),
                    "status": attrs.get("status"),
                    "roles": [r.get("id") for r in u.get("relationships", {}).get("roles", {}).get("data", [])],
                    "created_at": attrs.get("created_at"),
                })
            meta = body.get("meta", {})
            page_meta = meta.get("page", {})
            total = page_meta.get("total_count", 0)
            if (page_number + 1) * page_size >= total:
                break
            page_number += 1
        return users

    async def _collect_dashboards(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{DD_API_V1}/dashboard/lists/manual",
            headers=self._headers(),
        )
        r.raise_for_status()
        body = r.json()
        dashboards = body.get("dashboard_lists", [])
        return [
            {
                "_type": "dashboard",
                "id": d.get("id"),
                "name": d.get("name"),
                "modified": d.get("modified"),
                "created": d.get("created"),
            }
            for d in dashboards
        ]

    async def _collect_slos(self, client: httpx.AsyncClient) -> list[dict]:
        slos = []
        offset = 0
        limit = 100
        while True:
            r = await client.get(
                f"{DD_API_V1}/slo",
                headers=self._headers(),
                params={"limit": limit, "offset": offset},
            )
            r.raise_for_status()
            body = r.json()
            data = body.get("data", [])
            if not data:
                break
            for s in data:
                slos.append({
                    "_type": "slo",
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "type": s.get("type"),
                    "status": s.get("overall_status"),
                    "thresholds": s.get("thresholds", []),
                    "created_at": s.get("created_at"),
                    "modified_at": s.get("modified_at"),
                })
            if len(data) < limit:
                break
            offset += limit
        return slos

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "monitor":
                result.append(self._norm_monitor(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "dashboard":
                result.append(self._norm_dashboard(item))
            elif t == "slo":
                result.append(self._norm_slo(item))
            # skip error sentinels silently
        return result

    def _norm_monitor(self, raw: dict) -> dict:
        return {
            "integration": "datadog",
            "control": "logging_monitoring",
            "evidence_type": "datadog_monitors",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "tags": raw.get("tags", []),
                "message": raw.get("message"),
                "modified": raw.get("modified"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "datadog",
            "control": "access_control",
            "evidence_type": "datadog_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": raw.get("email"),
                "name": raw.get("name"),
                "status": raw.get("status"),
                "roles": raw.get("roles", []),
            },
        }

    def _norm_dashboard(self, raw: dict) -> dict:
        return {
            "integration": "datadog",
            "control": "logging_monitoring",
            "evidence_type": "datadog_dashboards",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "modified": raw.get("modified"),
            },
        }

    def _norm_slo(self, raw: dict) -> dict:
        return {
            "integration": "datadog",
            "control": "logging_monitoring",
            "evidence_type": "datadog_slos",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "thresholds": raw.get("thresholds", []),
                "modified_at": raw.get("modified_at"),
            },
        }
