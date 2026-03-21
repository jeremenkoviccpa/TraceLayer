from integrations.base import IntegrationAdapter

# Import lazily to avoid loading all SDKs at startup
_REGISTRY: dict[str, str] = {
    # ── Fully implemented ─────────────────────────────────────────────────────
    "aws":               "integrations.aws.adapter.AWSIntegration",
    "github":            "integrations.github.adapter.GithubIntegration",
    "slack":             "integrations.slack.adapter.SlackIntegration",
    "google_workspace":  "integrations.google_workspace.adapter.GoogleWorkspaceIntegration",
    "jira":              "integrations.jira.adapter.JiraIntegration",
    "okta":              "integrations.okta.adapter.OktaIntegration",
    "azure_ad":          "integrations.azure_ad.adapter.AzureADIntegration",
    # ── Newly implemented ─────────────────────────────────────────────────────
    "gitlab":            "integrations.gitlab.adapter.GitLabIntegration",
    "linear":            "integrations.linear.adapter.LinearIntegration",
    "vercel":            "integrations.vercel.adapter.VercelIntegration",
    "datadog":           "integrations.datadog.adapter.DatadogIntegration",
    "pagerduty":         "integrations.pagerduty.adapter.PagerDutyIntegration",
    "sentry":            "integrations.sentry.adapter.SentryIntegration",
    "cloudflare":        "integrations.cloudflare.adapter.CloudflareIntegration",
    "terraform_cloud":   "integrations.terraform_cloud.adapter.TerraformCloudIntegration",
    "stripe":            "integrations.stripe.adapter.StripeIntegration",
    "1password":         "integrations.onepassword.adapter.OnePasswordIntegration",
    "rippling":          "integrations.rippling.adapter.RipplingIntegration",
    "bamboohr":          "integrations.bamboohr.adapter.BambooHRIntegration",
    "google_cloud":      "integrations.google_cloud.adapter.GoogleCloudIntegration",
    "microsoft_teams":   "integrations.microsoft_teams.adapter.MicrosoftTeamsIntegration",
    "crowdstrike":       "integrations.crowdstrike.adapter.CrowdStrikeIntegration",
    "jamf":              "integrations.jamf.adapter.JamfIntegration",
    "sentinelone":       "integrations.sentinelone.adapter.SentinelOneIntegration",
    "kandji":            "integrations.kandji.adapter.KandjiIntegration",
    "kolide":            "integrations.kolide.adapter.KolideIntegration",
    "snyk":              "integrations.snyk.adapter.SnykIntegration",
    "hackerone":         "integrations.hackerone.adapter.HackerOneIntegration",
    "wiz":               "integrations.wiz.adapter.WizIntegration",
    "splunk":            "integrations.splunk.adapter.SplunkIntegration",
    "duo":               "integrations.duo.adapter.DuoIntegration",
    "notion":            "integrations.notion.adapter.NotionIntegration",
    "confluence":        "integrations.confluence.adapter.ConfluenceIntegration",
    "servicenow":        "integrations.servicenow.adapter.ServiceNowIntegration",
    "new_relic":         "integrations.new_relic.adapter.NewRelicIntegration",
    "tenable":           "integrations.tenable.adapter.TenableIntegration",
    "vault":             "integrations.vault.adapter.VaultIntegration",
}


def get_adapter(integration_type: str) -> IntegrationAdapter:
    """Return a fresh adapter instance for the given integration type."""
    import importlib

    path = _REGISTRY.get(integration_type)
    if not path:
        raise ValueError(f"Unknown integration type: '{integration_type}'. "
                         f"Available: {list(_REGISTRY.keys())}")

    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name)
    return cls()


def available_integrations() -> list[str]:
    return list(_REGISTRY.keys())
