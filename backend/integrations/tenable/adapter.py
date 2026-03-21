from __future__ import annotations

"""
Tenable.io integration via Tenable REST API.

Credentials:
  access_key — Tenable API access key
  secret_key — Tenable API secret key
"""
import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

TENABLE_API = "https://cloud.tenable.com"


class TenableIntegration(IntegrationAdapter):

    def __init__(self):
        self._access_key: str | None = None
        self._secret_key: str | None = None

    def _headers(self) -> dict:
        return {
            "X-ApiKeys": f"accessKey={self._access_key};secretKey={self._secret_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        access_key = credentials.get("access_key", "").strip()
        secret_key = credentials.get("secret_key", "").strip()
        if not access_key or not secret_key:
            raise IntegrationAuthError("access_key and secret_key are required")
        self._access_key = access_key
        self._secret_key = secret_key
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{TENABLE_API}/session",
                headers=self._headers(),
            )
            if resp.status_code == 401:
                raise IntegrationAuthError("Invalid Tenable API keys")
            resp.raise_for_status()
        return True

    async def collect_evidence(self, credentials: dict) -> list[dict]:
        await self.connect(credentials)
        evidence: list[dict] = []

        async with httpx.AsyncClient(timeout=60) as client:
            # Scans
            resp = await client.get(f"{TENABLE_API}/scans", headers=self._headers())
            if resp.status_code == 200:
                for scan in resp.json().get("scans") or []:
                    evidence.append(self.normalize(
                        resource_type="scan",
                        resource_id=str(scan.get("id", "")),
                        data={
                            "name": scan.get("name"),
                            "status": scan.get("status"),
                            "last_modification_date": scan.get("last_modification_date"),
                            "enabled": scan.get("enabled"),
                        },
                    ))

            # Agents
            resp = await client.get(
                f"{TENABLE_API}/scanners/null/agents",
                headers=self._headers(),
                params={"limit": 200},
            )
            if resp.status_code == 200:
                for agent in resp.json().get("agents") or []:
                    evidence.append(self.normalize(
                        resource_type="agent",
                        resource_id=str(agent.get("id", "")),
                        data={
                            "name": agent.get("name"),
                            "status": agent.get("status"),
                            "platform": agent.get("platform"),
                            "last_connect": agent.get("last_connect"),
                        },
                    ))

            # Users
            resp = await client.get(f"{TENABLE_API}/users", headers=self._headers())
            if resp.status_code == 200:
                for user in resp.json().get("users") or []:
                    evidence.append(self.normalize(
                        resource_type="user",
                        resource_id=str(user.get("id", "")),
                        data={
                            "username": user.get("username"),
                            "email": user.get("email"),
                            "role": user.get("permissions"),
                            "enabled": user.get("enabled"),
                        },
                    ))

        return evidence

    def normalize(self, raw_data=None, **kwargs):
        """Satisfies abstract interface; also works as single-item builder."""
        if raw_data is not None:
            return raw_data
        from datetime import datetime, timezone
        rt = kwargs.get("resource_type", "unknown")
        control_map = {
            "scan": "vulnerability_management",
            "agent": "infrastructure_security",
            "user": "access_control",
        }
        return {
            "integration": "tenable",
            "control": control_map.get(rt, "vulnerability_management"),
            "evidence_type": f"tenable_{rt}",
            "source_id": kwargs.get("resource_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": kwargs.get("data", {}),
        }
