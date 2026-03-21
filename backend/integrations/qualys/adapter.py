from __future__ import annotations
"""
Qualys integration via Qualys API v2 (FOD/VM APIs).

Credentials:
  username — Qualys username
  password — Qualys password
  api_url  — Base API URL (e.g. "https://qualysapi.qualys.com")
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class QualysIntegration(IntegrationAdapter):

    def __init__(self):
        self._username: str | None = None
        self._password: str | None = None
        self._api_url: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._password)

    def _headers(self) -> dict:
        return {
            "X-Requested-With": "TraceLayer",
            "Accept": "application/json",
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()
        api_url = credentials.get("api_url", "").rstrip("/").strip()

        if not username or not password or not api_url:
            raise IntegrationAuthError("username, password, and api_url are required.")

        auth = (username, password)
        headers = {"X-Requested-With": "TraceLayer", "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{api_url}/api/2.0/fo/activity_log/",
                auth=auth,
                headers=headers,
                params={"action": "list", "truncation_limit": 1, "output_format": "JSON"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Qualys credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Qualys connect failed HTTP {r.status_code}")

        self._username = username
        self._password = password
        self._api_url = api_url
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_scans,
                self._collect_assets,
                self._collect_reports,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Qualys collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _post_json(
        self, client: httpx.AsyncClient, path: str, extra_params: dict | None = None
    ) -> dict:
        params = {"output_format": "JSON"}
        if extra_params:
            params.update(extra_params)
        r = await client.post(
            f"{self._api_url}{path}",
            auth=self._auth(),
            headers=self._headers(),
            params=params,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Qualys {path} HTTP {r.status_code}")
        return r.json()

    async def _collect_scans(self, client: httpx.AsyncClient) -> list[dict]:
        body = await self._post_json(
            client,
            "/api/2.0/fo/scan/",
            {"action": "list"},
        )
        # Response shape: {"RESPONSE": {"SCAN_LIST": {"SCAN": [...]}}}
        response = body.get("RESPONSE", body)
        scan_list = response.get("SCAN_LIST", {})
        scans = scan_list.get("SCAN", [])
        if isinstance(scans, dict):
            scans = [scans]
        return [{"_type": "vulnerability_scans", **s} for s in (scans or [])]

    async def _collect_assets(self, client: httpx.AsyncClient) -> list[dict]:
        body = await self._post_json(
            client,
            "/api/2.0/fo/asset/host/",
            {"action": "list", "truncation_limit": 100},
        )
        response = body.get("RESPONSE", body)
        host_list = response.get("HOST_LIST", {})
        hosts = host_list.get("HOST", [])
        if isinstance(hosts, dict):
            hosts = [hosts]
        return [{"_type": "assets", **h} for h in (hosts or [])]

    async def _collect_reports(self, client: httpx.AsyncClient) -> list[dict]:
        body = await self._post_json(
            client,
            "/api/2.0/fo/report/",
            {"action": "list"},
        )
        response = body.get("RESPONSE", body)
        report_list = response.get("REPORT_LIST", {})
        reports = report_list.get("REPORT", [])
        if isinstance(reports, dict):
            reports = [reports]
        return [{"_type": "reports", **rp} for rp in (reports or [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "vulnerability_scans":
                result.append(self._norm_scan(item))
            elif t == "assets":
                result.append(self._norm_asset(item))
            elif t == "reports":
                result.append(self._norm_report(item))
        return result

    def _norm_scan(self, raw: dict) -> dict:
        return {
            "integration": "qualys",
            "control": "vulnerability_management",
            "evidence_type": "vulnerability_scans",
            "source_id": str(raw.get("ID", raw.get("id", ""))),
            "timestamp": raw.get("LAUNCH_DATETIME") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "scan_ref": raw.get("REF"),
                "title": raw.get("TITLE"),
                "type": raw.get("TYPE"),
                "status": raw.get("STATUS", {}).get("STATE") if isinstance(raw.get("STATUS"), dict) else raw.get("STATUS"),
                "target": raw.get("TARGET"),
                "launched_by": raw.get("LAUNCHED_BY", {}).get("USERNAME") if isinstance(raw.get("LAUNCHED_BY"), dict) else None,
                "launch_datetime": raw.get("LAUNCH_DATETIME"),
            },
        }

    def _norm_asset(self, raw: dict) -> dict:
        return {
            "integration": "qualys",
            "control": "asset_management",
            "evidence_type": "assets",
            "source_id": str(raw.get("ID", raw.get("id", ""))),
            "timestamp": raw.get("LAST_SCAN_DATETIME") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "ip": raw.get("IP"),
                "tracking_method": raw.get("TRACKING_METHOD"),
                "os": raw.get("OS"),
                "dns": raw.get("DNS"),
                "netbios": raw.get("NETBIOS"),
                "last_scan_datetime": raw.get("LAST_SCAN_DATETIME"),
            },
        }

    def _norm_report(self, raw: dict) -> dict:
        return {
            "integration": "qualys",
            "control": "reporting",
            "evidence_type": "reports",
            "source_id": str(raw.get("ID", raw.get("id", ""))),
            "timestamp": raw.get("LAUNCH_DATETIME") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("TITLE"),
                "type": raw.get("TYPE"),
                "status": raw.get("STATUS", {}).get("STATE") if isinstance(raw.get("STATUS"), dict) else raw.get("STATUS"),
                "size": raw.get("SIZE"),
                "launch_datetime": raw.get("LAUNCH_DATETIME"),
                "expiration_datetime": raw.get("EXPIRATION_DATETIME"),
            },
        }
