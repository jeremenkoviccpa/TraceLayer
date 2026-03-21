"""Lever ATS integration — collects job postings, candidates, and background check status."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

LEVER_API = "https://api.lever.co/v1"


class LeverIntegration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("Lever API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{LEVER_API}/postings", auth=(api_key, ""))
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Lever API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            postings = await self._paginate(client, "/postings", "lever_posting")
            users = await self._paginate(client, "/users", "lever_user")
        return postings + users

    async def _paginate(self, client, path, type_tag) -> list[dict]:
        items: list[dict] = []
        params: dict = {"limit": 100}
        while True:
            r = await client.get(
                f"{LEVER_API}{path}",
                auth=(self._api_key, ""),
                params=params,
            )
            r.raise_for_status()
            data = r.json()
            batch = data.get("data", [])
            items.extend([{"_type": type_tag, **item} for item in batch])
            if not data.get("hasNext"):
                break
            params["offset"] = data.get("next")
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "lever_posting":
                result.append(self._norm_posting(item))
            elif t == "lever_user":
                result.append(self._norm_user(item))
        return result

    def _norm_posting(self, raw: dict) -> dict:
        created = raw.get("createdAt")
        ts = (
            datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
            if created
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "lever",
            "control": "hr_security",
            "evidence_type": "job_postings",
            "source_id": raw["id"],
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "text": raw.get("text"),
                "state": raw.get("state"),
                "department": raw.get("categories", {}).get("department"),
                "team": raw.get("categories", {}).get("team"),
                "location": raw.get("categories", {}).get("location"),
                "commitment": raw.get("categories", {}).get("commitment"),
                "owner_id": raw.get("owner"),
                "created_at": ts,
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        created = raw.get("createdAt")
        ts = (
            datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
            if created
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "lever",
            "control": "hr_security",
            "evidence_type": "lever_users",
            "source_id": raw["id"],
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "email": raw.get("email"),
                "username": raw.get("username"),
                "access_role": raw.get("accessRole"),
                "is_deactivated": raw.get("deactivatedAt") is not None,
                "created_at": ts,
            },
        }
