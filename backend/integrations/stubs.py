"""
Stub adapters for integrations that are connected and validated but don't yet
have full evidence collectors. Each one validates credentials against the real
API so users get immediate feedback, and collect_evidence returns an empty list
until the full collector is built.
"""
import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class _StubBase(IntegrationAdapter):
    """Minimal base: collect_evidence and normalize are no-ops."""

    async def collect_evidence(self) -> list[dict]:
        return []

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        return []


# ── Vercel ────────────────────────────────────────────────────────────────────

class VercelIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("API Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://api.vercel.com/v2/user",
                            headers={"Authorization": f"Bearer {token}"})
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Vercel API token.")
            r.raise_for_status()
        return True


# ── GitLab ────────────────────────────────────────────────────────────────────

class GitLabIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("token") or credentials.get("api_token")
        if not token:
            raise IntegrationAuthError("Personal Access Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get("https://gitlab.com/api/v4/user",
                            headers={"PRIVATE-TOKEN": token})
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid GitLab token.")
            r.raise_for_status()
        return True


# ── Linear ────────────────────────────────────────────────────────────────────

class LinearIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        key = credentials.get("api_key") or credentials.get("token")
        if not key:
            raise IntegrationAuthError("API Key is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(
                "https://api.linear.app/graphql",
                json={"query": "{ viewer { id name } }"},
                headers={"Authorization": key, "Content-Type": "application/json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Linear API key.")
            r.raise_for_status()
            data = r.json()
            if "errors" in data:
                raise IntegrationAuthError(data["errors"][0].get("message", "Auth failed"))
        return True


# ── Notion ────────────────────────────────────────────────────────────────────

class NotionIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        key = credentials.get("api_key") or credentials.get("token")
        if not key:
            raise IntegrationAuthError("Integration Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.notion.com/v1/users/me",
                headers={"Authorization": f"Bearer {key}",
                         "Notion-Version": "2022-06-28"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Notion token.")
            r.raise_for_status()
        return True


# ── Cloudflare ────────────────────────────────────────────────────────────────

class CloudflareIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("API Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.cloudflare.com/client/v4/user/tokens/verify",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Cloudflare API token.")
            r.raise_for_status()
            data = r.json()
            if not data.get("success"):
                raise IntegrationAuthError("Cloudflare token verification failed.")
        return True


# ── Datadog ───────────────────────────────────────────────────────────────────

class DatadogIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key")
        app_key = credentials.get("app_key") or credentials.get("application_key", "")
        if not api_key:
            raise IntegrationAuthError("API Key is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.datadoghq.com/api/v1/validate",
                headers={"DD-API-KEY": api_key},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Datadog API key.")
            r.raise_for_status()
        return True


# ── PagerDuty ─────────────────────────────────────────────────────────────────

class PagerDutyIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("API Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.pagerduty.com/users?limit=1",
                headers={"Authorization": f"Token token={token}",
                         "Accept": "application/vnd.pagerduty+json;version=2"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid PagerDuty API token.")
            r.raise_for_status()
        return True


# ── Sentry ────────────────────────────────────────────────────────────────────

class SentryIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("auth_token") or credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("Auth Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://sentry.io/api/0/",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Sentry auth token.")
            r.raise_for_status()
        return True


# ── Stripe ────────────────────────────────────────────────────────────────────

class StripeIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        key = credentials.get("api_key") or credentials.get("secret_key") or credentials.get("token")
        if not key:
            raise IntegrationAuthError("API Key is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.stripe.com/v1/account",
                headers={"Authorization": f"Bearer {key}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Stripe API key.")
            r.raise_for_status()
        return True


# ── Terraform Cloud ───────────────────────────────────────────────────────────

class TerraformCloudIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("API Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://app.terraform.io/api/v2/account/details",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/vnd.api+json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Terraform Cloud token.")
            r.raise_for_status()
        return True


# ── 1Password ─────────────────────────────────────────────────────────────────

class OnePasswordIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("service_account_token") or credentials.get("api_token") or credentials.get("token")
        if not token:
            raise IntegrationAuthError("Service Account Token is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.1password.com/v1/vaults",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid 1Password service account token.")
            r.raise_for_status()
        return True


# ── Rippling ──────────────────────────────────────────────────────────────────

class RipplingIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        key = credentials.get("api_key") or credentials.get("token")
        if not key:
            raise IntegrationAuthError("API Key is required.")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                "https://api.rippling.com/platform/api/me",
                headers={"Authorization": f"Bearer {key}"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Rippling API key.")
            r.raise_for_status()
        return True


# ── BambooHR ──────────────────────────────────────────────────────────────────

class BambooHRIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key") or credentials.get("token")
        subdomain = credentials.get("subdomain") or credentials.get("company_domain", "")
        if not api_key:
            raise IntegrationAuthError("API Key is required.")
        if not subdomain:
            raise IntegrationAuthError("Company subdomain is required.")
        import base64
        basic = base64.b64encode(f"{api_key}:x".encode()).decode()
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(
                f"https://api.bamboohr.com/api/gateway.php/{subdomain}/v1/employees/directory",
                headers={"Authorization": f"Basic {basic}", "Accept": "application/json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid BambooHR credentials.")
            r.raise_for_status()
        return True


# ── Google Cloud ──────────────────────────────────────────────────────────────

class GoogleCloudIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        import json
        sa_json = credentials.get("service_account_json") or credentials.get("credentials_json")
        if not sa_json:
            raise IntegrationAuthError("Service Account JSON is required.")
        try:
            sa = json.loads(sa_json) if isinstance(sa_json, str) else sa_json
            if sa.get("type") != "service_account":
                raise IntegrationAuthError("JSON must be a service_account key file.")
            if not sa.get("client_email") or not sa.get("private_key"):
                raise IntegrationAuthError("Service account JSON is missing required fields.")
        except (json.JSONDecodeError, AttributeError):
            raise IntegrationAuthError("Invalid JSON format.")
        return True


# ── Microsoft Teams ───────────────────────────────────────────────────────────

class MicrosoftTeamsIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id")
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        if not all([tenant_id, client_id, client_secret]):
            raise IntegrationAuthError("Tenant ID, Client ID, and Client Secret are all required.")
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError("Invalid Microsoft credentials. Check Tenant ID, Client ID, and Secret.")
            r.raise_for_status()
            if not r.json().get("access_token"):
                raise IntegrationAuthError("Could not obtain access token.")
        return True


# ── CrowdStrike ───────────────────────────────────────────────────────────────

class CrowdStrikeIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id")
        client_secret = credentials.get("client_secret")
        if not client_id or not client_secret:
            raise IntegrationAuthError("Client ID and Client Secret are required.")
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                "https://api.crowdstrike.com/oauth2/token",
                data={"client_id": client_id, "client_secret": client_secret},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if r.status_code in (400, 401):
                raise IntegrationAuthError("Invalid CrowdStrike credentials.")
            r.raise_for_status()
            if not r.json().get("access_token"):
                raise IntegrationAuthError("Could not obtain CrowdStrike access token.")
        return True


# ── Jamf ──────────────────────────────────────────────────────────────────────

class JamfIntegration(_StubBase):
    async def connect(self, credentials: dict) -> bool:
        server_url = credentials.get("server_url", "").rstrip("/")
        username = credentials.get("username") or credentials.get("client_id")
        password = credentials.get("password") or credentials.get("client_secret")
        if not server_url:
            raise IntegrationAuthError("Jamf Pro server URL is required.")
        if not username or not password:
            raise IntegrationAuthError("Username and password are required.")
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(
                f"{server_url}/api/v1/auth/token",
                auth=(username, password),
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Jamf credentials.")
            r.raise_for_status()
        return True
