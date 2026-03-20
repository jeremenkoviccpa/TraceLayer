"""
GitLab integration via REST API v4.

Credentials:
  token — GitLab Personal Access Token (glpat-xxxx)

Evidence collected:
  - Projects (membership=true)          → change_management / gitlab_repos
  - Users (active, admin token only)    → access_control   / gitlab_users
  - Protected branches (per project)    → change_management / gitlab_protected_branches
  - Groups                              → access_control   / gitlab_groups
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

GITLAB_API = "https://gitlab.com/api/v4"


class GitLabIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    def _headers(self) -> dict:
        return {"PRIVATE-TOKEN": self._token}

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        token = (credentials.get("token") or credentials.get("api_token") or "").strip()
        if not token:
            raise IntegrationAuthError("GitLab Personal Access Token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{GITLAB_API}/user",
                headers={"PRIVATE-TOKEN": token},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid GitLab token — check the token value and its scopes (read_api minimum)."
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
                logger.error("GitLab: failed to collect projects: %s", exc)
                projects = []

            try:
                users = await self._collect_users(client)
                results.extend(users)
            except Exception as exc:
                logger.warning("GitLab: failed to collect users (admin token required): %s", exc)

            try:
                protected = await self._collect_protected_branches(client, projects)
                results.extend(protected)
            except Exception as exc:
                logger.error("GitLab: failed to collect protected branches: %s", exc)

            try:
                groups = await self._collect_groups(client)
                results.extend(groups)
            except Exception as exc:
                logger.error("GitLab: failed to collect groups: %s", exc)

        return results

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate GET /projects?membership=true."""
        projects: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{GITLAB_API}/projects",
                headers=self._headers(),
                params={"membership": "true", "per_page": 100, "page": page},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            projects.extend([{"_type": "project", **p} for p in batch])
            # GitLab sets X-Next-Page to empty string when there are no more pages
            next_page = r.headers.get("X-Next-Page", "")
            if not next_page:
                break
            page += 1
        return projects

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate GET /users?active=true — requires admin token; skip on 403."""
        users: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{GITLAB_API}/users",
                headers=self._headers(),
                params={"active": "true", "per_page": 100, "page": page},
            )
            if r.status_code == 403:
                logger.info("GitLab: /users endpoint requires admin scope — skipping.")
                return []
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            users.extend([{"_type": "user", **u} for u in batch])
            next_page = r.headers.get("X-Next-Page", "")
            if not next_page:
                break
            page += 1
        return users

    async def _collect_protected_branches(
        self, client: httpx.AsyncClient, projects: list[dict]
    ) -> list[dict]:
        """For each project collect GET /projects/{id}/protected_branches."""
        protected: list[dict] = []
        for project in projects:
            project_id = project.get("id")
            project_name = project.get("name", str(project_id))
            if not project_id:
                continue
            try:
                r = await client.get(
                    f"{GITLAB_API}/projects/{project_id}/protected_branches",
                    headers=self._headers(),
                    params={"per_page": 100},
                )
                if r.status_code == 404:
                    # Private project or no access — skip silently
                    continue
                r.raise_for_status()
                for branch in r.json():
                    protected.append(
                        {
                            "_type": "protected_branch",
                            "_project_id": project_id,
                            "_project_name": project_name,
                            **branch,
                        }
                    )
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "GitLab: could not fetch protected branches for project %s: %s",
                    project_name,
                    exc,
                )
        return protected

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate GET /groups."""
        groups: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{GITLAB_API}/groups",
                headers=self._headers(),
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            groups.extend([{"_type": "group", **g} for g in batch])
            next_page = r.headers.get("X-Next-Page", "")
            if not next_page:
                break
            page += 1
        return groups

    # ── Normalize ─────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "project":
                result.append(self._norm_project(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "protected_branch":
                result.append(self._norm_protected_branch(item))
            elif t == "group":
                result.append(self._norm_group(item))
        return result

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "gitlab",
            "control": "change_management",
            "evidence_type": "gitlab_repos",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "full_path": raw.get("path_with_namespace"),
                "visibility": raw.get("visibility"),
                "default_branch": raw.get("default_branch"),
                "namespace": raw.get("namespace", {}).get("full_path"),
                "archived": raw.get("archived", False),
                "last_activity_at": raw.get("last_activity_at"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "gitlab",
            "control": "access_control",
            "evidence_type": "gitlab_users",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "username": raw.get("username"),
                "name": raw.get("name"),
                "email": raw.get("email"),
                "state": raw.get("state"),
                "is_admin": raw.get("is_admin", False),
                "two_factor_enabled": raw.get("two_factor_enabled", False),
                "last_sign_in_at": raw.get("last_sign_in_at"),
            },
        }

    def _norm_protected_branch(self, raw: dict) -> dict:
        push_rules = raw.get("push_access_levels", [])
        merge_rules = raw.get("merge_access_levels", [])

        def _min_access(rules: list[dict]) -> str | None:
            levels = [r.get("access_level_description") for r in rules if r.get("access_level_description")]
            return levels[0] if levels else None

        return {
            "integration": "gitlab",
            "control": "change_management",
            "evidence_type": "gitlab_protected_branches",
            "source_id": f"{raw['_project_id']}:{raw['name']}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "project_id": raw.get("_project_id"),
                "project_name": raw.get("_project_name"),
                "branch_name": raw.get("name"),
                "push_access_level": _min_access(push_rules),
                "merge_access_level": _min_access(merge_rules),
                "allow_force_push": raw.get("allow_force_push", False),
                "code_owner_approval_required": raw.get("code_owner_approval_required", False),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "gitlab",
            "control": "access_control",
            "evidence_type": "gitlab_groups",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "full_path": raw.get("full_path"),
                "visibility": raw.get("visibility"),
                "member_count": raw.get("statistics", {}).get("member_count"),
            },
        }
