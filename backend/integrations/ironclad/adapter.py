"""
Ironclad integration adapter.

Collects workflow and signer evidence from the Ironclad Public API
(https://ironcladapp.com/public/api/v1/).
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

IRONCLAD_API_BASE = "https://ironcladapp.com/public/api/v1"


class IroncladIntegration(IntegrationAdapter):
    """Collects legal-compliance evidence from Ironclad."""

    def __init__(self) -> None:
        self._api_key: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by fetching a single workflow record."""
        api_key = (credentials.get("api_key") or "").strip()
        if not api_key:
            raise IntegrationAuthError("Ironclad api_key is required.")

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{IRONCLAD_API_BASE}/workflows",
                headers={"Authorization": f"Bearer {api_key}"},
                params={"limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Ironclad API key.")
            r.raise_for_status()

        self._api_key = api_key
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                workflows = await self._collect_workflows(client)
                raw.extend(workflows)
            except Exception as e:
                logger.exception("Ironclad: failed to collect workflows")
                raw.append({"_type": "error", "_source": "_collect_workflows", "_error": str(e)})

            try:
                executed = await self._collect_executed_workflows(client)
                raw.extend(executed)
            except Exception as e:
                logger.exception("Ironclad: failed to collect executed workflows")
                raw.append({"_type": "error", "_source": "_collect_executed_workflows", "_error": str(e)})

            try:
                signers = await self._collect_signers(client)
                raw.extend(signers)
            except Exception as e:
                logger.exception("Ironclad: failed to collect signers")
                raw.append({"_type": "error", "_source": "_collect_signers", "_error": str(e)})

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t in ("workflow", "executed_workflow"):
                result.append(self._norm_workflow(item, now))
            elif t == "signer":
                result.append(self._norm_signer(item, now))
            # skip error records

        return result

    # ------------------------------------------------------------------
    # Private helpers — headers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_workflows(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{IRONCLAD_API_BASE}/workflows",
            headers=self._auth_headers(),
            params={"limit": 50, "page": 0},
        )
        r.raise_for_status()
        body = r.json()
        items = body.get("records") or body.get("workflows") or []
        for item in items:
            item["_type"] = "workflow"
        return items

    async def _collect_executed_workflows(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{IRONCLAD_API_BASE}/workflows",
            headers=self._auth_headers(),
            params={"status": "executed", "limit": 50},
        )
        r.raise_for_status()
        body = r.json()
        items = body.get("records") or body.get("workflows") or []
        for item in items:
            item["_type"] = "executed_workflow"
        return items

    async def _collect_signers(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Fetch signers from the /signers endpoint.
        The endpoint may not be available on all plans; errors are caught
        by the caller and appended as error records.
        """
        r = await client.get(
            f"{IRONCLAD_API_BASE}/signers",
            headers=self._auth_headers(),
            params={"limit": 100},
        )
        r.raise_for_status()
        body = r.json()
        items = body.get("records") or []
        for item in items:
            item["_type"] = "signer"
        return items

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_workflow(self, item: dict, now: str) -> dict:
        return {
            "integration": "ironclad",
            "control": "legal_compliance",
            "evidence_type": "ironclad_workflow",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "type": item.get("type"),
                "status": item.get("status"),
                "creator": item.get("creator", {}).get("name", ""),
                "signerCount": len(item.get("signers", [])),
                "createdAt": item.get("createdAt"),
                "approvedAt": item.get("approvedAt"),
                "completedAt": item.get("completedAt"),
            },
        }

    def _norm_signer(self, item: dict, now: str) -> dict:
        return {
            "integration": "ironclad",
            "control": "legal_compliance",
            "evidence_type": "ironclad_signer",
            "source_id": item.get("id", ""),
            "timestamp": item.get("signedAt") or now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "email": item.get("email"),
                "role": item.get("role"),
                "signedAt": item.get("signedAt"),
                "status": item.get("status"),
            },
        }
