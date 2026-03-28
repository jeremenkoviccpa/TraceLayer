"""
Freshdesk integration adapter.

Collects agent accounts and recent ticket activity for access control
and change management evidence.

Credentials:
  subdomain — Freshdesk subdomain (e.g. "mycompany" for mycompany.freshdesk.com)
  api_key   — Freshdesk API key (found in Profile Settings)

Note: Freshdesk API uses HTTP Basic auth with the api_key as the username
and the literal string "X" as the password.
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_ACCEPT = "application/json"
_TICKETS_UPDATED_SINCE = "2024-01-01T00:00:00Z"


class FreshdeskIntegration(IntegrationAdapter):

    def __init__(self):
        self._subdomain: str | None = None
        self._api_key: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        subdomain = credentials.get("subdomain", "").strip()
        api_key = credentials.get("api_key", "").strip()

        if not subdomain or not api_key:
            raise IntegrationAuthError("subdomain and api_key are required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                self._url(subdomain, "/agents"),
                auth=(api_key, "X"),
                headers={"Accept": _ACCEPT},
                params={"per_page": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Freshdesk auth failed ({r.status_code}): invalid api_key or subdomain"
                )
            r.raise_for_status()

        self._subdomain = subdomain
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            agents = await self._collect_agents(client)
            tickets = await self._collect_tickets(client)
        return agents + tickets

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "agent":
                result.append(self._norm_agent(item, now))
            elif t == "ticket":
                result.append(self._norm_ticket(item, now))
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, subdomain: str, path: str) -> str:
        return f"https://{subdomain}.freshdesk.com/api/v2{path}"

    def _base_url(self, path: str) -> str:
        return self._url(self._subdomain, path)

    def _auth(self) -> tuple[str, str]:
        return (self._api_key, "X")

    def _headers(self) -> dict:
        return {"Accept": _ACCEPT}

    async def _collect_agents(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                self._base_url("/agents"),
                auth=self._auth(),
                headers=self._headers(),
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            agents = r.json()
            if not agents:
                break
            for agent in agents:
                items.append({
                    "_type": "agent",
                    "id": agent.get("id"),
                    "name": agent.get("contact", {}).get("name") if isinstance(agent.get("contact"), dict) else None,
                    "email": agent.get("contact", {}).get("email") if isinstance(agent.get("contact"), dict) else None,
                    "role_ids": agent.get("role_ids", []),
                    "ticket_scope": agent.get("ticket_scope"),
                    "active": agent.get("contact", {}).get("active", True) if isinstance(agent.get("contact"), dict) else True,
                    "last_login_at": agent.get("last_login_at"),
                    "created_at": agent.get("created_at"),
                })
            if len(agents) < 100:
                break
            page += 1
        return items

    async def _collect_tickets(self, client: httpx.AsyncClient) -> list[dict]:
        """Collect recent tickets as change management evidence."""
        items: list[dict] = []
        try:
            page = 1
            while page <= 3:  # limit to 300 most recent tickets
                r = await client.get(
                    self._base_url("/tickets"),
                    auth=self._auth(),
                    headers=self._headers(),
                    params={
                        "per_page": 100,
                        "page": page,
                        "updated_since": _TICKETS_UPDATED_SINCE,
                        "order_by": "updated_at",
                        "order_type": "desc",
                    },
                )
                if r.status_code == 404:
                    break
                r.raise_for_status()
                tickets = r.json()
                if not tickets:
                    break
                for ticket in tickets:
                    items.append({
                        "_type": "ticket",
                        "id": ticket.get("id"),
                        "subject": ticket.get("subject"),
                        "status": ticket.get("status"),
                        "priority": ticket.get("priority"),
                        "type": ticket.get("type"),
                        "requester_id": ticket.get("requester_id"),
                        "responder_id": ticket.get("responder_id"),
                        "created_at": ticket.get("created_at"),
                        "updated_at": ticket.get("updated_at"),
                    })
                if len(tickets) < 100:
                    break
                page += 1
        except httpx.HTTPStatusError:
            pass
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_agent(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "freshdesk",
            "control": "access_control",
            "evidence_type": "freshdesk_agents",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or fallback_ts,
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "role_ids": raw.get("role_ids"),
                "ticket_scope": raw.get("ticket_scope"),
                "active": raw.get("active"),
                "last_login_at": raw.get("last_login_at"),
            },
        }

    def _norm_ticket(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "freshdesk",
            "control": "change_management",
            "evidence_type": "freshdesk_tickets",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or fallback_ts,
            "data": {
                "subject": raw.get("subject"),
                "status": raw.get("status"),
                "priority": raw.get("priority"),
                "type": raw.get("type"),
                "requester_id": raw.get("requester_id"),
                "responder_id": raw.get("responder_id"),
                "updated_at": raw.get("updated_at"),
            },
        }
