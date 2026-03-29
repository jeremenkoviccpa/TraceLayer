"""
Airtable integration adapter.

Collects table metadata, records (first 3 tables), and collaborators
from the Airtable REST API (https://api.airtable.com).
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

AIRTABLE_META_BASE = "https://api.airtable.com/v0/meta"
AIRTABLE_RECORDS_BASE = "https://api.airtable.com/v0"


class AirtableIntegration(IntegrationAdapter):
    """Collects data-management and change-management evidence from Airtable."""

    def __init__(self) -> None:
        self._personal_access_token: str | None = None
        self._base_id: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate credentials by fetching the tables metadata for the base."""
        personal_access_token = (credentials.get("personal_access_token") or "").strip()
        base_id = (credentials.get("base_id") or "").strip()

        if not personal_access_token or not base_id:
            raise IntegrationAuthError(
                "Airtable credentials require: personal_access_token and base_id."
            )

        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{AIRTABLE_META_BASE}/bases/{base_id}/tables",
                headers={"Authorization": f"Bearer {personal_access_token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid Airtable personal access token or base ID."
                )
            r.raise_for_status()

        self._personal_access_token = personal_access_token
        self._base_id = base_id
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Collect table metadata first — records collection depends on it.
            tables: list[dict] = []
            try:
                tables = await self._collect_tables(client)
                raw.extend(tables)
            except Exception as e:
                logger.exception("Airtable: failed to collect tables")
                raw.append({"_type": "error", "_source": "_collect_tables", "_error": str(e)})

            # Records for first 3 tables only.
            for table in tables[:3]:
                table_id = table.get("id", "")
                table_name = table.get("name", "")
                if not table_id:
                    continue
                try:
                    records = await self._collect_records(client, table_id, table_name)
                    raw.extend(records)
                except Exception as e:
                    logger.exception("Airtable: failed to collect records for table %s", table_id)
                    raw.append({
                        "_type": "error",
                        "_source": f"_collect_records:{table_id}",
                        "_error": str(e),
                    })

            try:
                collaborators = await self._collect_collaborators(client)
                raw.extend(collaborators)
            except Exception as e:
                logger.exception("Airtable: failed to collect collaborators")
                raw.append({"_type": "error", "_source": "_collect_collaborators", "_error": str(e)})

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "table":
                result.append(self._norm_table(item, now))
            elif t == "record":
                result.append(self._norm_record(item, now))
            elif t == "collaborator":
                result.append(self._norm_collaborator(item, now))
            # skip error records

        return result

    # ------------------------------------------------------------------
    # Private helpers — headers
    # ------------------------------------------------------------------

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._personal_access_token}"}

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    async def _collect_tables(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch all table definitions for the configured base."""
        r = await client.get(
            f"{AIRTABLE_META_BASE}/bases/{self._base_id}/tables",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        items = r.json().get("tables", [])
        for item in items:
            item["_type"] = "table"
        return items

    async def _collect_records(
        self,
        client: httpx.AsyncClient,
        table_id: str,
        table_name: str,
    ) -> list[dict]:
        """Fetch up to 50 records from a single table."""
        r = await client.get(
            f"{AIRTABLE_RECORDS_BASE}/{self._base_id}/{table_id}",
            headers=self._auth_headers(),
            params={"maxRecords": 50},
        )
        r.raise_for_status()
        records = r.json().get("records", [])
        for record in records:
            record["_type"] = "record"
            record["_table"] = table_name
        return records

    async def _collect_collaborators(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Fetch workspace collaborators via /meta/workspaces.
        The workspace list endpoint may not always be accessible; errors
        are caught by the caller and appended as error records.
        """
        r = await client.get(
            f"{AIRTABLE_META_BASE}/workspaces",
            headers=self._auth_headers(),
        )
        r.raise_for_status()
        workspaces = r.json().get("workspaces", [])
        collaborators: list[dict] = []
        for workspace in workspaces:
            for collab in workspace.get("collaborators", []):
                collab["_type"] = "collaborator"
                collaborators.append(collab)
        return collaborators

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_table(self, item: dict, now: str) -> dict:
        return {
            "integration": "airtable",
            "control": "data_management",
            "evidence_type": "airtable_table",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "id": item.get("id"),
                "name": item.get("name"),
                "description": item.get("description"),
                "field_count": len(item.get("fields", [])),
                "view_count": len(item.get("views", [])),
                "primary_field_id": item.get("primaryFieldId", ""),
            },
        }

    def _norm_record(self, item: dict, now: str) -> dict:
        return {
            "integration": "airtable",
            "control": "change_management",
            "evidence_type": "airtable_record",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdTime") or now,
            "data": {
                "id": item.get("id"),
                "table": item.get("_table", ""),
                "fields_keys": list(item.get("fields", {}).keys()),
                "createdTime": item.get("createdTime", ""),
            },
        }

    def _norm_collaborator(self, item: dict, now: str) -> dict:
        return {
            "integration": "airtable",
            "control": "access_control",
            "evidence_type": "airtable_collaborator",
            "source_id": item.get("id", ""),
            "timestamp": now,
            "data": {
                "id": item.get("id"),
                "email": item.get("email"),
                "name": item.get("name"),
                "permissionLevel": item.get("permissionLevel"),
            },
        }
