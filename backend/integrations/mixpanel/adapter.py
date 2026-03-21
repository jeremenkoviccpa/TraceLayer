"""Mixpanel integration — collects project settings, users, and data residency configuration."""
from datetime import datetime, timezone
import base64

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

MIXPANEL_API = "https://mixpanel.com/api/2.0"
MIXPANEL_DATA_API = "https://data.mixpanel.com/api/2.0"


class MixpanelIntegration(IntegrationAdapter):
    def __init__(self):
        self._project_id: str | None = None
        self._secret: str | None = None
        self._auth_header: str | None = None

    async def connect(self, credentials: dict) -> bool:
        project_id = credentials.get("project_id", "").strip()
        secret = credentials.get("service_account_secret", "").strip()
        username = credentials.get("service_account_username", "").strip()
        if not project_id or not secret or not username:
            raise IntegrationAuthError("Project ID, service account username, and secret are required.")
        encoded = base64.b64encode(f"{username}:{secret}".encode()).decode()
        headers = {"Authorization": f"Basic {encoded}"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{MIXPANEL_API}/projects/{project_id}",
                headers=headers,
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Mixpanel service account credentials.")
            r.raise_for_status()
        self._project_id = project_id
        self._secret = secret
        self._auth_header = f"Basic {encoded}"
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": self._auth_header}
        async with httpx.AsyncClient(timeout=30) as client:
            project = await self._collect_project(client, headers)
            members = await self._collect_members(client, headers)
        return project + members

    async def _collect_project(self, client, headers) -> list[dict]:
        r = await client.get(f"{MIXPANEL_API}/projects/{self._project_id}", headers=headers)
        r.raise_for_status()
        return [{"_type": "mixpanel_project", **r.json().get("results", r.json())}]

    async def _collect_members(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{MIXPANEL_API}/projects/{self._project_id}/members",
            headers=headers,
        )
        if r.status_code == 404:
            return []
        r.raise_for_status()
        members = r.json().get("results", r.json() if isinstance(r.json(), list) else [])
        return [{"_type": "mixpanel_member", **m} for m in (members if isinstance(members, list) else [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "mixpanel_project":
                result.append(self._norm_project(item))
            elif t == "mixpanel_member":
                result.append(self._norm_member(item))
        return result

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "mixpanel",
            "control": "data_protection",
            "evidence_type": "mixpanel_project",
            "source_id": str(raw.get("id", self._project_id)),
            "timestamp": raw.get("updated_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "api_secret": "REDACTED",
                "timezone": raw.get("timezone"),
                "created": raw.get("created"),
                "api_host": raw.get("api_host"),
            },
        }

    def _norm_member(self, raw: dict) -> dict:
        return {
            "integration": "mixpanel",
            "control": "access_control",
            "evidence_type": "mixpanel_members",
            "source_id": str(raw.get("id", raw.get("user_id", "unknown"))),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id") or raw.get("user_id"),
                "email": raw.get("email"),
                "name": raw.get("name"),
                "role": raw.get("role"),
                "created": raw.get("created"),
            },
        }
