"""
Monday.com integration via Monday.com GraphQL API v2.

Credentials:
  api_token — Monday.com API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_GRAPHQL_URL = "https://api.monday.com/v2"


class MondayIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": self._api_token,
            "Content-Type": "application/json",
        }

    # ── GraphQL helper ─────────────────────────────────────────────────────────

    async def _graphql(self, client: httpx.AsyncClient, query: str) -> dict:
        r = await client.post(
            _GRAPHQL_URL,
            json={"query": query},
            headers=self._headers(),
        )
        return r.json()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _GRAPHQL_URL,
                json={"query": "{ me { id name email } }"},
                headers={
                    "Authorization": api_token,
                    "Content-Type": "application/json",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Monday.com API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Monday.com connect failed HTTP {r.status_code}")
            body = r.json()
            if body.get("errors") or not body.get("data", {}).get("me"):
                raise IntegrationAuthError("Invalid Monday.com API token.")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_boards,
                self._collect_teams,
                self._collect_account,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Monday.com collection error in %s: %s",
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

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        query = "{ users(limit: 100) { id name email enabled is_admin is_guest created_at } }"
        body = await self._graphql(client, query)
        if body.get("errors"):
            raise RuntimeError(f"Monday.com users query error: {body['errors']}")
        users = body.get("data", {}).get("users", [])
        return [{"_type": "user", **u} for u in users]

    async def _collect_boards(self, client: httpx.AsyncClient) -> list[dict]:
        query = (
            "{ boards(limit: 50, order_by: created_at) "
            "{ id name description state board_kind owner { id name } created_at } }"
        )
        body = await self._graphql(client, query)
        if body.get("errors"):
            raise RuntimeError(f"Monday.com boards query error: {body['errors']}")
        boards = body.get("data", {}).get("boards", [])
        return [{"_type": "board", **b} for b in boards]

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        query = "{ teams { id name picture_url users { id name } } }"
        body = await self._graphql(client, query)
        if body.get("errors"):
            raise RuntimeError(f"Monday.com teams query error: {body['errors']}")
        teams = body.get("data", {}).get("teams", [])
        return [{"_type": "team", **t} for t in teams]

    async def _collect_account(self, client: httpx.AsyncClient) -> list[dict]:
        query = "{ account { id name slug tier } }"
        body = await self._graphql(client, query)
        if body.get("errors"):
            raise RuntimeError(f"Monday.com account query error: {body['errors']}")
        account = body.get("data", {}).get("account")
        if not account:
            return []
        return [{"_type": "account", **account}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item, now))
            elif t == "board":
                result.append(self._norm_board(item, now))
            elif t == "team":
                result.append(self._norm_team(item, now))
            elif t == "account":
                result.append(self._norm_account(item, now))
        return result

    def _norm_user(self, raw: dict, now: str) -> dict:
        return {
            "integration": "monday",
            "control": "access_control",
            "evidence_type": "monday_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "enabled": raw.get("enabled"),
                "is_admin": raw.get("is_admin"),
                "is_guest": raw.get("is_guest"),
            },
        }

    def _norm_board(self, raw: dict, now: str) -> dict:
        owner = raw.get("owner")
        return {
            "integration": "monday",
            "control": "change_management",
            "evidence_type": "monday_boards",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "state": raw.get("state"),
                "board_kind": raw.get("board_kind"),
                "owner": owner.get("name") if isinstance(owner, dict) else None,
                "description": raw.get("description"),
            },
        }

    def _norm_team(self, raw: dict, now: str) -> dict:
        return {
            "integration": "monday",
            "control": "access_control",
            "evidence_type": "monday_teams",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "member_count": len(raw.get("users", [])),
            },
        }

    def _norm_account(self, raw: dict, now: str) -> dict:
        return {
            "integration": "monday",
            "control": "cloud_infrastructure",
            "evidence_type": "monday_account",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "tier": raw.get("tier"),
            },
        }
