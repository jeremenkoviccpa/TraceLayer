from __future__ import annotations
"""
Zscaler integration via Zscaler Internet Access (ZIA) API v1.

Credentials:
  hostname — Zscaler API hostname (e.g. "zsapi.zscalerthree.net")
  username — Admin username
  password — Admin password
  api_key  — Zscaler API key (obfuscated before use)
"""
import logging
import time
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


def _obfuscate_api_key(api_key: str) -> tuple[str, str]:
    now_ms = str(int(time.time() * 1000))
    n = now_ms[-6:]
    r = str(int(n) >> 1).zfill(6)
    key = ""
    for i in range(0, 12, 2):
        key += api_key[int(n[i // 2])]
    for i in range(0, 12, 2):
        key += api_key[int(r[i // 2]) + 2]
    return key, now_ms


class ZscalerIntegration(IntegrationAdapter):

    def __init__(self):
        self._hostname: str | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._api_key: str | None = None
        self._cookies: dict | None = None

    def _base_url(self) -> str:
        return f"https://{self._hostname}/api/v1"

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        hostname = credentials.get("hostname", "").strip()
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()
        api_key = credentials.get("api_key", "").strip()

        if not hostname or not username or not password or not api_key:
            raise IntegrationAuthError("hostname, username, password, and api_key are required.")

        obfuscated_key, timestamp_ms = _obfuscate_api_key(api_key)

        async with httpx.AsyncClient(timeout=15) as client:
            auth_resp = await client.post(
                f"https://{hostname}/api/v1/authenticatedSession",
                json={
                    "username": username,
                    "password": password,
                    "apiKey": obfuscated_key,
                    "timestamp": timestamp_ms,
                },
            )
            if auth_resp.status_code == 401:
                raise IntegrationAuthError("Invalid Zscaler credentials.")
            if auth_resp.status_code != 200:
                raise RuntimeError(f"Zscaler authentication failed HTTP {auth_resp.status_code}")

            cookies = dict(auth_resp.cookies)

            # Validate session by checking status endpoint
            status_resp = await client.get(
                f"https://{hostname}/api/v1/status",
                cookies=cookies,
            )
            if status_resp.status_code == 401:
                raise IntegrationAuthError("Invalid Zscaler credentials.")
            if status_resp.status_code != 200:
                raise RuntimeError(f"Zscaler status check failed HTTP {status_resp.status_code}")

        self._hostname = hostname
        self._username = username
        self._password = password
        self._api_key = api_key
        self._cookies = cookies
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_groups,
                self._collect_locations,
                self._collect_url_categories,
                self._collect_firewall_rules,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Zscaler collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/users",
            cookies=self._cookies,
            params={"pageSize": 1000},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zscaler users HTTP {r.status_code}")
        return [{"_type": "user", **u} for u in r.json()]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/groups",
            cookies=self._cookies,
            params={"pageSize": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zscaler groups HTTP {r.status_code}")
        return [{"_type": "group", **g} for g in r.json()]

    async def _collect_locations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/locations",
            cookies=self._cookies,
            params={"pageSize": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zscaler locations HTTP {r.status_code}")
        return [{"_type": "location", **loc} for loc in r.json()]

    async def _collect_url_categories(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/urlCategories",
            cookies=self._cookies,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zscaler URL categories HTTP {r.status_code}")
        categories = r.json()[:50]
        return [{"_type": "url_category", **cat} for cat in categories]

    async def _collect_firewall_rules(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/firewallFilteringRules",
            cookies=self._cookies,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zscaler firewall rules HTTP {r.status_code}")
        return [{"_type": "firewall_rule", **rule} for rule in r.json()]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "location":
                result.append(self._norm_location(item))
            elif t == "url_category":
                result.append(self._norm_url_category(item))
            elif t == "firewall_rule":
                result.append(self._norm_firewall_rule(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        dept = raw.get("department")
        dept_name = dept.get("name") if isinstance(dept, dict) else None
        return {
            "integration": "zscaler",
            "control": "network_security",
            "evidence_type": "zscaler_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "type": raw.get("type"),
                "department": dept_name,
                "adminUser": raw.get("adminUser"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "zscaler",
            "control": "network_security",
            "evidence_type": "zscaler_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "idpId": raw.get("idpId"),
                "comments": raw.get("comments"),
            },
        }

    def _norm_location(self, raw: dict) -> dict:
        return {
            "integration": "zscaler",
            "control": "network_security",
            "evidence_type": "zscaler_locations",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "country": raw.get("country"),
                "city": raw.get("city"),
                "authRequired": raw.get("authRequired"),
                "sslScanEnabled": raw.get("sslScanEnabled"),
            },
        }

    def _norm_url_category(self, raw: dict) -> dict:
        return {
            "integration": "zscaler",
            "control": "network_security",
            "evidence_type": "zscaler_url_categories",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "configuredName": raw.get("configuredName"),
                "type": raw.get("type"),
                "dbCategorizedUrls": raw.get("dbCategorizedUrls", [])[:5],
            },
        }

    def _norm_firewall_rule(self, raw: dict) -> dict:
        return {
            "integration": "zscaler",
            "control": "network_security",
            "evidence_type": "zscaler_firewall_rules",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "action": raw.get("action"),
                "enabled": raw.get("enabled"),
                "rank": raw.get("rank"),
            },
        }
