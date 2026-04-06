"""OpenAI integration — collects API keys, projects, usage, and model access for AI vendor compliance evidence."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

OPENAI_API = "https://api.openai.com/v1"


class OpenAIIntegration(IntegrationAdapter):
    """
    Collects OpenAI organization configuration, project structure, API key inventory,
    and available models as evidence for AI vendor risk management and data processing controls.
    """

    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("OpenAI API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{OPENAI_API}/models",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid OpenAI API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        async with httpx.AsyncClient(timeout=30) as client:
            models = await self._collect_models(client, headers)
            org = await self._collect_org(client, headers)
            projects = await self._collect_projects(client, headers)
            api_keys = await self._collect_api_keys(client, headers)
        return models + org + projects + api_keys

    async def _collect_models(self, client, headers) -> list[dict]:
        r = await client.get(f"{OPENAI_API}/models", headers=headers)
        r.raise_for_status()
        return [{"_type": "openai_model", **m} for m in r.json().get("data", [])]

    async def _collect_org(self, client, headers) -> list[dict]:
        r = await client.get(f"{OPENAI_API}/organization/details", headers=headers)
        if r.status_code in (403, 404):
            return []
        r.raise_for_status()
        return [{"_type": "openai_org", **r.json()}]

    async def _collect_projects(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{OPENAI_API}/organization/projects",
            headers=headers,
            params={"limit": 100},
        )
        if r.status_code in (403, 404):
            return []
        r.raise_for_status()
        return [{"_type": "openai_project", **p} for p in r.json().get("data", [])]

    async def _collect_api_keys(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{OPENAI_API}/organization/api_keys",
            headers=headers,
            params={"limit": 100},
        )
        if r.status_code in (403, 404):
            return []
        r.raise_for_status()
        return [{"_type": "openai_api_key", **k} for k in r.json().get("data", [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "openai_model":
                result.append(self._norm_model(item))
            elif t == "openai_org":
                result.append(self._norm_org(item))
            elif t == "openai_project":
                result.append(self._norm_project(item))
            elif t == "openai_api_key":
                result.append(self._norm_api_key(item))
        return result

    def _norm_model(self, raw: dict) -> dict:
        created = raw.get("created")
        ts = (
            datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()
            if created
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "openai",
            "control": "ai_supply_chain",
            "evidence_type": "openai_models",
            "source_id": raw["id"],
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "object": raw.get("object"),
                "owned_by": raw.get("owned_by"),
                "created": ts,
            },
        }

    def _norm_org(self, raw: dict) -> dict:
        return {
            "integration": "openai",
            "control": "ai_supply_chain",
            "evidence_type": "openai_organization",
            "source_id": raw.get("id", "org"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "title": raw.get("title"),
                "description": raw.get("description"),
                "settings": raw.get("settings", {}),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        created = raw.get("created_at")
        ts = (
            datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()
            if created
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "openai",
            "control": "ai_supply_chain",
            "evidence_type": "openai_projects",
            "source_id": raw["id"],
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "status": raw.get("status"),
                "archived_at": raw.get("archived_at"),
                "created_at": ts,
            },
        }

    def _norm_api_key(self, raw: dict) -> dict:
        created = raw.get("created_at")
        ts = (
            datetime.fromtimestamp(int(created), tz=timezone.utc).isoformat()
            if created
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "openai",
            "control": "access_control",
            "evidence_type": "openai_api_keys",
            "source_id": raw["id"],
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "redacted_value": raw.get("redacted_value"),
                "owner": raw.get("owner", {}),
                "created_at": ts,
                "last_used_at": raw.get("last_used_at"),
            },
        }
