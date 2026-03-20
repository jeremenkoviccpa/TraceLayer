"""
SentinelOne integration via SentinelOne Management API v2.1.

Credentials:
  management_url — e.g. "https://company.sentinelone.net"
  api_token      — SentinelOne API token
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class SentinelOneIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"ApiToken {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        management_url = credentials.get("management_url", "").strip().rstrip("/")
        api_token = credentials.get("api_token", "").strip()

        if not management_url or not api_token:
            raise IntegrationAuthError("management_url and api_token are required")

        if not management_url.startswith("http"):
            management_url = f"https://{management_url}"

        base = f"{management_url}/web/api/v2.1"

        async with httpx.AsyncClient(timeout=15) as client:
            headers = {
                "Authorization": f"ApiToken {api_token}",
                "Accept": "application/json",
            }
            # Probe system status — should be 200 regardless of token scope
            r = await client.get(f"{base}/system/status", headers=headers)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid SentinelOne API token")
            r.raise_for_status()

            # Probe users endpoint to confirm token has read scope
            r = await client.get(
                f"{base}/users", params={"limit": 1}, headers=headers
            )
            if r.status_code == 401:
                raise IntegrationAuthError("SentinelOne API token is invalid or expired")
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "SentinelOne API token lacks required scope (Accounts Read)"
                )
            r.raise_for_status()

        self._base = base
        self._token = api_token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            agents = await self._collect_agents(client)
            threats = await self._collect_threats(client)
            groups = await self._collect_groups(client)
            users = await self._collect_users(client)
        return agents + threats + groups + users

    # ------------------------------------------------------------------
    # agents (cursor pagination)
    # ------------------------------------------------------------------

    async def _collect_agents(self, client: httpx.AsyncClient) -> list[dict]:
        agents = []
        cursor: str | None = None
        limit = 100
        while True:
            try:
                params: dict = {"limit": limit, "isActive": "true"}
                if cursor:
                    params["cursor"] = cursor
                r = await client.get(
                    f"{self._base}/agents",
                    params=params,
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                for a in body.get("data", []):
                    agents.append({
                        "_type": "agent",
                        "id": a.get("id"),
                        "computer_name": a.get("computerName"),
                        "os_name": a.get("osName"),
                        "os_version": a.get("osRevision"),
                        "agent_version": a.get("agentVersion"),
                        "last_active_date": a.get("lastActiveDate"),
                        "is_active": a.get("isActive"),
                        "infected": a.get("infected"),
                        "is_up_to_date": a.get("isUpToDate"),
                    })
                pagination = body.get("pagination", {})
                cursor = pagination.get("nextCursor")
                if not cursor:
                    break
            except Exception as exc:
                print(f"[SentinelOne] agent collection failed: {exc}")
                break
        return agents

    # ------------------------------------------------------------------
    # threats (offset pagination)
    # ------------------------------------------------------------------

    async def _collect_threats(self, client: httpx.AsyncClient) -> list[dict]:
        threats = []
        cursor: str | None = None
        limit = 100
        while True:
            try:
                params: dict = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                r = await client.get(
                    f"{self._base}/threats",
                    params=params,
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                for t in body.get("data", []):
                    threats.append({
                        "_type": "threat",
                        "id": t.get("id"),
                        "computer_name": t.get("agentComputerName"),
                        "threat_name": t.get("threatName"),
                        "classification": t.get("classification"),
                        "mitigation_status": t.get("mitigationStatus"),
                        "created_at": t.get("createdAt"),
                        "severity": t.get("severity"),
                    })
                pagination = body.get("pagination", {})
                cursor = pagination.get("nextCursor")
                if not cursor:
                    break
            except Exception as exc:
                print(f"[SentinelOne] threat collection failed: {exc}")
                break
        return threats

    # ------------------------------------------------------------------
    # groups
    # ------------------------------------------------------------------

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        groups = []
        cursor: str | None = None
        limit = 100
        while True:
            try:
                params: dict = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                r = await client.get(
                    f"{self._base}/groups",
                    params=params,
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                for g in body.get("data", []):
                    groups.append({
                        "_type": "group",
                        "id": g.get("id"),
                        "name": g.get("name"),
                        "type": g.get("type"),
                        "total_agents": g.get("totalAgents"),
                        "registration_token": g.get("registrationToken"),
                    })
                pagination = body.get("pagination", {})
                cursor = pagination.get("nextCursor")
                if not cursor:
                    break
            except Exception as exc:
                print(f"[SentinelOne] group collection failed: {exc}")
                break
        return groups

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users = []
        cursor: str | None = None
        limit = 100
        while True:
            try:
                params: dict = {"limit": limit}
                if cursor:
                    params["cursor"] = cursor
                r = await client.get(
                    f"{self._base}/users",
                    params=params,
                    headers=self._headers(),
                )
                if r.status_code == 403:
                    # Users endpoint may be restricted — skip gracefully
                    break
                r.raise_for_status()
                body = r.json()
                for u in body.get("data", []):
                    users.append({
                        "_type": "user",
                        "id": u.get("id"),
                        "full_name": u.get("fullName"),
                        "email": u.get("email"),
                        "role_id": u.get("roleId"),
                        "last_login": u.get("lastLogin"),
                    })
                pagination = body.get("pagination", {})
                cursor = pagination.get("nextCursor")
                if not cursor:
                    break
            except Exception as exc:
                print(f"[SentinelOne] user collection failed: {exc}")
                break
        return users

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "agent":
                result.append(self._norm_agent(item))
            elif t == "threat":
                result.append(self._norm_threat(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "user":
                result.append(self._norm_user(item))
        return result

    def _norm_agent(self, raw: dict) -> dict:
        return {
            "integration": "sentinelone",
            "control": "endpoint_security",
            "evidence_type": "sentinelone_agents",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("last_active_date") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "computer_name": raw.get("computer_name"),
                "os_name": raw.get("os_name"),
                "os_version": raw.get("os_version"),
                "agent_version": raw.get("agent_version"),
                "last_active_date": raw.get("last_active_date"),
                "is_active": raw.get("is_active"),
                "infected": raw.get("infected"),
                "is_up_to_date": raw.get("is_up_to_date"),
            },
        }

    def _norm_threat(self, raw: dict) -> dict:
        return {
            "integration": "sentinelone",
            "control": "endpoint_security",
            "evidence_type": "sentinelone_threats",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "computer_name": raw.get("computer_name"),
                "threat_name": raw.get("threat_name"),
                "classification": raw.get("classification"),
                "mitigation_status": raw.get("mitigation_status"),
                "severity": raw.get("severity"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "sentinelone",
            "control": "endpoint_security",
            "evidence_type": "sentinelone_groups",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "total_agents": raw.get("total_agents"),
                "registration_token": raw.get("registration_token"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "sentinelone",
            "control": "access_control",
            "evidence_type": "sentinelone_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("last_login") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "full_name": raw.get("full_name"),
                "email": raw.get("email"),
                "role_id": raw.get("role_id"),
                "last_login": raw.get("last_login"),
            },
        }
