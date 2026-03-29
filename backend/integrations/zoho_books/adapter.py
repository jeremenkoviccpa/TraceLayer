"""
Zoho Books integration adapter.

Collects invoices, contacts, and journal entries for financial-controls
and data-protection evidence via the Zoho Books API v3.

Credentials:
  client_id       — Zoho OAuth2 client ID
  client_secret   — Zoho OAuth2 client secret
  refresh_token   — Zoho OAuth2 refresh token (offline access)
  organization_id — Zoho Books organization ID
  region          — Zoho API region suffix (default: "com"; e.g. "in", "eu")
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class ZohoBooksIntegration(IntegrationAdapter):
    """Collects financial-controls and data-protection evidence from Zoho Books."""

    def __init__(self) -> None:
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._refresh_token: str | None = None
        self._organization_id: str | None = None
        self._region: str = "com"
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
        region = (credentials.get("region") or "com").strip()

        if not all([client_id, client_secret, refresh_token, organization_id]):
            raise IntegrationAuthError(
                "client_id, client_secret, refresh_token, and organization_id are required."
            )

        access_token = await self._fetch_token(client_id, client_secret, refresh_token, region)

        # Validate the token against a lightweight endpoint
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://books.zoho.{region}/api/v3/invoices",
                headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
                params={"organization_id": organization_id, "per_page": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Zoho Books auth failed ({r.status_code}): invalid credentials."
                )
            if r.status_code not in (200, 204):
                raise RuntimeError(f"Zoho Books connect failed HTTP {r.status_code}")

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
                self._collect_invoices,
                self._collect_contacts,
                self._collect_journals,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Zoho Books collection error in %s: %s", fetch_fn.__name__, exc
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
            if t == "invoice":
                result.append(self._norm_invoice(item, now))
            elif t == "contact":
                result.append(self._norm_contact(item, now))
            elif t == "journal":
                result.append(self._norm_journal(item, now))

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
                    f"Zoho Books token refresh failed ({r.status_code})."
                )
            body = r.json()
            access_token = body.get("access_token")
            if not access_token:
                raise IntegrationAuthError(
                    "Zoho Books token refresh returned no access_token."
                )
            return access_token

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Zoho-oauthtoken {self._access_token}"}

    def _base_url(self) -> str:
        return f"https://books.zoho.{self._region}/api/v3"

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_invoices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/invoices",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Books invoices HTTP {r.status_code}")
        return [
            {"_type": "invoice", **inv}
            for inv in r.json().get("invoices", [])
        ]

    async def _collect_contacts(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/contacts",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Books contacts HTTP {r.status_code}")
        return [
            {"_type": "contact", **contact}
            for contact in r.json().get("contacts", [])
        ]

    async def _collect_journals(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base_url()}/journals",
            headers=self._auth_headers(),
            params={"organization_id": self._organization_id, "per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Zoho Books journals HTTP {r.status_code}")
        return [
            {"_type": "journal", **journal}
            for journal in r.json().get("journals", [])
        ]

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_invoice(self, raw: dict, now: str) -> dict:
        return {
            "integration": "zoho_books",
            "control": "financial_controls",
            "evidence_type": "zoho_books_invoice",
            "source_id": raw.get("invoice_id", ""),
            "timestamp": raw.get("created_time") or now,
            "data": {
                "invoice_number": raw.get("invoice_number"),
                "customer_name": raw.get("customer_name"),
                "status": raw.get("status"),
                "total": raw.get("total"),
                "currency_code": raw.get("currency_code"),
                "date": raw.get("date"),
                "due_date": raw.get("due_date"),
            },
        }

    def _norm_contact(self, raw: dict, now: str) -> dict:
        return {
            "integration": "zoho_books",
            "control": "data_protection",
            "evidence_type": "zoho_books_contact",
            "source_id": raw.get("contact_id", ""),
            "timestamp": now,
            "data": {
                "contact_name": raw.get("contact_name"),
                "company_name": raw.get("company_name"),
                "contact_type": raw.get("contact_type"),
                "email": raw.get("email"),
                "status": raw.get("status"),
            },
        }

    def _norm_journal(self, raw: dict, now: str) -> dict:
        return {
            "integration": "zoho_books",
            "control": "financial_controls",
            "evidence_type": "zoho_books_journal",
            "source_id": raw.get("journal_id", ""),
            "timestamp": raw.get("date") or now,
            "data": {
                "journal_number": raw.get("journal_number"),
                "reference_number": raw.get("reference_number"),
                "notes": raw.get("notes"),
                "total": raw.get("total"),
                "date": raw.get("date"),
                "status": raw.get("status"),
            },
        }
