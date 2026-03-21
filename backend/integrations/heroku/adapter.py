"""
Heroku integration via Heroku Platform API v3.

Credentials:
  api_key — Heroku API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.heroku.com"
_ACCEPT = "application/vnd.heroku+json; version=3"


class HerokuIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": _ACCEPT,
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/account",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": _ACCEPT,
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Heroku API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Heroku connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_apps,
                self._collect_team_members,
                self._collect_account_features,
                self._collect_addons,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Heroku collection error in %s: %s",
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

    async def _collect_apps(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/apps", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Heroku apps HTTP {r.status_code}")
        return [{"_type": "app", **app} for app in r.json()]

    async def _collect_team_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/teams", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Heroku teams HTTP {r.status_code}")
        teams = r.json()
        if not teams:
            return []

        # Fetch members for the first team only to avoid excessive requests
        team_name = teams[0].get("name", "")
        if not team_name:
            return []

        rm = await client.get(
            f"{_BASE}/teams/{team_name}/members",
            headers=self._headers(),
        )
        if rm.status_code != 200:
            raise RuntimeError(f"Heroku team members HTTP {rm.status_code}")
        return [{"_type": "team_member", **m} for m in rm.json()]

    async def _collect_account_features(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/account/features", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Heroku account features HTTP {r.status_code}")
        return [{"_type": "account_feature", **f} for f in r.json()]

    async def _collect_addons(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/addons", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Heroku addons HTTP {r.status_code}")
        return [{"_type": "addon", **a} for a in r.json()]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "app":
                result.append(self._norm_app(item, now))
            elif t == "team_member":
                result.append(self._norm_team_member(item, now))
            elif t == "account_feature":
                result.append(self._norm_account_feature(item, now))
            elif t == "addon":
                result.append(self._norm_addon(item, now))
        return result

    def _norm_app(self, raw: dict, now: str) -> dict:
        return {
            "integration": "heroku",
            "control": "change_management",
            "evidence_type": "heroku_apps",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "stack": raw.get("stack", {}).get("name"),
                "region": raw.get("region", {}).get("name"),
                "maintenance": raw.get("maintenance"),
                "archived_at": raw.get("archived_at"),
                "buildpack_provided_description": raw.get("buildpack_provided_description"),
                "web_url": raw.get("web_url"),
            },
        }

    def _norm_team_member(self, raw: dict, now: str) -> dict:
        return {
            "integration": "heroku",
            "control": "access_control",
            "evidence_type": "heroku_team_members",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "email": raw.get("email"),
                "role": raw.get("role"),
                "two_factor_authentication": raw.get("two_factor_authentication"),
            },
        }

    def _norm_account_feature(self, raw: dict, now: str) -> dict:
        return {
            "integration": "heroku",
            "control": "cloud_infrastructure",
            "evidence_type": "heroku_account_features",
            "source_id": raw.get("name", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "enabled": raw.get("enabled"),
                "state": raw.get("state"),
            },
        }

    def _norm_addon(self, raw: dict, now: str) -> dict:
        return {
            "integration": "heroku",
            "control": "cloud_infrastructure",
            "evidence_type": "heroku_addons",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "plan": raw.get("plan", {}).get("name"),
                "state": raw.get("state"),
                "app": raw.get("app", {}).get("name"),
            },
        }
