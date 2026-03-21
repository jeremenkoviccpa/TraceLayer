"""
DigitalOcean integration via DigitalOcean REST API v2.

Credentials:
  api_token — DigitalOcean personal access token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.digitalocean.com/v2"


class DigitalOceanIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/account",
                headers={"Authorization": f"Bearer {api_token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid DigitalOcean API token.")
            if r.status_code != 200:
                raise RuntimeError(f"DigitalOcean connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_droplets,
                self._collect_team_members,
                self._collect_firewalls,
                self._collect_databases,
                self._collect_spaces,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "DigitalOcean collection error in %s: %s",
                        fetch_fn.__name__,
                        exc,
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_droplets(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        url: str | None = f"{_BASE}/droplets"
        params = {"per_page": 200}

        while url:
            r = await client.get(url, headers=self._headers(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"DigitalOcean droplets HTTP {r.status_code}")
            body = r.json()
            for d in body.get("droplets", []):
                items.append({"_type": "droplet", **d})
            # Pagination: next URL is a full URL in body["links"]["pages"]["next"]
            next_url = body.get("links", {}).get("pages", {}).get("next")
            url = next_url
            params = {}  # next URL already contains query params

        return items

    async def _collect_team_members(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/teams/members", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"DigitalOcean team members HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "team_member", **m} for m in body.get("members", [])]

    async def _collect_firewalls(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/firewalls", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"DigitalOcean firewalls HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "firewall", **f} for f in body.get("firewalls", [])]

    async def _collect_databases(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/databases", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"DigitalOcean databases HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "database", **db} for db in body.get("databases", [])]

    async def _collect_spaces(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/spaces", headers=self._headers())
        if r.status_code == 404:
            logger.info("DigitalOcean Spaces endpoint not available, skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"DigitalOcean spaces HTTP {r.status_code}")
        body = r.json()
        buckets = body if isinstance(body, list) else body.get("spaces", body.get("buckets", []))
        return [{"_type": "space", **s} for s in buckets]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "droplet":
                result.append(self._norm_droplet(item, now))
            elif t == "team_member":
                result.append(self._norm_team_member(item, now))
            elif t == "firewall":
                result.append(self._norm_firewall(item, now))
            elif t == "database":
                result.append(self._norm_database(item, now))
        return result

    def _norm_droplet(self, raw: dict, now: str) -> dict:
        return {
            "integration": "digitalocean",
            "control": "cloud_infrastructure",
            "evidence_type": "digitalocean_droplets",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "region": raw.get("region", {}).get("slug"),
                "size": raw.get("size_slug"),
                "status": raw.get("status"),
                "image": raw.get("image", {}).get("slug"),
                "vcpus": raw.get("vcpus"),
                "memory": raw.get("memory"),
                "disk": raw.get("disk"),
            },
        }

    def _norm_team_member(self, raw: dict, now: str) -> dict:
        return {
            "integration": "digitalocean",
            "control": "access_control",
            "evidence_type": "digitalocean_team_members",
            "source_id": raw.get("uuid", ""),
            "timestamp": now,
            "data": {
                "email": raw.get("email"),
                "roles": raw.get("roles", []),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_firewall(self, raw: dict, now: str) -> dict:
        return {
            "integration": "digitalocean",
            "control": "network_security",
            "evidence_type": "digitalocean_firewalls",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
                "inbound_rules": raw.get("inbound_rules", []),
                "outbound_rules": raw.get("outbound_rules", []),
                "droplet_ids": raw.get("droplet_ids", []),
            },
        }

    def _norm_database(self, raw: dict, now: str) -> dict:
        return {
            "integration": "digitalocean",
            "control": "cloud_infrastructure",
            "evidence_type": "digitalocean_databases",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "engine": raw.get("engine"),
                "version": raw.get("version"),
                "status": raw.get("status"),
                "region": raw.get("region"),
                "size": raw.get("size"),
                "num_nodes": raw.get("num_nodes"),
            },
        }
