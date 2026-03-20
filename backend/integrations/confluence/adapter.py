"""
Confluence Cloud integration via REST API.
Credentials: { "domain": "mycompany", "email": "xxx@company.com", "api_token": "xxx" }
"""
import base64
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class ConfluenceIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._auth: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Basic {self._auth}",
            "Accept": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        domain = credentials.get("domain", "").strip().rstrip("/")
        email = credentials.get("email", "").strip()
        token = credentials.get("api_token", "").strip()
        if not domain or not email or not token:
            raise IntegrationAuthError("domain, email, and api_token are required")
        if not domain.startswith("http"):
            domain = f"https://{domain}.atlassian.net"
        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{domain}/wiki/rest/api/space",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
                params={"limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Confluence credentials")
            r.raise_for_status()
        self._base = f"{domain}/wiki/rest/api"
        self._auth = auth
        return True

    async def collect_evidence(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                results += await self._collect_spaces(client)
            except Exception:
                pass
            try:
                results += await self._collect_pages(client)
            except Exception:
                pass
            try:
                results += await self._collect_groups(client)
            except Exception:
                pass
        return results

    async def _collect_spaces(self, client: httpx.AsyncClient) -> list[dict]:
        spaces, start = [], 0
        while True:
            r = await client.get(f"{self._base}/space", headers=self._headers(),
                                 params={"limit": 50, "start": start})
            r.raise_for_status()
            data = r.json()
            for s in data.get("results", []):
                spaces.append({"_type": "space", **s})
            if data.get("size", 0) < 50:
                break
            start += 50
        return spaces

    async def _collect_pages(self, client: httpx.AsyncClient) -> list[dict]:
        pages, start = [], 0
        while True:
            r = await client.get(f"{self._base}/content", headers=self._headers(),
                                 params={"type": "page", "limit": 100, "start": start,
                                         "expand": "history,space"})
            r.raise_for_status()
            data = r.json()
            for p in data.get("results", []):
                pages.append({"_type": "page", **p})
            if data.get("size", 0) < 100:
                break
            start += 100
            if start > 500:  # cap at 500 pages
                break
        return pages

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        groups, start = [], 0
        while True:
            r = await client.get(f"{self._base}/group", headers=self._headers(),
                                 params={"limit": 100, "start": start})
            r.raise_for_status()
            data = r.json()
            for g in data.get("results", []):
                groups.append({"_type": "group", **g})
            if data.get("size", 0) < 100:
                break
            start += 100
        return groups

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "space":
                result.append({
                    "integration": "confluence",
                    "control": "change_management",
                    "evidence_type": "confluence_spaces",
                    "source_id": item.get("key", item.get("id", "")),
                    "timestamp": now,
                    "data": {
                        "key": item.get("key"),
                        "name": item.get("name"),
                        "type": item.get("type"),
                        "status": item.get("status"),
                    },
                })
            elif t == "page":
                history = item.get("history", {})
                result.append({
                    "integration": "confluence",
                    "control": "change_management",
                    "evidence_type": "confluence_pages",
                    "source_id": item["id"],
                    "timestamp": history.get("createdDate", now),
                    "data": {
                        "title": item.get("title"),
                        "space": item.get("space", {}).get("key"),
                        "created_date": history.get("createdDate"),
                        "last_updated": history.get("lastUpdated", {}).get("when"),
                        "created_by": history.get("createdBy", {}).get("displayName"),
                    },
                })
            elif t == "group":
                result.append({
                    "integration": "confluence",
                    "control": "access_control",
                    "evidence_type": "confluence_groups",
                    "source_id": item.get("id", item.get("name", "")),
                    "timestamp": now,
                    "data": {
                        "name": item.get("name"),
                        "type": item.get("type"),
                    },
                })
        return result
