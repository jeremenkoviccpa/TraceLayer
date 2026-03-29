"""
Leegality integration adapter.

Collects e-signature documents, templates, and audit trail events for
legal compliance evidence.

Credentials:
  api_key — Leegality API key (passed as x-auth-token header)

API base: https://app.leegality.com/api/v1
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE_URL = "https://app.leegality.com/api/v1"
_DEFAULT_LIMIT = 100


class LeegalityIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE_URL}/account/profile",
                headers=self._build_headers(api_key),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    f"Invalid Leegality API key ({r.status_code})"
                )
            r.raise_for_status()

        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            documents = await self._collect_documents(client)
            templates = await self._collect_templates(client)
            audit_events = await self._collect_audit_trail(client)
        return documents + templates + audit_events

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "document":
                result.append(self._norm_document(item, now))
            elif t == "template":
                result.append(self._norm_template(item, now))
            elif t == "audit_event":
                result.append(self._norm_audit_event(item, now))
            else:
                logger.debug("Leegality: skipping unknown _type: %s", t)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self, api_key: str) -> dict:
        return {
            "x-auth-token": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _headers(self) -> dict:
        return self._build_headers(self._api_key)

    def _extract_list(self, body: dict | list, *keys: str) -> list:
        """
        Extract a list from a response body that may be a plain list or a
        dict with one of the given envelope keys (checked in order).
        """
        if isinstance(body, list):
            return body
        for key in keys:
            if key in body and isinstance(body[key], list):
                return body[key]
        return []

    async def _collect_documents(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_BASE_URL}/documents",
                params={"limit": _DEFAULT_LIMIT, "page": 1},
                headers=self._headers(),
            )
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "documents")
            for doc in records:
                doc["_type"] = "document"
                items.append(doc)
        except httpx.HTTPStatusError as exc:
            logger.error("Leegality: failed to collect documents: %s", exc)
            items.append({"_type": "error", "source": "documents", "detail": str(exc)})
        return items

    async def _collect_templates(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_BASE_URL}/templates",
                params={"limit": _DEFAULT_LIMIT},
                headers=self._headers(),
            )
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "templates")
            for tmpl in records:
                tmpl["_type"] = "template"
                items.append(tmpl)
        except httpx.HTTPStatusError as exc:
            logger.error("Leegality: failed to collect templates: %s", exc)
            items.append({"_type": "error", "source": "templates", "detail": str(exc)})
        return items

    async def _collect_audit_trail(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        try:
            r = await client.get(
                f"{_BASE_URL}/audit-trail",
                params={"limit": _DEFAULT_LIMIT, "page": 1},
                headers=self._headers(),
            )
            if r.status_code == 404:
                # audit-trail endpoint may not be enabled on all plans.
                logger.info("Leegality: audit-trail endpoint not available (404), skipping")
                return items
            r.raise_for_status()
            records = self._extract_list(r.json(), "data", "audit_trail", "events")
            for event in records:
                event["_type"] = "audit_event"
                items.append(event)
        except httpx.HTTPStatusError as exc:
            logger.error("Leegality: failed to collect audit trail: %s", exc)
            items.append({"_type": "error", "source": "audit_trail", "detail": str(exc)})
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_document(self, raw: dict, fallback_ts: str) -> dict:
        source_id = str(raw.get("id") or raw.get("documentId") or "")
        timestamp = (
            raw.get("createdAt")
            or raw.get("created_at")
            or raw.get("createdDate")
            or fallback_ts
        )
        # signers_count and signed_count may arrive as int or be nested.
        signers = raw.get("signers_count") or raw.get("signersCount") or raw.get("totalSigners")
        signed = raw.get("signed_count") or raw.get("signedCount") or raw.get("completedSigners")
        return {
            "integration": "leegality",
            "control": "legal_compliance",
            "evidence_type": "leegality_document",
            "source_id": source_id,
            "timestamp": timestamp,
            "data": {
                "id": raw.get("id") or raw.get("documentId"),
                "title": raw.get("title") or raw.get("name") or raw.get("fileName"),
                "status": raw.get("status"),
                "signers_count": signers,
                "signed_count": signed,
                "createdAt": raw.get("createdAt") or raw.get("created_at"),
                "completedAt": raw.get("completedAt") or raw.get("completed_at"),
                "documentType": raw.get("documentType") or raw.get("type"),
            },
        }

    def _norm_template(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "leegality",
            "control": "legal_compliance",
            "evidence_type": "leegality_template",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdAt") or raw.get("created_at") or fallback_ts,
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name") or raw.get("title"),
                "description": raw.get("description"),
                "signerFields": raw.get("signerFields") or raw.get("signer_fields"),
                "createdAt": raw.get("createdAt") or raw.get("created_at"),
            },
        }

    def _norm_audit_event(self, raw: dict, fallback_ts: str) -> dict:
        # source_id prefers a dedicated "id" field; falls back to the event
        # timestamp string so it remains unique even when id is absent.
        source_id = str(raw.get("id") or raw.get("eventId") or raw.get("timestamp") or "")
        timestamp = str(raw.get("timestamp") or raw.get("createdAt") or raw.get("eventTime") or fallback_ts)
        return {
            "integration": "leegality",
            "control": "legal_compliance",
            "evidence_type": "leegality_audit_event",
            "source_id": source_id,
            "timestamp": timestamp,
            "data": raw,
        }
