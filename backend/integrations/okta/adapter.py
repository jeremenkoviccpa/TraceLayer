"""
Okta integration via Okta Management API.

Credentials:
  domain    — e.g. "mycompany.okta.com"
  api_token — Okta API token (SSWS)
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class OktaIntegration(IntegrationAdapter):

    def __init__(self):
        self._base: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"SSWS {self._token}",
            "Accept": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        domain = credentials.get("domain", "").strip().rstrip("/")
        token = credentials.get("api_token", "").strip()

        if not domain or not token:
            raise IntegrationAuthError("domain and api_token are required")

        if not domain.startswith("http"):
            domain = f"https://{domain}"

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{domain}/api/v1/users/me",
                headers={"Authorization": f"SSWS {token}", "Accept": "application/json"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Okta API token")
            if r.status_code == 403:
                raise IntegrationAuthError("Okta token lacks required permissions (need Read users and groups)")
            r.raise_for_status()

        self._base = domain
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client)
            groups = await self._collect_groups(client)
            policies = await self._collect_policies(client)
        return users + groups + policies

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        users, url = [], f"{self._base}/api/v1/users?limit=200&filter=status+eq+%22ACTIVE%22"
        while url:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            for u in r.json():
                users.append({"_type": "user", **u})
            # Okta uses Link header for pagination
            link = r.headers.get("Link", "")
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.strip().split(";")[0].strip("<> ")
                    break
        return users

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        groups, url = [], f"{self._base}/api/v1/groups?limit=200"
        while url:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            for g in r.json():
                groups.append({"_type": "group", **g})
            link = r.headers.get("Link", "")
            url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    url = part.strip().split(";")[0].strip("<> ")
                    break
        return groups

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/api/v1/policies?type=PASSWORD",
            headers=self._headers(),
        )
        r.raise_for_status()
        return [{"_type": "policy", **p} for p in r.json()]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        profile = raw.get("profile", {})
        return {
            "integration": "okta",
            "control": "access_control",
            "evidence_type": "okta_users",
            "source_id": raw["id"],
            "timestamp": raw.get("created", datetime.now(timezone.utc).isoformat()),
            "data": {
                "login": profile.get("login"),
                "email": profile.get("email"),
                "first_name": profile.get("firstName"),
                "last_name": profile.get("lastName"),
                "status": raw.get("status"),
                "last_login": raw.get("lastLogin"),
                "mfa_enrolled": bool(raw.get("credentials", {}).get("provider")),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        profile = raw.get("profile", {})
        return {
            "integration": "okta",
            "control": "access_control",
            "evidence_type": "okta_groups",
            "source_id": raw["id"],
            "timestamp": raw.get("created", datetime.now(timezone.utc).isoformat()),
            "data": {
                "name": profile.get("name"),
                "description": profile.get("description"),
                "type": raw.get("type"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "okta",
            "control": "access_control",
            "evidence_type": "okta_policies",
            "source_id": raw["id"],
            "timestamp": raw.get("created", datetime.now(timezone.utc).isoformat()),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "description": raw.get("description"),
            },
        }
