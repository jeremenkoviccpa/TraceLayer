"""
CrowdStrike Falcon integration via CrowdStrike Falcon API.

Credentials:
  client_id     — OAuth2 client ID
  client_secret — OAuth2 client secret
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_BASE = "https://api.crowdstrike.com"
_TOKEN_URL = f"{_BASE}/oauth2/token"


class CrowdStrikeIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _get_token(self, client_id: str, client_secret: str, client: httpx.AsyncClient) -> str:
        r = await client.post(
            _TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Accept": "application/json"},
        )
        if r.status_code in (401, 403):
            raise IntegrationAuthError("Invalid CrowdStrike client_id or client_secret")
        r.raise_for_status()
        body = r.json()
        token = body.get("access_token")
        if not token:
            raise IntegrationAuthError("CrowdStrike token response missing access_token")
        return token

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not client_id or not client_secret:
            raise IntegrationAuthError("client_id and client_secret are required")

        async with httpx.AsyncClient(timeout=15) as client:
            token = await self._get_token(client_id, client_secret, client)
            # Probe with a minimal devices query to confirm scope
            r = await client.get(
                f"{_BASE}/devices/queries/devices/v1",
                params={"limit": 1},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("CrowdStrike token rejected on devices endpoint")
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "CrowdStrike token lacks required scope (Devices:Read)"
                )
            r.raise_for_status()

        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            devices = await self._collect_devices(client)
            detections = await self._collect_detections(client)
            policies = await self._collect_policies(client)
        return devices + detections + policies

    # ------------------------------------------------------------------
    # devices
    # ------------------------------------------------------------------

    async def _collect_devices(self, client: httpx.AsyncClient) -> list[dict]:
        # Step 1: collect all device IDs (single page — CrowdStrike returns
        # up to 5000 per call; offset-paginate if needed)
        device_ids: list[str] = []
        offset = 0
        limit = 5000
        while True:
            r = await client.get(
                f"{_BASE}/devices/queries/devices/v1",
                params={"limit": limit, "offset": offset},
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            ids = body.get("resources", [])
            device_ids.extend(ids)
            meta = body.get("meta", {}).get("pagination", {})
            total = meta.get("total", 0)
            offset += len(ids)
            if not ids or offset >= total:
                break

        if not device_ids:
            return []

        # Step 2: fetch full device details in batches of 100
        devices = []
        for i in range(0, len(device_ids), 100):
            batch = device_ids[i : i + 100]
            try:
                r = await client.post(
                    f"{_BASE}/devices/entities/devices/v2",
                    json={"ids": batch},
                    headers=self._headers(),
                )
                r.raise_for_status()
                for d in r.json().get("resources", []):
                    devices.append({
                        "_type": "device",
                        "device_id": d.get("device_id"),
                        "hostname": d.get("hostname"),
                        "os_version": d.get("os_version"),
                        "platform_name": d.get("platform_name"),
                        "last_seen": d.get("last_seen"),
                        "status": d.get("status"),
                        "groups": d.get("groups", []),
                    })
            except Exception as exc:
                # Log and continue — partial evidence is better than none
                print(f"[CrowdStrike] device batch {i} failed: {exc}")
        return devices

    # ------------------------------------------------------------------
    # detections
    # ------------------------------------------------------------------

    async def _collect_detections(self, client: httpx.AsyncClient) -> list[dict]:
        detect_ids: list[str] = []
        offset = 0
        limit = 100
        while True:
            try:
                r = await client.get(
                    f"{_BASE}/detects/queries/detects/v1",
                    params={
                        "limit": limit,
                        "offset": offset,
                        "filter": "status:'new'+status:'in_progress'",
                    },
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                ids = body.get("resources", [])
                detect_ids.extend(ids)
                meta = body.get("meta", {}).get("pagination", {})
                total = meta.get("total", 0)
                offset += len(ids)
                if not ids or offset >= total:
                    break
            except Exception as exc:
                print(f"[CrowdStrike] detection query failed: {exc}")
                break

        if not detect_ids:
            return []

        detections = []
        for i in range(0, len(detect_ids), 100):
            batch = detect_ids[i : i + 100]
            try:
                r = await client.post(
                    f"{_BASE}/detects/entities/detect/summaries/v1",
                    json={"ids": batch},
                    headers=self._headers(),
                )
                r.raise_for_status()
                for d in r.json().get("resources", []):
                    detections.append({
                        "_type": "detection",
                        "device_id": d.get("device", {}).get("device_id"),
                        "created_on": d.get("created_timestamp"),
                        "status": d.get("status"),
                        "severity": d.get("max_severity_displayname"),
                        "filename": d.get("filename"),
                    })
            except Exception as exc:
                print(f"[CrowdStrike] detection batch {i} failed: {exc}")
        return detections

    # ------------------------------------------------------------------
    # prevention policies
    # ------------------------------------------------------------------

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        policies = []
        offset = 0
        limit = 100
        while True:
            try:
                r = await client.get(
                    f"{_BASE}/policy/combined/prevention/v1",
                    params={"limit": limit, "offset": offset},
                    headers=self._headers(),
                )
                r.raise_for_status()
                body = r.json()
                items = body.get("resources", [])
                for p in items:
                    policies.append({
                        "_type": "prevention_policy",
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "enabled": p.get("enabled"),
                        "platform_name": p.get("platform_name"),
                        "groups": [g.get("id") for g in p.get("groups", [])],
                    })
                meta = body.get("meta", {}).get("pagination", {})
                total = meta.get("total", 0)
                offset += len(items)
                if not items or offset >= total:
                    break
            except Exception as exc:
                print(f"[CrowdStrike] prevention policy collection failed: {exc}")
                break
        return policies

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "device":
                result.append(self._norm_device(item))
            elif t == "detection":
                result.append(self._norm_detection(item))
            elif t == "prevention_policy":
                result.append(self._norm_policy(item))
        return result

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "crowdstrike",
            "control": "endpoint_security",
            "evidence_type": "crowdstrike_devices",
            "source_id": raw.get("device_id", ""),
            "timestamp": raw.get("last_seen") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "hostname": raw.get("hostname"),
                "os_version": raw.get("os_version"),
                "platform_name": raw.get("platform_name"),
                "last_seen": raw.get("last_seen"),
                "status": raw.get("status"),
                "groups": raw.get("groups", []),
            },
        }

    def _norm_detection(self, raw: dict) -> dict:
        return {
            "integration": "crowdstrike",
            "control": "endpoint_security",
            "evidence_type": "crowdstrike_detections",
            "source_id": raw.get("device_id", "") + "_" + (raw.get("created_on") or ""),
            "timestamp": raw.get("created_on") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "device_id": raw.get("device_id"),
                "status": raw.get("status"),
                "severity": raw.get("severity"),
                "filename": raw.get("filename"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "crowdstrike",
            "control": "endpoint_security",
            "evidence_type": "crowdstrike_policies",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "platform_name": raw.get("platform_name"),
                "groups": raw.get("groups", []),
            },
        }
