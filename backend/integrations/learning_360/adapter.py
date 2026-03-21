"""360Learning LMS integration — collects learners, courses, and training completions."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

LEARNING_API = "https://app.360learning.com/api/v1"


class Learning360Integration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None
        self._company_id: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        company_id = credentials.get("company_id", "").strip()
        if not api_key or not company_id:
            raise IntegrationAuthError("API key and company ID are required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{LEARNING_API}/groups",
                params={"apiKey": api_key, "companyId": company_id},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid 360Learning API key or company ID.")
            r.raise_for_status()
        self._api_key = api_key
        self._company_id = company_id
        return True

    async def collect_evidence(self) -> list[dict]:
        params_base = {"apiKey": self._api_key, "companyId": self._company_id}
        async with httpx.AsyncClient(timeout=30) as client:
            learners = await self._collect_learners(client, params_base)
            programs = await self._collect_programs(client, params_base)
        return learners + programs

    async def _collect_learners(self, client, params_base) -> list[dict]:
        items: list[dict] = []
        skip = 0
        limit = 200
        while True:
            r = await client.get(
                f"{LEARNING_API}/learners",
                params={**params_base, "limit": limit, "skip": skip},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            data = batch if isinstance(batch, list) else batch.get("data", batch.get("learners", []))
            if not data:
                break
            items.extend([{"_type": "learner_360", **u} for u in data])
            if len(data) < limit:
                break
            skip += limit
        return items

    async def _collect_programs(self, client, params_base) -> list[dict]:
        items: list[dict] = []
        skip = 0
        limit = 100
        while True:
            r = await client.get(
                f"{LEARNING_API}/programs",
                params={**params_base, "limit": limit, "skip": skip},
            )
            r.raise_for_status()
            batch = r.json()
            data = batch if isinstance(batch, list) else batch.get("data", batch.get("programs", []))
            if not data:
                break
            items.extend([{"_type": "program_360", **p} for p in data])
            if len(data) < limit:
                break
            skip += limit
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "learner_360":
                result.append(self._norm_learner(item))
            elif t == "program_360":
                result.append(self._norm_program(item))
        return result

    def _norm_learner(self, raw: dict) -> dict:
        return {
            "integration": "360learning",
            "control": "security_awareness",
            "evidence_type": "learner_registrations",
            "source_id": str(raw.get("_id") or raw.get("id", "unknown")),
            "timestamp": raw.get("updatedAt", raw.get("updated_at", datetime.now(timezone.utc).isoformat())),
            "data": {
                "id": raw.get("_id") or raw.get("id"),
                "name": raw.get("name"),
                "email": raw.get("email"),
                "groups": raw.get("groups", []),
                "registered_at": raw.get("registeredAt") or raw.get("registered_at"),
                "last_activity": raw.get("lastActivity") or raw.get("last_activity"),
            },
        }

    def _norm_program(self, raw: dict) -> dict:
        return {
            "integration": "360learning",
            "control": "security_awareness",
            "evidence_type": "training_programs",
            "source_id": str(raw.get("_id") or raw.get("id", "unknown")),
            "timestamp": raw.get("updatedAt", raw.get("updated_at", datetime.now(timezone.utc).isoformat())),
            "data": {
                "id": raw.get("_id") or raw.get("id"),
                "title": raw.get("title"),
                "status": raw.get("status"),
                "completion_rate": raw.get("completionRate") or raw.get("completion_rate"),
                "learner_count": raw.get("learnerCount") or raw.get("learner_count"),
                "created_at": raw.get("createdAt") or raw.get("created_at"),
            },
        }
