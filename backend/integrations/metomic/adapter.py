"""Metomic data security integration — collects data policies, regexes, and risk events."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

METOMIC_API = "https://api.metomic.io/v1"


class MetomicIntegration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("Metomic API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{METOMIC_API}/policies",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Metomic API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            policies = await self._collect(client, headers, "/policies", "metomic_policy")
            regexes = await self._collect(client, headers, "/regexes", "metomic_regex")
        return policies + regexes

    async def _collect(self, client, headers, path, type_tag) -> list[dict]:
        items: list[dict] = []
        params: dict = {"limit": 100, "offset": 0}
        while True:
            r = await client.get(f"{METOMIC_API}{path}", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            # Support both list and paginated object responses
            batch = data if isinstance(data, list) else data.get("data", data.get("items", []))
            if not batch:
                break
            items.extend([{"_type": type_tag, **item} for item in batch])
            if isinstance(data, list) or len(batch) < params["limit"]:
                break
            params["offset"] += params["limit"]
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "metomic_policy":
                result.append(self._norm_policy(item))
            elif t == "metomic_regex":
                result.append(self._norm_regex(item))
        return result

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "metomic",
            "control": "data_protection",
            "evidence_type": "metomic_policies",
            "source_id": str(raw.get("id", raw.get("uuid", "unknown"))),
            "timestamp": raw.get("updatedAt", raw.get("updated_at", datetime.now(timezone.utc).isoformat())),
            "data": {
                "id": raw.get("id") or raw.get("uuid"),
                "name": raw.get("name"),
                "description": raw.get("description"),
                "is_active": raw.get("isActive", raw.get("is_active", True)),
                "action": raw.get("action"),
                "severity": raw.get("severity"),
                "created_at": raw.get("createdAt") or raw.get("created_at"),
            },
        }

    def _norm_regex(self, raw: dict) -> dict:
        return {
            "integration": "metomic",
            "control": "data_protection",
            "evidence_type": "metomic_classifiers",
            "source_id": str(raw.get("id", raw.get("uuid", "unknown"))),
            "timestamp": raw.get("updatedAt", raw.get("updated_at", datetime.now(timezone.utc).isoformat())),
            "data": {
                "id": raw.get("id") or raw.get("uuid"),
                "name": raw.get("name"),
                "description": raw.get("description"),
                "type": raw.get("type"),
                "is_active": raw.get("isActive", raw.get("is_active", True)),
            },
        }
