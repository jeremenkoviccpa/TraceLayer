"""
Simulation metadata for integration impact preview.

Each entry describes what evidence an integration would collect and
what data categories it touches — without making real API calls.
"""
from __future__ import annotations

# ── Evidence type metadata per integration ────────────────────────────────────
# `control` must match the value adapters write to Evidence.control
# (used to match against EXPECTED_TYPES during score simulation).

SIMULATION_META: dict[str, dict] = {
    "aws": {
        "label": "Amazon Web Services",
        "description": "IAM accounts, policies, and CloudTrail audit logs for your AWS environment.",
        "evidence_types": [
            {"type": "iam_users", "label": "IAM user accounts", "control": "access_control", "typical_count": 25},
            {"type": "iam_policies", "label": "IAM policies & roles", "control": "access_control", "typical_count": 40},
            {"type": "cloudtrail_logs", "label": "CloudTrail audit events", "control": "logging_monitoring", "typical_count": 500},
        ],
        "data_categories": ["user_identity", "audit_logs", "infrastructure"],
    },
    "github": {
        "label": "GitHub",
        "description": "Org membership, admin access, and repository change records.",
        "evidence_types": [
            {"type": "github_members", "label": "Org members", "control": "access_control", "typical_count": 18},
            {"type": "github_admin_members", "label": "Org admins", "control": "access_control", "typical_count": 3},
            {"type": "repositories", "label": "Repositories", "control": "change_management", "typical_count": 35},
        ],
        "data_categories": ["user_identity", "source_code", "audit_logs"],
    },
    "gitlab": {
        "label": "GitLab",
        "description": "Group members, projects, and merge request activity.",
        "evidence_types": [
            {"type": "gitlab_members", "label": "Group members", "control": "access_control", "typical_count": 18},
            {"type": "gitlab_projects", "label": "Projects", "control": "change_management", "typical_count": 25},
        ],
        "data_categories": ["user_identity", "source_code", "audit_logs"],
    },
    "okta": {
        "label": "Okta",
        "description": "SSO users, security groups, and MFA enrollment status.",
        "evidence_types": [
            {"type": "okta_users", "label": "User accounts", "control": "access_control", "typical_count": 45},
            {"type": "okta_groups", "label": "Security groups", "control": "access_control", "typical_count": 12},
            {"type": "okta_mfa_factors", "label": "MFA enrollments", "control": "access_control", "typical_count": 45},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "azure_ad": {
        "label": "Microsoft Entra ID",
        "description": "Azure AD users, roles, and conditional access policies.",
        "evidence_types": [
            {"type": "azure_users", "label": "Directory users", "control": "access_control", "typical_count": 35},
            {"type": "azure_roles", "label": "Role assignments", "control": "access_control", "typical_count": 20},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "google_workspace": {
        "label": "Google Workspace",
        "description": "Workspace users, admin accounts, and groups.",
        "evidence_types": [
            {"type": "workspace_users", "label": "Workspace users", "control": "access_control", "typical_count": 40},
            {"type": "workspace_admin_members", "label": "Admin accounts", "control": "access_control", "typical_count": 4},
            {"type": "workspace_groups", "label": "Security groups", "control": "access_control", "typical_count": 15},
        ],
        "data_categories": ["user_identity", "authentication", "communications"],
    },
    "slack": {
        "label": "Slack",
        "description": "Workspace users, guest accounts, and workspace security settings.",
        "evidence_types": [
            {"type": "slack_users", "label": "Workspace members", "control": "access_control", "typical_count": 40},
            {"type": "slack_workspace", "label": "Workspace settings", "control": "access_control", "typical_count": 1},
        ],
        "data_categories": ["user_identity", "communications"],
    },
    "jira": {
        "label": "Jira",
        "description": "Project members and active Jira projects.",
        "evidence_types": [
            {"type": "jira_users", "label": "Project members", "control": "access_control", "typical_count": 20},
            {"type": "jira_projects", "label": "Jira projects", "control": "change_management", "typical_count": 8},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "datadog": {
        "label": "Datadog",
        "description": "Monitor history, alert events, and user access logs.",
        "evidence_types": [
            {"type": "datadog_monitors", "label": "Monitor configurations", "control": "logging_monitoring", "typical_count": 30},
            {"type": "datadog_events", "label": "Alert events", "control": "logging_monitoring", "typical_count": 200},
            {"type": "datadog_users", "label": "Datadog users", "control": "access_control", "typical_count": 12},
        ],
        "data_categories": ["audit_logs", "infrastructure"],
    },
    "snyk": {
        "label": "Snyk",
        "description": "Vulnerability scan results and dependency risk scores.",
        "evidence_types": [
            {"type": "snyk_vulnerabilities", "label": "Open vulnerabilities", "control": "vulnerability_management", "typical_count": 45},
            {"type": "snyk_projects", "label": "Scanned projects", "control": "change_management", "typical_count": 20},
        ],
        "data_categories": ["vulnerability_data", "source_code"],
    },
    "crowdstrike": {
        "label": "CrowdStrike",
        "description": "Endpoint protection events and device inventory.",
        "evidence_types": [
            {"type": "crowdstrike_devices", "label": "Protected endpoints", "control": "asset_management", "typical_count": 60},
            {"type": "crowdstrike_detections", "label": "Detection events", "control": "logging_monitoring", "typical_count": 120},
        ],
        "data_categories": ["audit_logs", "infrastructure"],
    },
    "jamf": {
        "label": "Jamf",
        "description": "Mac device inventory, MDM policies, and compliance status.",
        "evidence_types": [
            {"type": "jamf_devices", "label": "Managed devices", "control": "asset_management", "typical_count": 55},
            {"type": "jamf_policies", "label": "MDM policies", "control": "asset_management", "typical_count": 12},
        ],
        "data_categories": ["infrastructure"],
    },
    "sentinelone": {
        "label": "SentinelOne",
        "description": "Endpoint detection events and threat intelligence.",
        "evidence_types": [
            {"type": "sentinelone_agents", "label": "Agent-protected devices", "control": "asset_management", "typical_count": 50},
            {"type": "sentinelone_threats", "label": "Threat detections", "control": "logging_monitoring", "typical_count": 80},
        ],
        "data_categories": ["audit_logs", "infrastructure"],
    },
    "pagerduty": {
        "label": "PagerDuty",
        "description": "Incident records, escalation policies, and on-call schedules.",
        "evidence_types": [
            {"type": "pagerduty_incidents", "label": "Incident records", "control": "incident_management", "typical_count": 90},
            {"type": "pagerduty_services", "label": "Services monitored", "control": "incident_management", "typical_count": 15},
        ],
        "data_categories": ["audit_logs"],
    },
    "1password": {
        "label": "1Password",
        "description": "Vault access, team members, and guest account inventory.",
        "evidence_types": [
            {"type": "1password_users", "label": "Vault members", "control": "access_control", "typical_count": 30},
            {"type": "1password_vaults", "label": "Vaults", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "rippling": {
        "label": "Rippling",
        "description": "Employee records, department assignments, and offboarding status.",
        "evidence_types": [
            {"type": "rippling_employees", "label": "Employee records", "control": "workforce_security", "typical_count": 50},
            {"type": "rippling_groups", "label": "Departments & groups", "control": "workforce_security", "typical_count": 12},
        ],
        "data_categories": ["user_identity", "hr_data"],
    },
    "bamboohr": {
        "label": "BambooHR",
        "description": "Employee directory, job history, and termination records.",
        "evidence_types": [
            {"type": "bamboohr_employees", "label": "Employee directory", "control": "workforce_security", "typical_count": 45},
        ],
        "data_categories": ["user_identity", "hr_data"],
    },
    "terraform_cloud": {
        "label": "Terraform Cloud",
        "description": "Infrastructure-as-code runs, workspace configs, and apply history.",
        "evidence_types": [
            {"type": "terraform_runs", "label": "Infrastructure runs", "control": "change_management", "typical_count": 60},
            {"type": "terraform_workspaces", "label": "Workspaces", "control": "change_management", "typical_count": 10},
        ],
        "data_categories": ["infrastructure", "audit_logs"],
    },
    "vercel": {
        "label": "Vercel",
        "description": "Deployment history, project settings, and team membership.",
        "evidence_types": [
            {"type": "vercel_deployments", "label": "Deployment records", "control": "change_management", "typical_count": 80},
            {"type": "vercel_projects", "label": "Projects", "control": "change_management", "typical_count": 5},
            {"type": "vercel_team", "label": "Team members", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["infrastructure", "audit_logs"],
    },
    "google_cloud": {
        "label": "Google Cloud",
        "description": "GCP IAM, project permissions, and audit log exports.",
        "evidence_types": [
            {"type": "gcp_iam_members", "label": "IAM members", "control": "access_control", "typical_count": 20},
            {"type": "gcp_audit_logs", "label": "Cloud Audit Logs", "control": "logging_monitoring", "typical_count": 300},
        ],
        "data_categories": ["user_identity", "audit_logs", "infrastructure"],
    },
    "azure": {
        "label": "Azure",
        "description": "Azure subscriptions, resource groups, and RBAC assignments.",
        "evidence_types": [
            {"type": "azure_role_assignments", "label": "RBAC assignments", "control": "access_control", "typical_count": 25},
            {"type": "azure_resources", "label": "Resource inventory", "control": "asset_management", "typical_count": 50},
        ],
        "data_categories": ["user_identity", "infrastructure"],
    },
    "wiz": {
        "label": "Wiz",
        "description": "Cloud security findings, misconfigurations, and vulnerability alerts.",
        "evidence_types": [
            {"type": "wiz_issues", "label": "Security issues", "control": "vulnerability_management", "typical_count": 35},
            {"type": "wiz_inventory", "label": "Cloud asset inventory", "control": "asset_management", "typical_count": 100},
        ],
        "data_categories": ["vulnerability_data", "infrastructure"],
    },
    "knowbe4": {
        "label": "KnowBe4",
        "description": "Security awareness training completion and phishing simulation results.",
        "evidence_types": [
            {"type": "knowbe4_training", "label": "Training completions", "control": "security_awareness", "typical_count": 45},
            {"type": "knowbe4_phishing", "label": "Phishing simulation results", "control": "security_awareness", "typical_count": 30},
        ],
        "data_categories": ["hr_data", "audit_logs"],
    },
    "duo": {
        "label": "Duo Security",
        "description": "MFA authentication logs and device trust status.",
        "evidence_types": [
            {"type": "duo_users", "label": "MFA-enrolled users", "control": "access_control", "typical_count": 40},
            {"type": "duo_auth_logs", "label": "Authentication events", "control": "logging_monitoring", "typical_count": 500},
        ],
        "data_categories": ["user_identity", "authentication", "audit_logs"],
    },
    "vault": {
        "label": "HashiCorp Vault",
        "description": "Secret access logs, policy bindings, and audit trails.",
        "evidence_types": [
            {"type": "vault_audit_logs", "label": "Secret access audit logs", "control": "logging_monitoring", "typical_count": 200},
            {"type": "vault_policies", "label": "Access policies", "control": "access_control", "typical_count": 15},
        ],
        "data_categories": ["authentication", "audit_logs"],
    },
    "stripe": {
        "label": "Stripe",
        "description": "Payment event logs, team access, and API key inventory.",
        "evidence_types": [
            {"type": "stripe_users", "label": "Dashboard users", "control": "access_control", "typical_count": 8},
            {"type": "stripe_events", "label": "Payment event log", "control": "logging_monitoring", "typical_count": 500},
        ],
        "data_categories": ["financial", "audit_logs", "user_identity"],
    },
    "sentry": {
        "label": "Sentry",
        "description": "Error events, alert rules, and project membership.",
        "evidence_types": [
            {"type": "sentry_issues", "label": "Error events", "control": "logging_monitoring", "typical_count": 150},
            {"type": "sentry_members", "label": "Project members", "control": "access_control", "typical_count": 12},
        ],
        "data_categories": ["audit_logs"],
    },
    "cloudflare": {
        "label": "Cloudflare",
        "description": "DNS records, WAF rules, and access team membership.",
        "evidence_types": [
            {"type": "cloudflare_zones", "label": "DNS zones", "control": "infrastructure_security", "typical_count": 5},
            {"type": "cloudflare_members", "label": "Account members", "control": "access_control", "typical_count": 6},
        ],
        "data_categories": ["infrastructure"],
    },
    "linear": {
        "label": "Linear",
        "description": "Issue tracking members and team project records.",
        "evidence_types": [
            {"type": "linear_members", "label": "Workspace members", "control": "access_control", "typical_count": 15},
            {"type": "linear_teams", "label": "Teams", "control": "change_management", "typical_count": 5},
        ],
        "data_categories": ["user_identity", "project_data"],
    },

    # ── Identity & Access (extended) ───────────────────────────────────────────
    "jumpcloud": {
        "label": "JumpCloud",
        "description": "Directory users, device compliance, and SSO application access.",
        "evidence_types": [
            {"type": "jumpcloud_users", "label": "Directory users", "control": "access_control", "typical_count": 40},
            {"type": "jumpcloud_devices", "label": "Managed devices", "control": "asset_management", "typical_count": 50},
            {"type": "jumpcloud_groups", "label": "User groups", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["user_identity", "authentication", "infrastructure"],
    },
    "tailscale": {
        "label": "Tailscale",
        "description": "Network peers, ACL policies, and zero-trust access records.",
        "evidence_types": [
            {"type": "tailscale_devices", "label": "Network peers (devices)", "control": "access_control", "typical_count": 35},
            {"type": "tailscale_acls", "label": "ACL policies", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["user_identity", "infrastructure"],
    },
    "bitwarden": {
        "label": "Bitwarden",
        "description": "Organization members, vault collections, and MFA status.",
        "evidence_types": [
            {"type": "bitwarden_members", "label": "Organization members", "control": "access_control", "typical_count": 30},
            {"type": "bitwarden_collections", "label": "Vault collections", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "lastpass": {
        "label": "LastPass",
        "description": "Team members, shared folders, and password policies.",
        "evidence_types": [
            {"type": "lastpass_users", "label": "Team members", "control": "access_control", "typical_count": 30},
            {"type": "lastpass_shared_folders", "label": "Shared folders", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "auth0": {
        "label": "Auth0",
        "description": "Users, applications, log streams, and tenant security settings.",
        "evidence_types": [
            {"type": "auth0_users", "label": "Tenant users", "control": "access_control", "typical_count": 1500},
            {"type": "auth0_applications", "label": "Applications registered", "control": "access_control", "typical_count": 8},
            {"type": "auth0_logs", "label": "Authentication log events", "control": "logging_monitoring", "typical_count": 300},
        ],
        "data_categories": ["user_identity", "authentication", "audit_logs"],
    },
    "doppler": {
        "label": "Doppler",
        "description": "Secret access logs, project configurations, and team members.",
        "evidence_types": [
            {"type": "doppler_members", "label": "Workspace members", "control": "access_control", "typical_count": 12},
            {"type": "doppler_projects", "label": "Secret projects", "control": "access_control", "typical_count": 6},
        ],
        "data_categories": ["authentication", "audit_logs"],
    },
    "ping_identity": {
        "label": "Ping Identity",
        "description": "Users, groups, applications, and identity governance policies.",
        "evidence_types": [
            {"type": "ping_users", "label": "Identity users", "control": "access_control", "typical_count": 350},
            {"type": "ping_groups", "label": "User groups", "control": "access_control", "typical_count": 20},
            {"type": "ping_applications", "label": "SSO applications", "control": "access_control", "typical_count": 15},
        ],
        "data_categories": ["user_identity", "authentication"],
    },
    "zscaler": {
        "label": "Zscaler",
        "description": "URL filtering policies, firewall rules, and audit logs.",
        "evidence_types": [
            {"type": "zscaler_users", "label": "Users in tenant", "control": "access_control", "typical_count": 200},
            {"type": "zscaler_policies", "label": "Security policies", "control": "infrastructure_security", "typical_count": 12},
            {"type": "zscaler_audit_logs", "label": "Admin audit logs", "control": "logging_monitoring", "typical_count": 150},
        ],
        "data_categories": ["user_identity", "audit_logs", "infrastructure"],
    },
    "okta_verify": {
        "label": "Okta Verify",
        "description": "MFA-enrolled users and device trust status.",
        "evidence_types": [
            {"type": "okta_verify_enrollments", "label": "MFA enrollments", "control": "access_control", "typical_count": 45},
        ],
        "data_categories": ["authentication"],
    },
    "microsoft_authenticator": {
        "label": "Microsoft Authenticator",
        "description": "MFA-enrolled users and registration policies.",
        "evidence_types": [
            {"type": "ms_auth_enrollments", "label": "MFA enrollments", "control": "access_control", "typical_count": 45},
        ],
        "data_categories": ["authentication"],
    },
    "google_authenticator": {
        "label": "Google Authenticator",
        "description": "MFA-enrolled accounts and 2FA usage records.",
        "evidence_types": [
            {"type": "google_auth_enrollments", "label": "2FA enrollments", "control": "access_control", "typical_count": 40},
        ],
        "data_categories": ["authentication"],
    },

    # ── Cloud Infrastructure (extended) ───────────────────────────────────────
    "digitalocean": {
        "label": "DigitalOcean",
        "description": "Droplets, team members, and firewall rules.",
        "evidence_types": [
            {"type": "do_droplets", "label": "Droplets (servers)", "control": "asset_management", "typical_count": 15},
            {"type": "do_members", "label": "Team members", "control": "access_control", "typical_count": 6},
        ],
        "data_categories": ["infrastructure", "user_identity"],
    },
    "heroku": {
        "label": "Heroku",
        "description": "Dynos, team members, and add-on inventory.",
        "evidence_types": [
            {"type": "heroku_apps", "label": "Applications", "control": "asset_management", "typical_count": 10},
            {"type": "heroku_members", "label": "Team members", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["infrastructure", "user_identity"],
    },
    "render": {
        "label": "Render",
        "description": "Services, team members, and deploy history.",
        "evidence_types": [
            {"type": "render_services", "label": "Services deployed", "control": "asset_management", "typical_count": 8},
            {"type": "render_members", "label": "Team members", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["infrastructure", "user_identity"],
    },
    "flyio": {
        "label": "Fly.io",
        "description": "Apps, machines, and organization members.",
        "evidence_types": [
            {"type": "fly_apps", "label": "Applications", "control": "asset_management", "typical_count": 6},
            {"type": "fly_members", "label": "Org members", "control": "access_control", "typical_count": 4},
        ],
        "data_categories": ["infrastructure", "user_identity"],
    },
    "netlify": {
        "label": "Netlify",
        "description": "Sites, deploy logs, and team members.",
        "evidence_types": [
            {"type": "netlify_sites", "label": "Sites deployed", "control": "change_management", "typical_count": 6},
            {"type": "netlify_members", "label": "Team members", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["infrastructure", "user_identity", "audit_logs"],
    },
    "oracle_cloud": {
        "label": "Oracle Cloud",
        "description": "IAM users, resource inventory, and audit logs.",
        "evidence_types": [
            {"type": "oci_users", "label": "IAM users", "control": "access_control", "typical_count": 20},
            {"type": "oci_audit_logs", "label": "Cloud audit events", "control": "logging_monitoring", "typical_count": 200},
        ],
        "data_categories": ["user_identity", "audit_logs", "infrastructure"],
    },

    # ── CI/CD & DevOps ────────────────────────────────────────────────────────
    "bitbucket": {
        "label": "Bitbucket",
        "description": "Repositories, workspace members, and pull request records.",
        "evidence_types": [
            {"type": "bitbucket_members", "label": "Workspace members", "control": "access_control", "typical_count": 15},
            {"type": "bitbucket_repos", "label": "Repositories", "control": "change_management", "typical_count": 20},
        ],
        "data_categories": ["user_identity", "source_code", "audit_logs"],
    },
    "circleci": {
        "label": "CircleCI",
        "description": "Pipelines, contexts, and org member access.",
        "evidence_types": [
            {"type": "circleci_pipelines", "label": "Pipeline runs", "control": "change_management", "typical_count": 80},
            {"type": "circleci_members", "label": "Org members", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["audit_logs", "source_code"],
    },
    "jenkins": {
        "label": "Jenkins",
        "description": "Build jobs, pipeline runs, and user accounts.",
        "evidence_types": [
            {"type": "jenkins_jobs", "label": "Build jobs", "control": "change_management", "typical_count": 40},
            {"type": "jenkins_users", "label": "Jenkins users", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["audit_logs", "source_code"],
    },
    "azure_devops": {
        "label": "Azure DevOps",
        "description": "Repositories, pipelines, and project member access.",
        "evidence_types": [
            {"type": "ado_members", "label": "Project members", "control": "access_control", "typical_count": 20},
            {"type": "ado_repos", "label": "Repositories", "control": "change_management", "typical_count": 15},
            {"type": "ado_pipelines", "label": "Pipeline runs", "control": "change_management", "typical_count": 60},
        ],
        "data_categories": ["user_identity", "source_code", "audit_logs"],
    },
    "argocd": {
        "label": "Argo CD",
        "description": "Application deployments, sync history, and RBAC roles.",
        "evidence_types": [
            {"type": "argocd_applications", "label": "Applications managed", "control": "change_management", "typical_count": 12},
            {"type": "argocd_sync_history", "label": "Sync/deploy events", "control": "change_management", "typical_count": 50},
        ],
        "data_categories": ["infrastructure", "audit_logs"],
    },
    "kubernetes": {
        "label": "Kubernetes",
        "description": "Cluster RBAC, namespaces, and workload inventory.",
        "evidence_types": [
            {"type": "k8s_rbac_roles", "label": "RBAC role bindings", "control": "access_control", "typical_count": 30},
            {"type": "k8s_namespaces", "label": "Namespaces", "control": "asset_management", "typical_count": 10},
            {"type": "k8s_pods", "label": "Running workloads", "control": "asset_management", "typical_count": 60},
        ],
        "data_categories": ["user_identity", "infrastructure"],
    },

    # ── Monitoring & Security (extended) ──────────────────────────────────────
    "new_relic": {
        "label": "New Relic",
        "description": "Alert policies, dashboards, and user access.",
        "evidence_types": [
            {"type": "new_relic_alerts", "label": "Alert policies", "control": "logging_monitoring", "typical_count": 20},
            {"type": "new_relic_users", "label": "Platform users", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["audit_logs", "infrastructure"],
    },
    "tenable": {
        "label": "Tenable",
        "description": "Vulnerability scan results and asset exposure scores.",
        "evidence_types": [
            {"type": "tenable_vulns", "label": "Vulnerability findings", "control": "vulnerability_management", "typical_count": 120},
            {"type": "tenable_assets", "label": "Scanned assets", "control": "asset_management", "typical_count": 80},
        ],
        "data_categories": ["vulnerability_data", "infrastructure"],
    },
    "qualys": {
        "label": "Qualys",
        "description": "Vulnerability scan findings, patch status, and asset inventory.",
        "evidence_types": [
            {"type": "qualys_vulns", "label": "Vulnerability findings", "control": "vulnerability_management", "typical_count": 100},
            {"type": "qualys_assets", "label": "Scanned hosts", "control": "asset_management", "typical_count": 70},
        ],
        "data_categories": ["vulnerability_data", "infrastructure"],
    },
    "microsoft_sentinel": {
        "label": "Microsoft Sentinel",
        "description": "Security incidents, alert rules, and SIEM analytics.",
        "evidence_types": [
            {"type": "sentinel_incidents", "label": "Security incidents", "control": "logging_monitoring", "typical_count": 30},
            {"type": "sentinel_alerts", "label": "Active alert rules", "control": "logging_monitoring", "typical_count": 15},
        ],
        "data_categories": ["audit_logs"],
    },
    "grafana": {
        "label": "Grafana",
        "description": "Dashboards, alert rules, and user permissions.",
        "evidence_types": [
            {"type": "grafana_users", "label": "Org users", "control": "access_control", "typical_count": 10},
            {"type": "grafana_alerts", "label": "Alert rules", "control": "logging_monitoring", "typical_count": 20},
        ],
        "data_categories": ["audit_logs", "user_identity"],
    },
    "graylog": {
        "label": "Graylog",
        "description": "Log streams, alert conditions, and user accounts.",
        "evidence_types": [
            {"type": "graylog_streams", "label": "Log streams", "control": "logging_monitoring", "typical_count": 10},
            {"type": "graylog_users", "label": "Users", "control": "access_control", "typical_count": 6},
        ],
        "data_categories": ["audit_logs", "user_identity"],
    },
    "elastic": {
        "label": "Elastic",
        "description": "Security alerts, log ingestion stats, and user roles.",
        "evidence_types": [
            {"type": "elastic_alerts", "label": "Security alerts", "control": "logging_monitoring", "typical_count": 40},
            {"type": "elastic_users", "label": "Cluster users", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["audit_logs", "user_identity"],
    },
    "splunk": {
        "label": "Splunk",
        "description": "Search alert rules, log ingestion, and user roles.",
        "evidence_types": [
            {"type": "splunk_alerts", "label": "Saved alert searches", "control": "logging_monitoring", "typical_count": 15},
            {"type": "splunk_users", "label": "Splunk users", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["audit_logs", "user_identity"],
    },
    "veracode": {
        "label": "Veracode",
        "description": "SAST/DAST scan results and application security findings.",
        "evidence_types": [
            {"type": "veracode_findings", "label": "Security findings", "control": "vulnerability_management", "typical_count": 60},
            {"type": "veracode_scans", "label": "Scan records", "control": "change_management", "typical_count": 15},
        ],
        "data_categories": ["vulnerability_data", "source_code"],
    },
    "aquasec": {
        "label": "Aqua Security",
        "description": "Container vulnerability scans and runtime policy violations.",
        "evidence_types": [
            {"type": "aquasec_vulns", "label": "Container vulnerabilities", "control": "vulnerability_management", "typical_count": 80},
            {"type": "aquasec_images", "label": "Scanned container images", "control": "asset_management", "typical_count": 30},
        ],
        "data_categories": ["vulnerability_data", "infrastructure"],
    },
    "detectify": {
        "label": "Detectify",
        "description": "Web application security scan findings.",
        "evidence_types": [
            {"type": "detectify_findings", "label": "Security findings", "control": "vulnerability_management", "typical_count": 40},
        ],
        "data_categories": ["vulnerability_data"],
    },
    "nightfall": {
        "label": "Nightfall",
        "description": "DLP findings across cloud services and code repos.",
        "evidence_types": [
            {"type": "nightfall_findings", "label": "DLP violations", "control": "logging_monitoring", "typical_count": 25},
        ],
        "data_categories": ["audit_logs", "pii"],
    },
    "opsgenie": {
        "label": "Opsgenie",
        "description": "Incident records, on-call schedules, and team members.",
        "evidence_types": [
            {"type": "opsgenie_incidents", "label": "Incident records", "control": "incident_management", "typical_count": 40},
            {"type": "opsgenie_teams", "label": "On-call teams", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["audit_logs"],
    },
    "hackerone": {
        "label": "HackerOne",
        "description": "Bug bounty reports, severity ratings, and remediation status.",
        "evidence_types": [
            {"type": "hackerone_reports", "label": "Vulnerability reports", "control": "vulnerability_management", "typical_count": 20},
        ],
        "data_categories": ["vulnerability_data"],
    },
    "bugcrowd": {
        "label": "Bugcrowd",
        "description": "Bug bounty submissions and triage records.",
        "evidence_types": [
            {"type": "bugcrowd_submissions", "label": "Bug submissions", "control": "vulnerability_management", "typical_count": 15},
        ],
        "data_categories": ["vulnerability_data"],
    },
    "stackhawk": {
        "label": "StackHawk",
        "description": "API security scan results integrated into CI/CD.",
        "evidence_types": [
            {"type": "stackhawk_findings", "label": "API security findings", "control": "vulnerability_management", "typical_count": 25},
        ],
        "data_categories": ["vulnerability_data", "source_code"],
    },
    "betteruptime": {
        "label": "Better Uptime",
        "description": "Uptime monitors, incident log, and on-call schedules.",
        "evidence_types": [
            {"type": "betteruptime_monitors", "label": "Uptime monitors", "control": "logging_monitoring", "typical_count": 15},
            {"type": "betteruptime_incidents", "label": "Downtime incidents", "control": "incident_management", "typical_count": 10},
        ],
        "data_categories": ["audit_logs"],
    },

    # ── Project Management ────────────────────────────────────────────────────
    "asana": {
        "label": "Asana",
        "description": "Workspace members and project records.",
        "evidence_types": [
            {"type": "asana_members", "label": "Workspace members", "control": "access_control", "typical_count": 20},
            {"type": "asana_projects", "label": "Projects", "control": "change_management", "typical_count": 12},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "monday": {
        "label": "Monday.com",
        "description": "Team members, boards, and workspace settings.",
        "evidence_types": [
            {"type": "monday_members", "label": "Team members", "control": "access_control", "typical_count": 20},
            {"type": "monday_boards", "label": "Boards", "control": "change_management", "typical_count": 10},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "shortcut": {
        "label": "Shortcut",
        "description": "Members and project/story records.",
        "evidence_types": [
            {"type": "shortcut_members", "label": "Members", "control": "access_control", "typical_count": 12},
            {"type": "shortcut_projects", "label": "Projects", "control": "change_management", "typical_count": 8},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "clickup": {
        "label": "ClickUp",
        "description": "Workspace members and space/folder records.",
        "evidence_types": [
            {"type": "clickup_members", "label": "Workspace members", "control": "access_control", "typical_count": 18},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "trello": {
        "label": "Trello",
        "description": "Board members and workspace settings.",
        "evidence_types": [
            {"type": "trello_members", "label": "Board members", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["user_identity", "project_data"],
    },
    "zendesk": {
        "label": "Zendesk",
        "description": "Agents, roles, and ticket audit records.",
        "evidence_types": [
            {"type": "zendesk_agents", "label": "Support agents", "control": "access_control", "typical_count": 15},
            {"type": "zendesk_audit_logs", "label": "Audit log events", "control": "logging_monitoring", "typical_count": 100},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },
    "servicenow": {
        "label": "ServiceNow",
        "description": "Users, change requests, and incident records.",
        "evidence_types": [
            {"type": "servicenow_users", "label": "Platform users", "control": "access_control", "typical_count": 50},
            {"type": "servicenow_changes", "label": "Change requests", "control": "change_management", "typical_count": 30},
        ],
        "data_categories": ["user_identity", "audit_logs", "project_data"],
    },

    # ── Communication ─────────────────────────────────────────────────────────
    "zoom": {
        "label": "Zoom",
        "description": "Account users, meeting security settings, and SSO configuration.",
        "evidence_types": [
            {"type": "zoom_users", "label": "Account users", "control": "access_control", "typical_count": 40},
            {"type": "zoom_settings", "label": "Security settings snapshot", "control": "access_control", "typical_count": 1},
        ],
        "data_categories": ["user_identity", "communications"],
    },
    "intercom": {
        "label": "Intercom",
        "description": "Teammate access and workspace security settings.",
        "evidence_types": [
            {"type": "intercom_teammates", "label": "Teammates", "control": "access_control", "typical_count": 12},
        ],
        "data_categories": ["user_identity", "communications"],
    },
    "webex": {
        "label": "Webex",
        "description": "Organization users and security policy settings.",
        "evidence_types": [
            {"type": "webex_users", "label": "Org users", "control": "access_control", "typical_count": 35},
        ],
        "data_categories": ["user_identity", "communications"],
    },
    "microsoft_teams": {
        "label": "Microsoft Teams",
        "description": "Team members, channels, and external access settings.",
        "evidence_types": [
            {"type": "teams_members", "label": "Team members", "control": "access_control", "typical_count": 40},
            {"type": "teams_channels", "label": "Teams & channels", "control": "access_control", "typical_count": 20},
        ],
        "data_categories": ["user_identity", "communications"],
    },

    # ── HR & People ───────────────────────────────────────────────────────────
    "checkr": {
        "label": "Checkr",
        "description": "Background check reports and candidate clearance status.",
        "evidence_types": [
            {"type": "checkr_reports", "label": "Background check reports", "control": "workforce_security", "typical_count": 25},
        ],
        "data_categories": ["hr_data"],
    },
    "lattice": {
        "label": "Lattice",
        "description": "Employee performance records and team org structure.",
        "evidence_types": [
            {"type": "lattice_employees", "label": "Employee profiles", "control": "workforce_security", "typical_count": 45},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "trainual": {
        "label": "Trainual",
        "description": "Training completion records and policy acknowledgements.",
        "evidence_types": [
            {"type": "trainual_completions", "label": "Training completions", "control": "security_awareness", "typical_count": 40},
        ],
        "data_categories": ["hr_data", "audit_logs"],
    },
    "greenhouse": {
        "label": "Greenhouse",
        "description": "Candidate records, job stages, and hiring team access.",
        "evidence_types": [
            {"type": "greenhouse_jobs", "label": "Active job postings", "control": "workforce_security", "typical_count": 8},
            {"type": "greenhouse_users", "label": "Hiring team users", "control": "access_control", "typical_count": 12},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "hibob": {
        "label": "HiBob",
        "description": "Employee directory, department structure, and offboarding records.",
        "evidence_types": [
            {"type": "hibob_employees", "label": "Employee records", "control": "workforce_security", "typical_count": 50},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "personio": {
        "label": "Personio",
        "description": "Employee records, absence tracking, and document management.",
        "evidence_types": [
            {"type": "personio_employees", "label": "Employee records", "control": "workforce_security", "typical_count": 45},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "deel": {
        "label": "Deel",
        "description": "Contractor and employee contracts, payments, and compliance docs.",
        "evidence_types": [
            {"type": "deel_workers", "label": "Workers (employees + contractors)", "control": "workforce_security", "typical_count": 30},
        ],
        "data_categories": ["hr_data", "user_identity", "financial"],
    },
    "remote": {
        "label": "Remote",
        "description": "Global employee records, contracts, and equipment.",
        "evidence_types": [
            {"type": "remote_employees", "label": "Employee records", "control": "workforce_security", "typical_count": 25},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "lever": {
        "label": "Lever",
        "description": "Candidate pipeline, job postings, and recruiter access.",
        "evidence_types": [
            {"type": "lever_postings", "label": "Job postings", "control": "workforce_security", "typical_count": 6},
            {"type": "lever_users", "label": "Recruiter users", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "360learning": {
        "label": "360Learning",
        "description": "Course completions and security awareness training records.",
        "evidence_types": [
            {"type": "learning360_completions", "label": "Course completions", "control": "security_awareness", "typical_count": 45},
        ],
        "data_categories": ["hr_data", "audit_logs"],
    },

    # ── Data & Analytics ──────────────────────────────────────────────────────
    "snowflake": {
        "label": "Snowflake",
        "description": "Users, roles, privilege grants, and query audit logs.",
        "evidence_types": [
            {"type": "snowflake_users", "label": "Database users", "control": "access_control", "typical_count": 25},
            {"type": "snowflake_grants", "label": "Privilege grants", "control": "access_control", "typical_count": 60},
            {"type": "snowflake_query_logs", "label": "Query audit logs", "control": "logging_monitoring", "typical_count": 1000},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },
    "databricks": {
        "label": "Databricks",
        "description": "Workspace users, access control lists, and cluster configs.",
        "evidence_types": [
            {"type": "databricks_users", "label": "Workspace users", "control": "access_control", "typical_count": 20},
            {"type": "databricks_clusters", "label": "Cluster configurations", "control": "asset_management", "typical_count": 8},
        ],
        "data_categories": ["user_identity", "infrastructure"],
    },
    "google_analytics": {
        "label": "Google Analytics",
        "description": "Property users and account-level permissions.",
        "evidence_types": [
            {"type": "ga_users", "label": "Property users", "control": "access_control", "typical_count": 8},
        ],
        "data_categories": ["user_identity"],
    },
    "segment": {
        "label": "Segment",
        "description": "Workspace members, source access, and audit trail.",
        "evidence_types": [
            {"type": "segment_members", "label": "Workspace members", "control": "access_control", "typical_count": 10},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },

    # ── Documentation & Knowledge ─────────────────────────────────────────────
    "notion": {
        "label": "Notion",
        "description": "Workspace members, guest access, and page permissions.",
        "evidence_types": [
            {"type": "notion_members", "label": "Workspace members", "control": "access_control", "typical_count": 30},
        ],
        "data_categories": ["user_identity", "communications"],
    },
    "confluence": {
        "label": "Confluence",
        "description": "Space members, user groups, and permission schemes.",
        "evidence_types": [
            {"type": "confluence_users", "label": "Space users", "control": "access_control", "typical_count": 25},
        ],
        "data_categories": ["user_identity", "project_data"],
    },

    # ── CRM & Marketing ───────────────────────────────────────────────────────
    "hubspot": {
        "label": "HubSpot",
        "description": "Portal users, roles, and API access audit.",
        "evidence_types": [
            {"type": "hubspot_users", "label": "Portal users", "control": "access_control", "typical_count": 15},
        ],
        "data_categories": ["user_identity", "pii"],
    },
    "salesforce": {
        "label": "Salesforce",
        "description": "Users, profiles, permission sets, and login audit logs.",
        "evidence_types": [
            {"type": "sf_users", "label": "Org users", "control": "access_control", "typical_count": 40},
            {"type": "sf_profiles", "label": "Permission profiles", "control": "access_control", "typical_count": 10},
            {"type": "sf_login_logs", "label": "Login audit events", "control": "logging_monitoring", "typical_count": 300},
        ],
        "data_categories": ["user_identity", "audit_logs", "pii"],
    },
    "mailchimp": {
        "label": "Mailchimp",
        "description": "Account users and API key inventory.",
        "evidence_types": [
            {"type": "mailchimp_users", "label": "Account users", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["user_identity", "pii"],
    },

    # ── AI Vendor Compliance ───────────────────────────────────────────────────
    "openai": {
        "label": "OpenAI",
        "description": "Org members, API keys, and project access.",
        "evidence_types": [
            {"type": "openai_members", "label": "Org members", "control": "access_control", "typical_count": 10},
            {"type": "openai_api_keys", "label": "API keys", "control": "access_control", "typical_count": 5},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },
    "google_gemini": {
        "label": "Google Gemini",
        "description": "API keys and project-level access settings.",
        "evidence_types": [
            {"type": "gemini_api_keys", "label": "API keys", "control": "access_control", "typical_count": 3},
        ],
        "data_categories": ["user_identity"],
    },
    "anthropic": {
        "label": "Anthropic",
        "description": "Workspace members, API keys, and usage audit.",
        "evidence_types": [
            {"type": "anthropic_members", "label": "Workspace members", "control": "access_control", "typical_count": 8},
            {"type": "anthropic_api_keys", "label": "API keys", "control": "access_control", "typical_count": 4},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },

    # ── Data Security ─────────────────────────────────────────────────────────
    "metomic": {
        "label": "Metomic",
        "description": "DLP policy rules and sensitive data exposure findings.",
        "evidence_types": [
            {"type": "metomic_findings", "label": "Sensitive data findings", "control": "logging_monitoring", "typical_count": 30},
        ],
        "data_categories": ["audit_logs", "pii"],
    },

    # ── Device Management ─────────────────────────────────────────────────────
    "icloud": {
        "label": "iCloud (Apple Business Manager)",
        "description": "Managed Apple devices and MDM enrollment status.",
        "evidence_types": [
            {"type": "icloud_devices", "label": "Managed Apple devices", "control": "asset_management", "typical_count": 30},
        ],
        "data_categories": ["infrastructure"],
    },
    "kolide": {
        "label": "Kolide",
        "description": "Device health checks and fleet compliance status.",
        "evidence_types": [
            {"type": "kolide_devices", "label": "Fleet devices", "control": "asset_management", "typical_count": 55},
            {"type": "kolide_checks", "label": "Compliance check results", "control": "asset_management", "typical_count": 200},
        ],
        "data_categories": ["infrastructure"],
    },
    "kandji": {
        "label": "Kandji",
        "description": "Mac device compliance, MDM profiles, and patch status.",
        "evidence_types": [
            {"type": "kandji_devices", "label": "Managed Mac devices", "control": "asset_management", "typical_count": 50},
            {"type": "kandji_blueprints", "label": "MDM policy blueprints", "control": "asset_management", "typical_count": 5},
        ],
        "data_categories": ["infrastructure"],
    },

    # ── Time Tracking ─────────────────────────────────────────────────────────
    "harvest": {
        "label": "Harvest",
        "description": "Team members and time tracking records.",
        "evidence_types": [
            {"type": "harvest_users", "label": "Team members", "control": "access_control", "typical_count": 15},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },

    # ── Technical Assessments ─────────────────────────────────────────────────
    "hackerrank": {
        "label": "HackerRank",
        "description": "Candidate assessments and recruiter access.",
        "evidence_types": [
            {"type": "hackerrank_tests", "label": "Assessments administered", "control": "workforce_security", "typical_count": 20},
        ],
        "data_categories": ["hr_data"],
    },
    "leetcode": {
        "label": "LeetCode",
        "description": "Team assessment records.",
        "evidence_types": [
            {"type": "leetcode_assessments", "label": "Assessment records", "control": "workforce_security", "typical_count": 15},
        ],
        "data_categories": ["hr_data"],
    },
    # ── India-focused HR & ITSM ───────────────────────────────────────────────
    "zoho_people": {
        "label": "Zoho People",
        "description": "Employee directory, departments, and employment status from Zoho People HRMS.",
        "evidence_types": [
            {"type": "zoho_employees", "label": "Employee records", "control": "hr_security", "typical_count": 80},
            {"type": "zoho_departments", "label": "Departments", "control": "hr_security", "typical_count": 12},
        ],
        "data_categories": ["hr_data", "user_identity"],
    },
    "freshdesk": {
        "label": "Freshdesk",
        "description": "Support agent accounts and ticket activity for access control and change management evidence.",
        "evidence_types": [
            {"type": "freshdesk_agents", "label": "Support agents", "control": "access_control", "typical_count": 20},
            {"type": "freshdesk_tickets", "label": "Support tickets", "control": "change_management", "typical_count": 150},
        ],
        "data_categories": ["user_identity", "audit_logs"],
    },
    # ── India — Accounting & Finance ──────────────────────────────────────────
    "tally": {
        "label": "Tally Solutions",
        "description": "Company financials, ledger entries, and balance sheet from TallyPrime for financial controls and audit trail evidence.",
        "evidence_types": [
            {"type": "tally_company_info",  "label": "Company profile",   "control": "financial_controls", "typical_count": 1},
            {"type": "tally_ledger_entry",  "label": "Ledger entries",    "control": "financial_controls", "typical_count": 200},
            {"type": "tally_balance_sheet", "label": "Balance sheet",     "control": "financial_controls", "typical_count": 1},
        ],
        "data_categories": ["financial", "audit_logs"],
    },
    "zoho_books": {
        "label": "Zoho Books",
        "description": "Invoices, contacts, and journal entries from Zoho Books for financial controls and DPDP Act data-processor evidence.",
        "evidence_types": [
            {"type": "zoho_books_invoice",  "label": "Invoices",           "control": "financial_controls", "typical_count": 120},
            {"type": "zoho_books_contact",  "label": "Contacts (clients)", "control": "data_protection",   "typical_count": 60},
            {"type": "zoho_books_journal",  "label": "Journal entries",    "control": "financial_controls", "typical_count": 40},
        ],
        "data_categories": ["financial", "pii"],
    },
    "payu": {
        "label": "PayU India",
        "description": "Payment transactions and merchant account data for PCI DSS and DPDP Act financial controls evidence.",
        "evidence_types": [
            {"type": "payu_transaction",   "label": "Payment transactions", "control": "financial_controls", "typical_count": 500},
            {"type": "payu_merchant_info", "label": "Merchant profile",     "control": "data_protection",   "typical_count": 1},
        ],
        "data_categories": ["financial", "pii"],
    },
    "razorpay": {
        "label": "Razorpay",
        "description": "Payment records, refunds, and settlement data for PCI DSS and DPDP Act financial controls evidence.",
        "evidence_types": [
            {"type": "razorpay_payment",    "label": "Payments",    "control": "financial_controls", "typical_count": 400},
            {"type": "razorpay_refund",     "label": "Refunds",     "control": "financial_controls", "typical_count": 30},
            {"type": "razorpay_settlement", "label": "Settlements", "control": "financial_controls", "typical_count": 20},
        ],
        "data_categories": ["financial", "pii"],
    },
    "zoho_payroll": {
        "label": "Zoho Payroll",
        "description": "Employee payroll runs, tax declarations, and workforce data for DPDP Act HR security and financial controls.",
        "evidence_types": [
            {"type": "zoho_payroll_employee",        "label": "Payroll employees",  "control": "hr_security",        "typical_count": 80},
            {"type": "zoho_payroll_run",             "label": "Payroll runs",       "control": "financial_controls", "typical_count": 12},
            {"type": "zoho_payroll_tax_declaration", "label": "Tax declarations",   "control": "data_protection",    "typical_count": 80},
        ],
        "data_categories": ["hr_data", "financial", "pii"],
    },
    # ── India — HR, KYC & Legal ───────────────────────────────────────────────
    "keka": {
        "label": "Keka HR",
        "description": "Employee directory, departments, and attendance data for HR security and DPDP Act workforce controls.",
        "evidence_types": [
            {"type": "keka_employee",   "label": "Employees",   "control": "hr_security", "typical_count": 100},
            {"type": "keka_department", "label": "Departments", "control": "hr_security", "typical_count": 12},
            {"type": "keka_attendance", "label": "Attendance",  "control": "hr_security", "typical_count": 100},
        ],
        "data_categories": ["hr_data", "user_identity", "pii"],
    },
    "leegality": {
        "label": "Leegality",
        "description": "Signed documents, templates, and audit trail for legal compliance and DPDP Act consent management evidence.",
        "evidence_types": [
            {"type": "leegality_document",    "label": "Signed documents",  "control": "legal_compliance", "typical_count": 80},
            {"type": "leegality_template",    "label": "Document templates", "control": "legal_compliance", "typical_count": 15},
            {"type": "leegality_audit_event", "label": "Audit trail events", "control": "legal_compliance", "typical_count": 200},
        ],
        "data_categories": ["audit_logs", "pii"],
    },
    "digilocker": {
        "label": "DigiLocker",
        "description": "Aadhaar-linked verified documents and user profile for DPDP Act identity verification and consent evidence.",
        "evidence_types": [
            {"type": "digilocker_issued_document",   "label": "Issued documents",   "control": "identity_verification", "typical_count": 5},
            {"type": "digilocker_uploaded_document", "label": "Uploaded documents", "control": "data_protection",       "typical_count": 3},
            {"type": "digilocker_user_profile",      "label": "Verified profile",   "control": "identity_verification", "typical_count": 1},
        ],
        "data_categories": ["pii", "user_identity"],
    },
    "signzy": {
        "label": "Signzy",
        "description": "KYC verifications, video KYC, and bank account verification records for DPDP Act and RBI compliance evidence.",
        "evidence_types": [
            {"type": "signzy_kyc_record",        "label": "KYC verifications",   "control": "identity_verification", "typical_count": 150},
            {"type": "signzy_digital_kyc",       "label": "Video KYC sessions",  "control": "identity_verification", "typical_count": 50},
            {"type": "signzy_bank_verification", "label": "Bank verifications",  "control": "financial_controls",    "typical_count": 80},
        ],
        "data_categories": ["pii", "user_identity", "financial"],
    },
    # ── US — Accounting ───────────────────────────────────────────────────────
    "quickbooks": {
        "label": "QuickBooks Online",
        "description": "Invoices, vendors, accounts, and employees from QuickBooks Online for financial controls and SOC 2 audit trail.",
        "evidence_types": [
            {"type": "qbo_invoice",  "label": "Invoices",         "control": "financial_controls", "typical_count": 150},
            {"type": "qbo_vendor",   "label": "Vendors",          "control": "vendor_management",  "typical_count": 40},
            {"type": "qbo_account",  "label": "Chart of accounts","control": "financial_controls", "typical_count": 30},
            {"type": "qbo_employee", "label": "Employees",        "control": "hr_security",        "typical_count": 20},
        ],
        "data_categories": ["financial", "hr_data", "pii"],
    },
    "xero": {
        "label": "Xero",
        "description": "Invoices, contacts, bank transactions, and user access from Xero for financial controls and audit evidence.",
        "evidence_types": [
            {"type": "xero_invoice",          "label": "Invoices",          "control": "financial_controls", "typical_count": 120},
            {"type": "xero_contact",          "label": "Contacts",          "control": "vendor_management",  "typical_count": 60},
            {"type": "xero_bank_transaction", "label": "Bank transactions", "control": "financial_controls", "typical_count": 200},
            {"type": "xero_user",             "label": "Xero users",        "control": "access_control",     "typical_count": 8},
        ],
        "data_categories": ["financial", "pii"],
    },
    # ── US — Legal & Contract Management ─────────────────────────────────────
    "ironclad": {
        "label": "Ironclad",
        "description": "Contract workflows, signers, and executed agreements for legal compliance, vendor management, and SOC 2 CC9 evidence.",
        "evidence_types": [
            {"type": "ironclad_workflow", "label": "Contract workflows", "control": "legal_compliance", "typical_count": 60},
            {"type": "ironclad_signer",   "label": "Contract signers",   "control": "legal_compliance", "typical_count": 80},
        ],
        "data_categories": ["audit_logs", "pii"],
    },
    # ── Logging ───────────────────────────────────────────────────────────────
    "papertrail": {
        "label": "Papertrail",
        "description": "Log systems, groups, saved searches, and recent events for logging and monitoring controls.",
        "evidence_types": [
            {"type": "papertrail_system",       "label": "Log sources",       "control": "logging_monitoring", "typical_count": 15},
            {"type": "papertrail_group",        "label": "Log groups",        "control": "logging_monitoring", "typical_count": 5},
            {"type": "papertrail_saved_search", "label": "Saved searches",    "control": "logging_monitoring", "typical_count": 8},
            {"type": "papertrail_log_event",    "label": "Recent log events", "control": "logging_monitoring", "typical_count": 100},
            {"type": "papertrail_account",      "label": "Account settings",  "control": "logging_monitoring", "typical_count": 1},
        ],
        "data_categories": ["audit_logs"],
    },
    # ── Data Management ───────────────────────────────────────────────────────
    "airtable": {
        "label": "Airtable",
        "description": "Tables, records, and collaborator access for data management and change management evidence.",
        "evidence_types": [
            {"type": "airtable_table",        "label": "Tables",        "control": "data_management",  "typical_count": 10},
            {"type": "airtable_record",       "label": "Records",       "control": "change_management","typical_count": 150},
            {"type": "airtable_collaborator", "label": "Collaborators", "control": "access_control",   "typical_count": 8},
        ],
        "data_categories": ["project_data", "user_identity"],
    },
}


# ── Data category regulatory metadata ─────────────────────────────────────────

DATA_CATEGORY_META: dict[str, dict] = {
    "user_identity": {
        "label": "User identity & access",
        "color": "blue",
        "regulatory_notes": [
            "GDPR Art. 5 — personal data (name, email, role) requires a lawful basis for processing",
            "SOC 2 CC6 — user account inventory supports access control evidence",
            "ISO 27001 A.9 — access management controls require documented user lists",
            "HIPAA §164.312(a) — workforce access authorisation must be documented",
        ],
    },
    "audit_logs": {
        "label": "Audit & event logs",
        "color": "purple",
        "regulatory_notes": [
            "SOC 2 CC7 — continuous audit logs are core monitoring evidence",
            "ISO 27001 A.12.4 — logging and monitoring controls require timestamped records",
            "HIPAA §164.312(b) — audit controls must record and examine system activity",
            "GDPR Art. 30 — processing activity records must be maintained",
        ],
    },
    "source_code": {
        "label": "Source code & commits",
        "color": "gray",
        "regulatory_notes": [
            "SOC 2 CC8 — change management requires PR approval records",
            "ISO 27001 A.12.1 — change management procedures must be documented",
        ],
    },
    "infrastructure": {
        "label": "Infrastructure & cloud resources",
        "color": "orange",
        "regulatory_notes": [
            "SOC 2 CC6 — asset inventory is required for access control",
            "ISO 27001 A.8 — asset management controls require a maintained inventory",
        ],
    },
    "authentication": {
        "label": "Authentication & MFA",
        "color": "green",
        "regulatory_notes": [
            "SOC 2 CC6 — MFA enforcement is a key access control criterion",
            "ISO 27001 A.9.4 — system access must use secure authentication",
            "HIPAA §164.312(d) — authentication of persons accessing ePHI is required",
        ],
    },
    "vulnerability_data": {
        "label": "Vulnerability & security findings",
        "color": "red",
        "regulatory_notes": [
            "SOC 2 CC7 — vulnerability management is a monitoring control requirement",
            "ISO 27001 A.12.6 — technical vulnerabilities must be managed",
            "PCI DSS 6.3 — security vulnerabilities must be identified and addressed",
        ],
    },
    "hr_data": {
        "label": "HR & employee records",
        "color": "teal",
        "regulatory_notes": [
            "GDPR Art. 9 — employment records may include special-category data",
            "HIPAA §164.308(a)(3) — workforce clearance procedures must be documented",
            "SOC 2 CC1 — background checks and training records support COSO principles",
        ],
    },
    "financial": {
        "label": "Financial & payment data",
        "color": "yellow",
        "regulatory_notes": [
            "PCI DSS — cardholder data environments require strict access control logging",
            "SOC 2 CC6 — financial system access must be monitored and recorded",
        ],
    },
    "communications": {
        "label": "Communications & messaging",
        "color": "indigo",
        "regulatory_notes": [
            "ISO 27001 A.13 — communications security controls require workspace audits",
            "GDPR Art. 32 — appropriate security of processing includes communication channels",
        ],
    },
    "project_data": {
        "label": "Project & issue tracking",
        "color": "slate",
        "regulatory_notes": [
            "SOC 2 CC8 — change management evidence includes issue tracking records",
            "ISO 27001 A.12.1 — operational procedures and responsibilities must be documented",
        ],
    },
    "pii": {
        "label": "Personal identifiable information (PII)",
        "color": "red",
        "regulatory_notes": [
            "GDPR Art. 5 — PII must be processed lawfully, fairly, and transparently",
            "GDPR Art. 25 — data protection by design and by default is required",
            "CCPA — consumers have rights to know, delete, and opt out of PII sale",
            "HIPAA §164.514 — de-identification standards apply to protected health information",
        ],
    },
}
