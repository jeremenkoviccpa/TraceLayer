from __future__ import annotations

"""
Trello integration via Trello REST API v1.

Credentials:
  api_key — Trello API key
  token   — Trello OAuth token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.trello.com/1"


class TrelloIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_key: str | None = None
        self._token: str | None = None

    def _params(self, **extra) -> dict:
        return {"key": self._api_key, "token": self._token, **extra}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        token = credentials.get("token", "").strip()
        if not api_key or not token:
            raise IntegrationAuthError("api_key and token are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/members/me",
                params={"key": api_key, "token": token},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Trello credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Trello connect failed HTTP {r.status_code}")

        self._api_key = api_key
        self._token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_member,
                self._collect_boards,
                self._collect_organizations,
                self._collect_cards,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Trello collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_member(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/members/me",
            params=self._params(fields="all"),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Trello member HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "member", **body}]

    async def _collect_boards(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/members/me/boards",
            params=self._params(
                filter="all",
                fields="id,name,desc,closed,prefs,idOrganization",
            ),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Trello boards HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "board", **b} for b in body]

    async def _collect_organizations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/members/me/organizations",
            params=self._params(fields="all"),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Trello organizations HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "organization", **o} for o in body]

    async def _collect_cards(self, client: httpx.AsyncClient) -> list[dict]:
        # First fetch all boards to get the open ones
        r = await client.get(
            f"{_BASE}/members/me/boards",
            params=self._params(filter="all", fields="id,name,closed"),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Trello boards (for cards) HTTP {r.status_code}")
        boards = r.json()
        open_boards = [b for b in boards if not b.get("closed")][:3]

        cards: list[dict] = []
        for board in open_boards:
            board_id = board["id"]
            rc = await client.get(
                f"{_BASE}/boards/{board_id}/cards",
                params=self._params(
                    limit=50,
                    fields="id,name,closed,due,dueComplete,idList",
                ),
            )
            if rc.status_code != 200:
                logger.warning(
                    "Trello cards for board %s HTTP %s", board_id, rc.status_code
                )
                continue
            cards.extend([{"_type": "card", **c} for c in rc.json()])

        return cards

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "member":
                result.append(self._norm_member(item, now))
            elif t == "board":
                result.append(self._norm_board(item, now))
            elif t == "organization":
                result.append(self._norm_organization(item, now))
            elif t == "card":
                result.append(self._norm_card(item, now))
        return result

    def _norm_member(self, item: dict, now: str) -> dict:
        return {
            "integration": "trello",
            "control": "access_control",
            "evidence_type": "trello_member",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "username": item.get("username"),
                "fullName": item.get("fullName"),
                "email": item.get("email"),
                "memberType": item.get("memberType"),
            },
        }

    def _norm_board(self, item: dict, now: str) -> dict:
        prefs = item.get("prefs")
        return {
            "integration": "trello",
            "control": "change_management",
            "evidence_type": "trello_boards",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "desc": item.get("desc"),
                "closed": item.get("closed"),
                "permissionLevel": prefs.get("permissionLevel") if isinstance(prefs, dict) else None,
                "votingEnabled": prefs.get("voting") if isinstance(prefs, dict) else None,
            },
        }

    def _norm_organization(self, item: dict, now: str) -> dict:
        return {
            "integration": "trello",
            "control": "access_control",
            "evidence_type": "trello_organizations",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "displayName": item.get("displayName"),
                "name": item.get("name"),
                "website": item.get("website"),
                "products": item.get("products", []),
            },
        }

    def _norm_card(self, item: dict, now: str) -> dict:
        return {
            "integration": "trello",
            "control": "change_management",
            "evidence_type": "trello_cards",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "name": item.get("name"),
                "closed": item.get("closed"),
                "due": item.get("due"),
                "dueComplete": item.get("dueComplete"),
                "idList": item.get("idList"),
            },
        }
