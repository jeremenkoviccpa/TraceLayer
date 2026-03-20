"""
Kolide integration via Kolide K2 API v0.

Credentials:
  api_key — Kolide API key
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_BASE = "https://k2.kolide.com/api/v0"


class KolideIntegration(IntegrationAdapter):

    def __init__(self):
        self._key: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._key}",
            "Accept": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()

        if not api_key:
            raise IntegrationAuthError("api_key is required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/devices",
                params={"per_page": 1},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Kolide API key")
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "Kolide API key lacks required permissions"
                )
            r.raise_for_status()

        self._key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            devices = await self._collect_devices(client)
            checks = await self._collect_checks(client)
            people = await self._collect_people(client)
        return devices + checks + people

    # ------------------------------------------------------------------
    # devices (cursor / page-based pagination)
    # ------------------------------------------------------------------

    async def _collect_devices(self, client: httpx.AsyncClient) -> list[dict]:
        devices = []
        page = 1
        per_page = 100
        while True:
            try:
                r = await client.get(
                    f"{_BASE}/devices",
                    params={"per_page": per_page, "page": page},
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                # Kolide wraps in {"data": [...], "pagination": {...}}
                items = body.get("data", body) if isinstance(body, dict) else body
                if not items:
                    break
                for d in items:
                    devices.append({
                        "_type": "device",
                        "id": d.get("id"),
                        "name": d.get("name"),
                        "operating_system": d.get("operating_system"),
                        "registered_at": d.get("registered_at"),
                        "last_seen_at": d.get("last_seen_at"),
                        "primary_user_email": d.get("primary_user_email"),
                        "failing_checks_count": d.get("failing_checks_count"),
                    })
                pagination = body.get("pagination", {}) if isinstance(body, dict) else {}
                # Kolide uses next_cursor or next_page
                next_cursor = pagination.get("next_cursor") or pagination.get("next_page")
                if not next_cursor or len(items) < per_page:
                    break
                page += 1
            except Exception as exc:
                print(f"[Kolide] device collection page {page} failed: {exc}")
                break
        return devices

    # ------------------------------------------------------------------
    # checks (no pagination documented — single request)
    # ------------------------------------------------------------------

    async def _collect_checks(self, client: httpx.AsyncClient) -> list[dict]:
        checks = []
        try:
            r = await client.get(
                f"{_BASE}/checks",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            items = body.get("data", body) if isinstance(body, dict) else body
            for c in items:
                checks.append({
                    "_type": "check",
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "description": c.get("description"),
                    "category": c.get("category"),
                    "failing_device_count": c.get("failing_device_count"),
                })
        except Exception as exc:
            print(f"[Kolide] check collection failed: {exc}")
        return checks

    # ------------------------------------------------------------------
    # people
    # ------------------------------------------------------------------

    async def _collect_people(self, client: httpx.AsyncClient) -> list[dict]:
        people = []
        page = 1
        per_page = 100
        while True:
            try:
                r = await client.get(
                    f"{_BASE}/people",
                    params={"per_page": per_page, "page": page},
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                items = body.get("data", body) if isinstance(body, dict) else body
                if not items:
                    break
                for p in items:
                    people.append({
                        "_type": "person",
                        "id": p.get("id"),
                        "email": p.get("email"),
                        "name": p.get("name"),
                        "device_count": p.get("device_count"),
                    })
                pagination = body.get("pagination", {}) if isinstance(body, dict) else {}
                next_cursor = pagination.get("next_cursor") or pagination.get("next_page")
                if not next_cursor or len(items) < per_page:
                    break
                page += 1
            except Exception as exc:
                print(f"[Kolide] people collection page {page} failed: {exc}")
                break
        return people

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "device":
                result.append(self._norm_device(item))
            elif t == "check":
                result.append(self._norm_check(item))
            elif t == "person":
                result.append(self._norm_person(item))
        return result

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "kolide",
            "control": "endpoint_security",
            "evidence_type": "kolide_devices",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("last_seen_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "operating_system": raw.get("operating_system"),
                "registered_at": raw.get("registered_at"),
                "last_seen_at": raw.get("last_seen_at"),
                "primary_user_email": raw.get("primary_user_email"),
                "failing_checks_count": raw.get("failing_checks_count"),
            },
        }

    def _norm_check(self, raw: dict) -> dict:
        return {
            "integration": "kolide",
            "control": "endpoint_security",
            "evidence_type": "kolide_checks",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "category": raw.get("category"),
                "failing_device_count": raw.get("failing_device_count"),
            },
        }

    def _norm_person(self, raw: dict) -> dict:
        return {
            "integration": "kolide",
            "control": "access_control",
            "evidence_type": "kolide_people",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": raw.get("email"),
                "name": raw.get("name"),
                "device_count": raw.get("device_count"),
            },
        }
