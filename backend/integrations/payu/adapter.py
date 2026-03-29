"""
PayU India integration adapter.

Collects payment transactions and merchant information from the PayU
payment gateway (India) using hash-based API authentication.

Credentials:
  merchant_key  — PayU merchant key
  merchant_salt — PayU merchant salt
  is_production — "true" for production, "false" for test (default: "false")
"""

import hashlib
import logging
from datetime import datetime, timedelta, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_PRODUCTION_URL = "https://info.payu.in"
_TEST_URL = "https://test.payu.in"
_POSTSERVICE_PATH = "/merchant/postservice.php"


def _sha512_hash(*parts: str) -> str:
    """Compute SHA-512 hex digest of pipe-joined parts."""
    return hashlib.sha512("|".join(parts).encode()).hexdigest()


class PayUIntegration(IntegrationAdapter):
    """Collects financial-controls evidence from PayU India."""

    def __init__(self) -> None:
        self._merchant_key: str | None = None
        self._merchant_salt: str | None = None
        self._is_production: bool = False
        self._api_url: str = _TEST_URL

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """
        Validate credentials by posting a verify_payment probe to PayU.
        PayU returns a data/error response (not 401) for invalid transactions,
        so any non-401/403 HTTP response is treated as a live, authenticated
        connection. Only genuine auth rejections or network failures raise
        IntegrationAuthError.
        """
        merchant_key = (credentials.get("merchant_key") or "").strip()
        merchant_salt = (credentials.get("merchant_salt") or "").strip()
        is_production_raw = str(credentials.get("is_production", "false")).lower()
        is_production = is_production_raw == "true"

        if not merchant_key or not merchant_salt:
            raise IntegrationAuthError("merchant_key and merchant_salt are required.")

        api_url = _PRODUCTION_URL if is_production else _TEST_URL

        command = "verify_payment"
        var1 = "dummy_txn_id"
        hash_value = _sha512_hash(merchant_key, command, var1, "", merchant_salt)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await client.post(
                    f"{api_url}{_POSTSERVICE_PATH}",
                    data={
                        "key": merchant_key,
                        "command": command,
                        "var1": var1,
                        "hash": hash_value,
                    },
                )
                if r.status_code in (401, 403):
                    raise IntegrationAuthError(
                        f"PayU auth rejected ({r.status_code}): check merchant_key and merchant_salt."
                    )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise IntegrationAuthError(
                f"Cannot connect to PayU at {api_url}."
            ) from exc

        self._merchant_key = merchant_key
        self._merchant_salt = merchant_salt
        self._is_production = is_production
        self._api_url = api_url
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_transactions,
                self._collect_merchant_info,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "PayU collection error in %s: %s", fetch_fn.__name__, exc
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
            if t == "transaction":
                result.append(self._norm_transaction(item, now))
            elif t == "merchant_info":
                result.append(self._norm_merchant_info(item, now))

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_transactions(self, client: httpx.AsyncClient) -> list[dict]:
        now_utc = datetime.now(timezone.utc)
        start_dt = now_utc - timedelta(days=30)
        # PayU expects date in "YYYY-MM-DD" format for var1
        var1 = start_dt.strftime("%Y-%m-%d")
        end_date = now_utc.strftime("%Y-%m-%d")

        command = "get_transaction_details"
        hash_value = _sha512_hash(self._merchant_key, command, var1, "", self._merchant_salt)

        r = await client.post(
            f"{self._api_url}{_POSTSERVICE_PATH}",
            data={
                "key": self._merchant_key,
                "command": command,
                "var1": var1,
                "var2": end_date,
                "hash": hash_value,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"PayU get_transaction_details HTTP {r.status_code}")

        body = r.json()
        # PayU wraps transactions under the date key or as a flat list
        transactions: list[dict] = []
        if isinstance(body, list):
            transactions = body
        elif isinstance(body, dict):
            for value in body.values():
                if isinstance(value, list):
                    transactions.extend(value)
                elif isinstance(value, dict):
                    transactions.append(value)

        return [{"_type": "transaction", **txn} for txn in transactions]

    async def _collect_merchant_info(self, client: httpx.AsyncClient) -> list[dict]:
        command = "get_merchant_ibibo_codes"
        var1 = self._merchant_key
        hash_value = _sha512_hash(self._merchant_key, command, var1, "", self._merchant_salt)

        r = await client.post(
            f"{self._api_url}{_POSTSERVICE_PATH}",
            data={
                "key": self._merchant_key,
                "command": command,
                "var1": var1,
                "hash": hash_value,
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"PayU get_merchant_ibibo_codes HTTP {r.status_code}")

        body = r.json()
        return [{"_type": "merchant_info", **body}]

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_transaction(self, raw: dict, now: str) -> dict:
        return {
            "integration": "payu",
            "control": "financial_controls",
            "evidence_type": "payu_transaction",
            "source_id": raw.get("mihpayid") or raw.get("txnid", ""),
            "timestamp": raw.get("addedon") or now,
            "data": {
                "txnid": raw.get("txnid"),
                "status": raw.get("status"),
                "amount": raw.get("amount"),
                "mode": raw.get("mode"),
                "productinfo": raw.get("productinfo"),
                "email": raw.get("email"),
                "mihpayid": raw.get("mihpayid"),
            },
        }

    def _norm_merchant_info(self, raw: dict, now: str) -> dict:
        data = {k: v for k, v in raw.items() if not k.startswith("_")}
        return {
            "integration": "payu",
            "control": "data_protection",
            "evidence_type": "payu_merchant_info",
            "source_id": "merchant",
            "timestamp": now,
            "data": data,
        }
