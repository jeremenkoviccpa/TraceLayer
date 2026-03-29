"""
Zoho Payroll integration adapter.

Collects employee records, payroll runs, and tax declarations for
HR-security, financial-controls, and data-protection evidence via
the Zoho Payroll API v1.

Credentials:
  client_id       — Zoho OAuth2 client ID
  client_secret   — Zoho OAuth2 client secret
  refresh_token   — Zoho OAuth2 refresh token (offline access)
  organization_id — Zoho Payroll organization ID
  region          — Zoho API region suffix (default: "in"; e.g. "com", "eu")
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class ZohoPayrollIntegration(IntegrationAdapter):
    """Collects HR-security, financial-controls, and data-protection evidence from Zoho Payroll."""

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None
        self._organization_id: str | None = None
        self._region: str = "in"
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Exchange the refresh token for an access token and validate it."""
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        refresh_token = credentials.get("refresh_token", "").strip()
        organization_id = credentials.get("organization_id", "").strip()
        region = (credentials.get("region") or "in").strip()

        if not all([client_id, client_secret, refresh_token, organization_id]):
            raise IntegrationAuthError(
                "client_id, client_secret, refresh_token, and organization_id are required."
            )

        access_token = await self._fetch_token(client_id, client_secret, refresh_token, region)

        # Validate against the employees endpoint
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://payroll.zoho.{region}/api/v1/employees",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
                params={"organization_id": organization_id, "per_page": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Zoho Payroll auth failed ({r.status_code}): invalid credentials."
                )
            if r.status_code not in (200, 204):
                raise RuntimeError(f"Zoho Payroll connect failed HTTP {r.status_code}")

        self._client_id = client_id
        self._client_secret = client_secret
        self._refresh_token = refresh_token
        self._organization_id = organization_id
        self._region = region
        self._access_token = access_token
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_employees,
                self._collect_payroll_runs,
                self._collect_tax_declarations,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Zoho Payroll collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "payroll_run":
                result.append(self._norm_payroll_run(item, now))
            elif t == "tax_declaration":
                result.append(self._norm_tax_declaration(item, now))

        return result

    # ------------------------------------------------------------------
    # Private helpers — token refresh
    # ------------------------------------------------------------------

    async def _fetch_token(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        region: str,
    ) -> str:
        token_url = f"https://accounts.zoho.{region}/oauth/v2/token"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                token_url,
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
            )
            if r.status_code != 200:
                raise IntegrationAuthError(
                    f"Zoho Payroll token refresh failed ({r.status_code})."
                )
            body = r.json()
            access_token = body.get("access_token")
            if not access_token:
                raise IntegrationAuthError(
                    "Zoho Payroll token refresh returned no access_token."
                )
            return access_token

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Zoho-oauthtoken {self._access_token}"}

    def _base_url(self) -> str:
        return f"https://payroll.zoho.{self._region}/api/v1"

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/employees",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 200},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Payroll employees HTTP {r.status_code}")
        return [
            {"_type": "employee", **emp}
            for emp in r.json().get("employees", [])
        ]

    async def _collect_payroll_runs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/payrolls",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 50},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Payroll payrolls HTTP {r.status_code}")
        return [
            {"_type": "payroll_run", **payroll}
            for payroll in r.json().get("payrolls", [])
        ]

    async def _collect_tax_declarations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/tax_declarations",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Payroll tax_declarations HTTP {r.status_code}")
        body = r.json()
        # Response may be wrapped under "tax_declarations" or returned as a list
        records = body.get("tax_declarations", body if isinstance(body, list) else [])
        return [{"_type": "tax_declaration", **record} for record in records]

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_employee(self, raw: dict, now: str) -> dict:
        return {
            "integration": "zoho_payroll",
            "control": "hr_security",
            "evidence_type": "zoho_payroll_employee",
            "source_id": raw.get("employee_id", ""),
            "timestamp": raw.get("date_of_joining") or now,
            "data": {
                "employee_id": raw.get("employee_id"),
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "email": raw.get("email"),
                "designation": raw.get("designation"),
                "department": raw.get("department"),
                "date_of_joining": raw.get("date_of_joining"),
                "employment_type": raw.get("employment_type"),
                "status": raw.get("status"),
            },
        }

    def _norm_payroll_run(self, raw: dict, now: str) -> dict:
        return {
            "integration": "zoho_payroll",
            "control": "financial_controls",
            "evidence_type": "zoho_payroll_run",
            "source_id": raw.get("payroll_id", ""),
            "timestamp": raw.get("pay_date") or now,
            "data": {
                "payroll_id": raw.get("payroll_id"),
                "pay_period_start": raw.get("pay_period_start"),
                "pay_period_end": raw.get("pay_period_end"),
                "pay_date": raw.get("pay_date"),
                "status": raw.get("status"),
                "total_gross_pay": raw.get("total_gross_pay"),
                "total_net_pay": raw.get("total_net_pay"),
                "employee_count": raw.get("employee_count"),
            },
        }

    def _norm_tax_declaration(self, raw: dict, now: str) -> dict:
        source_id = raw.get("declaration_id") or raw.get("employee_id", "")
        data = {k: v for k, v in raw.items() if not k.startswith("_")}
        return {
            "integration": "zoho_payroll",
            "control": "data_protection",
            "evidence_type": "zoho_payroll_tax_declaration",
            "source_id": source_id,
            "timestamp": now,
            "data": data,
        }
