"""
Tailscale integration via Tailscale REST API v2.

Credentials:
  api_key  — Tailscale API key (Bearer token)
  tailnet  — Org tailnet name (e.g. "mycompany.com")
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.tailscale.com/api/v2"


class TailscaleIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None
        self._tailnet: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        tailnet = credentials.get("tailnet", "").strip()

        if not api_key or not tailnet:
            raise IntegrationAuthError("api_key and tailnet are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/tailnet/{tailnet}/devices",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"fields": "all"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Tailscale credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Tailscale connect failed HTTP {r.status_code}")

        self._api_key = api_key
        self._tailnet = tailnet
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_devices,
                self._collect_users,
                self._collect_acl,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Tailscale collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_devices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/tailnet/{self._tailnet}/devices",
            headers=self._headers(),
            params={"fields": "all"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Tailscale devices HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "device", **d} for d in body.get("devices", [])]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/tailnet/{self._tailnet}/users",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Tailscale users HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "user", **u} for u in body.get("users", [])]

    async def _collect_acl(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/tailnet/{self._tailnet}/acl",
            headers={**self._headers(), "Accept": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Tailscale ACL HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "acl", **body}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "device":
                result.append(self._norm_device(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "acl":
                result.append(self._norm_acl(item))
        return result

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "tailscale",
            "control": "network_security",
            "evidence_type": "tailscale_devices",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("lastSeen") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "hostname": raw.get("hostname"),
                "os": raw.get("os"),
                "user": raw.get("user"),
                "authorized": raw.get("authorized"),
                "keyExpiryDisabled": raw.get("keyExpiryDisabled"),
                "lastSeen": raw.get("lastSeen"),
                "addresses": raw.get("addresses"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "tailscale",
            "control": "access_control",
            "evidence_type": "tailscale_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "loginName": raw.get("loginName"),
                "displayName": raw.get("displayName"),
                "role": raw.get("role"),
                "status": raw.get("status"),
                "created": raw.get("created"),
            },
        }

    def _norm_acl(self, raw: dict) -> dict:
        return {
            "integration": "tailscale",
            "control": "network_security",
            "evidence_type": "tailscale_acl",
            "source_id": "acl",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "acls": raw.get("acls", []),
                "groups": raw.get("groups", {}),
                "tagOwners": raw.get("tagOwners", {}),
            },
        }
