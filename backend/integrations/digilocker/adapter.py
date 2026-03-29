"""
DigiLocker integration adapter.

DigiLocker is India's official document wallet, linked to Aadhaar.
Used for DPDP Act consent management and identity verification evidence.

Credentials:
  client_id     — DigiLocker OAuth2 client ID (registered app)
  client_secret — DigiLocker OAuth2 client secret
  access_token  — Pre-obtained OAuth2 bearer token. DigiLocker uses the
                  authorization_code flow; the user completes the browser
                  OAuth consent and provides the resulting access token here.
                  Re-authorize when the token expires.

Note: aadhaar_number is intentionally excluded from normalized output to
avoid storing sensitive PII in the evidence store.
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_OAUTH_BASE = "https://api.digitallocker.gov.in/public/oauth2"
_USER_BASE = f"{_OAUTH_BASE}/3"


class DigiLockerIntegration(IntegrationAdapter):

    def __init__(self):
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        access_token = credentials.get("access_token", "").strip()

        if not client_id or not client_secret or not access_token:
            raise IntegrationAuthError(
                "client_id, client_secret, and access_token are required"
            )

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_USER_BASE}/user",
                headers=self._build_headers(access_token),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid DigiLocker access token — please re-authorize"
                )
            r.raise_for_status()

        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            issued = await self._collect_issued_documents(client)
            uploaded = await self._collect_uploaded_documents(client)
            profile = await self._collect_user_profile(client)
        return issued + uploaded + profile

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "issued_document":
                result.append(self._norm_issued_document(item, now))
            elif t == "uploaded_document":
                result.append(self._norm_uploaded_document(item, now))
            elif t == "user_profile":
                result.append(self._norm_user_profile(item, now))
            else:
                logger.debug("DigiLocker: skipping unknown _type: %s", t)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _headers(self) -> dict:
        return self._build_headers(self._access_token)

    async def _collect_issued_documents(self, client: httpx.AsyncClient) -> list[dict]:
        """Documents issued to the user by government issuers."""
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_USER_BASE}/files/issued",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            # Response: {"files": [...]} or {"issued": [...]} or plain list.
            files = (
                body.get("files")
                or body.get("issued")
                or (body if isinstance(body, list) else [])
            )
            for doc in files:
                doc["_type"] = "issued_document"
                items.append(doc)
        except httpx.HTTPStatusError as exc:
            logger.error("DigiLocker: failed to collect issued documents: %s", exc)
            items.append({"_type": "error", "source": "issued_documents", "detail": str(exc)})
        return items

    async def _collect_uploaded_documents(self, client: httpx.AsyncClient) -> list[dict]:
        """Documents uploaded by the user themselves."""
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_USER_BASE}/files/uploaded",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            files = (
                body.get("files")
                or body.get("uploaded")
                or (body if isinstance(body, list) else [])
            )
            for doc in files:
                doc["_type"] = "uploaded_document"
                items.append(doc)
        except httpx.HTTPStatusError as exc:
            logger.error("DigiLocker: failed to collect uploaded documents: %s", exc)
            items.append({"_type": "error", "source": "uploaded_documents", "detail": str(exc)})
        return items

    async def _collect_user_profile(self, client: httpx.AsyncClient) -> list[dict]:
        """User profile — used as identity verification evidence."""
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_USER_BASE}/user",
                headers=self._headers(),
            )
            r.raise_for_status()
            profile = r.json()
            if isinstance(profile, dict):
                profile["_type"] = "user_profile"
                items.append(profile)
        except httpx.HTTPStatusError as exc:
            logger.error("DigiLocker: failed to collect user profile: %s", exc)
            items.append({"_type": "error", "source": "user_profile", "detail": str(exc)})
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_issued_document(self, raw: dict, fallback_ts: str) -> dict:
        # Build a composite source_id from doctype + date since DigiLocker
        # issued documents do not have a simple unique ID field.
        doctype = raw.get("doctype") or raw.get("type") or ""
        date = raw.get("date") or raw.get("issueDate") or ""
        source_id = f"{doctype}_{date}".strip("_") or fallback_ts

        return {
            "integration": "digilocker",
            "control": "identity_verification",
            "evidence_type": "digilocker_issued_document",
            "source_id": source_id,
            "timestamp": raw.get("date") or raw.get("issueDate") or fallback_ts,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "doctype": raw.get("doctype") or raw.get("type"),
                "issuer": raw.get("issuer"),
                "issuer_name": raw.get("issuer_name") or raw.get("issuerName"),
                "date": raw.get("date") or raw.get("issueDate"),
                "uri": raw.get("uri") or raw.get("url"),
                "size": raw.get("size"),
            },
        }

    def _norm_uploaded_document(self, raw: dict, fallback_ts: str) -> dict:
        name = raw.get("name") or raw.get("fileName") or ""
        date = raw.get("date") or raw.get("uploadDate") or ""
        source_id = f"{name}_{date}".strip("_") or fallback_ts

        return {
            "integration": "digilocker",
            "control": "data_protection",
            "evidence_type": "digilocker_uploaded_document",
            "source_id": source_id,
            "timestamp": raw.get("date") or raw.get("uploadDate") or fallback_ts,
            "data": {
                "name": raw.get("name") or raw.get("fileName"),
                "description": raw.get("description"),
                "date": raw.get("date") or raw.get("uploadDate"),
                "type": raw.get("type") or raw.get("doctype"),
                "size": raw.get("size"),
                "mime_type": raw.get("mime_type") or raw.get("mimeType") or raw.get("contentType"),
            },
        }

    def _norm_user_profile(self, raw: dict, fallback_ts: str) -> dict:
        source_id = str(raw.get("digilocker_id") or raw.get("id") or "profile")
        return {
            "integration": "digilocker",
            "control": "identity_verification",
            "evidence_type": "digilocker_user_profile",
            "source_id": source_id,
            "timestamp": fallback_ts,
            "data": {
                # aadhaar_number intentionally excluded — PII minimisation.
                "name": raw.get("name"),
                "dob": raw.get("dob") or raw.get("dateOfBirth"),
                "gender": raw.get("gender"),
                "eaadhaar_linked": raw.get("eaadhaar_linked") or raw.get("eAadhaarLinked"),
                "mobile": raw.get("mobile") or raw.get("phone"),
                "email": raw.get("email"),
                "reference_key": raw.get("reference_key") or raw.get("referenceKey"),
            },
        }
