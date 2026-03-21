from __future__ import annotations
"""
Doppler integration via Doppler API v3.

Credentials:
  api_token — Doppler service token or personal token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_API_BASE = "https://api.doppler.com/v3"


class DopplerIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _auth(self) -> tuple[str, str]:
        # Basic auth: token as username, empty password
        return (self._api_token, "")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_API_BASE}/me",
                auth=(api_token, ""),
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Doppler API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Doppler connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_workplaces,
                self._collect_projects,
                self._collect_members,
                self._collect_audit_logs,
                self._collect_service_accounts,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Doppler collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_workplaces(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/workplace", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Doppler workplace HTTP {r.status_code}")
        workplace = r.json().get("workplace", {})
        return [{"_type": "workplace", **workplace}]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/projects", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Doppler projects HTTP {r.status_code}")
        return [{"_type": "project", **p} for p in r.json().get("projects", [])]

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/workplace/members", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Doppler members HTTP {r.status_code}")
        return [{"_type": "member", **m} for m in r.json().get("members", [])]

    async def _collect_audit_logs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_API_BASE}/logs",
            auth=self._auth(),
            params={"page": 1, "per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Doppler audit logs HTTP {r.status_code}")
        return [{"_type": "audit_log", **log} for log in r.json().get("logs", [])]

    async def _collect_service_accounts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_API_BASE}/workplace/service_accounts", auth=self._auth())
        if r.status_code == 404:
            logger.info("Doppler service accounts endpoint not available (404); skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Doppler service accounts HTTP {r.status_code}")
        return [{"_type": "service_account", **sa} for sa in r.json().get("service_accounts", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "workplace":
                result.append(self._norm_workplace(item))
            elif t == "project":
                result.append(self._norm_project(item))
            elif t == "member":
                result.append(self._norm_member(item))
            elif t == "audit_log":
                result.append(self._norm_audit_log(item))
            elif t == "service_account":
                result.append(self._norm_service_account(item))
        return result

    def _norm_workplace(self, raw: dict) -> dict:
        return {
            "integration": "doppler",
            "control": "access_control",
            "evidence_type": "doppler_workplace",
            "source_id": raw.get("id", "workplace"),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "billing_email": raw.get("billing_email"),
                "security_email": raw.get("security_email"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "doppler",
            "control": "access_control",
            "evidence_type": "doppler_projects",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "slug": raw.get("slug"),
            },
        }

    def _norm_member(self, raw: dict) -> dict:
        return {
            "integration": "doppler",
            "control": "access_control",
            "evidence_type": "doppler_members",
            "source_id": raw.get("slug", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "email": raw.get("email"),
                "username": raw.get("username") or raw.get("slug"),
                "access": raw.get("access"),
            },
        }

    def _norm_audit_log(self, raw: dict) -> dict:
        return {
            "integration": "doppler",
            "control": "logging_monitoring",
            "evidence_type": "doppler_audit_logs",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "type": raw.get("type"),
                "user": raw.get("user", {}).get("email"),
                "project": raw.get("project"),
                "environment": raw.get("environment"),
                "ip": raw.get("ip"),
            },
        }

    def _norm_service_account(self, raw: dict) -> dict:
        return {
            "integration": "doppler",
            "control": "access_control",
            "evidence_type": "doppler_service_accounts",
            "source_id": raw.get("slug", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "workplace_role": raw.get("workplace_role", {}).get("identifier"),
            },
        }
