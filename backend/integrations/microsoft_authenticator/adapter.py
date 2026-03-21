"""Microsoft Authenticator MFA integration — collects MFA method registrations and policies via Microsoft Graph."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

GRAPH_API = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"


class MicrosoftAuthenticatorIntegration(IntegrationAdapter):
    """
    Microsoft Authenticator is Microsoft's MFA app. This adapter queries Microsoft Graph
    for authentication method registrations, MFA policies, and conditional access rules,
    providing dedicated evidence that Microsoft Authenticator is enforced in Entra ID.
    """

    def __init__(self):
        self._token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        if not all([tenant_id, client_id, client_secret]):
            raise IntegrationAuthError("Tenant ID, Client ID, and Client Secret are required.")
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                TOKEN_URL.format(tenant_id=tenant_id),
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError(f"Azure AD authentication failed: {r.json().get('error_description', 'invalid credentials')}")
            r.raise_for_status()
            self._token = r.json()["access_token"]
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users_mfa(client, headers)
            policies = await self._collect_auth_policies(client, headers)
            ca_policies = await self._collect_conditional_access(client, headers)
        return users + policies + ca_policies

    async def _collect_users_mfa(self, client, headers) -> list[dict]:
        """Get users with their MFA registration details."""
        items: list[dict] = []
        url = f"{GRAPH_API}/reports/authenticationMethods/userRegistrationDetails"
        params = {"$top": 200}
        while url:
            r = await client.get(url, headers=headers, params=params)
            if r.status_code == 403:
                return []  # Missing Reports.Read.All permission — non-fatal
            r.raise_for_status()
            data = r.json()
            for user in data.get("value", []):
                items.append({"_type": "ms_auth_user", **user})
            url = data.get("@odata.nextLink")
            params = {}
        return items

    async def _collect_auth_policies(self, client, headers) -> list[dict]:
        r = await client.get(f"{GRAPH_API}/policies/authenticationMethodsPolicy", headers=headers)
        if r.status_code == 403:
            return []
        r.raise_for_status()
        policy = r.json()
        items = [{"_type": "ms_auth_policy", **policy}]
        for method in policy.get("authenticationMethodConfigurations", []):
            items.append({"_type": "ms_auth_method_config", **method})
        return items

    async def _collect_conditional_access(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{GRAPH_API}/identity/conditionalAccess/policies",
            headers=headers,
            params={"$top": 100},
        )
        if r.status_code == 403:
            return []
        r.raise_for_status()
        return [{"_type": "ms_ca_policy", **p} for p in r.json().get("value", [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "ms_auth_user":
                result.append(self._norm_user(item))
            elif t == "ms_auth_policy":
                result.append(self._norm_auth_policy(item))
            elif t == "ms_auth_method_config":
                result.append(self._norm_method_config(item))
            elif t == "ms_ca_policy":
                result.append(self._norm_ca_policy(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "microsoft_authenticator",
            "control": "access_control",
            "evidence_type": "mfa_user_registrations",
            "source_id": raw["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw["id"],
                "user_principal_name": raw.get("userPrincipalName"),
                "display_name": raw.get("userDisplayName"),
                "is_mfa_registered": raw.get("isMfaRegistered", False),
                "is_mfa_capable": raw.get("isMfaCapable", False),
                "is_sspr_registered": raw.get("isSsprRegistered", False),
                "methods_registered": raw.get("methodsRegistered", []),
                "default_mfa_method": raw.get("defaultMfaMethod"),
            },
        }

    def _norm_auth_policy(self, raw: dict) -> dict:
        return {
            "integration": "microsoft_authenticator",
            "control": "access_control",
            "evidence_type": "mfa_auth_policy",
            "source_id": "authenticationMethodsPolicy",
            "timestamp": raw.get("lastModifiedDateTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw.get("id"),
                "display_name": raw.get("displayName"),
                "description": raw.get("description"),
                "policy_version": raw.get("policyVersion"),
                "registration_enforcement": raw.get("registrationEnforcement"),
            },
        }

    def _norm_method_config(self, raw: dict) -> dict:
        return {
            "integration": "microsoft_authenticator",
            "control": "access_control",
            "evidence_type": "mfa_method_configurations",
            "source_id": raw.get("id", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id"),
                "state": raw.get("state"),
                "exclude_targets": raw.get("excludeTargets", []),
                "include_targets": raw.get("includeTargets", []),
            },
        }

    def _norm_ca_policy(self, raw: dict) -> dict:
        return {
            "integration": "microsoft_authenticator",
            "control": "access_control",
            "evidence_type": "conditional_access_policies",
            "source_id": raw["id"],
            "timestamp": raw.get("modifiedDateTime", raw.get("createdDateTime", datetime.now(timezone.utc).isoformat())),
            "data": {
                "id": raw["id"],
                "display_name": raw.get("displayName"),
                "state": raw.get("state"),
                "conditions": raw.get("conditions", {}),
                "grant_controls": raw.get("grantControls"),
            },
        }
