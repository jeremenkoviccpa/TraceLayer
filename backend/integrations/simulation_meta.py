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
}
