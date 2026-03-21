"""Salesforce CRM integration — collects users, profiles, permission sets, and org security settings."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

SF_TOKEN_URL = "https://login.salesforce.com/services/oauth2/token"
SF_TOKEN_URL_SANDBOX = "https://test.salesforce.com/services/oauth2/token"


class SalesforceIntegration(IntegrationAdapter):
    def __init__(self):
        self._access_token: str | None = None
        self._instance_url: str | None = None

    async def connect(self, credentials: dict) -> bool:
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()
        security_token = credentials.get("security_token", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        is_sandbox = credentials.get("is_sandbox", "false").lower() == "true"

        if not all([username, password, client_id, client_secret]):
            raise IntegrationAuthError("Username, password, client ID, and client secret are required.")

        token_url = SF_TOKEN_URL_SANDBOX if is_sandbox else SF_TOKEN_URL
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                token_url,
                data={
                    "grant_type": "password",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "username": username,
                    "password": f"{password}{security_token}",
                },
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError(f"Salesforce authentication failed: {r.json().get('error_description', 'invalid credentials')}")
            r.raise_for_status()
            data = r.json()
            self._access_token = data["access_token"]
            self._instance_url = data["instance_url"]
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._query(client, headers, "SELECT Id,Name,Email,IsActive,ProfileId,LastLoginDate,CreatedDate FROM User WHERE IsActive=true", "sf_user")
            profiles = await self._query(client, headers, "SELECT Id,Name,UserType,Description FROM Profile", "sf_profile")
            perm_sets = await self._query(client, headers, "SELECT Id,Name,Label,IsCustom,Description FROM PermissionSet WHERE IsCustom=true", "sf_perm_set")
            org = await self._collect_org(client, headers)
        return users + profiles + perm_sets + org

    async def _query(self, client, headers, soql: str, type_tag: str) -> list[dict]:
        items: list[dict] = []
        url = f"{self._instance_url}/services/data/v59.0/query"
        params: dict = {"q": soql}
        while url:
            r = await client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            items.extend([{"_type": type_tag, **record} for record in data.get("records", [])])
            next_url = data.get("nextRecordsUrl")
            url = f"{self._instance_url}{next_url}" if next_url else None
            params = {}
        return items

    async def _collect_org(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{self._instance_url}/services/data/v59.0/query",
            headers=headers,
            params={"q": "SELECT Id,Name,Country,LanguageLocaleKey,DefaultLocaleSidKey FROM Organization"},
        )
        r.raise_for_status()
        records = r.json().get("records", [])
        return [{"_type": "sf_org", **rec} for rec in records]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "sf_user":
                result.append(self._norm_user(item))
            elif t == "sf_profile":
                result.append(self._norm_profile(item))
            elif t == "sf_perm_set":
                result.append(self._norm_perm_set(item))
            elif t == "sf_org":
                result.append(self._norm_org(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "salesforce",
            "control": "access_control",
            "evidence_type": "salesforce_users",
            "source_id": raw["Id"],
            "timestamp": raw.get("CreatedDate", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["Id"],
                "name": raw.get("Name"),
                "email": raw.get("Email"),
                "is_active": raw.get("IsActive", True),
                "profile_id": raw.get("ProfileId"),
                "last_login_date": raw.get("LastLoginDate"),
                "created_date": raw.get("CreatedDate"),
            },
        }

    def _norm_profile(self, raw: dict) -> dict:
        return {
            "integration": "salesforce",
            "control": "access_control",
            "evidence_type": "salesforce_profiles",
            "source_id": raw["Id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw["Id"],
                "name": raw.get("Name"),
                "user_type": raw.get("UserType"),
                "description": raw.get("Description"),
            },
        }

    def _norm_perm_set(self, raw: dict) -> dict:
        return {
            "integration": "salesforce",
            "control": "access_control",
            "evidence_type": "salesforce_permission_sets",
            "source_id": raw["Id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw["Id"],
                "name": raw.get("Name"),
                "label": raw.get("Label"),
                "is_custom": raw.get("IsCustom", False),
                "description": raw.get("Description"),
            },
        }

    def _norm_org(self, raw: dict) -> dict:
        return {
            "integration": "salesforce",
            "control": "data_protection",
            "evidence_type": "salesforce_org",
            "source_id": raw.get("Id", "org"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("Id"),
                "name": raw.get("Name"),
                "country": raw.get("Country"),
                "language": raw.get("LanguageLocaleKey"),
                "locale": raw.get("DefaultLocaleSidKey"),
            },
        }
