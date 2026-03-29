"""
Xero integration adapter.

Collects invoices, contacts, bank transactions, and users from the Xero
Accounting API (https://api.xero.com/api.xro/2.0/).
OAuth2 credentials are refreshed automatically before each session.
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_API_BASE = "https://api.xero.com/api.xro/2.0"


class XeroIntegration(IntegrationAdapter):
    """Collects financial-controls evidence from Xero."""

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None
        self._tenant_id: str | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by refreshing the token and fetching organisation info."""
        self._client_id = (credentials.get("client_id") or "").strip()
        self._client_secret = (credentials.get("client_secret") or "").strip()
        self._refresh_token = (credentials.get("refresh_token") or "").strip()
        self._tenant_id = (credentials.get("tenant_id") or "").strip()

        if not all([self._client_id, self._client_secret, self._refresh_token, self._tenant_id]):
            raise IntegrationAuthError(
                "Xero credentials require: client_id, client_secret, refresh_token, tenant_id."
            )

        await self._refresh_access_token()

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{XERO_API_BASE}/Organisation",
                headers=self._auth_headers(),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid Xero credentials or expired token."
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
                logger.exception("Xero: failed to collect invoices")
                raw.append({"_type": "error", "_source": "_collect_invoices", "_error": str(e)})

            try:
                contacts = await self._collect_contacts(client)
                raw.extend(contacts)
            except Exception as e:
                logger.exception("Xero: failed to collect contacts")
                raw.append({"_type": "error", "_source": "_collect_contacts", "_error": str(e)})

            try:
                bank_transactions = await self._collect_bank_transactions(client)
                raw.extend(bank_transactions)
            except Exception as e:
                logger.exception("Xero: failed to collect bank transactions")
                raw.append({"_type": "error", "_source": "_collect_bank_transactions", "_error": str(e)})

            try:
                users = await self._collect_users(client)
                raw.extend(users)
            except Exception as e:
                logger.exception("Xero: failed to collect users")
                raw.append({"_type": "error", "_source": "_collect_users", "_error": str(e)})

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
            elif t == "contact":
                result.append(self._norm_contact(item, now))
            elif t == "bank_transaction":
                result.append(self._norm_bank_transaction(item, now))
            elif t == "user":
                result.append(self._norm_user(item, now))
            # skip error records

        return result

    # ------------------------------------------------------------------
    # Private helpers — token & headers
    # ------------------------------------------------------------------

    async def _refresh_access_token(self) -> None:
        """Exchange the refresh token for a new access token."""
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                XERO_TOKEN_URL,
                auth=httpx.BasicAuth(self._client_id, self._client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
                headers={"Accept": "application/json"},
            )
            if r.status_code in (400, 401, 403):
                raise IntegrationAuthError(
                    "Invalid Xero credentials or expired token."
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
            "Xero-tenant-id": self._tenant_id,
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_invoices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{XERO_API_BASE}/Invoices",
            headers=self._auth_headers(),
            params={"where": 'Status!="DRAFT"', "page": 1, "pageSize": 100},
        )
        r.raise_for_status()
        items = r.json().get("Invoices", [])
        for item in items:
            item["_type"] = "invoice"
        return items

    async def _collect_contacts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{XERO_API_BASE}/Contacts",
            headers=self._auth_headers(),
            params={"page": 1, "pageSize": 100},
        )
        r.raise_for_status()
        items = r.json().get("Contacts", [])
        for item in items:
            item["_type"] = "contact"
        return items

    async def _collect_bank_transactions(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{XERO_API_BASE}/BankTransactions",
            headers=self._auth_headers(),
            params={"page": 1, "pageSize": 100},
        )
        r.raise_for_status()
        items = r.json().get("BankTransactions", [])
        for item in items:
            item["_type"] = "bank_transaction"
        return items

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{XERO_API_BASE}/Users",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        items = r.json().get("Users", [])
        for item in items:
            item["_type"] = "user"
        return items

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_invoice(self, item: dict, now: str) -> dict:
        return {
            "integration": "xero",
            "control": "financial_controls",
            "evidence_type": "xero_invoice",
            "source_id": item.get("InvoiceID", ""),
            "timestamp": item.get("DateString") or item.get("Date") or now,
            "data": {
                "InvoiceID": item.get("InvoiceID"),
                "InvoiceNumber": item.get("InvoiceNumber"),
                "Type": item.get("Type"),
                "Status": item.get("Status"),
                "Contact_Name": item.get("Contact", {}).get("Name", ""),
                "AmountDue": item.get("AmountDue"),
                "AmountPaid": item.get("AmountPaid"),
                "Total": item.get("Total"),
                "CurrencyCode": item.get("CurrencyCode"),
                "DueDate": item.get("DueDate"),
            },
        }

    def _norm_contact(self, item: dict, now: str) -> dict:
        return {
            "integration": "xero",
            "control": "vendor_management",
            "evidence_type": "xero_contact",
            "source_id": item.get("ContactID", ""),
            "timestamp": now,
            "data": {
                "ContactID": item.get("ContactID"),
                "Name": item.get("Name"),
                "IsCustomer": item.get("IsCustomer"),
                "IsSupplier": item.get("IsSupplier"),
                "EmailAddress": item.get("EmailAddress"),
                "IsArchived": item.get("IsArchived"),
                "ContactStatus": item.get("ContactStatus"),
            },
        }

    def _norm_bank_transaction(self, item: dict, now: str) -> dict:
        return {
            "integration": "xero",
            "control": "financial_controls",
            "evidence_type": "xero_bank_transaction",
            "source_id": item.get("BankTransactionID", ""),
            "timestamp": item.get("DateString") or now,
            "data": {
                "BankTransactionID": item.get("BankTransactionID"),
                "Type": item.get("Type"),
                "Status": item.get("Status"),
                "Total": item.get("Total"),
                "CurrencyCode": item.get("CurrencyCode"),
                "DateString": item.get("DateString"),
                "BankAccount_Name": item.get("BankAccount", {}).get("Name", ""),
            },
        }

    def _norm_user(self, item: dict, now: str) -> dict:
        return {
            "integration": "xero",
            "control": "access_control",
            "evidence_type": "xero_user",
            "source_id": item.get("UserID", ""),
            "timestamp": now,
            "data": {
                "UserID": item.get("UserID"),
                "EmailAddress": item.get("EmailAddress"),
                "FirstName": item.get("FirstName"),
                "LastName": item.get("LastName"),
                "IsSubscriber": item.get("IsSubscriber"),
                "OrganisationRole": item.get("OrganisationRole"),
                "UpdatedDateUTC": item.get("UpdatedDateUTC"),
            },
        }
