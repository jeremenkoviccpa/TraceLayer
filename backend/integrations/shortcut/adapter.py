"""
Shortcut integration via Shortcut REST API v3.

Credentials:
  api_token — Shortcut API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.app.shortcut.com/api/v3"


class ShortcutIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {"Shortcut-Token": self._api_token}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/member",
                headers={"Shortcut-Token": api_token},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Shortcut API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Shortcut connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_members,
                self._collect_groups,
                self._collect_workflows,
                self._collect_epics,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Shortcut collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/members", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Shortcut members HTTP {r.status_code}")
        return [{"_type": "member", **item} for item in r.json()]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/groups", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Shortcut groups HTTP {r.status_code}")
        return [{"_type": "group", **item} for item in r.json()]

    async def _collect_workflows(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/workflows", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Shortcut workflows HTTP {r.status_code}")
        return [{"_type": "workflow", **item} for item in r.json()]

    async def _collect_epics(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/epics", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Shortcut epics HTTP {r.status_code}")
        return [{"_type": "epic", **item} for item in r.json()[:100]]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "member":
                result.append(self._norm_member(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "workflow":
                result.append(self._norm_workflow(item))
            elif t == "epic":
                result.append(self._norm_epic(item))
        return result

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _norm_member(self, raw: dict) -> dict:
        profile = raw.get("profile", {})
        return {
            "integration": "shortcut",
            "control": "access_control",
            "evidence_type": "shortcut_members",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": profile.get("name"),
                "email_address": profile.get("email_address"),
                "role": raw.get("role"),
                "disabled": raw.get("disabled"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "shortcut",
            "control": "access_control",
            "evidence_type": "shortcut_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "archived": raw.get("archived"),
                "num_stories_started": raw.get("num_stories_started"),
            },
        }

    def _norm_workflow(self, raw: dict) -> dict:
        return {
            "integration": "shortcut",
            "control": "change_management",
            "evidence_type": "shortcut_workflows",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "states": [s.get("name") for s in raw.get("states", [])],
            },
        }

    def _norm_epic(self, raw: dict) -> dict:
        return {
            "integration": "shortcut",
            "control": "change_management",
            "evidence_type": "shortcut_epics",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "state": raw.get("state"),
                "completed": raw.get("completed"),
                "archived": raw.get("archived"),
                "owner_ids": raw.get("owner_ids", []),
            },
        }
