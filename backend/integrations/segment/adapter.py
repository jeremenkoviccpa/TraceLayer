"""Segment (Twilio) CDP integration — collects sources, destinations, warehouses, and workspace users."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

SEGMENT_API = "https://api.segmentapis.com"


class SegmentIntegration(IntegrationAdapter):
    def __init__(self):
        self._token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("access_token", "").strip()
        if not token:
            raise IntegrationAuthError("Segment Public API access token is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{SEGMENT_API}/workspaces",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Segment access token.")
            r.raise_for_status()
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            workspace = await self._collect_workspace(client, headers)
            sources = await self._paginate(client, headers, "/sources", "sources", "segment_source")
            destinations = await self._paginate(client, headers, "/destinations", "destinations", "segment_destination")
            warehouses = await self._paginate(client, headers, "/warehouses", "warehouses", "segment_warehouse")
            users = await self._paginate(client, headers, "/iam/users", "users", "segment_user")
        return workspace + sources + destinations + warehouses + users

    async def _collect_workspace(self, client, headers) -> list[dict]:
        r = await client.get(f"{SEGMENT_API}/workspaces", headers=headers)
        r.raise_for_status()
        w = r.json().get("data", {}).get("workspace", {})
        return [{"_type": "segment_workspace", **w}] if w else []

    async def _paginate(self, client, headers, path, data_key, type_tag) -> list[dict]:
        items: list[dict] = []
        cursor: str | None = None
        while True:
            params: dict = {"pagination[count]": 200}
            if cursor:
                params["pagination[cursor]"] = cursor
            r = await client.get(f"{SEGMENT_API}{path}", headers=headers, params=params)
            if r.status_code == 403:
                return []  # May not have permission for this resource
            r.raise_for_status()
            data = r.json().get("data", {})
            batch = data.get(data_key, [])
            items.extend([{"_type": type_tag, **item} for item in batch])
            pagination = data.get("pagination", {})
            cursor = pagination.get("next")
            if not cursor:
                break
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "segment_workspace":
                result.append(self._norm_workspace(item))
            elif t == "segment_source":
                result.append(self._norm_source(item))
            elif t == "segment_destination":
                result.append(self._norm_destination(item))
            elif t == "segment_warehouse":
                result.append(self._norm_warehouse(item))
            elif t == "segment_user":
                result.append(self._norm_user(item))
        return result

    def _norm_workspace(self, raw: dict) -> dict:
        return {
            "integration": "segment",
            "control": "data_protection",
            "evidence_type": "segment_workspace",
            "source_id": raw.get("id", "workspace"),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "created_at": raw.get("createdAt"),
            },
        }

    def _norm_source(self, raw: dict) -> dict:
        return {
            "integration": "segment",
            "control": "data_protection",
            "evidence_type": "segment_sources",
            "source_id": raw.get("id", "unknown"),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "enabled": raw.get("enabled"),
                "write_key": "REDACTED",
                "metadata": raw.get("metadata", {}).get("name"),
            },
        }

    def _norm_destination(self, raw: dict) -> dict:
        return {
            "integration": "segment",
            "control": "vendor_management",
            "evidence_type": "segment_destinations",
            "source_id": raw.get("id", "unknown"),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "metadata": raw.get("metadata", {}).get("name"),
            },
        }

    def _norm_warehouse(self, raw: dict) -> dict:
        return {
            "integration": "segment",
            "control": "data_protection",
            "evidence_type": "segment_warehouses",
            "source_id": raw.get("id", "unknown"),
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "metadata": raw.get("metadata", {}).get("name"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "segment",
            "control": "access_control",
            "evidence_type": "segment_users",
            "source_id": raw.get("id", "unknown"),
            "timestamp": raw.get("createdAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "email": raw.get("email"),
                "roles": raw.get("roles", []),
                "created_at": raw.get("createdAt"),
            },
        }
