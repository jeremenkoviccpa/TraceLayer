"""Harvest time-tracking integration — collects users, projects, and time entries."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

HARVEST_API = "https://api.harvestapp.com/v2"


class HarvestIntegration(IntegrationAdapter):
    def __init__(self):
        self._token: str | None = None
        self._account_id: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("access_token", "").strip()
        account_id = credentials.get("account_id", "").strip()
        if not token or not account_id:
            raise IntegrationAuthError("Access token and account ID are required.")
        headers = {
            "Authorization": f"Bearer {token}",
            "Harvest-Account-Id": account_id,
            "User-Agent": "TraceLayer-Compliance/1.0",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{HARVEST_API}/users/me", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Harvest access token or account ID.")
            r.raise_for_status()
        self._token = token
        self._account_id = account_id
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Harvest-Account-Id": self._account_id,
            "User-Agent": "TraceLayer-Compliance/1.0",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._paginate(client, headers, "/users", "users", "harvest_user")
            projects = await self._paginate(client, headers, "/projects", "projects", "harvest_project")
            clients = await self._paginate(client, headers, "/clients", "clients", "harvest_client")
        return users + projects + clients

    async def _paginate(self, client, headers, path, key, type_tag) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{HARVEST_API}{path}",
                headers=headers,
                params={"page": page, "per_page": 100},
            )
            r.raise_for_status()
            data = r.json()
            batch = data.get(key, [])
            items.extend([{"_type": type_tag, **item} for item in batch])
            if not data.get("next_page"):
                break
            page += 1
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "harvest_user":
                result.append(self._norm_user(item))
            elif t == "harvest_project":
                result.append(self._norm_project(item))
            elif t == "harvest_client":
                result.append(self._norm_client(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "harvest",
            "control": "access_control",
            "evidence_type": "harvest_users",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "email": raw.get("email"),
                "is_active": raw.get("is_active", True),
                "is_admin": raw.get("is_admin", False),
                "access_roles": raw.get("access_roles", []),
                "timezone": raw.get("timezone"),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "harvest",
            "control": "change_management",
            "evidence_type": "harvest_projects",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "code": raw.get("code"),
                "is_active": raw.get("is_active", True),
                "is_billable": raw.get("is_billable"),
                "budget": raw.get("budget"),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_client(self, raw: dict) -> dict:
        return {
            "integration": "harvest",
            "control": "vendor_management",
            "evidence_type": "harvest_clients",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "is_active": raw.get("is_active", True),
                "currency": raw.get("currency"),
                "created_at": raw.get("created_at"),
            },
        }
