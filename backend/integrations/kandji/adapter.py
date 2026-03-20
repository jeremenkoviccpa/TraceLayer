"""
Kandji integration via Kandji API v1.

Credentials:
  subdomain — e.g. "company" (resolves to company.api.kandji.io)
  api_token — Kandji API token
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class KandjiIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        subdomain = credentials.get("subdomain", "").strip().rstrip("/")
        api_token = credentials.get("api_token", "").strip()

        if not subdomain or not api_token:
            raise IntegrationAuthError("subdomain and api_token are required")

        base = f"https://{subdomain}.api.kandji.io/api/v1"

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{base}/devices",
                params={"limit": 1},
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Accept": "application/json",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Kandji API token")
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "Kandji API token lacks required permissions (Devices:Read)"
                )
            r.raise_for_status()

        self._base = base
        self._token = api_token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            devices = await self._collect_devices(client)
            blueprints = await self._collect_blueprints(client)
            library_items = await self._collect_library_items(client)
        return devices + blueprints + library_items

    # ------------------------------------------------------------------
    # devices (offset / limit pagination via next URL in response)
    # ------------------------------------------------------------------

    async def _collect_devices(self, client: httpx.AsyncClient) -> list[dict]:
        devices = []
        limit = 300
        offset = 0
        while True:
            try:
                r = await client.get(
                    f"{self._base}/devices",
                    params={"limit": limit, "offset": offset},
                    headers=self._headers(),
                )
                r.raise_for_status()
                # Kandji returns a list directly or {"results": [...], "count": n}
                body = r.json()
                items = body.get("results", body) if isinstance(body, dict) else body
                if not items:
                    break
                for d in items:
                    devices.append({
                        "_type": "device",
                        "device_id": d.get("device_id"),
                        "device_name": d.get("device_name"),
                        "serial_number": d.get("serial_number"),
                        "os_version": d.get("os_version"),
                        "platform": d.get("platform"),
                        "last_check_in": d.get("last_check_in"),
                        "blueprint_name": d.get("blueprint_name"),
                        "asset_tag": d.get("asset_tag"),
                    })
                if len(items) < limit:
                    break
                offset += len(items)
            except Exception as exc:
                print(f"[Kandji] device collection offset {offset} failed: {exc}")
                break
        return devices

    # ------------------------------------------------------------------
    # blueprints
    # ------------------------------------------------------------------

    async def _collect_blueprints(self, client: httpx.AsyncClient) -> list[dict]:
        blueprints = []
        try:
            r = await client.get(
                f"{self._base}/blueprints",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            items = body.get("results", body) if isinstance(body, dict) else body
            for b in items:
                blueprints.append({
                    "_type": "blueprint",
                    "id": b.get("id"),
                    "name": b.get("name"),
                    "computers_count": b.get("computers_count"),
                })
        except Exception as exc:
            print(f"[Kandji] blueprint collection failed: {exc}")
        return blueprints

    # ------------------------------------------------------------------
    # library items
    # ------------------------------------------------------------------

    async def _collect_library_items(self, client: httpx.AsyncClient) -> list[dict]:
        library_items = []
        try:
            r = await client.get(
                f"{self._base}/library/library-items",
                headers=self._headers(),
            )
            r.raise_for_status()
            body = r.json()
            items = body.get("results", body) if isinstance(body, dict) else body
            for item in items:
                library_items.append({
                    "_type": "library_item",
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "type": item.get("type"),
                    "active": item.get("active"),
                })
        except Exception as exc:
            print(f"[Kandji] library item collection failed: {exc}")
        return library_items

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "device":
                result.append(self._norm_device(item))
            elif t == "blueprint":
                result.append(self._norm_blueprint(item))
            elif t == "library_item":
                result.append(self._norm_library_item(item))
        return result

    def _norm_device(self, raw: dict) -> dict:
        return {
            "integration": "kandji",
            "control": "endpoint_security",
            "evidence_type": "kandji_devices",
            "source_id": raw.get("device_id", ""),
            "timestamp": raw.get("last_check_in") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "device_name": raw.get("device_name"),
                "serial_number": raw.get("serial_number"),
                "os_version": raw.get("os_version"),
                "platform": raw.get("platform"),
                "last_check_in": raw.get("last_check_in"),
                "blueprint_name": raw.get("blueprint_name"),
                "asset_tag": raw.get("asset_tag"),
            },
        }

    def _norm_blueprint(self, raw: dict) -> dict:
        return {
            "integration": "kandji",
            "control": "endpoint_security",
            "evidence_type": "kandji_blueprints",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "computers_count": raw.get("computers_count"),
            },
        }

    def _norm_library_item(self, raw: dict) -> dict:
        return {
            "integration": "kandji",
            "control": "endpoint_security",
            "evidence_type": "kandji_library_items",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "active": raw.get("active"),
            },
        }
