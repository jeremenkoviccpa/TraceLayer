"""
Zoom integration via Zoom REST API v2.

Credentials:
  account_id    — Zoom account ID (Server-to-Server OAuth)
  client_id     — OAuth client ID
  client_secret — OAuth client secret
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_TOKEN_URL = "https://zoom.us/oauth/token"
_BASE = "https://api.zoom.us/v2"


class ZoomIntegration(IntegrationAdapter):

    def __init__(self):
        self._account_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    async def _fetch_token(self, account_id: str, client_id: str, client_secret: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _TOKEN_URL,
                params={"grant_type": "account_credentials", "account_id": account_id},
                auth=(client_id, client_secret),
            )
            if r.status_code != 200:
                raise IntegrationAuthError("Invalid Zoom credentials.")
            return r.json()["access_token"]

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        account_id = credentials.get("account_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not account_id or not client_id or not client_secret:
            raise IntegrationAuthError("account_id, client_id, and client_secret are required.")

        token = await self._fetch_token(account_id, client_id, client_secret)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Zoom credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Zoom connect failed HTTP {r.status_code}")

        self._account_id = account_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_account_settings,
                self._collect_roles,
                self._collect_groups,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Zoom collection error in %s: %s", fetch_fn.__name__, exc
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
        users: list[dict] = []
        url = f"{_BASE}/users"
        params = {"status": "active", "page_size": 300}

        while True:
            r = await client.get(url, headers=self._auth_headers(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"Zoom users HTTP {r.status_code}")
            body = r.json()
            users.extend(body.get("users", []))
            next_token = body.get("next_page_token")
            if not next_token:
                break
            params = {"status": "active", "page_size": 300, "next_page_token": next_token}

        return [{"_type": "user", **u} for u in users]

    async def _collect_account_settings(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/accounts/me/settings",
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoom account settings HTTP {r.status_code}")
        return [{"_type": "account_settings", **r.json()}]

    async def _collect_roles(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/roles", headers=self._auth_headers())
        if r.status_code != 200:
            raise RuntimeError(f"Zoom roles HTTP {r.status_code}")
        return [{"_type": "role", **item} for item in r.json().get("roles", [])]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/groups", headers=self._auth_headers())
        if r.status_code != 200:
            raise RuntimeError(f"Zoom groups HTTP {r.status_code}")
        return [{"_type": "group", **item} for item in r.json().get("groups", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "account_settings":
                result.append(self._norm_account_settings(item))
            elif t == "role":
                result.append(self._norm_role(item))
            elif t == "group":
                result.append(self._norm_group(item))
        return result

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "zoom",
            "control": "access_control",
            "evidence_type": "zoom_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "email": raw.get("email"),
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "pmi": raw.get("pmi"),
                "timezone": raw.get("timezone"),
                "last_login_time": raw.get("last_login_time"),
                "two_factor_authentication": raw.get("two_factor_authentication"),
            },
        }

    def _norm_account_settings(self, raw: dict) -> dict:
        security = raw.get("security", {})
        pwd_req = security.get("password_requirement", {})
        meeting_security = raw.get("meeting_security", {})
        return {
            "integration": "zoom",
            "control": "access_control",
            "evidence_type": "zoom_account_settings",
            "source_id": "account_settings",
            "timestamp": self._now(),
            "data": {
                "password_require_uppercase": pwd_req.get("have_upper_and_lower_characters"),
                "mfa_enabled": security.get("sign_in_with_two_factor_auth"),
                "waiting_room": meeting_security.get("waiting_room"),
                "require_password_for_meetings": meeting_security.get(
                    "require_password_for_all_meetings"
                ),
            },
        }

    def _norm_role(self, raw: dict) -> dict:
        return {
            "integration": "zoom",
            "control": "access_control",
            "evidence_type": "zoom_roles",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "total_members": raw.get("total_members"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "zoom",
            "control": "access_control",
            "evidence_type": "zoom_groups",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "total_members": raw.get("total_members"),
            },
        }
