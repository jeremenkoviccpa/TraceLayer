from __future__ import annotations

"""
Snowflake integration via Snowflake SQL API (REST).

Credentials:
  account  — Snowflake account identifier (e.g. "xy12345.us-east-1")
  username — Snowflake login name
  password — Snowflake password
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_SESSION_PATH = "/session/v1/login-request"
_STATEMENT_PATH = "/api/v2/statements"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SnowflakeIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._account: str | None = None
        self._token: str | None = None

    def _base_url(self) -> str:
        return f"https://{self._account}.snowflakecomputing.com"

    def _auth_header(self) -> dict[str, str]:
        return {"Authorization": f'Snowflake Token="{self._token}"'}

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _rows_to_dicts(metadata: list[dict], data: list[list]) -> list[dict]:
        """Zip Snowflake resultSetMetaData.rowType column names onto each data row."""
        columns = [col["name"] for col in metadata]
        return [dict(zip(columns, row)) for row in data]

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        account = credentials.get("account", "").strip().rstrip(".")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()

        if not account or not username or not password:
            raise IntegrationAuthError("account, username, and password are required.")

        base = f"https://{account}.snowflakecomputing.com"

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"{base}{_SESSION_PATH}",
                auth=(username, password),
                json={},
                headers={"Content-Type": "application/json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Snowflake credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"Snowflake login failed HTTP {r.status_code}")

            body = r.json()
            token = body.get("data", {}).get("token")
            if not token:
                raise IntegrationAuthError("Snowflake login did not return a session token.")

        self._account = account
        self._token = token
        return True

    # ── Statement helper ───────────────────────────────────────────────────────

    async def _run_statement(self, client: httpx.AsyncClient, sql: str) -> list[dict]:
        r = await client.post(
            f"{self._base_url()}{_STATEMENT_PATH}",
            json={"statement": sql},
            headers={
                "Content-Type": "application/json",
                **self._auth_header(),
            },
        )
        if r.status_code in (401, 403):
            raise IntegrationAuthError("Snowflake token rejected while collecting evidence.")
        r.raise_for_status()
        body = r.json()
        metadata = body.get("resultSetMetaData", {}).get("rowType", [])
        data = body.get("data", [])
        return self._rows_to_dicts(metadata, data)

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_roles,
                self._collect_databases,
                self._collect_warehouses,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Snowflake collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        rows = await self._run_statement(client, "SHOW USERS")
        return [{"_type": "user", **row} for row in rows]

    async def _collect_roles(self, client: httpx.AsyncClient) -> list[dict]:
        rows = await self._run_statement(client, "SHOW ROLES")
        return [{"_type": "role", **row} for row in rows]

    async def _collect_databases(self, client: httpx.AsyncClient) -> list[dict]:
        rows = await self._run_statement(client, "SHOW DATABASES")
        return [{"_type": "database", **row} for row in rows]

    async def _collect_warehouses(self, client: httpx.AsyncClient) -> list[dict]:
        rows = await self._run_statement(client, "SHOW WAREHOUSES")
        return [{"_type": "warehouse", **row} for row in rows]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "role":
                result.append(self._norm_role(item))
            elif t == "database":
                result.append(self._norm_database(item))
            elif t == "warehouse":
                result.append(self._norm_warehouse(item))
            # skip error sentinels silently
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "snowflake",
            "control": "access_control",
            "evidence_type": "snowflake_users",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("created_on") or _now(),
            "data": {
                "name": raw.get("name"),
                "login_name": raw.get("login_name"),
                "display_name": raw.get("display_name"),
                "email": raw.get("email"),
                "disabled": raw.get("disabled"),
                "default_role": raw.get("default_role"),
                "default_warehouse": raw.get("default_warehouse"),
            },
        }

    def _norm_role(self, raw: dict) -> dict:
        return {
            "integration": "snowflake",
            "control": "access_control",
            "evidence_type": "snowflake_roles",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("created_on") or _now(),
            "data": {
                "name": raw.get("name"),
                "owner": raw.get("owner"),
                "comment": raw.get("comment"),
            },
        }

    def _norm_database(self, raw: dict) -> dict:
        return {
            "integration": "snowflake",
            "control": "data_security",
            "evidence_type": "snowflake_databases",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("created_on") or _now(),
            "data": {
                "name": raw.get("name"),
                "owner": raw.get("owner"),
                "origin": raw.get("origin"),
                "comment": raw.get("comment"),
            },
        }

    def _norm_warehouse(self, raw: dict) -> dict:
        return {
            "integration": "snowflake",
            "control": "infrastructure_security",
            "evidence_type": "snowflake_warehouses",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("created_on") or _now(),
            "data": {
                "name": raw.get("name"),
                "state": raw.get("state"),
                "type": raw.get("type"),
                "size": raw.get("size"),
                "owner": raw.get("owner"),
            },
        }
