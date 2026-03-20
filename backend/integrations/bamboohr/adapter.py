"""
BambooHR integration adapter.

Collects employee directory and time-off data for HR security evidence.

Credentials:
  subdomain — BambooHR company subdomain (e.g. "mycompany")
  api_key   — BambooHR API key

Note: BambooHR API uses HTTP Basic auth with the api_key as the username
and the literal string "x" as the password.
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_ACCEPT = "application/json"
_TIME_OFF_START = "2024-01-01"
_TIME_OFF_END = "2025-12-31"


class BambooHRIntegration(IntegrationAdapter):

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
                self._url(subdomain, "/employees/directory"),
                auth=(api_key, "x"),
                headers={"Accept": _ACCEPT},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"BambooHR auth failed ({r.status_code}): "
                    "invalid api_key or subdomain"
                )
            r.raise_for_status()

        self._subdomain = subdomain
        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            employees = await self._collect_employees(client)
            time_off = await self._collect_time_off(client)
        return employees + time_off

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "time_off":
                result.append(self._norm_time_off(item, now))
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _url(self, subdomain: str, path: str) -> str:
        return (
            f"https://{subdomain}.bamboohr.com/api/gateway.php/{subdomain}/v1{path}"
        )

    def _base_url(self, path: str) -> str:
        return self._url(self._subdomain, path)

    def _auth(self) -> tuple[str, str]:
        return (self._api_key, "x")

    def _headers(self) -> dict:
        return {"Accept": _ACCEPT}

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        """
        BambooHR's /employees/directory returns all employees in one shot
        (no server-side pagination); the response envelope is:
          { "fields": [...], "employees": [...] }
        """
        items: list[dict] = []
        r = await client.get(
            self._base_url("/employees/directory"),
            auth=self._auth(),
            headers=self._headers(),
        )
        r.raise_for_status()
        data = r.json()
        for emp in data.get("employees", []):
            items.append({
                "_type": "employee",
                "id": emp.get("id"),
                "displayName": emp.get("displayName"),
                "firstName": emp.get("firstName"),
                "lastName": emp.get("lastName"),
                "jobTitle": emp.get("jobTitle"),
                "department": emp.get("department"),
                "workEmail": emp.get("workEmail"),
                "employmentHistoryStatus": emp.get("employmentHistoryStatus"),
                "hireDate": emp.get("hireDate"),
                "location": emp.get("location"),
            })
        return items

    async def _collect_time_off(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Approved time-off requests for the configured date window.
        This sub-collection is best-effort; failures are swallowed.
        """
        items: list[dict] = []
        try:
            r = await client.get(
                self._base_url("/time_off/requests/"),
                auth=self._auth(),
                headers=self._headers(),
                params={
                    "status": "approved",
                    "start": _TIME_OFF_START,
                    "end": _TIME_OFF_END,
                },
            )
            if r.status_code == 404:
                # Time-off module not enabled for this account
                return items
            r.raise_for_status()
            records = r.json()
            # Response may be a list or wrapped in a key
            if isinstance(records, dict):
                records = records.get("requests", records.get("data", []))
            for rec in records:
                items.append({
                    "_type": "time_off",
                    "id": rec.get("id"),
                    "employeeId": rec.get("employeeId"),
                    "name": rec.get("name"),
                    "type": rec.get("type", {}).get("name") if isinstance(rec.get("type"), dict) else rec.get("type"),
                    "status": rec.get("status", {}).get("status") if isinstance(rec.get("status"), dict) else rec.get("status"),
                    "startDate": rec.get("start"),
                    "endDate": rec.get("end"),
                    "amount": rec.get("amount", {}).get("amount") if isinstance(rec.get("amount"), dict) else None,
                    "unit": rec.get("amount", {}).get("unit") if isinstance(rec.get("amount"), dict) else None,
                })
        except httpx.HTTPStatusError:
            # Time-off data is supplementary; do not abort the full collection
            pass
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_employee(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "bamboohr",
            "control": "hr_security",
            "evidence_type": "bamboohr_employees",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("hireDate") or fallback_ts,
            "data": {
                "display_name": raw.get("displayName"),
                "first_name": raw.get("firstName"),
                "last_name": raw.get("lastName"),
                "job_title": raw.get("jobTitle"),
                "department": raw.get("department"),
                "work_email": raw.get("workEmail"),
                "employment_status": raw.get("employmentHistoryStatus"),
                "hire_date": raw.get("hireDate"),
                "location": raw.get("location"),
            },
        }

    def _norm_time_off(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "bamboohr",
            "control": "hr_security",
            "evidence_type": "bamboohr_time_off",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("startDate") or fallback_ts,
            "data": {
                "employee_id": raw.get("employeeId"),
                "employee_name": raw.get("name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "start_date": raw.get("startDate"),
                "end_date": raw.get("endDate"),
                "amount": raw.get("amount"),
                "unit": raw.get("unit"),
            },
        }
