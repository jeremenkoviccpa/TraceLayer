"""
TallyPrime integration adapter.

Collects company info, ledger entries, and balance sheet data from the
TallyPrime REST API (typically running locally at http://localhost:9000).

Credentials:
  tally_url — Base URL for the TallyPrime REST server (default: "http://localhost:9000")
  company   — Company name to scope queries (default: "##ALL COMPANIES##")
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_DEFAULT_URL = "http://localhost:9000"
_DEFAULT_COMPANY = "##ALL COMPANIES##"
_MAX_LEDGER_ENTRIES = 200


class TallyIntegration(IntegrationAdapter):
    """Collects financial-controls evidence from TallyPrime."""

    def __init__(self) -> None:
        self._tally_url: str = _DEFAULT_URL
        self._company: str = _DEFAULT_COMPANY

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Verify connectivity to the TallyPrime REST server."""
        tally_url = (credentials.get("tally_url") or _DEFAULT_URL).rstrip("/")
        company = credentials.get("company") or _DEFAULT_COMPANY

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{tally_url}/api/4/master/company")
                if r.status_code != 200:
                    raise IntegrationAuthError(
                        f"Cannot connect to Tally — unexpected status {r.status_code}."
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise IntegrationAuthError(
                "Cannot connect to Tally — is TallyPrime running?"
            ) from exc

        self._tally_url = tally_url
        self._company = company
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_company_info,
                self._collect_ledgers,
                self._collect_balance_sheet,
            ):
                try:
                    items = await fetch_fn(client)
                    raw.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Tally collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    raw.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        ledger_count = 0
        for item in raw_data:
            t = item.get("_type")
            if t == "company_info":
                result.append(self._norm_company_info(item, now))
            elif t == "ledger":
                if ledger_count >= _MAX_LEDGER_ENTRIES:
                    continue
                result.append(self._norm_ledger(item, now))
                ledger_count += 1
            elif t == "balance_sheet":
                result.append(self._norm_balance_sheet(item, now))

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_company_info(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{self._tally_url}/api/4/master/company")
        r.raise_for_status()
        data = r.json()
        # Response may be a list or a single object
        if isinstance(data, list):
            companies = data
        else:
            companies = [data]
        items: list[dict] = []
        for company in companies:
            items.append({"_type": "company_info", **company})
        return items

    async def _collect_ledgers(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._tally_url}/api/4/master/ledger",
            params={"company": self._company},
        )
        r.raise_for_status()
        data = r.json()
        if isinstance(data, list):
            ledgers = data
        else:
            ledgers = data.get("ledgers", data.get("data", [data]))
        return [{"_type": "ledger", **entry} for entry in ledgers]

    async def _collect_balance_sheet(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._tally_url}/api/4/report/balance-sheet",
            params={"company": self._company},
        )
        r.raise_for_status()
        return [{"_type": "balance_sheet", **r.json()}]

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_company_info(self, raw: dict, now: str) -> dict:
        return {
            "integration": "tally",
            "control": "financial_controls",
            "evidence_type": "tally_company_info",
            "source_id": raw.get("name", "tally"),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "basecurrencysymbol": raw.get("basecurrencysymbol"),
                "guid": raw.get("guid"),
            },
        }

    def _norm_ledger(self, raw: dict, now: str) -> dict:
        source_id = raw.get("guid") or raw.get("name", "")
        return {
            "integration": "tally",
            "control": "financial_controls",
            "evidence_type": "tally_ledger_entry",
            "source_id": source_id,
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "openingbalance": raw.get("openingbalance"),
                "closingbalance": raw.get("closingbalance"),
                "parent": raw.get("parent"),
            },
        }

    def _norm_balance_sheet(self, raw: dict, now: str) -> dict:
        # Strip the internal _type tag before passing through as data
        data = {k: v for k, v in raw.items() if not k.startswith("_")}
        return {
            "integration": "tally",
            "control": "financial_controls",
            "evidence_type": "tally_balance_sheet",
            "source_id": "balance_sheet",
            "timestamp": now,
            "data": data,
        }
