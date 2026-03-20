"""
Jamf Pro integration via Jamf Pro API (v1) and Classic API.

Credentials:
  server   — e.g. "https://company.jamfcloud.com"
  username — Jamf Pro username
  password — Jamf Pro password
"""
import base64
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class JamfIntegration(IntegrationAdapter):

    def __init__(self):
        self._server: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    def _classic_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def _get_token(
        self, server: str, username: str, password: str, client: httpx.AsyncClient
    ) -> str:
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        r = await client.post(
            f"{server}/api/v1/auth/token",
            headers={
                "Authorization": f"Basic {credentials}",
                "Accept": "application/json",
            },
        )
        if r.status_code == 401:
            raise IntegrationAuthError("Invalid Jamf Pro username or password")
        if r.status_code == 403:
            raise IntegrationAuthError("Jamf Pro account lacks required permissions")
        r.raise_for_status()
        body = r.json()
        token = body.get("token")
        if not token:
            raise IntegrationAuthError("Jamf Pro token response missing token field")
        return token

    async def connect(self, credentials: dict) -> bool:
        server = credentials.get("server", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()

        if not server or not username or not password:
            raise IntegrationAuthError("server, username, and password are required")

        if not server.startswith("http"):
            server = f"https://{server}"

        async with httpx.AsyncClient(timeout=15) as client:
            token = await self._get_token(server, username, password, client)
            # Probe Jamf Pro information endpoint to confirm token works
            r = await client.get(
                f"{server}/api/v1/jamf-pro-information",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Jamf Pro token rejected on verification endpoint")
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "Jamf Pro token lacks permission to read server information"
                )
            r.raise_for_status()

        self._server = server
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            computers = await self._collect_computers(client)
            policies = await self._collect_policies(client)
        return computers + policies

    # ------------------------------------------------------------------
    # computers (Pro API v1)
    # ------------------------------------------------------------------

    async def _collect_computers(self, client: httpx.AsyncClient) -> list[dict]:
        computers = []
        page = 0
        page_size = 100
        while True:
            try:
                r = await client.get(
                    f"{self._server}/api/v1/computers-preview",
                    params={"page": page, "page-size": page_size},
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                items = body.get("results", body) if isinstance(body, dict) else body
                if not items:
                    break
                for c in items:
                    general = c.get("general", c)
                    hardware = c.get("hardware", {})
                    user_loc = c.get("userAndLocation", {})
                    computers.append({
                        "_type": "computer",
                        "id": str(c.get("id", general.get("id", ""))),
                        "name": general.get("name", c.get("name")),
                        "last_contact_time": general.get(
                            "lastContactTime", c.get("lastContactTime")
                        ),
                        "os_name": hardware.get("osName"),
                        "os_version": hardware.get("osVersion"),
                        "username": user_loc.get("username"),
                    })
                # Stop when we get fewer results than requested
                if len(items) < page_size:
                    break
                page += 1
            except Exception as exc:
                print(f"[Jamf] computer collection page {page} failed: {exc}")
                break
        return computers

    # ------------------------------------------------------------------
    # policies (Classic API)
    # ------------------------------------------------------------------

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        policies = []
        try:
            r = await client.get(
                f"{self._server}/JSSResource/policies",
                headers=self._classic_headers(),
            )
            r.raise_for_status()
            body = r.json()
            # Classic API wraps in {"policies": [...]}
            raw_list = body.get("policies", body) if isinstance(body, dict) else body
            for p in raw_list:
                policies.append({
                    "_type": "policy",
                    "id": str(p.get("id", "")),
                    "name": p.get("name"),
                    "enabled": p.get("enabled"),
                    "scope": p.get("scope"),
                })
        except Exception as exc:
            print(f"[Jamf] policy collection failed: {exc}")
        return policies

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "computer":
                result.append(self._norm_computer(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
        return result

    def _norm_computer(self, raw: dict) -> dict:
        return {
            "integration": "jamf",
            "control": "endpoint_security",
            "evidence_type": "jamf_computers",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("last_contact_time") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "last_contact_time": raw.get("last_contact_time"),
                "os_name": raw.get("os_name"),
                "os_version": raw.get("os_version"),
                "username": raw.get("username"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "jamf",
            "control": "endpoint_security",
            "evidence_type": "jamf_policies",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "scope": raw.get("scope"),
            },
        }
