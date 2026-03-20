"""
Splunk integration via Splunk REST API.

Credentials:
  host     — full base URL including port, e.g. "https://company.splunkcloud.com:8089"
  username — Splunk username
  password — Splunk password

Note: Splunk Enterprise and some Splunk Cloud instances use self-signed TLS certificates.
verify=False is used with a warning comment; in production, supply the CA bundle path instead.
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class SplunkIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._username: str | None = None
        self._password: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def _client(self, timeout: int = 30) -> httpx.AsyncClient:
        # verify=False accommodates self-signed certs common in Splunk deployments.
        # Replace with verify="/path/to/ca-bundle.crt" for production environments
        # that have a valid CA-signed certificate.
        return httpx.AsyncClient(timeout=timeout, verify=False)

    async def connect(self, credentials: dict) -> bool:
        host = credentials.get("host", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()

        if not host or not username or not password:
            raise IntegrationAuthError("host, username, and password are required")

        async with self._client(timeout=15) as client:
            r = await client.get(
                f"{host}/services/authentication/current-context",
                params={"output_mode": "json"},
                auth=(username, password),
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Splunk credentials")
            if r.status_code == 403:
                raise IntegrationAuthError("Splunk credentials lack required permissions")
            r.raise_for_status()

        self._base = host
        self._username = username
        self._password = password
        return True

    async def collect_evidence(self) -> list[dict]:
        async with self._client() as client:
            searches = await self._collect_saved_searches(client)
            alerts = await self._collect_alerts(client)
            users = await self._collect_users(client)
        return searches + alerts + users

    async def _collect_saved_searches(self, client: httpx.AsyncClient) -> list[dict]:
        items = []
        offset = 0
        count = 100
        try:
            while True:
                r = await client.get(
                    f"{self._base}/services/saved/searches",
                    params={"output_mode": "json", "count": count, "offset": offset},
                    auth=self._auth(),
                )
                r.raise_for_status()
                data = r.json()
                entries = data.get("entry", [])
                if not entries:
                    break
                for entry in entries:
                    content = entry.get("content", {})
                    items.append(
                        {
                            "_type": "saved_search",
                            "name": entry.get("name"),
                            "description": content.get("description"),
                            "search": content.get("search"),
                            "alert_type": content.get("alert_type"),
                            "is_scheduled": content.get("is_scheduled"),
                            "cron_schedule": content.get("cron_schedule"),
                        }
                    )
                if len(entries) < count:
                    break
                offset += count
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Splunk saved searches: {exc}") from exc
        return items

    async def _collect_alerts(self, client: httpx.AsyncClient) -> list[dict]:
        items = []
        offset = 0
        count = 100
        try:
            while True:
                r = await client.get(
                    f"{self._base}/services/alerts/fired_alerts",
                    params={"output_mode": "json", "count": count, "offset": offset},
                    auth=self._auth(),
                )
                r.raise_for_status()
                data = r.json()
                entries = data.get("entry", [])
                if not entries:
                    break
                for entry in entries:
                    content = entry.get("content", {})
                    items.append(
                        {
                            "_type": "alert",
                            "name": entry.get("name"),
                            "triggered_alert_count": content.get("triggered_alert_count"),
                            "savedsearch_name": content.get("savedsearch_name"),
                        }
                    )
                if len(entries) < count:
                    break
                offset += count
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Splunk alerts: {exc}") from exc
        return items

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        items = []
        offset = 0
        count = 100
        try:
            while True:
                r = await client.get(
                    f"{self._base}/services/authentication/users",
                    params={"output_mode": "json", "count": count, "offset": offset},
                    auth=self._auth(),
                )
                r.raise_for_status()
                data = r.json()
                entries = data.get("entry", [])
                if not entries:
                    break
                for entry in entries:
                    content = entry.get("content", {})
                    items.append(
                        {
                            "_type": "user",
                            "name": entry.get("name"),
                            "roles": content.get("roles", []),
                            "email": content.get("email"),
                            "type": content.get("type"),
                        }
                    )
                if len(entries) < count:
                    break
                offset += count
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Splunk users: {exc}") from exc
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "saved_search":
                result.append(self._norm_saved_search(item))
            elif t == "alert":
                result.append(self._norm_alert(item))
            elif t == "user":
                result.append(self._norm_user(item))
        return result

    def _norm_saved_search(self, raw: dict) -> dict:
        return {
            "integration": "splunk",
            "control": "logging_monitoring",
            "evidence_type": "splunk_saved_searches",
            "source_id": raw.get("name", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "search": raw.get("search"),
                "alert_type": raw.get("alert_type"),
                "is_scheduled": raw.get("is_scheduled"),
                "cron_schedule": raw.get("cron_schedule"),
            },
        }

    def _norm_alert(self, raw: dict) -> dict:
        return {
            "integration": "splunk",
            "control": "logging_monitoring",
            "evidence_type": "splunk_alerts",
            "source_id": raw.get("name", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "triggered_alert_count": raw.get("triggered_alert_count"),
                "savedsearch_name": raw.get("savedsearch_name"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "splunk",
            "control": "access_control",
            "evidence_type": "splunk_users",
            "source_id": raw.get("name", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "roles": raw.get("roles", []),
                "email": raw.get("email"),
                "type": raw.get("type"),
            },
        }
