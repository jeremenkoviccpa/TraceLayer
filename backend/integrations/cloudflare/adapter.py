"""
Cloudflare integration adapter.

Collects zone configuration, per-zone security settings, account details,
and account member roster from the Cloudflare v4 API.
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

CF_API = "https://api.cloudflare.com/client/v4"

# Settings keys we care about for security evidence
SECURITY_SETTING_KEYS = {
    "security_level",
    "ssl",
    "min_tls_version",
    "waf",
}


class CloudflareIntegration(IntegrationAdapter):
    """Collects network-security and access-control evidence from Cloudflare."""

    def __init__(self) -> None:
        self._token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate the API token against /user/tokens/verify."""
        api_token = (credentials.get("api_token") or "").strip()
        if not api_token:
            raise IntegrationAuthError("Cloudflare api_token is required.")

        headers = self._auth_headers(api_token)
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{CF_API}/user/tokens/verify", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Cloudflare API token.")
            r.raise_for_status()
            body = r.json()
            if body.get("result", {}).get("status") != "active":
                raise IntegrationAuthError(
                    f"Cloudflare token is not active (status: "
                    f"{body.get('result', {}).get('status')!r})."
                )

        self._token = api_token
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        headers = self._auth_headers(self._token)
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # ── Zones ──────────────────────────────────────────────────
            try:
                zones = await self._collect_zones(client, headers)
                raw.extend(zones)
            except Exception:
                logger.exception("Cloudflare: failed to collect zones")

            # ── Per-zone settings ──────────────────────────────────────
            zone_ids = [z["id"] for z in zones if z.get("_type") == "zone"]
            for zone_id in zone_ids:
                try:
                    settings = await self._collect_zone_settings(client, headers, zone_id)
                    raw.extend(settings)
                except Exception:
                    logger.exception("Cloudflare: failed to collect settings for zone %s", zone_id)

            # ── Accounts ───────────────────────────────────────────────
            try:
                accounts = await self._collect_accounts(client, headers)
                raw.extend(accounts)
            except Exception:
                logger.exception("Cloudflare: failed to collect accounts")

            # ── Members per account ────────────────────────────────────
            account_ids = [a["id"] for a in accounts if a.get("_type") == "account"]
            for account_id in account_ids:
                try:
                    members = await self._collect_members(client, headers, account_id)
                    raw.extend(members)
                except Exception:
                    logger.exception(
                        "Cloudflare: failed to collect members for account %s", account_id
                    )

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "zone":
                result.append(self._norm_zone(item, now))
            elif t == "zone_settings":
                result.append(self._norm_zone_settings(item, now))
            elif t == "member":
                result.append(self._norm_member(item, now))
            # "account" items are collected for context but not emitted as
            # separate evidence records; their data surfaces via members.

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    def _auth_headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async def _collect_zones(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        zones: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{CF_API}/zones",
                headers=headers,
                params={"per_page": 50, "page": page},
            )
            r.raise_for_status()
            body = r.json()
            results = body.get("result", [])
            if not results:
                break
            for zone in results:
                zones.append({
                    "_type": "zone",
                    "id": zone.get("id"),
                    "name": zone.get("name"),
                    "status": zone.get("status"),
                    "plan": zone.get("plan", {}).get("name"),
                    "ssl": zone.get("meta", {}).get("ssl_certificate_provisioning_count"),
                    "created_on": zone.get("created_on"),
                })
            result_info = body.get("result_info", {})
            if page >= result_info.get("total_pages", 1):
                break
            page += 1
        return zones

    async def _collect_zone_settings(
        self, client: httpx.AsyncClient, headers: dict, zone_id: str
    ) -> list[dict]:
        r = await client.get(f"{CF_API}/zones/{zone_id}/settings", headers=headers)
        r.raise_for_status()
        settings_list = r.json().get("result", [])

        # Flatten the list of setting objects into a single dict, filtered to
        # keys we care about.
        filtered: dict = {}
        for setting in settings_list:
            key = setting.get("id")
            if key in SECURITY_SETTING_KEYS:
                filtered[key] = setting.get("value")

        return [{
            "_type": "zone_settings",
            "zone_id": zone_id,
            "security_level": filtered.get("security_level"),
            "ssl": filtered.get("ssl"),
            "min_tls_version": filtered.get("min_tls_version"),
            "waf": filtered.get("waf"),
        }]

    async def _collect_accounts(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        accounts: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{CF_API}/accounts",
                headers=headers,
                params={"per_page": 50, "page": page},
            )
            r.raise_for_status()
            body = r.json()
            results = body.get("result", [])
            if not results:
                break
            for account in results:
                accounts.append({
                    "_type": "account",
                    "id": account.get("id"),
                    "name": account.get("name"),
                    "settings": account.get("settings", {}),
                    "created_on": account.get("created_on"),
                })
            result_info = body.get("result_info", {})
            if page >= result_info.get("total_pages", 1):
                break
            page += 1
        return accounts

    async def _collect_members(
        self, client: httpx.AsyncClient, headers: dict, account_id: str
    ) -> list[dict]:
        members: list[dict] = []
        page = 1
        while True:
            r = await client.get(
                f"{CF_API}/accounts/{account_id}/members",
                headers=headers,
                params={"per_page": 50, "page": page},
            )
            r.raise_for_status()
            body = r.json()
            results = body.get("result", [])
            if not results:
                break
            for m in results:
                user = m.get("user", {})
                members.append({
                    "_type": "member",
                    "id": m.get("id"),
                    "account_id": account_id,
                    "email": user.get("email"),
                    "status": m.get("status"),
                    "roles": [r_.get("name") for r_ in m.get("roles", [])],
                })
            result_info = body.get("result_info", {})
            if page >= result_info.get("total_pages", 1):
                break
            page += 1
        return members

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_zone(self, raw: dict, now: str) -> dict:
        return {
            "integration": "cloudflare",
            "control": "network_security",
            "evidence_type": "cloudflare_zones",
            "source_id": raw["id"],
            "timestamp": raw.get("created_on") or now,
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
                "plan": raw.get("plan"),
                "ssl": raw.get("ssl"),
            },
        }

    def _norm_zone_settings(self, raw: dict, now: str) -> dict:
        return {
            "integration": "cloudflare",
            "control": "network_security",
            "evidence_type": "cloudflare_security_settings",
            "source_id": f"settings_{raw['zone_id']}",
            "timestamp": now,
            "data": {
                "zone_id": raw.get("zone_id"),
                "security_level": raw.get("security_level"),
                "ssl": raw.get("ssl"),
                "min_tls_version": raw.get("min_tls_version"),
                "waf": raw.get("waf"),
            },
        }

    def _norm_member(self, raw: dict, now: str) -> dict:
        return {
            "integration": "cloudflare",
            "control": "access_control",
            "evidence_type": "cloudflare_members",
            "source_id": raw.get("id") or raw.get("email", "unknown"),
            "timestamp": now,
            "data": {
                "email": raw.get("email"),
                "status": raw.get("status"),
                "roles": raw.get("roles", []),
                "account_id": raw.get("account_id"),
            },
        }
