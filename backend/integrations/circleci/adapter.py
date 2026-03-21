"""
CircleCI integration via CircleCI API v2.

Credentials:
  api_token — CircleCI personal API token
  org_slug  — (optional) Organization slug, e.g. "github/myorg"
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

CCI_BASE = "https://circleci.com/api/v2"


class CircleCIIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None
        self._org_slug: str | None = None

    def _headers(self) -> dict:
        return {
            "Circle-Token": self._api_token,
            "Accept": "application/json",
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        headers = {"Circle-Token": api_token, "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{CCI_BASE}/me", headers=headers)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid CircleCI API token.")
            if r.status_code != 200:
                raise RuntimeError(f"CircleCI connect failed HTTP {r.status_code}")

        self._api_token = api_token
        self._org_slug = credentials.get("org_slug", "").strip() or None
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # /me — account info
            try:
                me = await self._collect_me(client)
                results.extend(me)
            except Exception as exc:
                logger.warning("CircleCI /me error: %s", exc)
                results.append({"_type": "error", "_source": "me", "_error": str(exc)})

            # /project/{org_slug} — project settings (only if org_slug provided)
            if self._org_slug:
                try:
                    projects = await self._collect_projects(client)
                    results.extend(projects)
                except Exception as exc:
                    logger.warning("CircleCI projects error: %s", exc)
                    results.append({"_type": "error", "_source": "projects", "_error": str(exc)})

            # /me/collaborations — organizations
            try:
                orgs = await self._collect_collaborations(client)
                results.extend(orgs)
            except Exception as exc:
                logger.warning("CircleCI collaborations error: %s", exc)
                results.append({"_type": "error", "_source": "collaborations", "_error": str(exc)})

            # /pipeline — recent pipelines
            try:
                pipelines = await self._collect_pipelines(client)
                results.extend(pipelines)
            except Exception as exc:
                logger.warning("CircleCI pipelines error: %s", exc)
                results.append({"_type": "error", "_source": "pipelines", "_error": str(exc)})

        return results

    async def _collect_me(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{CCI_BASE}/me", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"CircleCI /me HTTP {r.status_code}")
        data = r.json()
        return [{"_type": "account_info", **data}]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{CCI_BASE}/project/{self._org_slug}",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"CircleCI project settings HTTP {r.status_code}")
        data = r.json()
        return [{"_type": "project_settings", **data}]

    async def _collect_collaborations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{CCI_BASE}/me/collaborations", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"CircleCI collaborations HTTP {r.status_code}")
        items = r.json()
        if not isinstance(items, list):
            items = items.get("items", [])
        return [{"_type": "organizations", **org} for org in items]

    async def _collect_pipelines(self, client: httpx.AsyncClient) -> list[dict]:
        params: dict = {}
        if self._org_slug:
            params["org-slug"] = self._org_slug
        r = await client.get(
            f"{CCI_BASE}/pipeline",
            headers=self._headers(),
            params=params,
        )
        if r.status_code != 200:
            raise RuntimeError(f"CircleCI pipelines HTTP {r.status_code}")
        body = r.json()
        items = body.get("items", [])
        return [{"_type": "pipelines", **p} for p in items]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "account_info":
                result.append(self._norm_account(item))
            elif t == "project_settings":
                result.append(self._norm_project(item))
            elif t == "organizations":
                result.append(self._norm_org(item))
            elif t == "pipelines":
                result.append(self._norm_pipeline(item))
        return result

    def _norm_account(self, raw: dict) -> dict:
        return {
            "integration": "circleci",
            "control": "access_control",
            "evidence_type": "account_info",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "login": raw.get("login"),
                "name": raw.get("name"),
                "id": raw.get("id"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "circleci",
            "control": "source_control",
            "evidence_type": "project_settings",
            "source_id": raw.get("slug") or raw.get("name", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "organization_name": raw.get("organization_name"),
                "vcs_url": raw.get("vcs_url"),
            },
        }

    def _norm_org(self, raw: dict) -> dict:
        return {
            "integration": "circleci",
            "control": "access_control",
            "evidence_type": "organizations",
            "source_id": raw.get("id") or raw.get("slug", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "vcs_type": raw.get("vcs_type"),
                "avatar_url": raw.get("avatar_url"),
            },
        }

    def _norm_pipeline(self, raw: dict) -> dict:
        return {
            "integration": "circleci",
            "control": "change_management",
            "evidence_type": "pipelines",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id"),
                "number": raw.get("number"),
                "state": raw.get("state"),
                "created_at": raw.get("created_at"),
                "updated_at": raw.get("updated_at"),
                "vcs_branch": raw.get("vcs", {}).get("branch") if isinstance(raw.get("vcs"), dict) else None,
                "trigger_type": raw.get("trigger", {}).get("type") if isinstance(raw.get("trigger"), dict) else None,
            },
        }
