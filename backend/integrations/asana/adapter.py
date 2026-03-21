"""
Asana integration via Asana REST API v1.0.

Credentials:
  access_token  — Asana personal access token
  workspace_gid — (optional) Asana workspace GID; auto-detected from /users/me if omitted
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://app.asana.com/api/1.0"


class AsanaIntegration(IntegrationAdapter):

    def __init__(self):
        self._access_token: str | None = None
        self._workspace_gid: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        access_token = credentials.get("access_token", "").strip()
        workspace_gid = credentials.get("workspace_gid", "").strip()
        if not access_token:
            raise IntegrationAuthError("access_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/users/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Asana access token.")
            if r.status_code != 200:
                raise RuntimeError(f"Asana connect failed HTTP {r.status_code}")

            if not workspace_gid:
                body = r.json()
                workspaces = body.get("data", {}).get("workspaces", [])
                if workspaces:
                    workspace_gid = workspaces[0].get("gid", "")

        self._access_token = access_token
        self._workspace_gid = workspace_gid
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_teams,
                self._collect_projects,
                self._collect_workspace,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Asana collection error in %s: %s",
                        fetch_fn.__name__,
                        exc,
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/workspaces/{self._workspace_gid}/users",
            headers=self._headers(),
            params={"opt_fields": "gid,name,email,resource_type", "limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Asana users HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "user", **u} for u in body.get("data", [])]

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/organizations/{self._workspace_gid}/teams",
            headers=self._headers(),
            params={"opt_fields": "gid,name,description", "limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Asana teams HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "team", **t} for t in body.get("data", [])]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/workspaces/{self._workspace_gid}/projects",
            headers=self._headers(),
            params={
                "opt_fields": "gid,name,privacy_setting,archived,created_at,owner",
                "limit": 100,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"Asana projects HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "project", **p} for p in body.get("data", [])]

    async def _collect_workspace(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/workspaces/{self._workspace_gid}",
            headers=self._headers(),
            params={"opt_fields": "gid,name,is_organization,email_domains"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Asana workspace HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", {})
        return [{"_type": "workspace", **data}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item, now))
            elif t == "team":
                result.append(self._norm_team(item, now))
            elif t == "project":
                result.append(self._norm_project(item, now))
            elif t == "workspace":
                result.append(self._norm_workspace(item, now))
        return result

    def _norm_user(self, raw: dict, now: str) -> dict:
        return {
            "integration": "asana",
            "control": "access_control",
            "evidence_type": "asana_users",
            "source_id": raw.get("gid", ""),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "resource_type": raw.get("resource_type"),
            },
        }

    def _norm_team(self, raw: dict, now: str) -> dict:
        return {
            "integration": "asana",
            "control": "access_control",
            "evidence_type": "asana_teams",
            "source_id": raw.get("gid", ""),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
            },
        }

    def _norm_project(self, raw: dict, now: str) -> dict:
        owner = raw.get("owner")
        return {
            "integration": "asana",
            "control": "change_management",
            "evidence_type": "asana_projects",
            "source_id": raw.get("gid", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "privacy_setting": raw.get("privacy_setting"),
                "archived": raw.get("archived"),
                "owner": owner.get("name") if isinstance(owner, dict) else None,
            },
        }

    def _norm_workspace(self, raw: dict, now: str) -> dict:
        return {
            "integration": "asana",
            "control": "change_management",
            "evidence_type": "asana_workspace",
            "source_id": raw.get("gid", ""),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "is_organization": raw.get("is_organization"),
                "email_domains": raw.get("email_domains"),
            },
        }
