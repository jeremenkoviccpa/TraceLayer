"""
Zoho People integration adapter.

Collects employee records and department data for HR security evidence.

Credentials:
  client_id     — Zoho OAuth client ID
  client_secret — Zoho OAuth client secret
  refresh_token — Zoho OAuth refresh token (offline access)
  region        — Zoho datacenter region: "com", "eu", "in", "com.au", "jp"
                  Defaults to "com". Use "in" for India-hosted accounts.

Note: Zoho uses OAuth 2.0. The adapter exchanges the refresh_token for a
short-lived access_token on every connect() and collect_evidence() call.
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_TOKEN_URL = "https://accounts.zoho.{region}/oauth/v2/token"
_API_BASE = "https://people.zoho.{region}/people/api"


class ZohoPeopleIntegration(IntegrationAdapter):

    def __init__(self):
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None
        self._region: str = "com"
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        self._client_id = credentials.get("client_id", "").strip()
        self._client_secret = credentials.get("client_secret", "").strip()
        self._refresh_token = credentials.get("refresh_token", "").strip()
        self._region = credentials.get("region", "com").strip() or "com"

        if not self._client_id or not self._client_secret or not self._refresh_token:
            raise IntegrationAuthError("client_id, client_secret, and refresh_token are required")

        await self._refresh_access_token()
        # Verify connectivity with a lightweight call
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{self._api_base()}/forms/P_EmployeeView/getRecords",
                headers=self._auth_headers(),
                params={"sIndex": 1, "limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Zoho People auth failed ({r.status_code}): invalid credentials or insufficient scope"
                )
            r.raise_for_status()
        return True

    async def collect_evidence(self) -> list[dict]:
        await self._refresh_access_token()
        async with httpx.AsyncClient(timeout=60) as client:
            employees = await self._collect_employees(client)
            departments = await self._collect_departments(client)
        return employees + departments

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "department":
                result.append(self._norm_department(item, now))
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _api_base(self) -> str:
        return _API_BASE.replace("{region}", self._region)

    def _token_url(self) -> str:
        return _TOKEN_URL.replace("{region}", self._region)

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Zoho-oauthtoken {self._access_token}"}

    async def _refresh_access_token(self) -> None:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                self._token_url(),
                data={
                    "grant_type": "refresh_token",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "refresh_token": self._refresh_token,
                },
            )
            if not r.is_success:
                raise IntegrationAuthError(
                    f"Zoho token refresh failed ({r.status_code}): {r.text[:200]}"
                )
            data = r.json()
            access_token = data.get("access_token")
            if not access_token:
                raise IntegrationAuthError(f"No access_token in Zoho response: {data}")
            self._access_token = access_token

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        s_index = 1
        limit = 200
        while True:
            r = await client.get(
                f"{self._api_base()}/forms/P_EmployeeView/getRecords",
                headers=self._auth_headers(),
                params={"sIndex": s_index, "limit": limit},
            )
            r.raise_for_status()
            data = r.json()
            records = data.get("response", {}).get("result", [])
            if not records:
                break
            for rec in records:
                emp = rec if isinstance(rec, dict) else {}
                items.append({
                    "_type": "employee",
                    "id": emp.get("Zoho_ID") or emp.get("EmployeeID", ""),
                    "first_name": emp.get("FirstName", ""),
                    "last_name": emp.get("LastName", ""),
                    "email": emp.get("EmailID", ""),
                    "designation": emp.get("Designation", ""),
                    "department": emp.get("Department", ""),
                    "employment_type": emp.get("EmploymentType", ""),
                    "date_of_joining": emp.get("Dateofjoining", ""),
                    "employee_status": emp.get("EmployeeStatus", ""),
                })
            if len(records) < limit:
                break
            s_index += limit
        return items

    async def _collect_departments(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{self._api_base()}/department/getDepartments",
                headers=self._auth_headers(),
            )
            if r.status_code == 404:
                return items
            r.raise_for_status()
            data = r.json()
            departments = data.get("response", {}).get("result", [])
            for dept in departments:
                d = dept if isinstance(dept, dict) else {}
                items.append({
                    "_type": "department",
                    "id": d.get("departmentId", ""),
                    "name": d.get("departmentName", ""),
                })
        except httpx.HTTPStatusError:
            pass
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_employee(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "zoho_people",
            "control": "hr_security",
            "evidence_type": "zoho_employees",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("date_of_joining") or fallback_ts,
            "data": {
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "email": raw.get("email"),
                "designation": raw.get("designation"),
                "department": raw.get("department"),
                "employment_type": raw.get("employment_type"),
                "date_of_joining": raw.get("date_of_joining"),
                "employee_status": raw.get("employee_status"),
            },
        }

    def _norm_department(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "zoho_people",
            "control": "hr_security",
            "evidence_type": "zoho_departments",
            "source_id": str(raw.get("id", "")),
            "timestamp": fallback_ts,
            "data": {
                "department_name": raw.get("name"),
            },
        }
