"""
Intercom integration via Intercom REST API.

Credentials:
  access_token — Intercom access token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.intercom.io"
_INTERCOM_VERSION = "2.10"


class IntercomIntegration(IntegrationAdapter):

    def __init__(self):
        self._access_token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
            "Intercom-Version": _INTERCOM_VERSION,
        }

    def _ts(self, value) -> str:
        """Convert a Unix timestamp int or ISO string to ISO-8601. Returns now if falsy."""
        if not value:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, int):
            return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
        return value

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        access_token = credentials.get("access_token", "").strip()
        if not access_token:
            raise IntegrationAuthError("access_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                    "Intercom-Version": _INTERCOM_VERSION,
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Intercom access token.")
            if r.status_code != 200:
                raise RuntimeError(f"Intercom connect failed HTTP {r.status_code}")

        self._access_token = access_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_admins,
                self._collect_teams,
                self._collect_app,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Intercom collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_admins(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/admins", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Intercom admins HTTP {r.status_code}")
        return [{"_type": "admin", **item} for item in r.json().get("admins", [])]

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/teams", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Intercom teams HTTP {r.status_code}")
        return [{"_type": "team", **item} for item in r.json().get("teams", [])]

    async def _collect_app(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/me", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Intercom /me HTTP {r.status_code}")
        app = r.json().get("app", {})
        return [{"_type": "app", **app}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "admin":
                result.append(self._norm_admin(item))
            elif t == "team":
                result.append(self._norm_team(item))
            elif t == "app":
                result.append(self._norm_app(item))
        return result

    def _norm_admin(self, raw: dict) -> dict:
        return {
            "integration": "intercom",
            "control": "access_control",
            "evidence_type": "intercom_admins",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._ts(raw.get("created_at")),
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "type": raw.get("type"),
                "has_inbox_seat": raw.get("has_inbox_seat"),
                "two_factor_auth_enabled": raw.get("two_factor_auth_enabled"),
            },
        }

    def _norm_team(self, raw: dict) -> dict:
        return {
            "integration": "intercom",
            "control": "access_control",
            "evidence_type": "intercom_teams",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "admin_ids": raw.get("admin_ids", []),
            },
        }

    def _norm_app(self, raw: dict) -> dict:
        return {
            "integration": "intercom",
            "control": "access_control",
            "evidence_type": "intercom_app",
            "source_id": str(raw.get("id_code", "")),
            "timestamp": self._ts(raw.get("created_at")),
            "data": {
                "name": raw.get("name"),
                "region": raw.get("region"),
                "timezone": raw.get("timezone"),
                "identity_verification": raw.get("identity_verification"),
            },
        }
