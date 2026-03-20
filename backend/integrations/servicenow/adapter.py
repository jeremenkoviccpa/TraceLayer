"""
ServiceNow integration via REST Table API.
Credentials: { "instance": "company", "username": "xxx", "password": "xxx" }
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class ServiceNowIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._auth: tuple | None = None

    async def connect(self, credentials: dict) -> bool:
        instance = credentials.get("instance", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()
        if not instance or not username or not password:
            raise IntegrationAuthError("instance, username, and password are required")
        if not instance.startswith("http"):
            instance = f"https://{instance}.service-now.com"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{instance}/api/now/table/sys_user",
                auth=(username, password),
                headers={"Accept": "application/json"},
                params={"sysparm_limit": 1},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid ServiceNow credentials")
            r.raise_for_status()
        self._base = f"{instance}/api/now"
        self._auth = (username, password)
        return True

    async def collect_evidence(self) -> list[dict]:
        results = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                results += await self._collect_table(client, "incident",
                    "sys_id,number,short_description,state,priority,severity,opened_at,resolved_at,category")
            except Exception:
                pass
            try:
                results += await self._collect_table(client, "change_request",
                    "sys_id,number,short_description,state,type,risk,priority,start_date,end_date")
            except Exception:
                pass
            try:
                results += await self._collect_table(client, "sys_user",
                    "sys_id,user_name,email,active,last_login_time,title,department")
            except Exception:
                pass
        return results

    async def _collect_table(self, client: httpx.AsyncClient, table: str, fields: str) -> list[dict]:
        items, offset = [], 0
        limit = 100
        while True:
            r = await client.get(
                f"{self._base}/table/{table}",
                auth=self._auth,
                headers={"Accept": "application/json"},
                params={"sysparm_limit": limit, "sysparm_offset": offset, "sysparm_fields": fields},
            )
            r.raise_for_status()
            batch = r.json().get("result", [])
            for item in batch:
                items.append({"_type": table, **item})
            if len(batch) < limit:
                break
            offset += limit
            if offset > 1000:  # cap
                break
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "incident":
                result.append({
                    "integration": "servicenow",
                    "control": "logging_monitoring",
                    "evidence_type": "servicenow_incidents",
                    "source_id": item.get("sys_id", item.get("number", "")),
                    "timestamp": item.get("opened_at", now),
                    "data": {
                        "number": item.get("number"),
                        "description": item.get("short_description"),
                        "state": item.get("state"),
                        "priority": item.get("priority"),
                        "severity": item.get("severity"),
                        "category": item.get("category"),
                        "opened_at": item.get("opened_at"),
                        "resolved_at": item.get("resolved_at"),
                    },
                })
            elif t == "change_request":
                result.append({
                    "integration": "servicenow",
                    "control": "change_management",
                    "evidence_type": "servicenow_changes",
                    "source_id": item.get("sys_id", item.get("number", "")),
                    "timestamp": item.get("start_date", now),
                    "data": {
                        "number": item.get("number"),
                        "description": item.get("short_description"),
                        "state": item.get("state"),
                        "type": item.get("type"),
                        "risk": item.get("risk"),
                        "priority": item.get("priority"),
                        "start_date": item.get("start_date"),
                        "end_date": item.get("end_date"),
                    },
                })
            elif t == "sys_user":
                result.append({
                    "integration": "servicenow",
                    "control": "access_control",
                    "evidence_type": "servicenow_users",
                    "source_id": item.get("sys_id", item.get("user_name", "")),
                    "timestamp": now,
                    "data": {
                        "username": item.get("user_name"),
                        "email": item.get("email"),
                        "active": item.get("active"),
                        "title": item.get("title"),
                        "department": item.get("department"),
                        "last_login": item.get("last_login_time"),
                    },
                })
        return result
