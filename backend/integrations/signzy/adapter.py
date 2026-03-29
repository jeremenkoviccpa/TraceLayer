"""
Signzy integration adapter.

Collects KYC records, digital KYC sessions, and bank account verifications
for identity verification and financial controls evidence.

Credentials:
  username  — Signzy portal username (email)
  password  — Signzy portal password
  base_url  — API base URL (default: https://preproduction.signzy.tech;
               use https://api.signzy.com for production)

Auth flow:
  Signzy uses a login endpoint (/api/v2/patrons/login) that returns a patron
  id and a session token. Subsequent requests use the composite
  Authorization header: "{patron_id} {token}".
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://preproduction.signzy.tech"
_DEFAULT_LIMIT = 100


class SignzyIntegration(IntegrationAdapter):

    def __init__(self):
        self._username: str | None = None
        self._password: str | None = None
        self._base_url: str = _DEFAULT_BASE_URL
        self._patron_id: str | None = None
        self._token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()
        base_url = credentials.get("base_url", _DEFAULT_BASE_URL).strip().rstrip("/")

        if not username or not password:
            raise IntegrationAuthError("username and password are required")

        patron_id, token = await self._login(username, password, base_url)

        self._username = username
        self._password = password
        self._base_url = base_url
        self._patron_id = patron_id
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            kyc_records = await self._collect_kyc_records(client)
            digital_kycs = await self._collect_digital_kycs(client)
            bank_verifications = await self._collect_bank_verifications(client)
        return kyc_records + digital_kycs + bank_verifications

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "kyc_record":
                result.append(self._norm_kyc_record(item, now))
            elif t == "digital_kyc":
                result.append(self._norm_digital_kyc(item, now))
            elif t == "bank_verification":
                result.append(self._norm_bank_verification(item, now))
            else:
                logger.debug("Signzy: skipping unknown _type: %s", t)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {
            # Signzy composite auth: "{patron_id} {token}"
            "Authorization": f"{self._patron_id} {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _login(
        self, username: str, password: str, base_url: str
    ) -> tuple[str, str]:
        """POST /api/v2/patrons/login → returns (patron_id, token)."""
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{base_url}/api/v2/patrons/login",
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Signzy credentials")
            if r.status_code == 400:
                raise IntegrationAuthError(
                    f"Signzy login rejected (400): {r.text[:200]}"
                )
            r.raise_for_status()
            body = r.json()

            # Response may be wrapped in a "result" envelope or be flat.
            payload = body.get("result") or body if isinstance(body, dict) else {}
            patron_id = str(payload.get("id") or payload.get("patronId") or "")
            token = str(payload.get("token") or payload.get("accessToken") or "")

            if not patron_id or not token:
                raise IntegrationAuthError(
                    "Signzy login response missing id or token fields"
                )
            return patron_id, token

    def _patron_url(self, path: str) -> str:
        return f"{self._base_url}/api/v2/patrons/{self._patron_id}/{path}"

    def _extract_list(self, body: dict | list, *keys: str) -> list:
        if isinstance(body, list):
            return body
        for key in keys:
            if key in body and isinstance(body[key], list):
                return body[key]
        return []

    async def _collect_kyc_records(self, client: httpx.AsyncClient) -> list[dict]:
        """Financial / KYC records attached to this patron."""
        items: list[dict] = []
        try:
            r = await client.get(
                self._patron_url("financialrecords"),
                params={"filter[limit]": _DEFAULT_LIMIT},
                headers=self._headers(),
            )
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "financialrecords", "result")
            for rec in records:
                rec["_type"] = "kyc_record"
                items.append(rec)
        except httpx.HTTPStatusError as exc:
            logger.error("Signzy: failed to collect KYC records: %s", exc)
            items.append({"_type": "error", "source": "kyc_records", "detail": str(exc)})
        return items

    async def _collect_digital_kycs(self, client: httpx.AsyncClient) -> list[dict]:
        """Digital KYC (video KYC / eKYC) sessions."""
        items: list[dict] = []
        try:
            r = await client.get(
                self._patron_url("digitalkycs"),
                params={"filter[limit]": _DEFAULT_LIMIT},
                headers=self._headers(),
            )
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "digitalkycs", "result")
            for rec in records:
                rec["_type"] = "digital_kyc"
                items.append(rec)
        except httpx.HTTPStatusError as exc:
            logger.error("Signzy: failed to collect digital KYCs: %s", exc)
            items.append({"_type": "error", "source": "digital_kycs", "detail": str(exc)})
        return items

    async def _collect_bank_verifications(self, client: httpx.AsyncClient) -> list[dict]:
        """Bank account penny-drop / IFSC verification records."""
        items: list[dict] = []
        try:
            r = await client.get(
                self._patron_url("bankaccounts"),
                params={"filter[limit]": _DEFAULT_LIMIT},
                headers=self._headers(),
            )
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "bankaccounts", "result")
            for rec in records:
                rec["_type"] = "bank_verification"
                items.append(rec)
        except httpx.HTTPStatusError as exc:
            logger.error("Signzy: failed to collect bank verifications: %s", exc)
            items.append({"_type": "error", "source": "bank_verifications", "detail": str(exc)})
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_kyc_record(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "signzy",
            "control": "identity_verification",
            "evidence_type": "signzy_kyc_record",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdAt") or raw.get("created_at") or fallback_ts,
            "data": {
                "id": raw.get("id"),
                "type": raw.get("type") or raw.get("recordType"),
                "status": raw.get("status"),
                "verificationResult": (
                    raw.get("verificationResult")
                    or raw.get("result")
                    or raw.get("verification_result")
                ),
                "createdAt": raw.get("createdAt") or raw.get("created_at"),
                "updatedAt": raw.get("updatedAt") or raw.get("updated_at"),
            },
        }

    def _norm_digital_kyc(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "signzy",
            "control": "identity_verification",
            "evidence_type": "signzy_digital_kyc",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdAt") or raw.get("created_at") or fallback_ts,
            "data": {
                "id": raw.get("id"),
                "status": raw.get("status"),
                "videoVerified": raw.get("videoVerified") or raw.get("video_verified"),
                "aadhaarVerified": raw.get("aadhaarVerified") or raw.get("aadhaar_verified"),
                "panVerified": raw.get("panVerified") or raw.get("pan_verified"),
                "createdAt": raw.get("createdAt") or raw.get("created_at"),
            },
        }

    def _norm_bank_verification(self, raw: dict, fallback_ts: str) -> dict:
        # Mask/truncate account number — store only last 4 digits if present.
        account_number = raw.get("accountNumber") or raw.get("account_number") or ""
        if isinstance(account_number, str) and len(account_number) > 4:
            account_number = f"****{account_number[-4:]}"

        return {
            "integration": "signzy",
            "control": "financial_controls",
            "evidence_type": "signzy_bank_verification",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdAt") or raw.get("created_at") or fallback_ts,
            "data": {
                "id": raw.get("id"),
                "status": raw.get("status"),
                "accountNumber": account_number,
                "ifscCode": raw.get("ifscCode") or raw.get("ifsc_code") or raw.get("ifsc"),
                "verificationStatus": (
                    raw.get("verificationStatus")
                    or raw.get("verification_status")
                    or raw.get("bankVerificationStatus")
                ),
                "createdAt": raw.get("createdAt") or raw.get("created_at"),
            },
        }
