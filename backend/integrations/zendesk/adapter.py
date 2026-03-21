"""
Zendesk integration via Zendesk REST API v2.

Credentials:
  subdomain  — Zendesk subdomain (e.g. "mycompany")
  email      — Agent email address
  api_token  — Zendesk API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class ZendeskIntegration(IntegrationAdapter):

    def __init__(self):
        self._subdomain: str | None = None
        self._email: str | None = None
        self._api_token: str | None = None

    def _base_url(self) -> str:
        return f"https://{self._subdomain}.zendesk.com/api/v2"

    def _auth(self) -> tuple[str, str]:
        # Zendesk token auth: username is "email/token"
        return (f"{self._email}/token", self._api_token)

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        subdomain = credentials.get("subdomain", "").strip()
        email = credentials.get("email", "").strip()
        api_token = credentials.get("api_token", "").strip()

        if not subdomain or not email or not api_token:
            raise IntegrationAuthError("subdomain, email, and api_token are required.")

        base = f"https://{subdomain}.zendesk.com/api/v2"
        auth = (f"{email}/token", api_token)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{base}/users/me.json", auth=auth)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Zendesk credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Zendesk connect failed HTTP {r.status_code}")

        self._subdomain = subdomain
        self._email = email
        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_agents,
                self._collect_sla_policies,
                self._collect_triggers,
                self._collect_groups,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Zendesk collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_agents(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/users.json",
            auth=self._auth(),
            params={"role": "agent", "page[size]": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zendesk agents HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "agents", **u} for u in body.get("users", [])]

    async def _collect_sla_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/sla_policies.json",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zendesk SLA policies HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "sla_policies", **p} for p in body.get("sla_policies", [])]

    async def _collect_triggers(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/triggers.json",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zendesk triggers HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "triggers", **t} for t in body.get("triggers", [])]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/groups.json",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zendesk groups HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "groups", **g} for g in body.get("groups", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "agents":
                result.append(self._norm_agent(item))
            elif t == "sla_policies":
                result.append(self._norm_sla_policy(item))
            elif t == "triggers":
                result.append(self._norm_trigger(item))
            elif t == "groups":
                result.append(self._norm_group(item))
        return result

    def _norm_agent(self, raw: dict) -> dict:
        return {
            "integration": "zendesk",
            "control": "access_control",
            "evidence_type": "agents",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "role": raw.get("role"),
                "active": raw.get("active"),
                "two_factor_auth_enabled": raw.get("two_factor_auth_enabled"),
                "last_login_at": raw.get("last_login_at"),
            },
        }

    def _norm_sla_policy(self, raw: dict) -> dict:
        return {
            "integration": "zendesk",
            "control": "availability",
            "evidence_type": "sla_policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "description": raw.get("description"),
                "active": raw.get("active"),
                "position": raw.get("position"),
            },
        }

    def _norm_trigger(self, raw: dict) -> dict:
        return {
            "integration": "zendesk",
            "control": "process_controls",
            "evidence_type": "triggers",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "active": raw.get("active"),
                "position": raw.get("position"),
                "description": raw.get("description"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "zendesk",
            "control": "access_control",
            "evidence_type": "groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "default": raw.get("default"),
                "deleted": raw.get("deleted"),
            },
        }
