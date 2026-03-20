"""
Notion integration via Notion API v1.
Credentials: { "api_key": "secret_xxx" }
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_BASE = "https://api.notion.com/v1"
_VERSION = "2022-06-28"


class NotionIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Notion-Version": _VERSION,
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_key", "").strip()
        if not token:
            raise IntegrationAuthError("api_key is required")
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{_BASE}/users", headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": _VERSION,
            })
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Notion integration token")
            r.raise_for_status()
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                results += await self._collect_users(client)
            except Exception:
                pass
            try:
                results += await self._search(client, "database")
            except Exception:
                pass
            try:
                results += await self._search(client, "page")
            except Exception:
                pass
        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users, cursor = [], None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            r = await client.get(f"{_BASE}/users", headers=self._headers(), params=params)
            r.raise_for_status()
            data = r.json()
            for u in data.get("results", []):
                users.append({"_type": "user", **u})
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return users

    async def _search(self, client: httpx.AsyncClient, obj_type: str) -> list[dict]:
        items, cursor = [], None
        while True:
            body: dict = {"filter": {"value": obj_type, "property": "object"}, "page_size": 100}
            if cursor:
                body["start_cursor"] = cursor
            r = await client.post(f"{_BASE}/search", headers=self._headers(), json=body)
            r.raise_for_status()
            data = r.json()
            for item in data.get("results", []):
                items.append({"_type": obj_type, **item})
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                person = item.get("person", {})
                result.append({
                    "integration": "notion",
                    "control": "access_control",
                    "evidence_type": "notion_users",
                    "source_id": item["id"],
                    "timestamp": now,
                    "data": {
                        "name": item.get("name"),
                        "email": person.get("email"),
                        "type": item.get("type"),
                        "avatar_url": item.get("avatar_url"),
                    },
                })
            elif t == "database":
                title = item.get("title", [])
                name = title[0].get("plain_text", "") if title else ""
                result.append({
                    "integration": "notion",
                    "control": "change_management",
                    "evidence_type": "notion_databases",
                    "source_id": item["id"],
                    "timestamp": item.get("created_time", now),
                    "data": {
                        "name": name,
                        "created_time": item.get("created_time"),
                        "last_edited_time": item.get("last_edited_time"),
                        "url": item.get("url"),
                    },
                })
            elif t == "page":
                props = item.get("properties", {})
                title_prop = props.get("title") or props.get("Name") or {}
                title_arr = title_prop.get("title", []) if isinstance(title_prop, dict) else []
                name = title_arr[0].get("plain_text", "") if title_arr else item["id"]
                result.append({
                    "integration": "notion",
                    "control": "change_management",
                    "evidence_type": "notion_pages",
                    "source_id": item["id"],
                    "timestamp": item.get("created_time", now),
                    "data": {
                        "title": name,
                        "created_time": item.get("created_time"),
                        "last_edited_time": item.get("last_edited_time"),
                        "url": item.get("url"),
                        "parent_type": item.get("parent", {}).get("type"),
                    },
                })
        return result
