from __future__ import annotations
"""
Auth0 integration via Auth0 Management API v2.

Credentials:
  domain        — Auth0 domain (e.g. "mycompany.auth0.com")
  client_id     — Machine-to-machine application client ID
  client_secret — Machine-to-machine application client secret
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class Auth0Integration(IntegrationAdapter):

    def __init__(self):
        self._domain: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    def _api_base(self) -> str:
        return f"https://{self._domain}/api/v2"

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        domain = credentials.get("domain", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not domain or not client_id or not client_secret:
            raise IntegrationAuthError("domain, client_id, and client_secret are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            # Obtain management API token
            token_resp = await client.post(
                f"https://{domain}/oauth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": f"https://{domain}/api/v2/",
                },
            )
            if token_resp.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Auth0 credentials.")
            if token_resp.status_code != 200:
                raise RuntimeError(f"Auth0 token request failed HTTP {token_resp.status_code}")

            access_token = token_resp.json().get("access_token", "")
            if not access_token:
                raise IntegrationAuthError("Auth0 did not return an access_token.")

            # Validate token against the users endpoint
            verify_resp = await client.get(
                f"https://{domain}/api/v2/users",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"per_page": 1, "include_totals": "true"},
            )
            if verify_resp.status_code in (401, 403):
                raise IntegrationAuthError("Auth0 management token is invalid or lacks permissions.")
            if verify_resp.status_code != 200:
                raise RuntimeError(f"Auth0 connect verification failed HTTP {verify_resp.status_code}")

        self._domain = domain
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token = access_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_connections,
                self._collect_clients,
                self._collect_rules,
                self._collect_tenant_settings,
                self._collect_mfa_policies,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Auth0 collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        for page in range(5):
            r = await client.get(
                f"{self._api_base()}/users",
                headers=self._auth_headers(),
                params={"per_page": 100, "include_totals": "true", "page": page},
            )
            if r.status_code != 200:
                raise RuntimeError(f"Auth0 users HTTP {r.status_code}")
            body = r.json()
            page_users = body.get("users", [])
            items.extend([{"_type": "user", **u} for u in page_users])
            if len(page_users) < 100:
                break
        return items

    async def _collect_connections(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api_base()}/connections",
            headers=self._auth_headers(),
            params={"per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Auth0 connections HTTP {r.status_code}")
        return [{"_type": "connection", **c} for c in r.json()]

    async def _collect_clients(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api_base()}/clients",
            headers=self._auth_headers(),
            params={"per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Auth0 clients HTTP {r.status_code}")
        return [{"_type": "client", **c} for c in r.json()]

    async def _collect_rules(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api_base()}/rules",
            headers=self._auth_headers(),
            params={"per_page": 100, "enabled": "true"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Auth0 rules HTTP {r.status_code}")
        return [{"_type": "rule", **rule} for rule in r.json()]

    async def _collect_tenant_settings(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api_base()}/tenants/settings",
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Auth0 tenant settings HTTP {r.status_code}")
        return [{"_type": "tenant_settings", **r.json()}]

    async def _collect_mfa_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._api_base()}/policies",
            headers=self._auth_headers(),
        )
        if r.status_code == 404:
            logger.info("Auth0 MFA policies endpoint not available (404); skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Auth0 MFA policies HTTP {r.status_code}")
        body = r.json()
        if isinstance(body, dict):
            body = [body]
        return [{"_type": "mfa_policy", **p} for p in body]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "connection":
                result.append(self._norm_connection(item))
            elif t == "client":
                result.append(self._norm_client(item))
            elif t == "rule":
                result.append(self._norm_rule(item))
            elif t == "tenant_settings":
                result.append(self._norm_tenant_settings(item))
            elif t == "mfa_policy":
                result.append(self._norm_mfa_policy(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_users",
            "source_id": raw.get("user_id", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "email": raw.get("email"),
                "name": raw.get("name"),
                "nickname": raw.get("nickname"),
                "email_verified": raw.get("email_verified"),
                "multifactor": raw.get("multifactor", []),
                "last_login": raw.get("last_login"),
                "logins_count": raw.get("logins_count"),
                "blocked": raw.get("blocked", False),
            },
        }

    def _norm_connection(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_connections",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or self._now(),
            "data": {
                "name": raw.get("name"),
                "strategy": raw.get("strategy"),
                "enabled_clients": raw.get("enabled_clients", []),
            },
        }

    def _norm_client(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_clients",
            "source_id": raw.get("client_id", ""),
            "timestamp": raw.get("client_id") or self._now(),
            "data": {
                "name": raw.get("name"),
                "app_type": raw.get("app_type"),
                "callbacks": raw.get("callbacks", []),
                "jwt_configuration": raw.get("jwt_configuration", {}),
                "token_endpoint_auth_method": raw.get("token_endpoint_auth_method"),
            },
        }

    def _norm_rule(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_rules",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "enabled": raw.get("enabled"),
                "stage": raw.get("stage"),
            },
        }

    def _norm_tenant_settings(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_tenant_settings",
            "source_id": "tenant",
            "timestamp": self._now(),
            "data": {
                "friendly_name": raw.get("friendly_name"),
                "support_email": raw.get("support_email"),
                "sandbox_version": raw.get("sandbox_version"),
                "mfa": raw.get("mfa", {}),
                "flags": raw.get("flags", {}),
            },
        }

    def _norm_mfa_policy(self, raw: dict) -> dict:
        return {
            "integration": "auth0",
            "control": "access_control",
            "evidence_type": "auth0_mfa_policies",
            "source_id": "mfa_policy",
            "timestamp": self._now(),
            "data": {k: v for k, v in raw.items() if k != "_type"},
        }
