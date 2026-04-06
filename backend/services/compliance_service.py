import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from models.control import Control
from models.evidence import Evidence
from models.score_snapshot import ScoreSnapshot

# Expected evidence types per framework per control category.
# Coverage score = how many expected types are present in collected evidence.
EXPECTED_TYPES: dict[str, dict[str, set[str]]] = {
    "soc2": {
        # CC1-2: Control environment — entity-level controls, tone at top, COSO
        "control_environment": {
            "iam_policies",
            "okta_policies",
            "github_repositories",
            "azure_roles",
        },
        # CC3, CC9.1: Risk assessment, risk management process
        "risk_assessment": {
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "iam_policies",
        },
        # CC6.1: Logical and physical access controls — identity and access management
        "access_control": {
            "iam_users", "iam_policies",
            "github_members", "github_admin_members",
            "slack_users",
            "workspace_users", "workspace_admin_members",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "jira_users",
        },
        # CC6.2-3: Privileged access, role-based access controls
        "privileged_access": {
            "iam_policies",
            "okta_groups",
            "azure_roles",
            "github_admin_members",
            "vault_policy", "vault_auth_method",
        },
        # CC4, CC7.1-2: Monitoring, SIEM, log management, anomaly detection
        "logging_monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_saved_searches", "splunk_alerts",
            "crowdstrike_detections",
            "sentinelone_threats",
            "wiz_issues",
        },
        # CC7.3-5: Incident detection, response, and resolution
        "incident_response": {
            "pagerduty_incidents", "pagerduty_services", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_schedules", "opsgenie_escalations",
        },
        # CC8.1: Change management — authorised, tested, and approved changes
        "change_management": {
            "github_repositories",
            "jira_projects",
            "servicenow_changes",
            "gitlab_repositories",
        },
        # CC6.6-7: Endpoint security — device management and malware protection
        "endpoint_security": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers", "jamf_policies",
            "kandji_devices", "kandji_blueprints",
            "kolide",
        },
        # CC5.3, CC7.1: Vulnerability identification and remediation
        "vulnerability_management": {
            "snyk_projects",
            "vulnerability_scans",
            "wiz_issues",
            "crowdstrike_detections",
            "hackerone_reports",
            "detectify_findings",
        },
        # CC9.2: Vendor risk management — third-party supplier assessments
        "vendor_risk": {
            "github_repositories",
            "snyk_projects",
            "wiz_issues",
            "cloudtrail_logs",
        },
        # A1.1-3: Availability — uptime SLOs, monitoring, DR, backup
        "availability": {
            "pagerduty_services",
            "datadog_slos", "datadog_monitors",
            "servicenow_changes",
            "vault_secrets_engine",
        },
        # C1.1-2: Confidentiality — encryption at rest and in transit
        "confidentiality": {
            "iam_policies",
            "vault_secrets_engine", "vault_policy",
            "cloudtrail_logs",
            "wiz_issues",
        },
    },
    "iso27001": {
        # A.5.15-18, A.8.2-3: Access control policy, user access mgmt, privileged access
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "workspace_users", "workspace_admin_members",
            "slack_users",
            "jira_users",
        },
        # A.8.8, A.8.19: Technical vulnerability management and patch SLAs
        "vulnerability_management": {
            "snyk_projects",
            "vulnerability_scans",
            "wiz_issues",
            "crowdstrike_detections",
            "hackerone_reports", "hackerone_programs",
            "detectify_findings",
            "assets",
        },
        # A.8.15-17: Event logging, security monitoring, clock synchronisation
        "logging_and_monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_saved_searches", "splunk_alerts",
            "grafana",
            "elastic",
        },
        # A.8.1, A.8.7: Endpoint devices, malware protection, MDM compliance
        "endpoint_security": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers", "jamf_policies",
            "kandji_devices", "kandji_blueprints",
            "kolide",
            "tailscale_devices",
        },
        # A.8.24: Cryptography policy, encryption, key management, certificates
        "cryptography": {
            "vault_secrets_engine", "vault_policy", "vault_auth_method",
            "iam_policies",
            "cloudtrail_logs",
        },
        # A.5.14, A.8.20-22: Network security, service security, segregation
        "network_security": {
            "cloudflare_security_settings", "cloudflare_zones",
            "tailscale_acl", "tailscale_devices",
            "network_policies",
            "pods",
        },
        # A.5.19-23: Supplier agreements, cloud service security, ongoing monitoring
        "supplier_security": {
            "github_repositories",
            "snyk_projects",
            "wiz_issues",
            "cloudtrail_logs",
        },
        # A.5.24-28: Incident classification, response, post-incident review, evidence
        "incident_management": {
            "pagerduty_incidents", "pagerduty_services", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_schedules", "opsgenie_escalations",
        },
        # A.5.29-30: BCM, ICT continuity, RTO/RPO, DR testing
        "business_continuity": {
            "pagerduty_services",
            "datadog_slos", "datadog_monitors",
            "servicenow_changes",
            "vault_secrets_engine",
        },
        # A.8.32-33: Change management procedures, test information management
        "change_management": {
            "github_repositories",
            "jira_projects",
            "servicenow_changes",
            "gitlab_repositories",
        },
        # A.8.25-31: Secure SDLC, secure coding, security testing, DAST/SAST
        "secure_development": {
            "github_repositories",
            "snyk_projects",
            "hackerone_reports",
            "detectify_findings",
            "wiz_issues",
        },
        # A.6.1-6.8: Screening, training, disciplinary, termination, remote working
        "hr_security": {
            "okta_users",
            "azure_users",
            "workspace_users",
            "iam_users",
            "slack_users",
        },
        # A.5.9-14: Asset inventory, acceptable use, classification, labelling
        "asset_management": {
            "github_repositories",
            "assets",
            "cloudtrail_logs",
            "iam_policies",
        },
        # A.5.1-8: Security policy, roles, segregation of duties, project security
        "organizational_controls": {
            "iam_policies",
            "okta_policies",
            "github_repositories",
            "azure_roles",
        },
    },
    "hipaa": {
        # §164.308(a)(1): Risk analysis, risk management, sanction policy, IS activity review
        "security_management": {
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "cloudtrail_logs",
            "iam_policies",
        },
        # §164.308(a)(3): Authorisation, supervision, workforce clearance, termination
        "workforce_security": {
            "okta_users", "okta_groups",
            "azure_users", "azure_roles",
            "workspace_users",
            "iam_users",
            "slack_users",
        },
        # §164.308(a)(4): Access authorisation, establishment and modification
        "information_access_management": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "workspace_users",
        },
        # §164.308(a)(5): Security awareness training, protection from malicious software,
        # log-in monitoring, password management
        "security_awareness": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers",
            "kandji_devices",
            "okta_users",
        },
        # §164.308(a)(6): Incident reporting, response, mitigation, documentation
        "incident_procedures": {
            "pagerduty_incidents", "pagerduty_services", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_schedules",
            "cloudtrail_logs",
        },
        # §164.308(a)(7): Contingency plan — data backup, DR, emergency mode, testing
        "contingency_plan": {
            "pagerduty_services",
            "datadog_slos", "datadog_monitors",
            "servicenow_changes",
            "vault_secrets_engine",
        },
        # §164.312(a): Unique user identification, emergency access, auto logoff, encryption
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_policies",
            "azure_users",
            "vault_policy", "vault_auth_method",
        },
        # §164.312(b): Audit controls — hardware, software, and procedural mechanisms
        "audit_controls": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_saved_searches", "splunk_alerts",
        },
        # §164.312(e): Transmission security — encryption and integrity controls
        "transmission_security": {
            "cloudflare_security_settings", "cloudflare_zones",
            "iam_policies",
            "vault_secrets_engine",
            "network_policies",
        },
    },
    # ── GDPR (EU 2016/679) ────────────────────────────────────────────────────────
    "gdpr": {
        # Art.6-9: Lawful basis for processing, consent management, special categories
        "lawful_basis": {
            "iam_users", "iam_policies",
            "okta_users", "okta_policies",
            "azure_users",
            "workspace_users",
            "dlp_policies",
        },
        # Art.15-22: Access, rectification, erasure, portability, objection rights
        "data_subject_rights": {
            "iam_users",
            "okta_users", "azure_users",
            "workspace_users",
            "jira_projects",
            "servicenow_incidents",
        },
        # Art.25: Data protection by design and by default
        "privacy_by_design": {
            "iam_policies",
            "okta_policies",
            "wiz_issues",
            "snyk_projects",
            "github_repositories",
        },
        # Art.37-39: DPO designation, tasks, and position
        "data_protection_officer": {
            "iam_users",
            "okta_users",
            "workspace_users",
        },
        # Art.30: Records of processing activities (ROPA)
        "records_of_processing": {
            "github_repositories",
            "iam_policies",
            "cloudtrail_logs",
        },
        # Art.28: Data processing agreements with processors
        "processor_agreements": {
            "github_repositories",
            "snyk_projects",
            "iam_policies",
        },
        # Art.33-34: 72-hour breach notification to supervisory authority
        "breach_notification": {
            "pagerduty_incidents", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts",
            "cloudtrail_logs",
            "datadog_monitors",
        },
        # Art.35-36: Data protection impact assessment, prior consultation
        "data_protection_impact": {
            "vulnerability_scans",
            "wiz_issues",
            "iam_policies",
            "github_repositories",
        },
        # Art.44-49: Transfer to third countries — adequacy, SCCs, BCRs
        "cross_border_transfers": {
            "cloudflare_security_settings",
            "iam_policies",
            "cloudtrail_logs",
            "network_policies",
        },
        # Art.32: Security of processing — encryption, pseudonymisation, resilience
        "security_of_processing": {
            "iam_policies", "iam_users",
            "cloudtrail_logs",
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "crowdstrike_policies",
            "vault_secrets_engine", "vault_policy",
        },
    },
    # ── PCI DSS v4.0 ─────────────────────────────────────────────────────────────
    "pci_dss": {
        # Req.1-2: Network security controls — firewalls, network segmentation
        "network_security_controls": {
            "cloudflare_security_settings", "cloudflare_zones",
            "network_policies",
            "tailscale_acl", "tailscale_devices",
            "wiz_issues",
        },
        # Req.2: Secure configuration — vendor defaults removed, hardening standards
        "secure_configuration": {
            "wiz_issues",
            "crowdstrike_policies",
            "iam_policies",
            "github_repositories",
        },
        # Req.3: Protection of stored account data — encryption, masking, retention
        "data_protection": {
            "vault_secrets_engine", "vault_policy",
            "iam_policies",
            "wiz_issues",
            "cloudtrail_logs",
        },
        # Req.4: Encryption of cardholder data in transit — TLS, certificates
        "encryption_in_transit": {
            "cloudflare_security_settings", "cloudflare_zones",
            "iam_policies",
            "vault_secrets_engine",
            "network_policies",
        },
        # Req.6, 11.3: Vulnerability management — patching, dependency scanning
        "vulnerability_management": {
            "snyk_projects",
            "vulnerability_scans",
            "wiz_issues",
            "crowdstrike_detections",
            "hackerone_reports",
            "detectify_findings",
        },
        # Req.7-8: Access control — least privilege, user ID management
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "vault_policy", "vault_auth_method",
        },
        # Req.9: Restrict physical access to cardholder data
        "physical_access": {
            "crowdstrike_devices",
            "jamf_computers",
            "kandji_devices",
            "iam_policies",
        },
        # Req.10: Log all access to network resources and cardholder data
        "logging_monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_saved_searches", "splunk_alerts",
            "crowdstrike_detections",
        },
        # Req.11: Security testing — penetration testing, vulnerability scans
        "security_testing": {
            "hackerone_reports", "hackerone_programs",
            "detectify_findings", "detectify_scan_profiles",
            "snyk_projects",
            "vulnerability_scans",
            "wiz_issues",
        },
        # Req.12: Security policy — maintain, review, and communicate
        "security_policy": {
            "github_repositories",
            "iam_policies",
            "okta_policies",
        },
        # Req.12.8: Third-party/service provider management
        "service_provider_management": {
            "github_repositories",
            "snyk_projects",
            "wiz_issues",
            "cloudtrail_logs",
        },
        # Req.8.4-5: Multi-factor authentication for all access
        "mfa_and_authentication": {
            "okta_users", "okta_policies",
            "azure_users", "azure_roles",
            "iam_policies",
            "mfa_policies", "mfa_enrollments",
        },
    },
    # ── NIST Cybersecurity Framework 2.0 ─────────────────────────────────────────
    "nist_csf": {
        # GV: Governance — cybersecurity strategy, roles, policy, oversight
        "govern": {
            "iam_policies",
            "okta_policies",
            "github_repositories",
            "azure_roles",
        },
        # ID: Identify — asset management, risk assessment, supply chain risk
        "identify": {
            "assets",
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "cloudtrail_logs",
            "github_repositories",
        },
        # PR: Protect — identity management, awareness training, data security
        "protect": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "crowdstrike_devices", "crowdstrike_policies",
            "jamf_computers",
            "kandji_devices",
            "vault_secrets_engine",
        },
        # DE: Detect — anomalies, events, continuous monitoring
        "detect": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_saved_searches", "splunk_alerts",
            "crowdstrike_detections",
            "sentinelone_threats",
            "wiz_issues",
        },
        # RS: Respond — incident response planning, communications, mitigation
        "respond": {
            "pagerduty_incidents", "pagerduty_services", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_schedules",
        },
        # RC: Recover — recovery planning, improvements, communications
        "recover": {
            "pagerduty_services",
            "datadog_slos",
            "servicenow_changes",
            "vault_secrets_engine",
        },
    },
    # ── CCPA / CPRA (California Consumer Privacy Act) ────────────────────────────
    "ccpa": {
        # §1798.100-130: Consumer rights — know, delete, correct, portability
        "consumer_rights": {
            "iam_users",
            "okta_users", "azure_users",
            "workspace_users",
            "jira_projects",
            "servicenow_incidents",
        },
        # §1798.100(b): Privacy notice at collection — disclosure of categories
        "privacy_notice": {
            "github_repositories",
            "iam_policies",
            "cloudtrail_logs",
        },
        # §1798.140: Data inventory — categories of PI collected, sold, disclosed
        "data_inventory": {
            "iam_policies",
            "cloudtrail_logs",
            "wiz_issues",
            "snyk_projects",
            "assets",
        },
        # §1798.120, 1798.135: Opt-out of sale/sharing, do not sell links
        "opt_out_mechanisms": {
            "iam_policies",
            "okta_policies",
            "cloudtrail_logs",
        },
        # §1798.140(ag): Service provider/contractor data sharing agreements
        "service_provider_contracts": {
            "github_repositories",
            "snyk_projects",
            "iam_policies",
        },
        # §1798.121, 1798.100(d): Sensitive PI — use limitation and disclosure controls
        "sensitive_personal_information": {
            "iam_policies",
            "vault_secrets_engine",
            "wiz_issues",
            "crowdstrike_policies",
            "okta_policies",
        },
    },
    "dpdp": {
        # Sec.4-7: Lawful basis, consent records, notice — India-specific consent
        # management tools are primary evidence; DLP + IAM as supporting evidence
        "lawful_processing": {
            "leegality_documents", "leegality_templates",
            "digilocker_documents", "digilocker_issued_documents",
            "signzy_verifications",
            "nightfall_policies", "nightfall_detectors",
            "okta_users", "azure_users", "workspace_users",
            "iam_policies",
        },
        # Sec.8, 8.3, 10: Security safeguards, data erasure, processor agreements
        "data_fiduciary_obligations": {
            "cloudtrail_logs",
            "iam_policies", "iam_users",
            "nightfall_policies", "nightfall_detectors",
            "wiz_issues",
            "crowdstrike_policies", "sentinelone_agents",
            "github_repositories",
        },
        # Sec.9: Children's data — DLP + identity/age-verification integrations
        "special_categories": {
            "nightfall_policies", "nightfall_detectors",
            "iam_policies", "okta_policies",
            "signzy_verifications",
        },
        # Sec.11-14, 17: DSR records are primary evidence — auto-generated
        # from Subject Requests module completions; supplemented by ticketing
        "data_principal_rights": {
            "dsr_records",
            "jira_projects", "servicenow_incidents",
            "okta_users", "workspace_users", "azure_users",
        },
        # Sec.8.6: DPBI breach notification records + detection capabilities
        "breach_notification": {
            "dpbi_notifications",
            "pagerduty_incidents", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_escalations",
            "sentinelone_threats", "wiz_issues",
            "cloudtrail_logs",
        },
        # Sec.16: Cross-border transfer controls — network policies + cloud region
        "cross_border_transfers": {
            "cloudflare_security_settings", "cloudflare_zones",
            "tailscale_acl",
            "iam_policies",
            "cloudtrail_logs",
        },
    },
    "cert_in": {
        # Dir.1, 5: 6-hour incident reporting — ticketing and on-call platforms
        # are primary evidence; certin_incidents is a native evidence type
        # generated when incidents are filed with CERT-In from the Incidents module
        "incident_reporting": {
            "certin_incidents",
            "pagerduty_services", "pagerduty_incidents",
            "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_escalations", "opsgenie_schedules",
        },
        # Dir.2, 12: NTP sync evidenced through timestamped audit logs;
        # cloud posture + hardening evidenced through security tools
        "it_infrastructure": {
            "cloudtrail_logs",
            "iam_policies",
            "network_policies", "pods",
            "wiz_issues",
            "crowdstrike_policies",
            "github_repositories",
        },
        # Dir.3: 180-day log retention — SIEM + CloudTrail are primary evidence;
        # Indian jurisdiction confirmed through storage region configuration
        "log_management": {
            "cloudtrail_logs",
            "splunk_saved_searches", "splunk_alerts",
            "datadog_monitors",
            "datadog_logs",
        },
        # Dir.4: KYC for VPS/VPN/cloud/DC providers — India-specific identity
        # verification tools are primary; IAM user records as supporting evidence
        "identity_verification": {
            "signzy_verifications",
            "okta_users", "azure_users",
            "workspace_users", "jira_users",
            "iam_users",
        },
        # Dir.6: Incident response plan — escalation policies, schedules, and
        # change records demonstrate a documented and tested IRP
        "incident_response": {
            "pagerduty_escalation_policies", "pagerduty_schedules", "pagerduty_services",
            "servicenow_incidents", "servicenow_changes",
            "opsgenie_schedules", "opsgenie_escalations",
        },
        # Dir.7: VA/PT + advisory response — scan results and exploit management
        "vulnerability_management": {
            "snyk_projects",
            "vulnerability_scans", "assets",
            "wiz_issues",
            "hackerone_reports", "hackerone_programs",
            "detectify_findings", "detectify_scan_profiles",
            "crowdstrike_detections",
            "github_repositories",
        },
        # Dir.8: MFA + PAM — all identity platforms with MFA/policy evidence;
        # vault for privileged access session logging
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_groups", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "workspace_users",
            "mfa_policies", "mfa_enrollments",
            "vault_auth_method", "vault_policy",
        },
        # Dir.9: Backups + BCP/DR — uptime monitoring and change records
        # demonstrate backup and continuity posture
        "resilience": {
            "pagerduty_services",
            "servicenow_changes",
            "vault_secrets_engine",
            "datadog_monitors",
            "datadog_slos",
        },
        # Dir.10: Continuous monitoring — SIEM, EDR, and cloud posture tools
        "monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_alerts",
            "crowdstrike_detections",
            "sentinelone_threats",
            "wiz_issues",
            "network_policies",
        },
        # Dir.11: Endpoint protection + MDM + encryption enforcement
        "endpoint_security": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers", "jamf_policies",
            "kandji_devices", "kandji_blueprints",
            "tailscale_devices",
        },
    },
    # ── Serbian LPDP (Law on Personal Data Protection, Official Gazette 87/2018) ──
    "lpdp": {
        # Art.5-11: Lawful basis — IAM and DLP tools demonstrate controlled access
        # and data handling consistent with specified lawful processing grounds
        "lawful_processing": {
            "iam_users", "iam_policies",
            "okta_users", "okta_policies",
            "azure_users",
            "workspace_users",
            "dlp_policies",
        },
        # Art.26-39: DSR handling — subject request records are primary evidence;
        # user directory data supports identity verification for access requests
        "data_subject_rights": {
            "iam_users",
            "okta_users", "azure_users",
            "workspace_users",
        },
        # Art.40-43, 54-56: ROPA, DPbD, DPIAs — policy documents and risk register
        # are the primary evidence artefacts
        "controller_obligations": {
            "github_repositories",
            "iam_policies",
            "okta_policies",
        },
        # Art.49: Technical/organizational security — IAM policies, audit logs,
        # and vulnerability tools demonstrate appropriate security measures
        "data_security": {
            "iam_policies",
            "cloudtrail_logs",
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "crowdstrike_policies",
            "okta_policies",
        },
        # Art.53: 72-hour Poverenik breach notification
        "breach_notification": {
            "cloudtrail_logs",
            "datadog_monitors",
            "pagerduty_incidents",
        },
        # Art.57-61: DPO appointment and registration with Poverenik
        "dpo_requirements": {
            "iam_users",
            "okta_users",
            "workspace_users",
        },
        # Art.65-74: Cross-border transfers — data flow configs and IAM policies
        # demonstrate transfer controls and adequacy safeguards
        "cross_border_transfers": {
            "iam_policies",
            "cloudtrail_logs",
            "network_policies",
        },
    },
    # ── NIS2 Directive (EU 2022/2555) ────────────────────────────────────────────
    "nis2": {
        # Art.21.2a: Risk management policy — vulnerability tools and risk register
        "risk_management": {
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "github_repositories",
            "iam_policies",
        },
        # Art.21.2b: Incident handling — on-call and ticketing platforms
        "incident_handling": {
            "pagerduty_incidents", "pagerduty_services", "pagerduty_escalation_policies",
            "servicenow_incidents",
            "opsgenie_alerts", "opsgenie_schedules",
        },
        # Art.21.2c: Business continuity — BCP and backup evidence
        "business_continuity": {
            "pagerduty_services",
            "datadog_monitors", "datadog_slos",
            "servicenow_changes",
            "vault_secrets_engine",
        },
        # Art.21.2d: Supply chain security — vendor and dependency scanning
        "supply_chain_security": {
            "snyk_projects",
            "github_repositories",
            "wiz_issues",
        },
        # Art.21.2e: Network and system security — cloud posture + vuln management
        "network_security": {
            "cloudtrail_logs",
            "iam_policies",
            "network_policies",
            "wiz_issues",
            "vulnerability_scans",
            "crowdstrike_policies",
        },
        # Art.21.2i: Access control and MFA
        "access_control": {
            "iam_users", "iam_policies",
            "okta_users", "okta_policies",
            "azure_users", "azure_roles",
            "github_members", "github_admin_members",
            "mfa_policies", "mfa_enrollments",
        },
        # Art.21.2h: Cryptography and encryption
        "cryptography": {
            "iam_policies",
            "cloudtrail_logs",
            "vault_secrets_engine", "vault_policy",
        },
        # Art.21.2g: Cyber hygiene and security training
        "cyber_hygiene": {
            "crowdstrike_devices", "crowdstrike_policies",
            "sentinelone_agents",
            "jamf_computers",
            "kandji_devices",
        },
        # Art.21.2e (monitoring): Security event monitoring and audit logging
        "logging_monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_alerts", "splunk_saved_searches",
            "crowdstrike_detections",
            "sentinelone_threats",
        },
        # Art.23: 3-stage CSIRT incident reporting (24h, 72h, 1 month)
        "incident_reporting": {
            "pagerduty_incidents", "pagerduty_services",
            "servicenow_incidents",
            "opsgenie_alerts",
        },
    },
    # ── ISO/IEC 42001:2023 (AI Management System) ─────────────────────────────
    "iso42001": {
        # Cl.4-5, 6.2: AI governance policy, roles, objectives, management reviews
        "ai_governance": {
            "iam_policies",
            "iam_users",
            "github_repositories",
            "okta_groups",
            "azure_roles",
        },
        # Cl.6.1: AI risk assessment and treatment plan
        "ai_risk_management": {
            "vulnerability_scans",
            "wiz_issues",
            "snyk_projects",
            "github_repositories",
        },
        # Cl.7: AI competence, training, and awareness programme
        "ai_competence": {
            "okta_users",
            "azure_users",
            "workspace_users",
            "iam_users",
        },
        # Cl.8.3: AI system impact assessment before deployment
        "ai_impact_assessment": {
            "github_repositories",
            "iam_policies",
        },
        # Cl.8.4: Training data governance — quality, provenance, bias, retention
        "data_governance": {
            "iam_policies",
            "cloudtrail_logs",
            "okta_policies",
            "wiz_issues",
        },
        # Cl.8.5: AI system development, testing, and validation artefacts
        "ai_development": {
            "github_repositories",
            "snyk_projects",
            "vulnerability_scans",
            "crowdstrike_policies",
        },
        # Cl.8.6: Human oversight mechanisms and intervention capabilities
        "human_oversight": {
            "iam_policies",
            "iam_users",
            "cloudtrail_logs",
            "pagerduty_services",
        },
        # Cl.9: Performance monitoring, internal audit, management review
        "ai_monitoring": {
            "cloudtrail_logs",
            "datadog_monitors", "datadog_logs",
            "splunk_alerts",
            "wiz_issues",
        },
        # Cl.10: Nonconformity handling and continual improvement records
        "continual_improvement": {
            "github_repositories",
            "jira_projects",
            "servicenow_changes",
        },
        # A.6.1: Transparency — model cards, explainability docs, disclosure notices
        "transparency": {
            "github_repositories",
            "cloudtrail_logs",
        },
        # A.6.2: Bias detection and fairness metric monitoring
        "fairness": {
            "vulnerability_scans",
            "cloudtrail_logs",
            "datadog_monitors",
        },
        # A.8.2: Privacy-by-design, AI DPIA, data minimisation controls
        "ai_privacy": {
            "iam_policies",
            "okta_policies",
            "cloudtrail_logs",
            "wiz_issues",
        },
        # A.9.1: AI incident detection, investigation, rollback capabilities
        "ai_incident_management": {
            "pagerduty_incidents", "pagerduty_services",
            "servicenow_incidents",
            "opsgenie_alerts",
            "cloudtrail_logs",
        },
        # A.10.1: Third-party AI supplier risk assessment and contractual controls
        # Primary evidence: AI provider model inventory + org/project/key configuration.
        # Supporting evidence: dependency scanning and cloud posture tools.
        "ai_supply_chain": {
            # OpenAI — model inventory, org config, project structure, API key audit
            "openai_models",
            "openai_organization",
            "openai_projects",
            "openai_api_keys",
            # Anthropic — Claude model inventory, workspaces, API key audit
            "anthropic_models",
            "anthropic_workspaces",
            "anthropic_api_keys",
            # Google Gemini — model inventory and configuration
            "gemini_models",
            # Supporting: dependency scanning + cloud posture for AI workloads
            "snyk_projects",
            "github_repositories",
            "wiz_issues",
            "vulnerability_scans",
        },
    },
}


def _compute_score(
    covered: set[str],
    expected: set[str],
    latest: Optional[datetime],
    total_count: int,
    reference: Optional[datetime] = None,
) -> int:
    if not expected:
        return 0

    coverage_ratio = len(covered) / len(expected)
    score = coverage_ratio * 70  # up to 70 from coverage

    # Recency bonus (up to 20) — relative to `reference` (defaults to now)
    if latest:
        ref = reference or datetime.now(timezone.utc)
        latest_tz = latest.replace(tzinfo=timezone.utc) if latest.tzinfo is None else latest
        age_days = (ref - latest_tz).days
        if age_days <= 7:
            score += 20
        elif age_days <= 30:
            score += 10

    # Volume bonus (up to 10)
    if total_count >= 10:
        score += 10
    elif total_count >= 3:
        score += 5

    return min(100, int(score))


async def get_compliance_score(
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
) -> dict:
    controls_result = await db.execute(
        select(Control).where(Control.framework == framework)
    )
    controls = list(controls_result.scalars().all())

    # Aggregate evidence by control + evidence_type
    rows = await db.execute(
        select(
            Evidence.control,
            Evidence.evidence_type,
            func.count().label("cnt"),
            func.max(Evidence.timestamp).label("latest"),
        )
        .where(Evidence.company_id == company_id)
        .group_by(Evidence.control, Evidence.evidence_type)
    )

    # Build lookup: control_category -> {types, count, latest}
    by_control: dict[str, dict] = {}
    for row in rows:
        entry = by_control.setdefault(row.control, {"types": set(), "count": 0, "latest": None})
        entry["types"].add(row.evidence_type)
        entry["count"] += row.cnt
        if row.latest and (entry["latest"] is None or row.latest > entry["latest"]):
            entry["latest"] = row.latest

    control_scores = []

    for control in controls:
        ev = by_control.get(control.category, {"types": set(), "count": 0, "latest": None})
        covered = ev["types"]
        count = ev["count"]
        latest = ev["latest"]
        expected = EXPECTED_TYPES.get(framework, {}).get(control.category, set())

        score = _compute_score(covered, expected, latest, count)

        if count == 0:
            status = "no_evidence"
        elif score >= 80:
            status = "passing"
        elif score >= 50:
            status = "warning"
        else:
            status = "failing"

        control_scores.append({
            "category": control.category,
            "name": control.name,
            "score": score,
            "status": status,
            "evidence_count": count,
            "covered_types": sorted(covered),
            "missing_types": sorted(expected - covered),
            "last_collected": latest.isoformat() if latest else None,
        })

    # Apply risk exceptions and control exclusions
    now = datetime.now(timezone.utc)
    try:
        from models.risk_exception import RiskException
        from models.control_exclusion import ControlExclusion

        exceptions = (await db.execute(
            select(RiskException).where(
                RiskException.company_id == company_id,
                RiskException.framework == framework,
                RiskException.status == "active",
            )
        )).scalars().all()
        active_exceptions = {
            e.control_category: e for e in exceptions
            if not e.expires_at or e.expires_at > now
        }

        exclusions = (await db.execute(
            select(ControlExclusion).where(
                ControlExclusion.company_id == company_id,
                ControlExclusion.framework == framework,
            )
        )).scalars().all()
        excluded_categories = {e.control_category: e for e in exclusions}

        for cs in control_scores:
            cat = cs["category"]
            if cat in excluded_categories:
                excl = excluded_categories[cat]
                cs["status"] = "excluded"
                cs["exclusion"] = {
                    "justification": excl.justification,
                    "type": excl.exclusion_type,
                    "id": str(excl.id),
                }
            elif cs["status"] == "failing" and cat in active_exceptions:
                exc = active_exceptions[cat]
                cs["status"] = "exception"
                cs["exception"] = {
                    "justification": exc.justification,
                    "owner_name": exc.owner_name,
                    "owner_email": exc.owner_email,
                    "expires_at": exc.expires_at.isoformat() if exc.expires_at else None,
                    "id": str(exc.id),
                }
    except Exception:
        pass  # Tables may not exist yet during migration

    # Overall score excludes "excluded" controls
    scoring = [cs for cs in control_scores if cs["status"] != "excluded"]
    total = sum(cs["score"] for cs in scoring)
    overall = int(total / len(scoring)) if scoring else 0

    # Snapshot at most once per hour per company+framework
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    existing = await db.execute(
        select(ScoreSnapshot.id)
        .where(
            ScoreSnapshot.company_id == company_id,
            ScoreSnapshot.framework == framework,
            ScoreSnapshot.snapshot_at >= cutoff,
        )
        .limit(1)
    )
    if not existing.scalar():
        db.add(ScoreSnapshot(
            company_id=company_id,
            framework=framework,
            overall_score=overall,
            snapshot_at=datetime.now(timezone.utc),
        ))
        await db.commit()

    return {
        "framework": framework,
        "overall_score": overall,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "controls": control_scores,
    }


async def get_score_history(
    company_id: uuid.UUID,
    framework: str,
    days: int,
    db: AsyncSession,
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await db.execute(
        select(ScoreSnapshot.overall_score, ScoreSnapshot.snapshot_at)
        .where(
            ScoreSnapshot.company_id == company_id,
            ScoreSnapshot.framework == framework,
            ScoreSnapshot.snapshot_at >= since,
        )
        .order_by(ScoreSnapshot.snapshot_at)
    )
    return [
        {"score": row.overall_score, "ts": row.snapshot_at.isoformat()}
        for row in rows
    ]


async def get_compliance_score_at(
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
    as_of: datetime,
) -> dict:
    """
    Point-in-time compliance score. Filters evidence to records that existed
    at `as_of` (Evidence.created_at <= as_of) and computes the score using
    `as_of` as the recency reference, so the result reflects compliance state
    on that exact date rather than today.
    """
    controls_result = await db.execute(
        select(Control).where(Control.framework == framework)
    )
    controls = list(controls_result.scalars().all())

    # Ensure as_of is timezone-aware
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    rows = await db.execute(
        select(
            Evidence.control,
            Evidence.evidence_type,
            func.count().label("cnt"),
            func.max(Evidence.timestamp).label("latest"),
        )
        .where(
            Evidence.company_id == company_id,
            Evidence.created_at <= as_of,
        )
        .group_by(Evidence.control, Evidence.evidence_type)
    )

    by_control: dict[str, dict] = {}
    for row in rows:
        entry = by_control.setdefault(row.control, {"types": set(), "count": 0, "latest": None})
        entry["types"].add(row.evidence_type)
        entry["count"] += row.cnt
        if row.latest and (entry["latest"] is None or row.latest > entry["latest"]):
            entry["latest"] = row.latest

    control_scores = []
    total = 0

    for control in controls:
        ev = by_control.get(control.category, {"types": set(), "count": 0, "latest": None})
        covered = ev["types"]
        count = ev["count"]
        latest = ev["latest"]
        expected = EXPECTED_TYPES.get(framework, {}).get(control.category, set())

        score = _compute_score(covered, expected, latest, count, reference=as_of)

        if count == 0:
            status = "no_evidence"
        elif score >= 80:
            status = "passing"
        elif score >= 50:
            status = "warning"
        else:
            status = "failing"

        control_scores.append({
            "category": control.category,
            "name": control.name,
            "score": score,
            "status": status,
            "evidence_count": count,
            "covered_types": sorted(covered),
            "missing_types": sorted(expected - covered),
            "last_collected": latest.isoformat() if latest else None,
        })
        total += score

    overall = int(total / len(control_scores)) if control_scores else 0

    return {
        "framework": framework,
        "overall_score": overall,
        "evaluated_at": as_of.isoformat(),
        "controls": control_scores,
    }


async def take_daily_snapshots_all_companies() -> None:
    """
    Nightly job: persist one ScoreSnapshot per company per framework so the
    time-machine endpoint always has dense historical data even for companies
    that haven't opened the dashboard recently.
    """
    import logging
    from models.company import Company
    from core.database import AsyncSessionLocal

    logger = logging.getLogger(__name__)
    frameworks = list(EXPECTED_TYPES.keys())
    now = datetime.now(timezone.utc)
    # Use midnight (start of day) as the canonical snapshot time
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    try:
        async with AsyncSessionLocal() as db:
            company_ids_result = await db.execute(select(Company.id))
            company_ids = [row[0] for row in company_ids_result.all()]

        for company_id in company_ids:
            for fw in frameworks:
                try:
                    async with AsyncSessionLocal() as db:
                        # Skip if a snapshot already exists for today
                        existing = await db.execute(
                            select(ScoreSnapshot.id)
                            .where(
                                ScoreSnapshot.company_id == company_id,
                                ScoreSnapshot.framework == fw,
                                ScoreSnapshot.snapshot_at >= today_midnight,
                            )
                            .limit(1)
                        )
                        if existing.scalar():
                            continue

                        result = await get_compliance_score_at(
                            company_id, fw, db, as_of=now
                        )
                        db.add(ScoreSnapshot(
                            company_id=company_id,
                            framework=fw,
                            overall_score=result["overall_score"],
                            snapshot_at=now,
                        ))
                        await db.commit()
                except Exception as exc:
                    logger.warning(
                        "Daily snapshot failed for company=%s fw=%s: %s",
                        company_id, fw, exc,
                    )
    except Exception as exc:
        logger.error("Daily snapshot job failed: %s", exc)


async def get_evidence_activity(
    company_id: uuid.UUID,
    days: int,
    db: AsyncSession,
) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = await db.execute(
        select(
            cast(Evidence.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(Evidence.company_id == company_id, Evidence.created_at >= since)
        .group_by(cast(Evidence.created_at, Date))
        .order_by(cast(Evidence.created_at, Date))
    )
    return [{"day": str(row.day), "count": row.cnt} for row in rows]
