from __future__ import annotations

"""
New Relic integration via New Relic REST API v2 and NerdGraph.

Credentials:
  api_key    — New Relic User API key (starts with NRAK-)
  account_id — New Relic account ID
"""
import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

NR_API = "https://api.newrelic.com/v2"
NR_GRAPHQL = "https://api.newrelic.com/graphql"


class NewRelicIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None
        self._account_id: str | None = None

    def _headers(self) -> dict:
        return {
            "Api-Key": self._api_key,
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        account_id = credentials.get("account_id", "").strip()
        if not api_key or not account_id:
            raise IntegrationAuthError("api_key and account_id are required")
        self._api_key = api_key
        self._account_id = account_id
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{NR_API}/users.json",
                headers=self._headers(),
            )
            if resp.status_code == 403:
                raise IntegrationAuthError("Invalid New Relic API key")
            resp.raise_for_status()
        return True

    async def collect_evidence(self, credentials: dict) -> list[dict]:
        await self.connect(credentials)
        evidence: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Users
            resp = await client.get(f"{NR_API}/users.json", headers=self._headers())
            if resp.status_code == 200:
                for user in resp.json().get("users", []):
                    evidence.append(self.normalize(
                        resource_type="user",
                        resource_id=str(user.get("id", "")),
                        data={"email": user.get("email"), "role": user.get("role"), "last_active": user.get("last_active_at")},
                    ))

            # Alert policies
            resp = await client.get(f"{NR_API}/alerts_policies.json", headers=self._headers())
            if resp.status_code == 200:
                for policy in resp.json().get("policies", []):
                    evidence.append(self.normalize(
                        resource_type="alert_policy",
                        resource_id=str(policy.get("id", "")),
                        data={"name": policy.get("name"), "incident_preference": policy.get("incident_preference")},
                    ))

            # Notification channels
            resp = await client.get(f"{NR_API}/alerts_channels.json", headers=self._headers())
            if resp.status_code == 200:
                for channel in resp.json().get("channels", []):
                    evidence.append(self.normalize(
                        resource_type="notification_channel",
                        resource_id=str(channel.get("id", "")),
                        data={"name": channel.get("name"), "type": channel.get("type")},
                    ))

        return evidence

    def normalize(self, raw_data=None, **kwargs):
        """Satisfies abstract interface; also works as single-item builder."""
        if raw_data is not None:
            return raw_data
        from datetime import datetime, timezone
        rt = kwargs.get("resource_type", "unknown")
        control_map = {
            "user": "access_control",
            "alert_policy": "monitoring",
            "notification_channel": "monitoring",
        }
        return {
            "integration": "new_relic",
            "control": control_map.get(rt, "monitoring"),
            "evidence_type": f"new_relic_{rt}",
            "source_id": kwargs.get("resource_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": kwargs.get("data", {}),
        }
