from __future__ import annotations
"""
Ping Identity integration via PingOne API v1.

Credentials:
  environment_id — PingOne environment ID
  client_id      — OAuth2 client ID
  client_secret  — OAuth2 client secret
  region         — One of: NorthAmerica (default), Europe, AsiaPacific, Canada
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_REGION_API_BASE = {
    "NorthAmerica": "https://api.pingone.com/v1",
    "Europe": "https://api.pingone.eu/v1",
    "AsiaPacific": "https://api.pingone.asia/v1",
    "Canada": "https://api.pingone.ca/v1",
}

_REGION_AUTH_BASE = {
    "NorthAmerica": "https://auth.pingone.com",
    "Europe": "https://auth.pingone.eu",
    "AsiaPacific": "https://auth.pingone.asia",
    "Canada": "https://auth.pingone.ca",
}


class PingIdentityIntegration(IntegrationAdapter):

    def __init__(self):
        self._environment_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._region: str = "NorthAmerica"
        self._token: str | None = None
        self._api_base: str | None = None
        self._auth_base: str | None = None

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        environment_id = credentials.get("environment_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        region = credentials.get("region", "NorthAmerica").strip()

        if not environment_id or not client_id or not client_secret:
            raise IntegrationAuthError("environment_id, client_id, and client_secret are required.")

        api_base = _REGION_API_BASE.get(region, _REGION_API_BASE["NorthAmerica"])
        auth_base = _REGION_AUTH_BASE.get(region, _REGION_AUTH_BASE["NorthAmerica"])

        async with httpx.AsyncClient(timeout=15) as client:
            # Obtain access token via client_credentials grant
            token_resp = await client.post(
                f"{auth_base}/{environment_id}/as/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                },
            )
            if token_resp.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Ping Identity credentials.")
            if token_resp.status_code != 200:
                raise RuntimeError(f"Ping Identity token request failed HTTP {token_resp.status_code}")

            token = token_resp.json().get("access_token", "")
            if not token:
                raise IntegrationAuthError("Ping Identity did not return an access_token.")

            # Validate by fetching the environment
            verify_resp = await client.get(
                f"{api_base}/environments/{environment_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if verify_resp.status_code in (401, 403):
                raise IntegrationAuthError("Ping Identity token lacks required permissions.")
            if verify_resp.status_code != 200:
                raise RuntimeError(f"Ping Identity connect verification failed HTTP {verify_resp.status_code}")

        self._environment_id = environment_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._region = region
        self._token = token
        self._api_base = api_base
        self._auth_base = auth_base
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_groups,
                self._collect_applications,
                self._collect_mfa_policies,
                self._collect_password_policies,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Ping Identity collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    def _env_url(self, path: str) -> str:
        return f"{self._api_base}/environments/{self._environment_id}{path}"

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._env_url("/users"),
            headers=self._auth_headers(),
            params={"limit": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ping Identity users HTTP {r.status_code}")
        body = r.json()
        users = body.get("_embedded", {}).get("users", []) or body.get("users", [])
        return [{"_type": "user", **u} for u in users]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._env_url("/groups"),
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ping Identity groups HTTP {r.status_code}")
        groups = r.json().get("_embedded", {}).get("groups", [])
        return [{"_type": "group", **g} for g in groups]

    async def _collect_applications(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._env_url("/applications"),
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ping Identity applications HTTP {r.status_code}")
        apps = r.json().get("_embedded", {}).get("applications", [])
        return [{"_type": "application", **a} for a in apps]

    async def _collect_mfa_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._env_url("/mfaPolicies"),
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ping Identity MFA policies HTTP {r.status_code}")
        policies = r.json().get("_embedded", {}).get("mfaPolicies", [])
        return [{"_type": "mfa_policy", **p} for p in policies]

    async def _collect_password_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            self._env_url("/passwordPolicies"),
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Ping Identity password policies HTTP {r.status_code}")
        policies = r.json().get("_embedded", {}).get("passwordPolicies", [])
        return [{"_type": "password_policy", **p} for p in policies]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "application":
                result.append(self._norm_application(item))
            elif t == "mfa_policy":
                result.append(self._norm_mfa_policy(item))
            elif t == "password_policy":
                result.append(self._norm_password_policy(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        email_field = raw.get("email")
        email = (
            email_field.get("address")
            if isinstance(email_field, dict)
            else email_field
        )
        account = raw.get("account")
        account_status = (
            account.get("status")
            if isinstance(account, dict)
            else None
        )
        return {
            "integration": "ping_identity",
            "control": "access_control",
            "evidence_type": "ping_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "username": raw.get("username"),
                "email": email,
                "enabled": raw.get("enabled"),
                "mfaEnabled": raw.get("mfaEnabled"),
                "accountStatus": account_status,
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "ping_identity",
            "control": "access_control",
            "evidence_type": "ping_groups",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "userCount": raw.get("userCount"),
            },
        }

    def _norm_application(self, raw: dict) -> dict:
        return {
            "integration": "ping_identity",
            "control": "access_control",
            "evidence_type": "ping_applications",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "enabled": raw.get("enabled"),
                "protocol": raw.get("protocol"),
            },
        }

    def _norm_mfa_policy(self, raw: dict) -> dict:
        return {
            "integration": "ping_identity",
            "control": "access_control",
            "evidence_type": "ping_mfa_policies",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "default": raw.get("default"),
                "deviceSelection": raw.get("deviceSelection"),
            },
        }

    def _norm_password_policy(self, raw: dict) -> dict:
        length_field = raw.get("length", {})
        min_length = length_field.get("min") if isinstance(length_field, dict) else None
        return {
            "integration": "ping_identity",
            "control": "access_control",
            "evidence_type": "ping_password_policies",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or self._now(),
            "data": {
                "name": raw.get("name"),
                "default": raw.get("default"),
                "minCharacters": raw.get("minCharacters"),
                "length": min_length,
            },
        }
