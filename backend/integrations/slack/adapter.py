from __future__ import annotations
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

SLACK_API = "https://slack.com/api"


class SlackIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("bot_token")
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SLACK_API}/auth.test",
                headers={"Authorization": f"Bearer {token}"},
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                raise IntegrationAuthError(data.get("error", "Slack auth failed"))
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client, headers)
            team = await self._collect_team(client, headers)
        return users + team

    async def _collect_users(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        users = []
        cursor = None
        while True:
            params: dict = {"limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = await client.get(f"{SLACK_API}/users.list", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                break
            users.extend([{"_type": "slack_user", **u} for u in data.get("members", [])])
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return users

    async def _collect_team(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        r = await client.get(f"{SLACK_API}/team.info", headers=headers)
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return [{"_type": "slack_team", **data.get("team", {})}]
        return []

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "slack_user":
                normalized = self._norm_user(item)
                if normalized:
                    result.append(normalized)
            elif t == "slack_team":
                result.append(self._norm_team(item))
        return result

    def _norm_user(self, raw: dict) -> dict | None:
        # Skip deleted accounts and bots
        if raw.get("deleted") or raw.get("is_bot") or raw.get("id") == "USLACKBOT":
            return None

        updated = raw.get("updated")
        timestamp = (
            datetime.fromtimestamp(updated, tz=timezone.utc).isoformat()
            if updated
            else datetime.now(timezone.utc).isoformat()
        )

        return {
            "integration": "slack",
            "control": "access_control",
            "evidence_type": "slack_users",
            "source_id": raw["id"],
            "timestamp": timestamp,
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "real_name": raw.get("real_name"),
                "email": raw.get("profile", {}).get("email"),
                "is_admin": raw.get("is_admin", False),
                "is_owner": raw.get("is_owner", False),
                "is_primary_owner": raw.get("is_primary_owner", False),
                "two_factor_enabled": raw.get("two_factor_type") is not None,
            },
        }

    def _norm_team(self, raw: dict) -> dict:
        return {
            "integration": "slack",
            "control": "access_control",
            "evidence_type": "slack_workspace",
            "source_id": raw.get("id", "workspace"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "domain": raw.get("domain"),
                "email_domain": raw.get("email_domain"),
                "plan": raw.get("plan"),
            },
        }
