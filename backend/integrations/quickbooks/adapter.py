"""
QuickBooks Online integration adapter.

Collects invoices, vendors, accounts, and employees from the QuickBooks
Online REST API (https://quickbooks.api.intuit.com/v3/company/{realm_id}).
OAuth2 credentials are refreshed automatically before each session.
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

QBO_TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
QBO_API_BASE = "https://quickbooks.api.intuit.com/v3/company"


class QuickBooksIntegration(IntegrationAdapter):
    """Collects financial-controls evidence from QuickBooks Online."""

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None
        self._realm_id: str | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by refreshing the token and fetching company info."""
        self._client_id = (credentials.get("client_id") or "").strip()
        self._client_secret = (credentials.get("client_secret") or "").strip()
        self._refresh_token = (credentials.get("refresh_token") or "").strip()
        self._realm_id = (credentials.get("realm_id") or "").strip()

        if not all([self._client_id, self._client_secret, self._refresh_token, self._realm_id]):
            raise IntegrationAuthError(
                "QuickBooks credentials require: client_id, client_secret, refresh_token, realm_id."
            )

        await self._refresh_access_token()

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{QBO_API_BASE}/{self._realm_id}/companyinfo/{self._realm_id}",
                headers=self._auth_headers(),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid QuickBooks credentials or expired token."
                )
            r.raise_for_status()

        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                invoices = await self._collect_invoices(client)
                raw.extend(invoices)
            except Exception as e:
                logger.exception("QuickBooks: failed to collect invoices")
                raw.append({"_type": "error", "_source": "_collect_invoices", "_error": str(e)})

            try:
                vendors = await self._collect_vendors(client)
                raw.extend(vendors)
            except Exception as e:
                logger.exception("QuickBooks: failed to collect vendors")
                raw.append({"_type": "error", "_source": "_collect_vendors", "_error": str(e)})

            try:
                accounts = await self._collect_accounts(client)
                raw.extend(accounts)
            except Exception as e:
                logger.exception("QuickBooks: failed to collect accounts")
                raw.append({"_type": "error", "_source": "_collect_accounts", "_error": str(e)})

            try:
                employees = await self._collect_employees(client)
                raw.extend(employees)
            except Exception as e:
                logger.exception("QuickBooks: failed to collect employees")
                raw.append({"_type": "error", "_source": "_collect_employees", "_error": str(e)})

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "invoice":
                result.append(self._norm_invoice(item, now))
            elif t == "vendor":
                result.append(self._norm_vendor(item, now))
            elif t == "account":
                result.append(self._norm_account(item, now))
            elif t == "employee":
                result.append(self._norm_employee(item, now))
            # skip error records

        return result

    # ------------------------------------------------------------------
    # Private helpers — token & headers
    # ------------------------------------------------------------------

    async def _refresh_access_token(self) -> None:
        """Exchange the refresh token for a new access token."""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                QBO_TOKEN_URL,
                auth=httpx.BasicAuth(self._client_id, self._client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
                headers={"Accept": "application/json"},
            )
            if r.status_code in (400, 401, 403):
                raise IntegrationAuthError(
                    "Invalid QuickBooks credentials or expired token."
                )
            r.raise_for_status()
            body = r.json()
            self._access_token = body["access_token"]
            # Update refresh token if a new one is issued (token rotation).
            if body.get("refresh_token"):
                self._refresh_token = body["refresh_token"]

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def _query_url(self, sql: str) -> str:
        return f"{QBO_API_BASE}/{self._realm_id}/query"

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_invoices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._query_url("Invoice"),
            headers=self._auth_headers(),
            params={"query": "SELECT * FROM Invoice MAXRESULTS 100", "minorversion": "65"},
        )
        r.raise_for_status()
        items = r.json().get("QueryResponse", {}).get("Invoice", [])
        for item in items:
            item["_type"] = "invoice"
        return items

    async def _collect_vendors(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._query_url("Vendor"),
            headers=self._auth_headers(),
            params={"query": "SELECT * FROM Vendor MAXRESULTS 100", "minorversion": "65"},
        )
        r.raise_for_status()
        items = r.json().get("QueryResponse", {}).get("Vendor", [])
        for item in items:
            item["_type"] = "vendor"
        return items

    async def _collect_accounts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._query_url("Account"),
            headers=self._auth_headers(),
            params={"query": "SELECT * FROM Account MAXRESULTS 100", "minorversion": "65"},
        )
        r.raise_for_status()
        items = r.json().get("QueryResponse", {}).get("Account", [])
        for item in items:
            item["_type"] = "account"
        return items

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._query_url("Employee"),
            headers=self._auth_headers(),
            params={"query": "SELECT * FROM Employee MAXRESULTS 100", "minorversion": "65"},
        )
        r.raise_for_status()
        items = r.json().get("QueryResponse", {}).get("Employee", [])
        for item in items:
            item["_type"] = "employee"
        return items

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_invoice(self, item: dict, now: str) -> dict:
        return {
            "integration": "quickbooks",
            "control": "financial_controls",
            "evidence_type": "qbo_invoice",
            "source_id": item.get("Id", ""),
            "timestamp": item.get("MetaData", {}).get("CreateTime") or now,
            "data": {
                "Id": item.get("Id"),
                "DocNumber": item.get("DocNumber"),
                "TxnDate": item.get("TxnDate"),
                "DueDate": item.get("DueDate"),
                "TotalAmt": item.get("TotalAmt"),
                "Balance": item.get("Balance"),
                "CustomerRef_name": item.get("CustomerRef", {}).get("name", ""),
                "CurrencyRef_value": item.get("CurrencyRef", {}).get("value", ""),
                "status": item.get("EmailStatus", ""),
            },
        }

    def _norm_vendor(self, item: dict, now: str) -> dict:
        return {
            "integration": "quickbooks",
            "control": "vendor_management",
            "evidence_type": "qbo_vendor",
            "source_id": item.get("Id", ""),
            "timestamp": item.get("MetaData", {}).get("CreateTime") or now,
            "data": {
                "Id": item.get("Id"),
                "DisplayName": item.get("DisplayName"),
                "CompanyName": item.get("CompanyName"),
                "Active": item.get("Active"),
                "Balance": item.get("Balance"),
                "TaxIdentifier": item.get("TaxIdentifier"),
                "CurrencyRef_value": item.get("CurrencyRef", {}).get("value", ""),
            },
        }

    def _norm_account(self, item: dict, now: str) -> dict:
        return {
            "integration": "quickbooks",
            "control": "financial_controls",
            "evidence_type": "qbo_account",
            "source_id": item.get("Id", ""),
            "timestamp": item.get("MetaData", {}).get("CreateTime") or now,
            "data": {
                "Id": item.get("Id"),
                "Name": item.get("Name"),
                "AccountType": item.get("AccountType"),
                "AccountSubType": item.get("AccountSubType"),
                "CurrentBalance": item.get("CurrentBalance"),
                "Active": item.get("Active"),
                "CurrencyRef_value": item.get("CurrencyRef", {}).get("value", ""),
            },
        }

    def _norm_employee(self, item: dict, now: str) -> dict:
        return {
            "integration": "quickbooks",
            "control": "hr_security",
            "evidence_type": "qbo_employee",
            "source_id": item.get("Id", ""),
            "timestamp": item.get("MetaData", {}).get("CreateTime") or now,
            "data": {
                "Id": item.get("Id"),
                "DisplayName": item.get("DisplayName"),
                "GivenName": item.get("GivenName"),
                "FamilyName": item.get("FamilyName"),
                "Active": item.get("Active"),
                "PrimaryEmailAddr_Address": item.get("PrimaryEmailAddr", {}).get("Address", ""),
                "BillRate": item.get("BillRate"),
            },
        }
