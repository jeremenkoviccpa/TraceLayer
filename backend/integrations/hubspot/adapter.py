"""HubSpot CRM integration — collects users, roles, owners, and account security settings."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

HUBSPOT_API = "https://api.hubapi.com"


class HubSpotIntegration(IntegrationAdapter):
    def __init__(self):
        self._token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("access_token", "").strip()
        if not token:
            raise IntegrationAuthError("HubSpot private app access token is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{HUBSPOT_API}/crm/v3/owners",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid HubSpot access token. Ensure the private app has the required scopes.")
            r.raise_for_status()
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client, headers)
            owners = await self._collect_owners(client, headers)
            account = await self._collect_account(client, headers)
        return users + owners + account

    async def _collect_users(self, client, headers) -> list[dict]:
        items: list[dict] = []
        after: str | None = None
        while True:
            params: dict = {"limit": 100}
            if after:
                params["after"] = after
            r = await client.get(f"{HUBSPOT_API}/settings/v3/users", headers=headers, params=params)
            if r.status_code == 403:
                return []
            r.raise_for_status()
            data = r.json()
            items.extend([{"_type": "hubspot_user", **u} for u in data.get("results", [])])
            paging = data.get("paging", {}).get("next", {})
            after = paging.get("after")
            if not after:
                break
        return items

    async def _collect_owners(self, client, headers) -> list[dict]:
        items: list[dict] = []
        after: str | None = None
        while True:
            params: dict = {"limit": 100}
            if after:
                params["after"] = after
            r = await client.get(f"{HUBSPOT_API}/crm/v3/owners", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            items.extend([{"_type": "hubspot_owner", **o} for o in data.get("results", [])])
            paging = data.get("paging", {}).get("next", {})
            after = paging.get("after")
            if not after:
                break
        return items

    async def _collect_account(self, client, headers) -> list[dict]:
        r = await client.get(f"{HUBSPOT_API}/account-info/v3/details", headers=headers)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return [{"_type": "hubspot_account", **r.json()}]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "hubspot_user":
                result.append(self._norm_user(item))
            elif t == "hubspot_owner":
                result.append(self._norm_owner(item))
            elif t == "hubspot_account":
                result.append(self._norm_account(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "hubspot",
            "control": "access_control",
            "evidence_type": "hubspot_users",
            "source_id": str(raw.get("id", "unknown")),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "email": raw.get("email"),
                "first_name": raw.get("firstName"),
                "last_name": raw.get("lastName"),
                "role_id": raw.get("roleId"),
                "primary_team_id": raw.get("primaryTeamId"),
                "super_admin": raw.get("superAdmin", False),
            },
        }

    def _norm_owner(self, raw: dict) -> dict:
        return {
            "integration": "hubspot",
            "control": "access_control",
            "evidence_type": "hubspot_owners",
            "source_id": str(raw.get("id", "unknown")),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "email": raw.get("email"),
                "first_name": raw.get("firstName"),
                "last_name": raw.get("lastName"),
                "user_id": raw.get("userId"),
                "archived": raw.get("archived", False),
                "created_at": raw.get("createdAt"),
            },
        }

    def _norm_account(self, raw: dict) -> dict:
        return {
            "integration": "hubspot",
            "control": "data_protection",
            "evidence_type": "hubspot_account",
            "source_id": str(raw.get("portalId", "account")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "portal_id": raw.get("portalId"),
                "company_name": raw.get("companyName"),
                "time_zone": raw.get("timeZone"),
                "currency": raw.get("currency"),
                "data_hosting_location": raw.get("dataHostingLocation"),
                "ui_domain": raw.get("uiDomain"),
            },
        }
