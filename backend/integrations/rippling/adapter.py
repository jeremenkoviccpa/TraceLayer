from __future__ import annotations
"""
Rippling integration adapter.

Collects employee and department data for HR security evidence.

Credentials:
  api_key — Rippling platform API key

Required Rippling API permissions:
  Employees (read), Departments (read), Roles (read)
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_BASE = "https://app.rippling.com/api/platform/api"


class RipplingIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/employees",
                headers=self._build_headers(api_key),
                params={"limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Rippling auth failed ({r.status_code}): invalid or revoked api_key"
                )
            r.raise_for_status()

        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            employees = await self._collect_employees(client)
            departments = await self._collect_departments(client)
            roles = await self._collect_roles(client)
        return employees + departments + roles

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "department":
                result.append(self._norm_department(item, now))
        # roles are informational; fold them into hr_security as well
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self, api_key: str | None = None) -> dict:
        key = api_key or self._api_key
        return {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        }

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Rippling returns all employees in a single response when
        includeAll=true; fall back to cursor pagination if a nextCursor
        key is present in the response.
        """
        items: list[dict] = []
        params: dict = {"includeAll": "true"}
        url = f"{_BASE}/employees"

        while True:
            r = await client.get(url, headers=self._build_headers(), params=params)
            r.raise_for_status()
            data = r.json()

            # Rippling may return a list directly or wrap it in a dict
            records = data if isinstance(data, list) else data.get("results", data.get("data", []))
            for emp in records:
                items.append({
                    "_type": "employee",
                    "id": emp.get("id"),
                    "work_email": emp.get("workEmail") or emp.get("work_email"),
                    "first_name": emp.get("firstName") or emp.get("first_name"),
                    "last_name": emp.get("lastName") or emp.get("last_name"),
                    "title": emp.get("title") or emp.get("jobTitle"),
                    "department": emp.get("department"),
                    "employment_type": emp.get("employmentType") or emp.get("employment_type"),
                    "start_date": emp.get("startDate") or emp.get("start_date"),
                    "is_manager": emp.get("isManager") or emp.get("is_manager", False),
                    "manager_id": emp.get("managerId") or emp.get("manager_id"),
                })

            next_cursor = data.get("nextCursor") if isinstance(data, dict) else None
            if not next_cursor:
                break
            params["cursor"] = next_cursor

        return items

    async def _collect_departments(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_BASE}/departments",
                headers=self._build_headers(),
            )
            r.raise_for_status()
            data = r.json()
            records = data if isinstance(data, list) else data.get("results", data.get("data", []))
            for dept in records:
                items.append({
                    "_type": "department",
                    "id": dept.get("id"),
                    "name": dept.get("name"),
                    "manager": dept.get("manager") or dept.get("managerId"),
                })
        except httpx.HTTPStatusError as exc:
            # Departments endpoint may not be available on all Rippling plans
            if exc.response.status_code == 404:
                pass
            else:
                raise
        return items

    async def _collect_roles(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_BASE}/roles",
                headers=self._build_headers(),
            )
            if r.status_code == 404:
                return items  # endpoint not available on this plan
            r.raise_for_status()
            data = r.json()
            records = data if isinstance(data, list) else data.get("results", data.get("data", []))
            for role in records:
                items.append({
                    "_type": "role",
                    "id": role.get("id"),
                    "name": role.get("name"),
                    "description": role.get("description"),
                })
        except httpx.HTTPStatusError:
            # Roles endpoint is optional; swallow non-critical failures
            pass
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_employee(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "rippling",
            "control": "hr_security",
            "evidence_type": "rippling_employees",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("start_date") or fallback_ts,
            "data": {
                "work_email": raw.get("work_email"),
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "title": raw.get("title"),
                "department": raw.get("department"),
                "employment_type": raw.get("employment_type"),
                "start_date": raw.get("start_date"),
                "is_manager": raw.get("is_manager", False),
                "manager_id": raw.get("manager_id"),
            },
        }

    def _norm_department(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "rippling",
            "control": "hr_security",
            "evidence_type": "rippling_departments",
            "source_id": str(raw.get("id", "")),
            "timestamp": fallback_ts,
            "data": {
                "name": raw.get("name"),
                "manager": raw.get("manager"),
            },
        }
