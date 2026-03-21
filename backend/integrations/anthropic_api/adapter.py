"""Anthropic integration — collects API key inventory, model access, and usage for AI vendor compliance evidence."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

ANTHROPIC_API = "https://api.anthropic.com/v1"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicIntegration(IntegrationAdapter):
    """
    Collects Anthropic Claude model inventory, API key configurations, and organization
    settings as evidence for AI vendor risk management and data processing controls.
    Supports the Anthropic Administration API for key and usage management.
    """

    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("Anthropic API key is required.")
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{ANTHROPIC_API}/models", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Anthropic API key.")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            models = await self._collect_models(client, headers)
            api_keys = await self._collect_api_keys(client, headers)
            workspaces = await self._collect_workspaces(client, headers)
        return models + api_keys + workspaces

    async def _collect_models(self, client, headers) -> list[dict]:
        items: list[dict] = []
        before_id: str | None = None
        while True:
            params: dict = {"limit": 20}
            if before_id:
                params["before_id"] = before_id
            r = await client.get(f"{ANTHROPIC_API}/models", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            batch = data.get("data", [])
            items.extend([{"_type": "anthropic_model", **m} for m in batch])
            if not data.get("has_more"):
                break
            before_id = batch[-1]["id"] if batch else None
        return items

    async def _collect_api_keys(self, client, headers) -> list[dict]:
        """Collect API key inventory via Administration API (requires admin key)."""
        r = await client.get(
            f"{ANTHROPIC_API}/organizations/api_keys",
            headers={**headers, "anthropic-beta": "admin-api-2025-05-21"},
            params={"limit": 100},
        )
        if r.status_code in (400, 403, 404):
            return []  # Standard API key — admin API requires admin key
        r.raise_for_status()
        return [{"_type": "anthropic_api_key", **k} for k in r.json().get("data", [])]

    async def _collect_workspaces(self, client, headers) -> list[dict]:
        """Collect workspace configuration via Administration API."""
        r = await client.get(
            f"{ANTHROPIC_API}/organizations/workspaces",
            headers={**headers, "anthropic-beta": "admin-api-2025-05-21"},
            params={"limit": 100},
        )
        if r.status_code in (400, 403, 404):
            return []
        r.raise_for_status()
        return [{"_type": "anthropic_workspace", **w} for w in r.json().get("data", [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "anthropic_model":
                result.append(self._norm_model(item))
            elif t == "anthropic_api_key":
                result.append(self._norm_api_key(item))
            elif t == "anthropic_workspace":
                result.append(self._norm_workspace(item))
        return result

    def _norm_model(self, raw: dict) -> dict:
        return {
            "integration": "anthropic",
            "control": "vendor_management",
            "evidence_type": "anthropic_models",
            "source_id": raw["id"],
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "display_name": raw.get("display_name"),
                "created_at": raw.get("created_at"),
                "type": raw.get("type"),
            },
        }

    def _norm_api_key(self, raw: dict) -> dict:
        return {
            "integration": "anthropic",
            "control": "access_control",
            "evidence_type": "anthropic_api_keys",
            "source_id": raw["id"],
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "status": raw.get("status"),
                "hint": raw.get("hint"),
                "workspace_id": raw.get("workspace_id"),
                "created_by": raw.get("created_by", {}),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_workspace(self, raw: dict) -> dict:
        return {
            "integration": "anthropic",
            "control": "vendor_management",
            "evidence_type": "anthropic_workspaces",
            "source_id": raw["id"],
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "display_name": raw.get("display_name"),
                "status": raw.get("status"),
                "created_at": raw.get("created_at"),
            },
        }
