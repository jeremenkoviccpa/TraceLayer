"""HackerRank Work integration — collects tests, candidates, and assessment results."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

HACKERRANK_API = "https://www.hackerrank.com/x/api/v3"


class HackerRankIntegration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("HackerRank API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{HACKERRANK_API}/tests",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid HackerRank API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            tests = await self._paginate(client, headers, "/tests", "data", "hackerrank_test")
            candidates = await self._paginate(client, headers, "/candidates", "data", "hackerrank_candidate")
        return tests + candidates

    async def _paginate(self, client, headers, path, data_key, type_tag) -> list[dict]:
        items: list[dict] = []
        offset = 0
        limit = 100
        while True:
            r = await client.get(
                f"{HACKERRANK_API}{path}",
                headers=headers,
                params={"limit": limit, "offset": offset},
            )
            r.raise_for_status()
            data = r.json()
            batch = data.get(data_key, data.get("models", []))
            if not batch:
                break
            items.extend([{"_type": type_tag, **item} for item in batch])
            total = data.get("total", 0)
            offset += limit
            if offset >= total:
                break
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "hackerrank_test":
                result.append(self._norm_test(item))
            elif t == "hackerrank_candidate":
                result.append(self._norm_candidate(item))
        return result

    def _norm_test(self, raw: dict) -> dict:
        return {
            "integration": "hackerrank",
            "control": "hr_security",
            "evidence_type": "hackerrank_tests",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "state": raw.get("state"),
                "duration": raw.get("duration"),
                "candidate_count": raw.get("candidate_count"),
                "unique_id": raw.get("unique_id"),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_candidate(self, raw: dict) -> dict:
        return {
            "integration": "hackerrank",
            "control": "hr_security",
            "evidence_type": "hackerrank_candidates",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "email": raw.get("email"),
                "full_name": raw.get("full_name"),
                "status": raw.get("status"),
                "percentage_score": raw.get("percentage_score"),
                "test_id": raw.get("test_id"),
                "attempt_start_time": raw.get("attempt_start_time"),
                "attempt_end_time": raw.get("attempt_end_time"),
            },
        }
