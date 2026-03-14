"""
Azure Active Directory (Microsoft Entra ID) integration via Microsoft Graph API.

Credentials:
  tenant_id     — Azure AD tenant ID (GUID)
  client_id     — App registration client ID
  client_secret — App registration client secret

Required API permissions (application, not delegated):
  User.Read.All, Group.Read.All, Directory.Read.All
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_GRAPH = "https://graph.microsoft.com/v1.0"


class AzureADIntegration(IntegrationAdapter):

    def __init__(self):
        self._tenant_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    async def _get_token(self) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token",
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                    "grant_type": "client_credentials",
                },
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Azure AD client credentials")
            if r.status_code == 400:
                detail = r.json().get("error_description", "Bad request")
                raise IntegrationAuthError(f"Azure AD token error: {detail}")
            r.raise_for_status()
            return r.json()["access_token"]

    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not tenant_id or not client_id or not client_secret:
            raise IntegrationAuthError("tenant_id, client_id, and client_secret are required")

        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret

        token = await self._get_token()

        # Validate by fetching org info
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_GRAPH}/organization",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 403:
                raise IntegrationAuthError("App registration lacks required permissions (need User.Read.All, Group.Read.All)")
            r.raise_for_status()

        self._access_token = token
        return True

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}", "Accept": "application/json"}

    async def collect_evidence(self) -> list[dict]:
        self._access_token = await self._get_token()
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client)
            groups = await self._collect_groups(client)
            roles = await self._collect_roles(client)
        return users + groups + roles

    async def _paginate(self, client: httpx.AsyncClient, url: str, tag: str) -> list[dict]:
        items = []
        while url:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            data = r.json()
            for item in data.get("value", []):
                items.append({"_type": tag, **item})
            url = data.get("@odata.nextLink")
        return items

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{_GRAPH}/users"
            "?$select=id,displayName,userPrincipalName,accountEnabled,"
            "createdDateTime,lastSignInDateTime,assignedLicenses"
            "&$top=999"
        )
        return await self._paginate(client, url, "user")

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        url = f"{_GRAPH}/groups?$select=id,displayName,description,groupTypes,securityEnabled&$top=999"
        return await self._paginate(client, url, "group")

    async def _collect_roles(self, client: httpx.AsyncClient) -> list[dict]:
        # Activated directory role assignments
        url = f"{_GRAPH}/directoryRoles?$expand=members"
        r = await client.get(url, headers=self._headers())
        r.raise_for_status()
        return [{"_type": "role", **role} for role in r.json().get("value", [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "role":
                for member in item.get("members", []):
                    result.append(self._norm_role_member(item, member))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "azure_ad",
            "control": "access_control",
            "evidence_type": "azure_users",
            "source_id": raw["id"],
            "timestamp": raw.get("createdDateTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "display_name": raw.get("displayName"),
                "upn": raw.get("userPrincipalName"),
                "enabled": raw.get("accountEnabled", True),
                "last_sign_in": raw.get("lastSignInDateTime"),
                "licensed": bool(raw.get("assignedLicenses")),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "azure_ad",
            "control": "access_control",
            "evidence_type": "azure_groups",
            "source_id": raw["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "display_name": raw.get("displayName"),
                "description": raw.get("description"),
                "security_enabled": raw.get("securityEnabled", False),
                "group_types": raw.get("groupTypes", []),
            },
        }

    def _norm_role_member(self, role: dict, member: dict) -> dict:
        return {
            "integration": "azure_ad",
            "control": "access_control",
            "evidence_type": "azure_roles",
            "source_id": f"{role['id']}_{member['id']}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "role_name": role.get("displayName"),
                "role_description": role.get("description"),
                "member_id": member.get("id"),
                "member_upn": member.get("userPrincipalName"),
                "member_display_name": member.get("displayName"),
            },
        }
