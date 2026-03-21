from __future__ import annotations

"""
Render integration via Render REST API v1.

Credentials:
  api_key — Render API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.render.com/v1"


class RenderIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_key: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/owners",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Render API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Render connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_services,
                self._collect_env_groups,
                self._collect_owners,
                self._collect_deploys,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Render collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_services(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        cursor: str | None = None

        while True:
            params: dict = {"limit": 100}
            if cursor:
                params["cursor"] = cursor

            r = await client.get(
                f"{_BASE}/services",
                headers=self._headers(),
                params=params,
            )
            if r.status_code != 200:
                raise RuntimeError(f"Render services HTTP {r.status_code}")

            body: list[dict] = r.json()
            for entry in body:
                service = entry.get("service", {})
                items.append({"_type": "service", **service})

            if len(body) < 100:
                break

            # Use the cursor from the last entry if present
            last_cursor = body[-1].get("cursor") if body else None
            if not last_cursor:
                break
            cursor = last_cursor

        return items

    async def _collect_env_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/env-groups",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Render env-groups HTTP {r.status_code}")

        body: list[dict] = r.json()
        return [{"_type": "env_group", **entry.get("envGroup", {})} for entry in body]

    async def _collect_owners(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/owners",
            headers=self._headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Render owners HTTP {r.status_code}")

        body: list[dict] = r.json()
        return [{"_type": "owner", **entry.get("owner", {})} for entry in body]

    async def _collect_deploys(self, client: httpx.AsyncClient) -> list[dict]:
        # First collect services to get IDs
        services_raw = await self._collect_services(client)
        service_ids = [s.get("id") for s in services_raw if s.get("id")]

        items: list[dict] = []
        for service_id in service_ids[:3]:
            r = await client.get(
                f"{_BASE}/services/{service_id}/deploys",
                headers=self._headers(),
                params={"limit": 10},
            )
            if r.status_code != 200:
                logger.warning(
                    "Render deploys for service %s HTTP %s", service_id, r.status_code
                )
                continue

            body: list[dict] = r.json()
            for entry in body:
                deploy = entry.get("deploy", {})
                items.append({"_type": "deploy", **deploy})

        return items

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "service":
                result.append(self._norm_service(item))
            elif t == "env_group":
                result.append(self._norm_env_group(item))
            elif t == "owner":
                result.append(self._norm_owner(item))
            elif t == "deploy":
                result.append(self._norm_deploy(item))
        return result

    def _norm_service(self, item: dict) -> dict:
        return {
            "integration": "render",
            "control": "change_management",
            "evidence_type": "render_services",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or self._now(),
            "data": {
                "name": item.get("name"),
                "type": item.get("type"),
                "env": item.get("env"),
                "repo": item.get("repo"),
                "branch": item.get("branch"),
                "status": item.get("status"),
                "region": item.get("region"),
                "url": item.get("url"),
                "serviceDetails": item.get("serviceDetails", {}),
            },
        }

    def _norm_env_group(self, item: dict) -> dict:
        return {
            "integration": "render",
            "control": "change_management",
            "evidence_type": "render_env_groups",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or self._now(),
            "data": {
                "name": item.get("name"),
                "ownerId": item.get("ownerId"),
                "serviceLinks": item.get("serviceLinks", []),
            },
        }

    def _norm_owner(self, item: dict) -> dict:
        return {
            "integration": "render",
            "control": "access_control",
            "evidence_type": "render_owners",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or self._now(),
            "data": {
                "name": item.get("name"),
                "email": item.get("email"),
                "type": item.get("type"),
            },
        }

    def _norm_deploy(self, item: dict) -> dict:
        return {
            "integration": "render",
            "control": "change_management",
            "evidence_type": "render_deploys",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or self._now(),
            "data": {
                "status": item.get("status"),
                "trigger": item.get("trigger"),
                "commit": item.get("commit", {}),
                "finishedAt": item.get("finishedAt"),
                "serviceId": item.get("serviceId"),
            },
        }
