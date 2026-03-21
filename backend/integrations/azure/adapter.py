"""
Azure Infrastructure integration via Azure Resource Manager REST API.

Credentials:
  tenant_id        — Azure Active Directory tenant ID
  client_id        — Service principal / app registration client ID
  client_secret    — Service principal client secret
  subscription_id  — Target Azure subscription ID
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_ARM_BASE = "https://management.azure.com"


class AzureIntegration(IntegrationAdapter):

    def __init__(self):
        self._tenant_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._subscription_id: str | None = None
        self._access_token: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── OAuth helper ───────────────────────────────────────────────────────────

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        token_url = (
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        )
        r = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://management.azure.com/.default",
            },
        )
        if r.status_code in (401, 403):
            raise IntegrationAuthError("Azure OAuth failed — check tenant_id, client_id, client_secret.")
        if r.status_code != 200:
            raise RuntimeError(f"Azure token request failed HTTP {r.status_code}")
        body = r.json()
        token = body.get("access_token")
        if not token:
            raise IntegrationAuthError("Azure token response missing access_token.")
        return token

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        subscription_id = credentials.get("subscription_id", "").strip()

        if not all([tenant_id, client_id, client_secret, subscription_id]):
            raise IntegrationAuthError(
                "tenant_id, client_id, client_secret, and subscription_id are required."
            )

        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._subscription_id = subscription_id

        async with httpx.AsyncClient(timeout=15) as client:
            self._access_token = await self._get_token(client)

            r = await client.get(
                f"{_ARM_BASE}/subscriptions/{subscription_id}",
                headers=self._headers(),
                params={"api-version": "2020-01-01"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Azure subscription access denied — check RBAC permissions.")
            if r.status_code != 200:
                raise RuntimeError(f"Azure subscription check failed HTTP {r.status_code}")

        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_resource_groups,
                self._collect_role_assignments,
                self._collect_storage_accounts,
                self._collect_key_vaults,
                self._collect_security_contacts,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Azure collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_resource_groups(self, client: httpx.AsyncClient) -> list[dict]:
        sub = self._subscription_id
        r = await client.get(
            f"{_ARM_BASE}/subscriptions/{sub}/resourcegroups",
            headers=self._headers(),
            params={"api-version": "2021-04-01"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Azure resource groups HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "resource_group", **rg} for rg in body.get("value", [])]

    async def _collect_role_assignments(self, client: httpx.AsyncClient) -> list[dict]:
        sub = self._subscription_id
        r = await client.get(
            f"{_ARM_BASE}/subscriptions/{sub}/providers/Microsoft.Authorization/roleAssignments",
            headers=self._headers(),
            params={"api-version": "2022-04-01"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Azure role assignments HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "role_assignment", **ra} for ra in body.get("value", [])]

    async def _collect_storage_accounts(self, client: httpx.AsyncClient) -> list[dict]:
        sub = self._subscription_id
        r = await client.get(
            f"{_ARM_BASE}/subscriptions/{sub}/providers/Microsoft.Storage/storageAccounts",
            headers=self._headers(),
            params={"api-version": "2021-09-01"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Azure storage accounts HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "storage_account", **sa} for sa in body.get("value", [])]

    async def _collect_key_vaults(self, client: httpx.AsyncClient) -> list[dict]:
        sub = self._subscription_id
        r = await client.get(
            f"{_ARM_BASE}/subscriptions/{sub}/providers/Microsoft.KeyVault/vaults",
            headers=self._headers(),
            params={"api-version": "2022-07-01"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Azure key vaults HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "key_vault", **kv} for kv in body.get("value", [])]

    async def _collect_security_contacts(self, client: httpx.AsyncClient) -> list[dict]:
        sub = self._subscription_id
        r = await client.get(
            f"{_ARM_BASE}/subscriptions/{sub}/providers/Microsoft.Security/securityContacts",
            headers=self._headers(),
            params={"api-version": "2020-01-01-preview"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Azure security contacts HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "security_contact", **sc} for sc in body.get("value", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "resource_group":
                result.append(self._norm_resource_group(item))
            elif t == "role_assignment":
                result.append(self._norm_role_assignment(item))
            elif t == "storage_account":
                result.append(self._norm_storage_account(item))
            elif t == "key_vault":
                result.append(self._norm_key_vault(item))
            elif t == "security_contact":
                result.append(self._norm_security_contact(item))
        return result

    def _norm_resource_group(self, raw: dict) -> dict:
        return {
            "integration": "azure",
            "control": "cloud_infrastructure",
            "evidence_type": "azure_resource_groups",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "location": raw.get("location"),
                "provisioningState": raw.get("properties", {}).get("provisioningState"),
                "tags": raw.get("tags", {}),
            },
        }

    def _norm_role_assignment(self, raw: dict) -> dict:
        props = raw.get("properties", {})
        return {
            "integration": "azure",
            "control": "access_control",
            "evidence_type": "azure_role_assignments",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "roleDefinitionId": props.get("roleDefinitionId"),
                "principalId": props.get("principalId"),
                "principalType": props.get("principalType"),
                "scope": props.get("scope"),
            },
        }

    def _norm_storage_account(self, raw: dict) -> dict:
        props = raw.get("properties", {})
        return {
            "integration": "azure",
            "control": "cloud_infrastructure",
            "evidence_type": "azure_storage_accounts",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "location": raw.get("location"),
                "kind": raw.get("kind"),
                "httpsOnly": props.get("supportsHttpsTrafficOnly"),
                "allowBlobPublicAccess": props.get("allowBlobPublicAccess"),
                "minimumTlsVersion": props.get("minimumTlsVersion"),
            },
        }

    def _norm_key_vault(self, raw: dict) -> dict:
        props = raw.get("properties", {})
        return {
            "integration": "azure",
            "control": "access_control",
            "evidence_type": "azure_key_vaults",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "location": raw.get("location"),
                "sku": props.get("sku", {}).get("name"),
                "enableSoftDelete": props.get("enableSoftDelete"),
                "enablePurgeProtection": props.get("enablePurgeProtection"),
            },
        }

    def _norm_security_contact(self, raw: dict) -> dict:
        props = raw.get("properties", {})
        return {
            "integration": "azure",
            "control": "logging_monitoring",
            "evidence_type": "azure_security_contacts",
            "source_id": str(raw.get("id", "security_contacts")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": props.get("email"),
                "phone": props.get("phone"),
                "alertNotifications": props.get("alertNotifications"),
                "alertsToAdmins": props.get("alertsToAdmins"),
            },
        }
