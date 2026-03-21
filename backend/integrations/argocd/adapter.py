"""
Argo CD integration via Argo CD REST API v1.

Credentials:
  server_url  — Argo CD server URL (e.g. "https://argocd.mycompany.com")
  token       — Argo CD API token (Bearer)
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ArgoCDIntegration(IntegrationAdapter):

    def __init__(self):
        self._server_url: str | None = None
        self._token: str | None = None

    def _base_url(self) -> str:
        return f"{self._server_url}/api/v1"

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        server_url = credentials.get("server_url", "").strip().rstrip("/")
        token = credentials.get("token", "").strip()

        if not server_url or not token:
            raise IntegrationAuthError("server_url and token are required.")

        url = f"{server_url}/api/v1/applications?limit=1"
        headers = {"Authorization": f"Bearer {token}"}

        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            r = await client.get(url, headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Argo CD token.")
            if r.status_code != 200:
                raise RuntimeError(f"Argo CD connect failed HTTP {r.status_code}")

        self._server_url = server_url
        self._token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            for fetch_fn in (
                self._collect_applications,
                self._collect_projects,
                self._collect_repositories,
                self._collect_accounts,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Argo CD collection error in %s: %s",
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

    async def _collect_applications(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/applications",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Argo CD applications HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "application", **a} for a in (body.get("items") or [])]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/projects",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Argo CD projects HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "project", **p} for p in (body.get("items") or [])]

    async def _collect_repositories(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/repositories",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Argo CD repositories HTTP {r.status_code}")
        body = r.json()
        repos = body.get("items") or body.get("repositories") or []
        return [{"_type": "repository", **repo} for repo in repos]

    async def _collect_accounts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/accounts",
            headers=self._headers(),
        )
        if r.status_code in (403, 404):
            logger.warning(
                "Argo CD accounts endpoint returned %s — skipping",
                r.status_code,
            )
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Argo CD accounts HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "account", **a} for a in (body.get("items") or [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "application":
                result.append(self._norm_application(item))
            elif t == "project":
                result.append(self._norm_project(item))
            elif t == "repository":
                result.append(self._norm_repository(item))
            elif t == "account":
                result.append(self._norm_account(item))
        return result

    def _norm_application(self, raw: dict) -> dict:
        meta = raw.get("metadata", {})
        spec = raw.get("spec", {})
        status = raw.get("status", {})
        return {
            "integration": "argocd",
            "control": "change_management",
            "evidence_type": "argocd_applications",
            "source_id": meta.get("name", ""),
            "timestamp": meta.get("creationTimestamp") or _now(),
            "data": {
                "name": meta.get("name"),
                "namespace": meta.get("namespace"),
                "source_repo": spec.get("source", {}).get("repoURL"),
                "source_path": spec.get("source", {}).get("path"),
                "destination_namespace": spec.get("destination", {}).get("namespace"),
                "health_status": status.get("health", {}).get("status"),
                "sync_status": status.get("sync", {}).get("status"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        meta = raw.get("metadata", {})
        spec = raw.get("spec", {})
        return {
            "integration": "argocd",
            "control": "access_control",
            "evidence_type": "argocd_projects",
            "source_id": meta.get("name", ""),
            "timestamp": meta.get("creationTimestamp") or _now(),
            "data": {
                "name": meta.get("name"),
                "description": spec.get("description"),
                "source_repos": spec.get("sourceRepos", []),
                "destinations": spec.get("destinations", []),
            },
        }

    def _norm_repository(self, raw: dict) -> dict:
        return {
            "integration": "argocd",
            "control": "change_management",
            "evidence_type": "argocd_repositories",
            "source_id": raw.get("repo", ""),
            "timestamp": _now(),
            "data": {
                "repo": raw.get("repo"),
                "type": raw.get("type"),
                "connectionState": raw.get("connectionState", {}).get("status"),
            },
        }

    def _norm_account(self, raw: dict) -> dict:
        return {
            "integration": "argocd",
            "control": "access_control",
            "evidence_type": "argocd_accounts",
            "source_id": raw.get("name", ""),
            "timestamp": _now(),
            "data": {
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "capabilities": raw.get("capabilities", []),
            },
        }
