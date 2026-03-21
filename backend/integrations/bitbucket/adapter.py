"""
Bitbucket integration via Bitbucket Cloud API 2.0.

Credentials:
  username     — Bitbucket username (or email)
  app_password — Bitbucket App Password
  workspace    — Workspace slug
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

BB_BASE = "https://api.bitbucket.org/2.0"


class BitbucketIntegration(IntegrationAdapter):

    def __init__(self):
        self._username: str | None = None
        self._app_password: str | None = None
        self._workspace: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._app_password)

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        username = credentials.get("username", "").strip()
        app_password = credentials.get("app_password", "").strip()
        workspace = credentials.get("workspace", "").strip()

        if not username or not app_password or not workspace:
            raise IntegrationAuthError("username, app_password, and workspace are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{BB_BASE}/workspaces/{workspace}",
                auth=(username, app_password),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Bitbucket credentials or workspace access denied.")
            if r.status_code != 200:
                raise RuntimeError(f"Bitbucket connect failed HTTP {r.status_code}")

        self._username = username
        self._app_password = app_password
        self._workspace = workspace
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            repos: list[dict] = []
            try:
                repos = await self._collect_repositories(client)
                results.extend(repos)
            except Exception as exc:
                logger.warning("Bitbucket repositories error: %s", exc)
                results.append({"_type": "error", "_source": "repositories", "_error": str(exc)})

            try:
                members = await self._collect_members(client)
                results.extend(members)
            except Exception as exc:
                logger.warning("Bitbucket members error: %s", exc)
                results.append({"_type": "error", "_source": "members", "_error": str(exc)})

            # Branch protections for up to 5 repos
            repo_items = [r for r in repos if r.get("_type") == "repositories"]
            for repo in repo_items[:5]:
                slug = repo.get("slug", "")
                if not slug:
                    continue
                try:
                    restrictions = await self._collect_branch_restrictions(client, slug)
                    results.extend(restrictions)
                except Exception as exc:
                    logger.warning("Bitbucket branch restrictions error for %s: %s", slug, exc)
                    results.append({
                        "_type": "error",
                        "_source": f"branch_restrictions/{slug}",
                        "_error": str(exc),
                    })

        return results

    async def _collect_repositories(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{BB_BASE}/repositories/{self._workspace}",
            auth=self._auth(),
            params={"pagelen": 50},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bitbucket repositories HTTP {r.status_code}")
        body = r.json()
        items = body.get("values", [])
        return [
            {
                "_type": "repositories",
                "name": repo.get("name"),
                "slug": repo.get("slug"),
                "is_private": repo.get("is_private"),
                "updated_on": repo.get("updated_on"),
                "created_on": repo.get("created_on"),
                "scm": repo.get("scm"),
                "full_name": repo.get("full_name"),
            }
            for repo in items
        ]

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{BB_BASE}/workspaces/{self._workspace}/members",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bitbucket members HTTP {r.status_code}")
        body = r.json()
        items = body.get("values", [])
        return [
            {
                "_type": "members",
                "role": m.get("role"),
                "display_name": m.get("user", {}).get("display_name"),
                "account_id": m.get("user", {}).get("account_id"),
                "nickname": m.get("user", {}).get("nickname"),
            }
            for m in items
        ]

    async def _collect_branch_restrictions(
        self, client: httpx.AsyncClient, slug: str
    ) -> list[dict]:
        r = await client.get(
            f"{BB_BASE}/repositories/{self._workspace}/{slug}/branch-restrictions",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bitbucket branch-restrictions ({slug}) HTTP {r.status_code}")
        body = r.json()
        items = body.get("values", [])
        return [
            {
                "_type": "branch_protections",
                "repo_slug": slug,
                "kind": br.get("kind"),
                "pattern": br.get("pattern"),
                "groups": [g.get("slug") for g in br.get("groups", [])],
                "value": br.get("value"),
            }
            for br in items
        ]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "repositories":
                result.append(self._norm_repo(item))
            elif t == "members":
                result.append(self._norm_member(item))
            elif t == "branch_protections":
                result.append(self._norm_branch_protection(item))
        return result

    def _norm_repo(self, raw: dict) -> dict:
        return {
            "integration": "bitbucket",
            "control": "source_control",
            "evidence_type": "repositories",
            "source_id": raw.get("full_name") or raw.get("slug", ""),
            "timestamp": raw.get("updated_on") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "is_private": raw.get("is_private"),
                "scm": raw.get("scm"),
                "updated_on": raw.get("updated_on"),
            },
        }

    def _norm_member(self, raw: dict) -> dict:
        return {
            "integration": "bitbucket",
            "control": "access_control",
            "evidence_type": "members",
            "source_id": raw.get("account_id") or raw.get("nickname", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "display_name": raw.get("display_name"),
                "role": raw.get("role"),
                "nickname": raw.get("nickname"),
            },
        }

    def _norm_branch_protection(self, raw: dict) -> dict:
        return {
            "integration": "bitbucket",
            "control": "change_management",
            "evidence_type": "branch_protections",
            "source_id": f"{raw.get('repo_slug', '')}:{raw.get('pattern', '')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "repo_slug": raw.get("repo_slug"),
                "kind": raw.get("kind"),
                "pattern": raw.get("pattern"),
                "groups": raw.get("groups", []),
            },
        }
