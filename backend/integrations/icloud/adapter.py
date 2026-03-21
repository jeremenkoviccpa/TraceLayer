"""Apple iCloud / Apple Business Manager integration — collects managed devices and users via MDM/ABM."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

# Apple Business Manager uses OAuth 2.0 + SCIM
ABM_API = "https://mdmenrollment.apple.com"
APPLE_TOKEN_URL = "https://appleid.apple.com/auth/token"


class ICloudIntegration(IntegrationAdapter):
    """
    Apple iCloud for Business / Apple Business Manager integration.
    Uses the Apple Business Manager API (MDM enrollment + SCIM) to collect
    managed device inventory, enrolled users, and MDM enrollment records
    as evidence for asset management and mobile device compliance controls.
    """

    def __init__(self):
        self._server_token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        server_token = credentials.get("server_token", "").strip()
        if not server_token:
            raise IntegrationAuthError("Apple Business Manager server token is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{ABM_API}/session",
                headers={
                    "X-Server-Protocol-Version": "3",
                    "X-ADM-Auth-Session": server_token,
                    "Content-Type": "application/json",
                },
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Apple Business Manager server token. Ensure it has not expired.")
            r.raise_for_status()
        self._server_token = server_token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            devices = await self._collect_devices(client)
        return devices

    async def _collect_devices(self, client) -> list[dict]:
        items: list[dict] = []
        cursor: str | None = None
        while True:
            body: dict = {"limit": 200}
            if cursor:
                body["cursor"] = cursor
            r = await client.post(
                f"{ABM_API}/devices/fetch",
                headers={
                    "X-Server-Protocol-Version": "3",
                    "X-ADM-Auth-Session": self._server_token,
                    "Content-Type": "application/json",
                },
                json=body,
            )
            r.raise_for_status()
            data = r.json()
            devices = data.get("devices", [])
            items.extend([{"_type": "abm_device", **d} for d in devices])
            cursor = data.get("cursor")
            more = data.get("more_to_follow", False)
            if not more:
                break
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            if item.get("_type") == "abm_device":
                result.append(self._norm_device(item))
        return result

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "icloud",
            "control": "asset_management",
            "evidence_type": "mdm_devices",
            "source_id": raw.get("serial_number", raw.get("device_id", "unknown")),
            "timestamp": raw.get("date_assigned", datetime.now(timezone.utc).isoformat()),
            "data": {
                "serial_number": raw.get("serial_number"),
                "device_family": raw.get("device_family"),
                "model": raw.get("model"),
                "description": raw.get("description"),
                "color": raw.get("color"),
                "os": raw.get("os"),
                "profile_status": raw.get("profile_status"),
                "profile_uuid": raw.get("profile_uuid"),
                "date_assigned": raw.get("date_assigned"),
                "response_status": raw.get("response_status"),
            },
        }
