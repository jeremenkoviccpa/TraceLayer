from integrations.base import IntegrationAdapter

# Import lazily to avoid loading all SDKs at startup
_REGISTRY: dict[str, str] = {
    "aws": "integrations.aws.adapter.AWSIntegration",
    "github": "integrations.github.adapter.GithubIntegration",
    "slack": "integrations.slack.adapter.SlackIntegration",
    "google_workspace": "integrations.google_workspace.adapter.GoogleWorkspaceIntegration",
    "jira": "integrations.jira.adapter.JiraIntegration",
    "okta": "integrations.okta.adapter.OktaIntegration",
    "azure_ad": "integrations.azure_ad.adapter.AzureADIntegration",
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
