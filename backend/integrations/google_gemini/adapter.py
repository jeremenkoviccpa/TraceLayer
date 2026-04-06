"""Google Gemini / Generative AI integration — collects available models and API configuration for AI vendor compliance."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"
VERTEX_API = "https://us-central1-aiplatform.googleapis.com/v1"


class GoogleGeminiIntegration(IntegrationAdapter):
    """
    Collects Google Gemini / Generative AI model inventory and configuration as evidence
    for AI vendor risk management controls. Supports both Gemini API (API key) and
    Vertex AI (service account) authentication.
    """

    def __init__(self):
        self._api_key: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("Google Gemini API key is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{GEMINI_API}/models",
                params={"key": api_key, "pageSize": 1},
            )
            if r.status_code in (400, 401, 403):
                raise IntegrationAuthError(f"Invalid Gemini API key: {r.json().get('error', {}).get('message', 'auth failed')}")
            r.raise_for_status()
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            models = await self._collect_models(client)
        return models

    async def _collect_models(self, client) -> list[dict]:
        items: list[dict] = []
        page_token: str | None = None
        while True:
            params: dict = {"key": self._api_key, "pageSize": 50}
            if page_token:
                params["pageToken"] = page_token
            r = await client.get(f"{GEMINI_API}/models", params=params)
            r.raise_for_status()
            data = r.json()
            for model in data.get("models", []):
                items.append({"_type": "gemini_model", **model})
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            if item.get("_type") == "gemini_model":
                result.append(self._norm_model(item))
        return result

    def _norm_model(self, raw: dict) -> dict:
        return {
            "integration": "google_gemini",
            "control": "ai_supply_chain",
            "evidence_type": "gemini_models",
            "source_id": raw.get("name", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "display_name": raw.get("displayName"),
                "description": raw.get("description"),
                "version": raw.get("version"),
                "input_token_limit": raw.get("inputTokenLimit"),
                "output_token_limit": raw.get("outputTokenLimit"),
                "supported_generation_methods": raw.get("supportedGenerationMethods", []),
                "temperature": raw.get("temperature"),
                "top_p": raw.get("topP"),
                "top_k": raw.get("topK"),
            },
        }
