from __future__ import annotations

"""
ClickUp integration via ClickUp REST API v2.

Credentials:
  api_token — ClickUp personal API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.clickup.com/api/v2"


class ClickUpIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_token: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": self._api_token}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/user",
                headers={"Authorization": api_token},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid ClickUp API token.")
            if r.status_code != 200:
                raise RuntimeError(f"ClickUp connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_user,
                self._collect_teams,
                self._collect_spaces,
                self._collect_members,
                self._collect_goals,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "ClickUp collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_user(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/user", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"ClickUp user HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "user", **body["user"]}]

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/team", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"ClickUp teams HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "team", **t} for t in body.get("teams", [])]

    async def _collect_spaces(self, client: httpx.AsyncClient) -> list[dict]:
        # Fetch teams first to get the first team_id
        r = await client.get(f"{_BASE}/team", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"ClickUp teams (for spaces) HTTP {r.status_code}")
        teams = r.json().get("teams", [])
        if not teams:
            return []
        team_id = teams[0]["id"]
        r2 = await client.get(
            f"{_BASE}/team/{team_id}/space",
            headers=self._headers(),
            params={"archived": "false"},
        )
        if r2.status_code != 200:
            raise RuntimeError(f"ClickUp spaces HTTP {r2.status_code}")
        body = r2.json()
        return [{"_type": "space", **s} for s in body.get("spaces", [])]

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/team", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"ClickUp teams (for members) HTTP {r.status_code}")
        teams = r.json().get("teams", [])
        if not teams:
            return []
        team_id = teams[0]["id"]
        r2 = await client.get(
            f"{_BASE}/team/{team_id}/member", headers=self._headers()
        )
        if r2.status_code == 404:
            return []
        if r2.status_code != 200:
            raise RuntimeError(f"ClickUp members HTTP {r2.status_code}")
        body = r2.json()
        return [{"_type": "member", **m} for m in body.get("members", [])]

    async def _collect_goals(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/team", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"ClickUp teams (for goals) HTTP {r.status_code}")
        teams = r.json().get("teams", [])
        if not teams:
            return []
        team_id = teams[0]["id"]
        r2 = await client.get(
            f"{_BASE}/team/{team_id}/goal", headers=self._headers()
        )
        if r2.status_code == 404:
            return []
        if r2.status_code != 200:
            raise RuntimeError(f"ClickUp goals HTTP {r2.status_code}")
        body = r2.json()
        return [{"_type": "goal", **g} for g in body.get("goals", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item, now))
            elif t == "team":
                result.append(self._norm_team(item, now))
            elif t == "space":
                result.append(self._norm_space(item, now))
            elif t == "member":
                result.append(self._norm_member(item, now))
            elif t == "goal":
                result.append(self._norm_goal(item, now))
        return result

    def _norm_user(self, item: dict, now: str) -> dict:
        return {
            "integration": "clickup",
            "control": "access_control",
            "evidence_type": "clickup_user",
            "source_id": str(item.get("id", "")),
            "timestamp": now,
            "data": {
                "username": item.get("username"),
                "email": item.get("email"),
                "role": item.get("role"),
                "profilePicture": None,
            },
        }

    def _norm_team(self, item: dict, now: str) -> dict:
        return {
            "integration": "clickup",
            "control": "access_control",
            "evidence_type": "clickup_teams",
            "source_id": str(item.get("id", "")),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "color": item.get("color"),
                "members": [
                    m.get("user", {}).get("email")
                    for m in item.get("members", [])
                ],
            },
        }

    def _norm_space(self, item: dict, now: str) -> dict:
        return {
            "integration": "clickup",
            "control": "change_management",
            "evidence_type": "clickup_spaces",
            "source_id": str(item.get("id", "")),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "private": item.get("private"),
                "statuses": [
                    s.get("status") for s in item.get("statuses", [])
                ],
            },
        }

    def _norm_member(self, item: dict, now: str) -> dict:
        user = item.get("user", {})
        return {
            "integration": "clickup",
            "control": "access_control",
            "evidence_type": "clickup_members",
            "source_id": str(user.get("id", "")),
            "timestamp": now,
            "data": {
                "email": user.get("email"),
                "username": user.get("username"),
                "role": item.get("role"),
                "role_id": item.get("role_id"),
            },
        }

    def _norm_goal(self, item: dict, now: str) -> dict:
        return {
            "integration": "clickup",
            "control": "change_management",
            "evidence_type": "clickup_goals",
            "source_id": item.get("id", ""),
            "timestamp": item.get("date_created") or now,
            "data": {
                "name": item.get("name"),
                "description": item.get("description"),
                "percent_completed": item.get("percent_completed"),
                "color": item.get("color"),
            },
        }
