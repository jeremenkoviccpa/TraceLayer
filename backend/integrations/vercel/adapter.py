"""
Vercel integration via REST API.

Credentials:
  api_token — Vercel API token

Evidence collected:
  - Projects       → change_management / vercel_projects
  - Deployments    → change_management / vercel_deployments
  - Teams          → access_control   / vercel_team
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

VERCEL_API = "https://api.vercel.com"


class VercelIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        token = (
            credentials.get("api_token") or credentials.get("token") or ""
        ).strip()
        if not token:
            raise IntegrationAuthError("Vercel API Token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{VERCEL_API}/v2/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError(
                    "Invalid Vercel API token — verify the token value and its scopes."
                )
            r.raise_for_status()

        self._token = token
        return True

    # ── Collection ────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                projects = await self._collect_projects(client)
                results.extend(projects)
            except Exception as exc:
                logger.error("Vercel: failed to collect projects: %s", exc)

            try:
                deployments = await self._collect_deployments(client)
                results.extend(deployments)
            except Exception as exc:
                logger.error("Vercel: failed to collect deployments: %s", exc)

            try:
                teams = await self._collect_teams(client)
                results.extend(teams)
            except Exception as exc:
                logger.error("Vercel: failed to collect teams: %s", exc)

            try:
                user = await self._collect_user(client)
                results.extend(user)
            except Exception as exc:
                logger.error("Vercel: failed to collect user: %s", exc)

        return results

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate GET /v9/projects using cursor-based pagination."""
        projects: list[dict] = []
        params: dict = {"limit": 100}
        while True:
            r = await client.get(
                f"{VERCEL_API}/v9/projects",
                headers=self._headers(),
                params=params,
            )
            r.raise_for_status()
            body = r.json()
            batch = body.get("projects", [])
            for p in batch:
                projects.append({"_type": "project", **p})
            # Vercel cursor pagination
            pagination = body.get("pagination", {})
            next_cursor = pagination.get("next")
            if not next_cursor or not batch:
                break
            params = {"limit": 100, "until": next_cursor}
        return projects

    async def _collect_deployments(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate GET /v6/deployments."""
        deployments: list[dict] = []
        params: dict = {"limit": 100}
        while True:
            r = await client.get(
                f"{VERCEL_API}/v6/deployments",
                headers=self._headers(),
                params=params,
            )
            r.raise_for_status()
            body = r.json()
            batch = body.get("deployments", [])
            for d in batch:
                deployments.append({"_type": "deployment", **d})
            pagination = body.get("pagination", {})
            next_cursor = pagination.get("next")
            if not next_cursor or not batch:
                break
            params = {"limit": 100, "until": next_cursor}
        return deployments

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        """GET /v2/teams — returns all teams the token has access to."""
        r = await client.get(f"{VERCEL_API}/v2/teams", headers=self._headers())
        r.raise_for_status()
        body = r.json()
        teams = body.get("teams", [])
        return [{"_type": "team", **t} for t in teams]

    async def _collect_user(self, client: httpx.AsyncClient) -> list[dict]:
        """GET /v2/user — the authenticated user's own profile."""
        r = await client.get(f"{VERCEL_API}/v2/user", headers=self._headers())
        r.raise_for_status()
        user = r.json().get("user", r.json())
        return [{"_type": "user", **user}]

    # ── Normalize ─────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "project":
                result.append(self._norm_project(item))
            elif t == "deployment":
                result.append(self._norm_deployment(item))
            elif t == "team":
                result.append(self._norm_team(item))
            # "user" records are collected but not emitted as separate evidence —
            # user identity is implicit in the connected credentials.
        return result

    def _norm_project(self, raw: dict) -> dict:
        # Count environment variables if present
        env_vars = raw.get("env", [])
        env_count = len(env_vars) if isinstance(env_vars, list) else 0

        # Detect git connection
        git_repo = raw.get("link", {})
        git_connected = bool(git_repo.get("repoId") or git_repo.get("repo"))

        return {
            "integration": "vercel",
            "control": "change_management",
            "evidence_type": "vercel_projects",
            "source_id": raw["id"],
            "timestamp": _ms_to_iso(raw.get("createdAt")),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "framework": raw.get("framework"),
                "env_vars_count": env_count,
                "git_connected": git_connected,
                "git_provider": git_repo.get("type"),
                "git_repo": git_repo.get("repo"),
                "node_version": raw.get("nodeVersion"),
                "updated_at": _ms_to_iso(raw.get("updatedAt")),
            },
        }

    def _norm_deployment(self, raw: dict) -> dict:
        meta = raw.get("meta", {}) or {}
        return {
            "integration": "vercel",
            "control": "change_management",
            "evidence_type": "vercel_deployments",
            "source_id": raw["uid"],
            "timestamp": _ms_to_iso(raw.get("createdAt")),
            "data": {
                "id": raw["uid"],
                "url": raw.get("url"),
                "name": raw.get("name"),
                "state": raw.get("state"),
                "target": raw.get("target"),  # "production" | "preview" | None
                "created_at": _ms_to_iso(raw.get("createdAt")),
                "ready_at": _ms_to_iso(raw.get("ready")),
                "commit_sha": meta.get("githubCommitSha") or meta.get("gitlabCommitSha"),
                "commit_message": meta.get("githubCommitMessage") or meta.get("gitlabCommitMessage"),
                "commit_author": meta.get("githubCommitAuthorName") or meta.get("gitlabCommitAuthorName"),
                "branch": meta.get("githubCommitRef") or meta.get("gitlabCommitRef"),
            },
        }

    def _norm_team(self, raw: dict) -> dict:
        membership = raw.get("membership", {}) or {}
        return {
            "integration": "vercel",
            "control": "access_control",
            "evidence_type": "vercel_team",
            "source_id": raw["id"],
            "timestamp": _ms_to_iso(raw.get("createdAt")),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "member_count": raw.get("memberCount"),
                "plan": raw.get("plan"),
                "current_user_role": membership.get("role"),
                "created_at": _ms_to_iso(raw.get("createdAt")),
            },
        }


def _ms_to_iso(ms: int | None) -> str:
    """Convert a Unix millisecond timestamp to an ISO 8601 string."""
    if ms is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).isoformat()
    except (ValueError, TypeError, OSError):
        return datetime.now(timezone.utc).isoformat()
