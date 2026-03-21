"""
JumpCloud integration via JumpCloud API v1/v2.

Credentials:
  api_key — JumpCloud API key (x-api-key header)
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

JC_BASE_V1 = "https://console.jumpcloud.com/api"
JC_BASE_V2 = "https://console.jumpcloud.com/api/v2"


class JumpCloudIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {
            "x-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{JC_BASE_V1}/users",
                headers=headers,
                params={"limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid JumpCloud API key.")
            if r.status_code != 200:
                raise RuntimeError(f"JumpCloud connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_user_groups,
                self._collect_policies,
                self._collect_devices,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("JumpCloud collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{JC_BASE_V1}/users",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"JumpCloud users HTTP {r.status_code}")
        data = r.json()
        # API returns {"results": [...]} or a plain list
        items = data.get("results", data) if isinstance(data, dict) else data
        return [{"_type": "users", **u} for u in (items or [])]

    async def _collect_user_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{JC_BASE_V1}/usergroups",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"JumpCloud usergroups HTTP {r.status_code}")
        items = r.json()
        if isinstance(items, dict):
            items = items.get("results", [])
        return [{"_type": "user_groups", **g} for g in (items or [])]

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{JC_BASE_V2}/policies",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"JumpCloud policies HTTP {r.status_code}")
        items = r.json()
        if isinstance(items, dict):
            items = items.get("results", [])
        return [{"_type": "policies", **p} for p in (items or [])]

    async def _collect_devices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{JC_BASE_V2}/devices",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"JumpCloud devices HTTP {r.status_code}")
        items = r.json()
        if isinstance(items, dict):
            items = items.get("results", [])
        return [{"_type": "devices", **d} for d in (items or [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "users":
                result.append(self._norm_user(item))
            elif t == "user_groups":
                result.append(self._norm_user_group(item))
            elif t == "policies":
                result.append(self._norm_policy(item))
            elif t == "devices":
                result.append(self._norm_device(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "jumpcloud",
            "control": "access_control",
            "evidence_type": "users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "username": raw.get("username"),
                "email": raw.get("email"),
                "firstname": raw.get("firstname"),
                "lastname": raw.get("lastname"),
                "account_locked": raw.get("account_locked"),
                "mfa_enrollment": raw.get("mfa", {}).get("configured") if isinstance(raw.get("mfa"), dict) else None,
                "suspended": raw.get("suspended"),
            },
        }

    def _norm_user_group(self, raw: dict) -> dict:
        return {
            "integration": "jumpcloud",
            "control": "access_control",
            "evidence_type": "user_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "description": raw.get("description"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "jumpcloud",
            "control": "policy_management",
            "evidence_type": "policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "template_id": raw.get("template", {}).get("id") if isinstance(raw.get("template"), dict) else None,
                "active": raw.get("active"),
            },
        }

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "jumpcloud",
            "control": "device_management",
            "evidence_type": "devices",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "hostname": raw.get("hostname"),
                "display_name": raw.get("displayName"),
                "os": raw.get("os"),
                "os_version": raw.get("osVersion"),
                "agent_version": raw.get("agentVersion"),
                "active": raw.get("active"),
                "remote_ip": raw.get("remoteIP"),
            },
        }
