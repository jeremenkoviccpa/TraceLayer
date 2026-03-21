"""
Bitwarden integration via Bitwarden Public API.

Credentials:
  client_id      — Bitwarden organization client ID
  client_secret  — Bitwarden organization client secret
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://identity.bitwarden.com/connect/token"
_API_BASE = "https://api.bitwarden.com"

_MEMBER_TYPE_MAP = {
    0: "Owner",
    1: "Admin",
    2: "User",
    3: "Manager",
    4: "Custom",
}


class BitwardenIntegration(IntegrationAdapter):

    def __init__(self):
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not client_id or not client_secret:
            raise IntegrationAuthError("client_id and client_secret are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "api.organization",
                },
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError("Invalid Bitwarden credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Bitwarden token request failed HTTP {r.status_code}")

            body = r.json()
            access_token = body.get("access_token")
            if not access_token:
                raise IntegrationAuthError("Bitwarden token response missing access_token.")

        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_members,
                self._collect_collections,
                self._collect_policies,
                self._collect_groups,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Bitwarden collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/public/members", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Bitwarden members HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "member", **m} for m in body.get("data", [])]

    async def _collect_collections(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/public/collections", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Bitwarden collections HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "collection", **c} for c in body.get("data", [])]

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/public/policies", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Bitwarden policies HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "policy", **p} for p in body.get("data", [])]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/public/groups", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Bitwarden groups HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "group", **g} for g in body.get("data", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "member":
                result.append(self._norm_member(item))
            elif t == "collection":
                result.append(self._norm_collection(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
            elif t == "group":
                result.append(self._norm_group(item))
        return result

    def _norm_member(self, raw: dict) -> dict:
        raw_type = raw.get("type")
        return {
            "integration": "bitwarden",
            "control": "access_control",
            "evidence_type": "bitwarden_members",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": raw.get("email"),
                "name": raw.get("name"),
                "type": _MEMBER_TYPE_MAP.get(raw_type, raw_type),
                "status": raw.get("status"),
                "twoFactorEnabled": raw.get("twoFactorEnabled"),
                "resetPasswordEnrolled": raw.get("resetPasswordEnrolled"),
            },
        }

    def _norm_collection(self, raw: dict) -> dict:
        return {
            "integration": "bitwarden",
            "control": "access_control",
            "evidence_type": "bitwarden_collections",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "externalId": raw.get("externalId"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "bitwarden",
            "control": "access_control",
            "evidence_type": "bitwarden_policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "type": raw.get("type"),
                "enabled": raw.get("enabled"),
                "data": raw.get("data"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "bitwarden",
            "control": "access_control",
            "evidence_type": "bitwarden_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "accessAll": raw.get("accessAll"),
            },
        }
