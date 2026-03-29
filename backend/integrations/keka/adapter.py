"""
Keka HR integration adapter.

Collects employee, department, and attendance data for HR security evidence.

Credentials:
  client_id     — Keka OAuth2 client ID
  client_secret — Keka OAuth2 client secret
  subdomain     — Keka company subdomain (e.g. "mycompany" → mycompany.keka.com)

Auth flow:
  Keka uses OAuth2 client_credentials grant. A token is fetched once during
  connect() and refreshed at the start of collect_evidence(). Tokens are
  short-lived (typically 1 hour).
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_PAGE_SIZE = 100
_TOKEN_SCOPE = "kekaapi"


class KekaIntegration(IntegrationAdapter):

    def __init__(self):
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._subdomain: str | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        subdomain = credentials.get("subdomain", "").strip().rstrip("/")

        if not client_id or not client_secret or not subdomain:
            raise IntegrationAuthError(
                "client_id, client_secret, and subdomain are required"
            )

        # Fetch token first; this validates client credentials.
        token = await self._fetch_token(client_id, client_secret, subdomain)

        # Verify token works by hitting a lightweight endpoint.
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://{subdomain}.keka.com/api/v1/hris/employees",
                params={"page": 0, "pagesize": 1},
                headers=self._auth_headers(token),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Keka token rejected on verification ({r.status_code})"
                )
            r.raise_for_status()

        self._client_id = client_id
        self._client_secret = client_secret
        self._subdomain = subdomain
        self._access_token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        # Re-fetch token to guarantee freshness for long-running collections.
        self._access_token = await self._fetch_token(
            self._client_id, self._client_secret, self._subdomain
        )

        async with httpx.AsyncClient(timeout=60) as client:
            employees = await self._collect_employees(client)
            departments = await self._collect_departments(client)
            attendance = await self._collect_attendance(client)

        return employees + departments + attendance

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "department":
                result.append(self._norm_department(item, now))
            elif t == "attendance_summary":
                result.append(self._norm_attendance(item, now))
            else:
                logger.debug("Skipping unknown _type: %s", t)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _base(self) -> str:
        return f"https://{self._subdomain}.keka.com"

    def _auth_headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _headers(self) -> dict:
        return self._auth_headers(self._access_token)

    async def _fetch_token(
        self, client_id: str, client_secret: str, subdomain: str
    ) -> str:
        """Exchange client credentials for an access token."""
        token_url = f"https://{subdomain}.keka.com/connect/token"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": _TOKEN_SCOPE,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError(
                    f"Keka token request failed ({r.status_code}): "
                    "invalid client_id or client_secret"
                )
            r.raise_for_status()
            body = r.json()
            token = body.get("access_token")
            if not token:
                raise IntegrationAuthError(
                    "Keka token response did not contain access_token"
                )
            return token

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate through /hris/employees (page=0,1,2,… until empty page)."""
        items: list[dict] = []
        try:
            page = 0
            while True:
                r = await client.get(
                    f"{self._base()}/api/v1/hris/employees",
                    params={"page": page, "pagesize": _PAGE_SIZE},
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                # Response may be a list directly or wrapped in a data envelope.
                records = body if isinstance(body, list) else body.get("data", body.get("employees", []))
                if not records:
                    break
                for emp in records:
                    emp["_type"] = "employee"
                    items.append(emp)
                # Stop if we got fewer records than a full page.
                if len(records) < _PAGE_SIZE:
                    break
                page += 1
        except httpx.HTTPStatusError as exc:
            logger.error("Keka: failed to collect employees: %s", exc)
            items.append({"_type": "error", "source": "employees", "detail": str(exc)})
        return items

    async def _collect_departments(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch all departments (single non-paginated endpoint)."""
        items: list[dict] = []
        try:
            r = await client.get(
                f"{self._base()}/api/v1/hris/departments",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            records = body if isinstance(body, list) else body.get("data", body.get("departments", []))
            for dept in records:
                dept["_type"] = "department"
                items.append(dept)
        except httpx.HTTPStatusError as exc:
            logger.error("Keka: failed to collect departments: %s", exc)
            items.append({"_type": "error", "source": "departments", "detail": str(exc)})
        return items

    async def _collect_attendance(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Fetch attendance summary. Keka exposes this under attendance/summary or
        hris/employees/attendance depending on the plan. We try the attendance
        summary first and fall back to the employee attendance endpoint.
        """
        items: list[dict] = []
        try:
            r = await client.get(
                f"{self._base()}/api/v1/hris/employees/attendance",
                params={"page": 0, "pagesize": 50},
                headers=self._headers(),
            )
            if r.status_code == 404:
                # Endpoint not available on this plan — skip silently.
                logger.info("Keka attendance endpoint not available (404), skipping")
                return items
            r.raise_for_status()
            body = r.json()
            records = body if isinstance(body, list) else body.get("data", body.get("attendance", []))
            for rec in records:
                rec["_type"] = "attendance_summary"
                items.append(rec)
        except httpx.HTTPStatusError as exc:
            logger.warning("Keka: failed to collect attendance: %s", exc)
            items.append({"_type": "error", "source": "attendance", "detail": str(exc)})
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_employee(self, raw: dict, fallback_ts: str) -> dict:
        source_id = str(
            raw.get("employeeId") or raw.get("id") or ""
        )
        return {
            "integration": "keka",
            "control": "hr_security",
            "evidence_type": "keka_employee",
            "source_id": source_id,
            "timestamp": raw.get("joiningDate") or fallback_ts,
            "data": {
                "employeeId": raw.get("employeeId") or raw.get("id"),
                "displayName": raw.get("displayName") or raw.get("name"),
                "email": raw.get("email") or raw.get("workEmail"),
                "designation": raw.get("designation") or raw.get("jobTitle"),
                "department": raw.get("department"),
                "businessUnit": raw.get("businessUnit"),
                "employmentStatus": raw.get("employmentStatus") or raw.get("status"),
                "joiningDate": raw.get("joiningDate") or raw.get("hireDate"),
            },
        }

    def _norm_department(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "keka",
            "control": "hr_security",
            "evidence_type": "keka_department",
            "source_id": str(raw.get("id", "")),
            "timestamp": fallback_ts,
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "description": raw.get("description"),
                "memberCount": raw.get("memberCount") or raw.get("employeeCount"),
            },
        }

    def _norm_attendance(self, raw: dict, fallback_ts: str) -> dict:
        source_id = str(
            raw.get("employeeId") or raw.get("id") or ""
        )
        return {
            "integration": "keka",
            "control": "hr_security",
            "evidence_type": "keka_attendance",
            "source_id": source_id,
            "timestamp": raw.get("date") or raw.get("month") or fallback_ts,
            "data": raw,
        }
