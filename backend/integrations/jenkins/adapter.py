"""
Jenkins integration via Jenkins REST API.

Credentials:
  url       — Jenkins base URL (e.g. "https://jenkins.mycompany.com")
  username  — Jenkins username
  api_token — Jenkins API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class JenkinsIntegration(IntegrationAdapter):

    def __init__(self):
        self._url: str | None = None
        self._username: str | None = None
        self._api_token: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._api_token)

    def _base(self) -> str:
        return self._url

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        url = credentials.get("url", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        api_token = credentials.get("api_token", "").strip()

        if not url or not username or not api_token:
            raise IntegrationAuthError("url, username, and api_token are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{url}/api/json",
                auth=(username, api_token),
                params={"tree": "nodeName,description"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Jenkins credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Jenkins connect failed HTTP {r.status_code}")

        self._url = url
        self._username = username
        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_jobs,
                self._collect_plugins,
                self._collect_system_info,
                self._collect_users,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Jenkins collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_jobs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/json",
            auth=self._auth(),
            params={
                "tree": (
                    "jobs[name,url,color,buildable,"
                    "lastBuild[number,result,timestamp,duration]]"
                )
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"Jenkins jobs HTTP {r.status_code}")
        jobs = r.json().get("jobs", [])
        return [{"_type": "job", **j} for j in jobs]

    async def _collect_plugins(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/pluginManager/api/json",
            auth=self._auth(),
            params={
                "tree": (
                    "plugins[shortName,longName,version,"
                    "active,enabled,hasUpdate]"
                )
            },
        )
        if r.status_code in (404, 403):
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Jenkins plugins HTTP {r.status_code}")
        plugins = r.json().get("plugins", [])
        return [{"_type": "plugin", **p} for p in plugins]

    async def _collect_system_info(self, client: httpx.AsyncClient) -> list[dict]:
        # Try /systemInfo/api/json first; fall back to /computer/api/json
        r = await client.get(
            f"{self._base()}/systemInfo/api/json",
            auth=self._auth(),
        )
        if r.status_code == 404:
            r = await client.get(
                f"{self._base()}/computer/api/json",
                auth=self._auth(),
                params={
                    "tree": "computer[displayName,numExecutors,offline]"
                },
            )
        if r.status_code in (404, 403):
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Jenkins system info HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "system_info", **body}]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/asynchPeople/api/json",
            auth=self._auth(),
            params={"tree": "users[user[id,fullName]]"},
        )
        if r.status_code in (404, 403):
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Jenkins users HTTP {r.status_code}")
        users = r.json().get("users", [])
        return [{"_type": "user", **u} for u in users]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "job":
                result.append(self._norm_job(item))
            elif t == "plugin":
                result.append(self._norm_plugin(item))
            elif t == "system_info":
                result.append(self._norm_system_info(item))
            elif t == "user":
                result.append(self._norm_user(item))
        return result

    def _norm_job(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        last_build = raw.get("lastBuild") or {}
        ts = str(last_build.get("timestamp", "")) or now
        return {
            "integration": "jenkins",
            "control": "change_management",
            "evidence_type": "jenkins_jobs",
            "source_id": raw.get("name", ""),
            "timestamp": ts,
            "data": {
                "name": raw.get("name"),
                "url": raw.get("url"),
                "color": raw.get("color"),
                "buildable": raw.get("buildable"),
                "last_build_result": last_build.get("result"),
                "last_build_number": last_build.get("number"),
            },
        }

    def _norm_plugin(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "jenkins",
            "control": "change_management",
            "evidence_type": "jenkins_plugins",
            "source_id": raw.get("shortName", ""),
            "timestamp": now,
            "data": {
                "shortName": raw.get("shortName"),
                "longName": raw.get("longName"),
                "version": raw.get("version"),
                "active": raw.get("active"),
                "enabled": raw.get("enabled"),
                "hasUpdate": raw.get("hasUpdate"),
            },
        }

    def _norm_system_info(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        data = {k: v for k, v in raw.items() if k != "_type"}
        return {
            "integration": "jenkins",
            "control": "change_management",
            "evidence_type": "jenkins_system_info",
            "source_id": "system",
            "timestamp": now,
            "data": data,
        }

    def _norm_user(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        user = raw.get("user") or {}
        return {
            "integration": "jenkins",
            "control": "access_control",
            "evidence_type": "jenkins_users",
            "source_id": user.get("id", ""),
            "timestamp": now,
            "data": {
                "id": user.get("id"),
                "fullName": user.get("fullName"),
            },
        }
