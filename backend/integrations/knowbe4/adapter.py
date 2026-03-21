"""KnowBe4 security awareness training integration — collects users, campaigns, and phishing results."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

KNOWBE4_API = "https://us.api.knowbe4.com/v1"


class KnowBe4Integration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("KnowBe4 API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{KNOWBE4_API}/account",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid KnowBe4 API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._paginate(client, headers, "/users", "knowbe4_user")
            campaigns = await self._paginate(client, headers, "/training/campaigns", "knowbe4_campaign")
            phishing = await self._paginate(client, headers, "/phishing/campaigns", "knowbe4_phishing")
        return users + campaigns + phishing

    async def _paginate(self, client, headers, path, type_tag) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{KNOWBE4_API}{path}",
                headers=headers,
                params={"per_page": 500, "page": page},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            items.extend([{"_type": type_tag, **item} for item in (batch if isinstance(batch, list) else [])])
            if len(batch) < 500:
                break
            page += 1
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "knowbe4_user":
                result.append(self._norm_user(item))
            elif t == "knowbe4_campaign":
                result.append(self._norm_campaign(item))
            elif t == "knowbe4_phishing":
                result.append(self._norm_phishing(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "knowbe4",
            "control": "security_awareness",
            "evidence_type": "knowbe4_users",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "email": raw.get("email"),
                "status": raw.get("status"),
                "current_risk_score": raw.get("current_risk_score"),
                "groups": raw.get("groups", []),
                "employee_start_date": raw.get("employee_start_date"),
            },
        }

    def _norm_campaign(self, raw: dict) -> dict:
        return {
            "integration": "knowbe4",
            "control": "security_awareness",
            "evidence_type": "training_campaigns",
            "source_id": str(raw["campaign_id"]),
            "timestamp": raw.get("last_modified_date", datetime.now(timezone.utc).isoformat()),
            "data": {
                "campaign_id": raw["campaign_id"],
                "name": raw.get("name"),
                "status": raw.get("status"),
                "content": raw.get("content", []),
                "completion_percentage": raw.get("completion_percentage"),
                "start_date": raw.get("start_date"),
                "end_date": raw.get("end_date"),
            },
        }

    def _norm_phishing(self, raw: dict) -> dict:
        return {
            "integration": "knowbe4",
            "control": "security_awareness",
            "evidence_type": "phishing_campaigns",
            "source_id": str(raw["campaign_id"]),
            "timestamp": raw.get("last_modified_date", datetime.now(timezone.utc).isoformat()),
            "data": {
                "campaign_id": raw["campaign_id"],
                "name": raw.get("name"),
                "status": raw.get("status"),
                "phish_prone_percentage": raw.get("phish_prone_percentage"),
                "start_date": raw.get("start_date"),
                "duration": raw.get("duration"),
                "groups": raw.get("groups", []),
            },
        }
