"""
Snyk integration via Snyk v1 REST API.

Credentials:
  api_token — Snyk API token
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_V1_BASE = "https://snyk.io/api/v1"


class SnykIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"token {self._token}",
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_token", "").strip()
        if not token:
            raise IntegrationAuthError("api_token is required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_V1_BASE}/user/me",
                headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Snyk API token")
            r.raise_for_status()

        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            orgs = await self._collect_orgs(client)
            projects = await self._collect_projects(client, orgs)
        return orgs + projects

    async def _collect_orgs(self, client: httpx.AsyncClient) -> list[dict]:
        try:
            r = await client.get(f"{_V1_BASE}/orgs", headers=self._headers())
            r.raise_for_status()
            data = r.json()
            return [
                {
                    "_type": "org",
                    "id": org.get("id"),
                    "name": org.get("name"),
                    "slug": org.get("slug"),
                }
                for org in data.get("orgs", [])
            ]
        except httpx.HTTPStatusError as exc:
            raise exc
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Snyk orgs: {exc}") from exc

    async def _collect_projects(self, client: httpx.AsyncClient, orgs: list[dict]) -> list[dict]:
        projects = []
        for org in orgs:
            org_id = org.get("id")
            if not org_id:
                continue
            try:
                r = await client.get(
                    f"{_V1_BASE}/org/{org_id}/projects",
                    headers=self._headers(),
                )
                r.raise_for_status()
                data = r.json()
                for proj in data.get("projects", []):
                    projects.append(
                        {
                            "_type": "project",
                            "org_id": org_id,
                            "id": proj.get("id"),
                            "name": proj.get("name"),
                            "type": proj.get("type"),
                            "created": proj.get("created"),
                            "lastTestedDate": proj.get("lastTestedDate"),
                            "issueCountsBySeverity": proj.get("issueCountsBySeverity", {}),
                        }
                    )
            except Exception as exc:
                # Skip orgs that fail; don't abort the whole collection
                continue
        return projects

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "org":
                result.append(self._norm_org(item))
            elif t == "project":
                result.append(self._norm_project(item))
        return result

    def _norm_org(self, raw: dict) -> dict:
        return {
            "integration": "snyk",
            "control": "access_control",
            "evidence_type": "snyk_organizations",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "snyk",
            "control": "vulnerability_management",
            "evidence_type": "snyk_projects",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "org_id": raw.get("org_id"),
                "last_tested": raw.get("lastTestedDate"),
                "issue_counts_by_severity": raw.get("issueCountsBySeverity", {}),
            },
        }
