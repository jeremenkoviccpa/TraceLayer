"""
Trainual integration via Trainual REST API v1.

Credentials:
  api_key — Trainual API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://app.trainual.com/api/v1"


class TrainualIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            # Try /account first; fall back to /users?per_page=1
            r = await client.get(f"{_BASE}/account", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Trainual API key.")
            if r.status_code != 200:
                # Try users endpoint as fallback
                r2 = await client.get(
                    f"{_BASE}/users", headers=headers, params={"per_page": 1}
                )
                if r2.status_code == 401:
                    raise IntegrationAuthError("Invalid Trainual API key.")
                if r2.status_code not in (200, 404):
                    raise RuntimeError(f"Trainual connect failed HTTP {r2.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_subjects,
                self._collect_account,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Trainual collection error in %s: %s", fetch_fn.__name__, exc
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
        r = await client.get(
            f"{_BASE}/users",
            headers=self._headers(),
            params={"per_page": 100},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Trainual users HTTP {r.status_code}")
        body = r.json()
        users = body.get("users", body if isinstance(body, list) else [])
        return [{"_type": "user", **u} for u in users]

    async def _collect_subjects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/subjects",
            headers=self._headers(),
            params={"per_page": 100},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Trainual subjects HTTP {r.status_code}")
        body = r.json()
        subjects = body.get("subjects", [])
        return [{"_type": "subject", **s} for s in subjects]

    async def _collect_account(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/account", headers=self._headers())
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Trainual account HTTP {r.status_code}")
        body = r.json()
        account = body.get("account", body) if isinstance(body, dict) else body
        if isinstance(account, dict):
            return [{"_type": "account", **account}]
        return []

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "subject":
                result.append(self._norm_subject(item))
            elif t == "account":
                result.append(self._norm_account(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        name = raw.get("name") or (
            f"{raw.get('first_name', '')} {raw.get('last_name', '')}".strip()
        )
        return {
            "integration": "trainual",
            "control": "security_training",
            "evidence_type": "trainual_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": name,
                "email": raw.get("email"),
                "role": raw.get("role"),
                "active": raw.get("active"),
            },
        }

    def _norm_subject(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "trainual",
            "control": "security_training",
            "evidence_type": "trainual_subjects",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "title": raw.get("title") or raw.get("name"),
                "published": raw.get("published"),
                "required": raw.get("required"),
                "completion_rate": (
                    raw.get("completion_rate") or raw.get("completions_percentage")
                ),
            },
        }

    def _norm_account(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "trainual",
            "control": "security_training",
            "evidence_type": "trainual_account",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "subdomain": raw.get("subdomain"),
                "plan": raw.get("plan") or raw.get("subscription_plan"),
            },
        }
