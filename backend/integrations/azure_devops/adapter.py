"""
Azure DevOps integration via Azure DevOps REST API v7.0.

Credentials:
  org  — Azure DevOps organization name
  pat  — Personal Access Token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AzureDevOpsIntegration(IntegrationAdapter):

    def __init__(self):
        self._org: str | None = None
        self._pat: str | None = None

    def _base_url(self) -> str:
        return f"https://dev.azure.com/{self._org}"

    def _vssps_url(self) -> str:
        return f"https://vssps.dev.azure.com/{self._org}"

    def _auth(self) -> httpx.BasicAuth:
        return httpx.BasicAuth("", self._pat)

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        org = credentials.get("org", "").strip()
        pat = credentials.get("pat", "").strip()

        if not org or not pat:
            raise IntegrationAuthError("org and pat are required.")

        url = f"https://dev.azure.com/{org}/_apis/projects?api-version=7.0&$top=1"
        auth = httpx.BasicAuth("", pat)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, auth=auth)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Azure DevOps credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Azure DevOps connect failed HTTP {r.status_code}")

        self._org = org
        self._pat = pat
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_projects,
                self._collect_users,
                self._collect_repos,
                self._collect_pipelines,
                self._collect_policies,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Azure DevOps collection error in %s: %s",
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

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        url = f"{self._base_url()}/_apis/projects?api-version=7.0&$top=100"
        r = await client.get(url, auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Azure DevOps projects HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "project", **p} for p in body.get("value", [])]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._vssps_url()}/_apis/graph/users"
            "?api-version=7.0-preview.1"
        )
        try:
            r = await client.get(url, auth=self._auth())
            if r.status_code in (403, 404):
                logger.warning(
                    "Azure DevOps users endpoint returned %s — skipping",
                    r.status_code,
                )
                return []
            if r.status_code != 200:
                raise RuntimeError(f"Azure DevOps users HTTP {r.status_code}")
            body = r.json()
            return [{"_type": "user", **u} for u in body.get("value", [])]
        except httpx.HTTPError as exc:
            logger.warning("Azure DevOps users HTTP error: %s", exc)
            return []

    async def _collect_repos(self, client: httpx.AsyncClient) -> list[dict]:
        # Fetch up to first 5 projects to enumerate their repos
        projects_url = (
            f"{self._base_url()}/_apis/projects?api-version=7.0&$top=5"
        )
        r = await client.get(projects_url, auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Azure DevOps projects (for repos) HTTP {r.status_code}")
        projects = r.json().get("value", [])

        repos: list[dict] = []
        for project in projects:
            project_id = project.get("id", "")
            repo_url = (
                f"{self._base_url()}/{project_id}/_apis/git/repositories"
                "?api-version=7.0"
            )
            rr = await client.get(repo_url, auth=self._auth())
            if rr.status_code != 200:
                logger.warning(
                    "Azure DevOps repos for project %s HTTP %s — skipping",
                    project_id,
                    rr.status_code,
                )
                continue
            for repo in rr.json().get("value", []):
                repos.append({"_type": "repo", **repo})

        return repos

    async def _collect_pipelines(self, client: httpx.AsyncClient) -> list[dict]:
        # Pipelines are scoped to a project — use the first project
        projects_url = (
            f"{self._base_url()}/_apis/projects?api-version=7.0&$top=1"
        )
        r = await client.get(projects_url, auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(
                f"Azure DevOps projects (for pipelines) HTTP {r.status_code}"
            )
        projects = r.json().get("value", [])
        if not projects:
            return []

        first_project_name = projects[0].get("name", "")
        url = (
            f"{self._base_url()}/{first_project_name}/_apis/pipelines"
            "?api-version=7.0"
        )
        rp = await client.get(url, auth=self._auth())
        if rp.status_code != 200:
            raise RuntimeError(f"Azure DevOps pipelines HTTP {rp.status_code}")
        body = rp.json()
        return [{"_type": "pipeline", **p} for p in body.get("value", [])]

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        # Policies are scoped to a project — use the first project
        projects_url = (
            f"{self._base_url()}/_apis/projects?api-version=7.0&$top=1"
        )
        r = await client.get(projects_url, auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(
                f"Azure DevOps projects (for policies) HTTP {r.status_code}"
            )
        projects = r.json().get("value", [])
        if not projects:
            return []

        first_project_name = projects[0].get("name", "")
        url = (
            f"{self._base_url()}/{first_project_name}"
            "/_apis/policy/configurations?api-version=7.0"
        )
        rp = await client.get(url, auth=self._auth())
        if rp.status_code != 200:
            raise RuntimeError(f"Azure DevOps policies HTTP {rp.status_code}")
        body = rp.json()
        return [{"_type": "policy", **p} for p in body.get("value", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "project":
                result.append(self._norm_project(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "repo":
                result.append(self._norm_repo(item))
            elif t == "pipeline":
                result.append(self._norm_pipeline(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
        return result

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "azure_devops",
            "control": "change_management",
            "evidence_type": "azure_devops_projects",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("lastUpdateTime") or _now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "state": raw.get("state"),
                "visibility": raw.get("visibility"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "azure_devops",
            "control": "access_control",
            "evidence_type": "azure_devops_users",
            "source_id": raw.get("descriptor", ""),
            "timestamp": _now(),
            "data": {
                "displayName": raw.get("displayName"),
                "mailAddress": raw.get("mailAddress"),
                "principalName": raw.get("principalName"),
                "subjectKind": raw.get("subjectKind"),
            },
        }

    def _norm_repo(self, raw: dict) -> dict:
        return {
            "integration": "azure_devops",
            "control": "change_management",
            "evidence_type": "azure_devops_repos",
            "source_id": raw.get("id", ""),
            "timestamp": _now(),
            "data": {
                "name": raw.get("name"),
                "defaultBranch": raw.get("defaultBranch"),
                "size": raw.get("size"),
                "project": raw.get("project", {}).get("name"),
            },
        }

    def _norm_pipeline(self, raw: dict) -> dict:
        return {
            "integration": "azure_devops",
            "control": "change_management",
            "evidence_type": "azure_devops_pipelines",
            "source_id": str(raw.get("id", "")),
            "timestamp": _now(),
            "data": {
                "name": raw.get("name"),
                "folder": raw.get("folder"),
                "revision": raw.get("revision"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "azure_devops",
            "control": "change_management",
            "evidence_type": "azure_devops_policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdDate") or _now(),
            "data": {
                "type": raw.get("type", {}).get("displayName"),
                "isEnabled": raw.get("isEnabled"),
                "isBlocking": raw.get("isBlocking"),
                "settings": raw.get("settings", {}),
            },
        }
