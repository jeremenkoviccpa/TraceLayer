from __future__ import annotations

"""
Graylog integration via Graylog REST API.

Credentials:
  url       — Graylog base URL (e.g. "https://graylog.mycompany.com")
  username  — Graylog username
  password  — Graylog password
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GraylogIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._url: str | None = None
        self._username: str | None = None
        self._password: str | None = None

    def _api(self) -> str:
        return f"{self._url}/api"

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)  # type: ignore[return-value]

    def _headers(self) -> dict[str, str]:
        return {"X-Requested-By": "XMLHttpRequest"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        url = credentials.get("url", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()

        if not url or not username or not password:
            raise IntegrationAuthError("url, username, and password are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{url}/api/system",
                auth=(username, password),
                headers={"X-Requested-By": "XMLHttpRequest"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Graylog credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Graylog connect failed HTTP {r.status_code}")

        self._url = url
        self._username = username
        self._password = password
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_streams,
                self._collect_alerts,
                self._collect_system_info,
                self._collect_inputs,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Graylog collection error in %s: %s", fetch_fn.__name__, exc
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
        r = await client.get(
            f"{self._api()}/users",
            auth=self._auth(),
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Graylog users HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "user", **u} for u in body.get("users", [])]

    async def _collect_streams(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api()}/streams",
            auth=self._auth(),
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Graylog streams HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "stream", **s} for s in body.get("streams", [])]

    async def _collect_alerts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api()}/alerts",
            auth=self._auth(),
            headers=self._headers(),
            params={"limit": 50},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Graylog alerts HTTP {r.status_code}")
        body = r.json()
        alerts = body.get("alerts") or body.get("data") or []
        return [{"_type": "alert", **a} for a in alerts]

    async def _collect_system_info(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api()}/system",
            auth=self._auth(),
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Graylog system HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "system_info", **body}]

    async def _collect_inputs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api()}/system/inputs",
            auth=self._auth(),
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Graylog inputs HTTP {r.status_code}")
        body = r.json()
        inputs = body.get("inputs") or []
        return [{"_type": "input", **i} for i in inputs]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "stream":
                result.append(self._norm_stream(item))
            elif t == "alert":
                result.append(self._norm_alert(item))
            elif t == "system_info":
                result.append(self._norm_system_info(item))
            elif t == "input":
                result.append(self._norm_input(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "graylog",
            "control": "access_control",
            "evidence_type": "graylog_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or _now(),
            "data": {
                "username": raw.get("username"),
                "email": raw.get("email"),
                "full_name": raw.get("full_name"),
                "roles": raw.get("roles", []),
                "read_only": raw.get("read_only"),
                "external": raw.get("external"),
            },
        }

    def _norm_stream(self, raw: dict) -> dict:
        return {
            "integration": "graylog",
            "control": "logging_monitoring",
            "evidence_type": "graylog_streams",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or _now(),
            "data": {
                "title": raw.get("title"),
                "description": raw.get("description"),
                "disabled": raw.get("disabled"),
                "alert_conditions": raw.get("alert_conditions", []),
                "matching_type": raw.get("matching_type"),
            },
        }

    def _norm_alert(self, raw: dict) -> dict:
        return {
            "integration": "graylog",
            "control": "logging_monitoring",
            "evidence_type": "graylog_alerts",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("triggered_at") or _now(),
            "data": {
                "description": raw.get("description"),
                "type": raw.get("type"),
                "is_interval": raw.get("is_interval"),
            },
        }

    def _norm_system_info(self, raw: dict) -> dict:
        return {
            "integration": "graylog",
            "control": "logging_monitoring",
            "evidence_type": "graylog_system_info",
            "source_id": "system",
            "timestamp": _now(),
            "data": {
                "version": raw.get("version"),
                "cluster_id": raw.get("cluster_id"),
                "node_id": raw.get("node_id"),
                "hostname": raw.get("hostname"),
                "is_leader": raw.get("is_leader"),
                "is_processing": raw.get("is_processing"),
                "lb_status": raw.get("lb_status"),
            },
        }

    def _norm_input(self, raw: dict) -> dict:
        return {
            "integration": "graylog",
            "control": "logging_monitoring",
            "evidence_type": "graylog_inputs",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or _now(),
            "data": {
                "title": raw.get("title"),
                "type": raw.get("type"),
                "global": raw.get("global"),
                "running": raw.get("running"),
            },
        }
