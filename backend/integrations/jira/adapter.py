"""
Jira (Atlassian Cloud) integration via REST API v3.

Credentials:
  domain    — e.g. "mycompany.atlassian.net"
  email     — admin email associated with the API token
  api_token — Atlassian API token
"""
import base64
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class JiraIntegration(IntegrationAdapter):

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
            domain = f"https://{domain}"

        auth = base64.b64encode(f"{email}:{token}".encode()).decode()
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{domain}/rest/api/3/myself",
                headers={"Authorization": f"Basic {auth}", "Accept": "application/json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Jira credentials — check email and API token")
            r.raise_for_status()

        self._base = domain
        self._auth = auth
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            projects = await self._collect_projects(client)
            users = await self._collect_users(client)
        return projects + users

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        projects, start = [], 0
        while True:
            r = await client.get(
                f"{self._base}/rest/api/3/project/search",
                headers=self._headers(),
                params={"startAt": start, "maxResults": 50, "expand": "lead"},
            )
            r.raise_for_status()
            data = r.json()
            values = data.get("values", [])
            for p in values:
                projects.append({"_type": "project", **p})
            if data.get("isLast", True) or not values:
                break
            start += len(values)
        return projects

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users, start = [], 0
        while True:
            r = await client.get(
                f"{self._base}/rest/api/3/users/search",
                headers=self._headers(),
                params={"startAt": start, "maxResults": 50},
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            for u in data:
                users.append({"_type": "user", **u})
            start += len(data)
            if len(data) < 50:
                break
        return users

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "project":
                result.append(self._norm_project(item))
            elif t == "user":
                result.append(self._norm_user(item))
        return result

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "jira",
            "control": "change_management",
            "evidence_type": "jira_projects",
            "source_id": raw["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "key": raw.get("key"),
                "name": raw.get("name"),
                "type": raw.get("projectTypeKey"),
                "style": raw.get("style"),
                "lead_email": raw.get("lead", {}).get("emailAddress"),
                "private": not raw.get("isPrivate", False),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "jira",
            "control": "access_control",
            "evidence_type": "jira_users",
            "source_id": raw.get("accountId", raw.get("emailAddress", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": raw.get("emailAddress"),
                "display_name": raw.get("displayName"),
                "active": raw.get("active", True),
                "account_type": raw.get("accountType"),
            },
        }
