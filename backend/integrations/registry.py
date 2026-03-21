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
    # ── New batch ─────────────────────────────────────────────────────────────
    "jumpcloud":         "integrations.jumpcloud.adapter.JumpCloudIntegration",
    "bitbucket":         "integrations.bitbucket.adapter.BitbucketIntegration",
    "zendesk":           "integrations.zendesk.adapter.ZendeskIntegration",
    "kubernetes":        "integrations.kubernetes.adapter.KubernetesIntegration",
    "circleci":          "integrations.circleci.adapter.CircleCIIntegration",
    "qualys":            "integrations.qualys.adapter.QualysIntegration",
    # ── Identity & Access ─────────────────────────────────────────────────────
    "tailscale":         "integrations.tailscale.adapter.TailscaleIntegration",
    "bitwarden":         "integrations.bitwarden.adapter.BitwardenIntegration",
    "lastpass":          "integrations.lastpass.adapter.LastPassIntegration",
    # ── Cloud Infrastructure ──────────────────────────────────────────────────
    "azure":             "integrations.azure.adapter.AzureIntegration",
    "digitalocean":      "integrations.digitalocean.adapter.DigitalOceanIntegration",
    "heroku":            "integrations.heroku.adapter.HerokuIntegration",
    # ── Project Management ────────────────────────────────────────────────────
    "asana":             "integrations.asana.adapter.AsanaIntegration",
    "monday":            "integrations.monday.adapter.MondayIntegration",
    "shortcut":          "integrations.shortcut.adapter.ShortcutIntegration",
    # ── Communication ─────────────────────────────────────────────────────────
    "zoom":              "integrations.zoom.adapter.ZoomIntegration",
    "intercom":          "integrations.intercom.adapter.IntercomIntegration",
    # ── Monitoring & Security ─────────────────────────────────────────────────
    "detectify":         "integrations.detectify.adapter.DetectifyIntegration",
    "nightfall":         "integrations.nightfall.adapter.NightfallIntegration",
    "opsgenie":          "integrations.opsgenie.adapter.OpsgenieIntegration",
    # ── HR & People ───────────────────────────────────────────────────────────
    "checkr":            "integrations.checkr.adapter.CheckrIntegration",
    "lattice":           "integrations.lattice.adapter.LatticeIntegration",
    "trainual":          "integrations.trainual.adapter.TrainualIntegration",
    "greenhouse":        "integrations.greenhouse.adapter.GreenhouseIntegration",
    "hibob":             "integrations.hibob.adapter.HiBobIntegration",
    "personio":          "integrations.personio.adapter.PersonioIntegration",
    "deel":              "integrations.deel.adapter.DeelIntegration",
    "remote":            "integrations.remote.adapter.RemoteIntegration",
    # ── CI/CD & DevOps ────────────────────────────────────────────────────────
    "jenkins":           "integrations.jenkins.adapter.JenkinsIntegration",
    "azure_devops":      "integrations.azure_devops.adapter.AzureDevOpsIntegration",
    "argocd":            "integrations.argocd.adapter.ArgoCDIntegration",
    "elastic":           "integrations.elastic.adapter.ElasticIntegration",
    # ── Identity & Access (extended) ──────────────────────────────────────────
    "auth0":             "integrations.auth0.adapter.Auth0Integration",
    "doppler":           "integrations.doppler.adapter.DopplerIntegration",
    "ping_identity":     "integrations.ping_identity.adapter.PingIdentityIntegration",
    "zscaler":           "integrations.zscaler.adapter.ZscalerIntegration",
    # ── Cloud Infrastructure (extended) ───────────────────────────────────────
    "render":            "integrations.render.adapter.RenderIntegration",
    "flyio":             "integrations.flyio.adapter.FlyioIntegration",
    "netlify":           "integrations.netlify.adapter.NetlifyIntegration",
    "oracle_cloud":      "integrations.oracle_cloud.adapter.OracleCloudIntegration",
    # ── Project Management (extended) ─────────────────────────────────────────
    "clickup":           "integrations.clickup.adapter.ClickUpIntegration",
    "trello":            "integrations.trello.adapter.TrelloIntegration",
    # ── Monitoring & Security (extended) ──────────────────────────────────────
    "microsoft_sentinel":"integrations.microsoft_sentinel.adapter.MicrosoftSentinelIntegration",
    "grafana":           "integrations.grafana.adapter.GrafanaIntegration",
    "graylog":           "integrations.graylog.adapter.GraylogIntegration",
    "veracode":          "integrations.veracode.adapter.VeracodeIntegration",
    "aquasec":           "integrations.aquasec.adapter.AquasecIntegration",
    "bugcrowd":          "integrations.bugcrowd.adapter.BugcrowdIntegration",
    "stackhawk":         "integrations.stackhawk.adapter.StackHawkIntegration",
    "betteruptime":      "integrations.betteruptime.adapter.BetterUptimeIntegration",
    # ── Data & Analytics ──────────────────────────────────────────────────────
    "snowflake":         "integrations.snowflake.adapter.SnowflakeIntegration",
    "databricks":        "integrations.databricks.adapter.DatabricksIntegration",
    "google_analytics":  "integrations.google_analytics.adapter.GoogleAnalyticsIntegration",
    # ── Time Tracking ─────────────────────────────────────────────────────────
    "harvest":           "integrations.harvest.adapter.HarvestIntegration",
    # ── Communication & Meetings ──────────────────────────────────────────────
    "webex":             "integrations.webex.adapter.WebExIntegration",
    # ── Data Security ─────────────────────────────────────────────────────────
    "metomic":           "integrations.metomic.adapter.MetomicIntegration",
    # ── MFA & Authentication ──────────────────────────────────────────────────
    "okta_verify":               "integrations.okta_verify.adapter.OktaVerifyIntegration",
    "microsoft_authenticator":   "integrations.microsoft_authenticator.adapter.MicrosoftAuthenticatorIntegration",
    "google_authenticator":      "integrations.google_authenticator.adapter.GoogleAuthenticatorIntegration",
    # ── Security Awareness Training ────────────────────────────────────────────
    "knowbe4":           "integrations.knowbe4.adapter.KnowBe4Integration",
    "360learning":       "integrations.learning_360.adapter.Learning360Integration",
    # ── HR & Recruiting ───────────────────────────────────────────────────────
    "lever":             "integrations.lever.adapter.LeverIntegration",
    # ── Technical Assessments ─────────────────────────────────────────────────
    "hackerrank":        "integrations.hackerrank.adapter.HackerRankIntegration",
    "leetcode":          "integrations.leetcode.adapter.LeetCodeIntegration",
    # ── Device Management ─────────────────────────────────────────────────────
    "icloud":            "integrations.icloud.adapter.ICloudIntegration",
    # ── CRM & Marketing ───────────────────────────────────────────────────────
    "hubspot":           "integrations.hubspot.adapter.HubSpotIntegration",
    "salesforce":        "integrations.salesforce.adapter.SalesforceIntegration",
    "mailchimp":         "integrations.mailchimp.adapter.MailchimpIntegration",
    # ── Customer Data Platform ────────────────────────────────────────────────
    "segment":           "integrations.segment.adapter.SegmentIntegration",
    "mixpanel":          "integrations.mixpanel.adapter.MixpanelIntegration",
    # ── AI Vendor Compliance ──────────────────────────────────────────────────
    "openai":            "integrations.openai_api.adapter.OpenAIIntegration",
    "google_gemini":     "integrations.google_gemini.adapter.GoogleGeminiIntegration",
    "anthropic":         "integrations.anthropic_api.adapter.AnthropicIntegration",
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
