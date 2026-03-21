from __future__ import annotations

"""
Personio integration via Personio REST API v1.

Credentials:
  client_id     — Personio OAuth client ID
  client_secret — Personio OAuth client secret
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.personio.de/v1"
_AUTH_URL = "https://api.personio.de/v1/auth"
_PARTNER_ID = "tracelayer"


class PersonioIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "X-Personio-Partner-ID": _PARTNER_ID,
        }

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    async def _fetch_token(self, client_id: str, client_secret: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _AUTH_URL,
                json={"client_id": client_id, "client_secret": client_secret},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Personio credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Personio auth failed HTTP {r.status_code}")
            body = r.json()
            return body["data"]["token"]

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not client_id or not client_secret:
            raise IntegrationAuthError("client_id and client_secret are required.")

        token = await self._fetch_token(client_id, client_secret)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE_URL}/company/employees",
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Personio-Partner-ID": _PARTNER_ID,
                },
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Personio credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Personio connect failed HTTP {r.status_code}")

        self._client_id = client_id
        self._client_secret = client_secret
        self._token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_employees,
                self._collect_absence_types,
                self._collect_projects,
                self._collect_company_info,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Personio collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        employees: list[dict] = []
        limit = 200
        offset = 0

        while True:
            r = await client.get(
                f"{_BASE_URL}/company/employees",
                headers=self._headers(),
                params={"limit": limit, "offset": offset},
            )
            if r.status_code != 200:
                raise RuntimeError(f"Personio employees HTTP {r.status_code}")
            body = r.json()
            page = body.get("data", []) or []
            employees.extend([{"_type": "employee", **e} for e in page])
            total = body.get("total_count", 0)
            offset += limit
            if offset >= total or not page:
                break

        return employees

    async def _collect_absence_types(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company/time-off-types",
            headers=self._headers(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Personio absence types HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", []) or []
        return [{"_type": "absence_type", **a} for a in data]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company/projects",
            headers=self._headers(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Personio projects HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", []) or []
        return [{"_type": "project", **p} for p in data]

    async def _collect_company_info(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Personio company HTTP {r.status_code}")
        body = r.json()
        company = body.get("data") or {}
        return [{"_type": "company", **company}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item))
            elif t == "absence_type":
                result.append(self._norm_absence_type(item))
            elif t == "project":
                result.append(self._norm_project(item))
            elif t == "company":
                result.append(self._norm_company(item))
        return result

    def _attr_value(self, item: dict, key: str):
        """Extract .value from an attributes sub-dict, falling back to the raw value."""
        attrs = item.get("attributes", {})
        field = attrs.get(key)
        if isinstance(field, dict):
            return field.get("value")
        return field

    def _norm_employee(self, raw: dict) -> dict:
        now = self._now()
        attrs = raw.get("attributes", {})

        # department: value may be a nested dict with "name"
        dept_field = attrs.get("department", {})
        if isinstance(dept_field, dict):
            dept_value = dept_field.get("value")
            department = dept_value.get("name") if isinstance(dept_value, dict) else None
        else:
            department = None

        return {
            "integration": "personio",
            "control": "hr_security",
            "evidence_type": "personio_employees",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "first_name": self._attr_value(raw, "first_name"),
                "last_name": self._attr_value(raw, "last_name"),
                "email": self._attr_value(raw, "email"),
                "status": self._attr_value(raw, "status"),
                "department": department,
            },
        }

    def _norm_absence_type(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "personio",
            "control": "hr_security",
            "evidence_type": "personio_absence_types",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": attrs.get("name"),
                "category": attrs.get("category"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "personio",
            "control": "change_management",
            "evidence_type": "personio_projects",
            "source_id": str(raw.get("id", "")),
            "timestamp": self._now(),
            "data": {
                "name": attrs.get("name"),
                "active": attrs.get("active"),
            },
        }

    def _norm_company(self, raw: dict) -> dict:
        return {
            "integration": "personio",
            "control": "hr_security",
            "evidence_type": "personio_company",
            "source_id": "company",
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "industry": raw.get("industry"),
            },
        }
