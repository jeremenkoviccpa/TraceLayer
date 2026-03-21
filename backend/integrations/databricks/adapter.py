from __future__ import annotations

"""
Databricks integration via Databricks REST API 2.0.

Credentials:
  host  — Databricks workspace URL (e.g. "adb-1234567890.1.azuredatabricks.net")
  token — Personal access token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_API_BASE = "/api/2.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class DatabricksIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._host: str | None = None
        self._token: str | None = None

    def _base(self) -> str:
        return f"https://{self._host}{_API_BASE}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        host = credentials.get("host", "").strip().rstrip("/")
        token = credentials.get("token", "").strip()

        if not host or not token:
            raise IntegrationAuthError("host and token are required.")

        # Strip scheme if provided so we can normalise to bare hostname
        host = host.removeprefix("https://").removeprefix("http://")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://{host}/api/2.0/clusters/list",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Databricks credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Databricks connect failed HTTP {r.status_code}")

        self._host = host
        self._token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_clusters,
                self._collect_users,
                self._collect_groups,
                self._collect_jobs,
                self._collect_secrets_scopes,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Databricks collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_clusters(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/clusters/list",
            headers=self._headers(),
        )
        r.raise_for_status()
        clusters = r.json().get("clusters", [])
        return [{"_type": "cluster", **c} for c in clusters]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/preview/scim/v2/Users",
            headers=self._headers(),
        )
        r.raise_for_status()
        users = r.json().get("Resources", [])
        return [{"_type": "user", **u} for u in users]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/preview/scim/v2/Groups",
            headers=self._headers(),
        )
        r.raise_for_status()
        groups = r.json().get("Resources", [])
        return [{"_type": "group", **g} for g in groups]

    async def _collect_jobs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/jobs/list",
            headers=self._headers(),
        )
        r.raise_for_status()
        jobs = r.json().get("jobs", [])
        return [{"_type": "job", **j} for j in jobs]

    async def _collect_secrets_scopes(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/secrets/scopes/list",
            headers=self._headers(),
        )
        if r.status_code == 403:
            # Token may lack secrets permission; return empty rather than error
            return []
        r.raise_for_status()
        scopes = r.json().get("scopes", [])
        return [{"_type": "secrets_scope", **s} for s in scopes]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "cluster":
                result.append(self._norm_cluster(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "job":
                result.append(self._norm_job(item))
            elif t == "secrets_scope":
                result.append(self._norm_secrets_scope(item))
            # skip error sentinels silently
        return result

    def _norm_cluster(self, raw: dict) -> dict:
        return {
            "integration": "databricks",
            "control": "infrastructure_security",
            "evidence_type": "databricks_clusters",
            "source_id": str(raw.get("cluster_id", "")),
            "timestamp": raw.get("start_time") or _now(),
            "data": {
                "cluster_id": raw.get("cluster_id"),
                "cluster_name": raw.get("cluster_name"),
                "state": raw.get("state"),
                "spark_version": raw.get("spark_version"),
                "creator_user_name": raw.get("creator_user_name"),
                "autotermination_minutes": raw.get("autotermination_minutes"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "databricks",
            "control": "access_control",
            "evidence_type": "databricks_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": _now(),
            "data": {
                "id": raw.get("id"),
                "userName": raw.get("userName"),
                "displayName": raw.get("displayName"),
                "active": raw.get("active"),
                "groups": [g.get("display") for g in raw.get("groups", [])],
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "databricks",
            "control": "access_control",
            "evidence_type": "databricks_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": _now(),
            "data": {
                "id": raw.get("id"),
                "displayName": raw.get("displayName"),
                "members_count": len(raw.get("members", [])),
            },
        }

    def _norm_job(self, raw: dict) -> dict:
        return {
            "integration": "databricks",
            "control": "infrastructure_security",
            "evidence_type": "databricks_jobs",
            "source_id": str(raw.get("job_id", "")),
            "timestamp": raw.get("created_time") or _now(),
            "data": {
                "job_id": raw.get("job_id"),
                "settings_name": raw.get("settings", {}).get("name"),
                "creator_user_name": raw.get("creator_user_name"),
            },
        }

    def _norm_secrets_scope(self, raw: dict) -> dict:
        return {
            "integration": "databricks",
            "control": "data_security",
            "evidence_type": "databricks_secrets_scopes",
            "source_id": str(raw.get("name", "")),
            "timestamp": _now(),
            "data": {
                "name": raw.get("name"),
                "backend_type": raw.get("backend_type"),
            },
        }
