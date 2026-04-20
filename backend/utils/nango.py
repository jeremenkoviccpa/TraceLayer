"""Nango OAuth infrastructure — token retrieval and credential building."""
import httpx

from core.config import settings

NANGO_API = "https://api.nango.dev"

# Maps our integration_type → Nango provider config key (set in Nango dashboard)
NANGO_PROVIDER_MAP: dict[str, str] = {
    "github":           "github",
    "slack":            "slack",
    "linear":           "linear",
    "notion":           "notion",
    "jira":             "jira",
    "confluence":       "confluence",
    "asana":            "asana",
    "zoom":             "zoom",
    "monday":           "monday",
    "zendesk":          "zendesk",
    "intercom":         "intercom",
    "google_workspace": "google-workspace",
    "microsoft_teams":  "microsoft-teams",
    "gitlab":           "gitlab",
    "bitbucket":        "bitbucket",
    "sentry":           "sentry",
    "snyk":             "snyk",
    "datadog":          "datadog",
    "stripe":           "stripe",
    "pagerduty":        "pagerduty",
    "shortcut":         "shortcut",
    "heroku":           "heroku",
    "opsgenie":         "opsgenie",
}

NANGO_OAUTH_TYPES: frozenset[str] = frozenset(NANGO_PROVIDER_MAP)


def is_nango_oauth(integration_type: str) -> bool:
    return integration_type in NANGO_OAUTH_TYPES


async def get_nango_token(connection_id: str, provider_config_key: str) -> str:
    """Return the current access token for a Nango connection, forcing a refresh."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{NANGO_API}/connection/{connection_id}",
            headers={"Authorization": f"Bearer {settings.nango_secret_key}"},
            params={"provider_config_key": provider_config_key, "force_refresh": "true"},
        )
        r.raise_for_status()
        creds = r.json().get("credentials", {})
        token = creds.get("access_token") or creds.get("apiKey") or creds.get("token")
        if not token:
            raise ValueError(f"No token found in Nango connection {connection_id}")
        return token


async def build_credentials(
    integration_type: str,
    connection_id: str,
    provider_config_key: str,
    extra: dict | None = None,
) -> dict:
    """Return a credentials dict suitable for the integration adapter, using a fresh Nango token."""
    token = await get_nango_token(connection_id, provider_config_key)
    base = extra or {}

    if integration_type == "slack":
        return {"bot_token": token, **base}
    if integration_type in ("linear", "notion", "jira", "confluence", "snyk", "datadog", "sentry", "stripe", "pagerduty", "opsgenie"):
        return {"api_key": token, **base}
    # github, gitlab, bitbucket, asana, zoom, monday, zendesk, intercom,
    # google_workspace, microsoft_teams, shortcut, heroku and everything else
    return {"token": token, **base}
