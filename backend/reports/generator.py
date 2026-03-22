"""
PDF report generator using ReportLab (pure Python, no system dependencies).
"""
import logging
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)

# ── Brand colours ─────────────────────────────────────────────────────────────
TEAL         = colors.HexColor("#0f766e")
TEAL_LIGHT   = colors.HexColor("#f0fdfa")
TEAL_MID     = colors.HexColor("#99f6e4")
INDIGO       = colors.HexColor("#4f46e5")
INDIGO_LIGHT = colors.HexColor("#eef2ff")
GRAY_900     = colors.HexColor("#111827")
GRAY_700     = colors.HexColor("#374151")
GRAY_500     = colors.HexColor("#6b7280")
GRAY_300     = colors.HexColor("#d1d5db")
GRAY_100     = colors.HexColor("#f3f4f6")
GREEN        = colors.HexColor("#059669")
GREEN_LIGHT  = colors.HexColor("#d1fae5")
AMBER        = colors.HexColor("#d97706")
AMBER_LIGHT  = colors.HexColor("#fef3c7")
RED          = colors.HexColor("#dc2626")
RED_LIGHT    = colors.HexColor("#fee2e2")
WHITE        = colors.white

FRAMEWORK_LABELS = {
    "soc2":     "SOC 2 Type II",
    "iso27001": "ISO/IEC 27001:2022",
    "hipaa":    "HIPAA Security Rule",
    "gdpr":     "GDPR",
    "pci_dss":  "PCI DSS v4.0",
    "ccpa":     "CCPA",
    "nist_csf": "NIST CSF 2.0",
}

CONTROL_DESCRIPTIONS = {
    "access_control":          "User access provisioning, privilege management, MFA enforcement, and authentication controls across all systems.",
    "change_management":       "Software development lifecycle, code review workflows, branch protection, and change approval processes.",
    "logging_monitoring":      "Audit logging configuration, security event monitoring, alerting rules, and SIEM integration.",
    "endpoint_security":       "Device management, endpoint protection agents, MDM policy enforcement, and device compliance.",
    "vulnerability_management":"Security scanning, penetration testing history, vulnerability tracking, and remediation timelines.",
    "hr_security":             "Employee onboarding records, background checks, security awareness training completion, and offboarding.",
    "network_security":        "Network segmentation, firewall and WAF rules, DNS security, and traffic monitoring.",
    "operations_security":     "Operational procedures, patch management cadence, incident response, and change control.",
    "communications_security": "Secure communication channels, encrypted messaging, and data-in-transit controls.",
    "audit_controls":          "System audit log retention, access record completeness, and log integrity for compliance.",
    "workforce_security":      "Staff access lifecycle management, least-privilege enforcement, and workforce security controls.",
}

REPORTS_DIR = Path("/tmp/tracelayer_reports")

# ── Framework criteria mapping ────────────────────────────────────────────────
# Maps framework → list of {id, name, control_category, description}
FRAMEWORK_CRITERIA: dict[str, list[dict]] = {
    "soc2": [
        # CC6 — Logical and Physical Access
        {"id": "CC6.1",  "name": "Logical access security measures",          "control": "access_control",          "desc": "Logical access restrictions via least-privilege, RBAC, and access reviews"},
        {"id": "CC6.2",  "name": "New access provisioning controls",           "control": "access_control",          "desc": "Prior authentication required; passwords and MFA enforced"},
        {"id": "CC6.3",  "name": "Role-based access authorization",            "control": "access_control",          "desc": "Authorization based on role, function, and least-privilege"},
        {"id": "CC6.6",  "name": "Logical access remediation",                 "control": "access_control",          "desc": "Timely removal of terminated user access"},
        {"id": "CC6.7",  "name": "Restricted access to sensitive data",        "control": "access_control",          "desc": "Encryption and access controls for data at rest and in transit"},
        {"id": "CC6.8",  "name": "Malicious software prevention",              "control": "endpoint_security",       "desc": "Anti-malware and endpoint detection tools deployed"},
        # CC7 — System Operations
        {"id": "CC7.1",  "name": "Vulnerability detection procedures",         "control": "vulnerability_management","desc": "Security vulnerabilities detected and evaluated"},
        {"id": "CC7.2",  "name": "Threat monitoring and detection",            "control": "logging_monitoring",      "desc": "System anomalies and security events monitored"},
        {"id": "CC7.3",  "name": "Security event evaluation",                  "control": "logging_monitoring",      "desc": "Security events evaluated, investigated, and documented"},
        {"id": "CC7.4",  "name": "Incident response procedures",               "control": "logging_monitoring",      "desc": "Security incidents responded to and documented"},
        {"id": "CC7.5",  "name": "Vulnerability disclosure response",          "control": "vulnerability_management","desc": "Identified vulnerabilities addressed on defined timelines"},
        # CC8 — Change Management
        {"id": "CC8.1",  "name": "Change management controls",                 "control": "change_management",       "desc": "System changes authorized, tested, approved, and documented"},
        # CC9 — Risk Mitigation
        {"id": "CC9.1",  "name": "Risk identification and assessment",         "control": "change_management",       "desc": "Ongoing risk assessment processes in place"},
        {"id": "CC9.2",  "name": "Vendor and partner risk management",         "control": "change_management",       "desc": "Vendor agreements include security and availability requirements"},
        # CC1 — Control Environment
        {"id": "CC1.3",  "name": "Organizational structure and reporting",     "control": "hr_security",             "desc": "Accountability and responsibility clearly defined"},
        {"id": "CC1.4",  "name": "Competence commitment",                      "control": "hr_security",             "desc": "Background checks and competence requirements enforced"},
        {"id": "CC1.5",  "name": "Enforcement of accountability",              "control": "hr_security",             "desc": "Workforce accountability measures in place"},
        # CC2 — Communication
        {"id": "CC2.2",  "name": "Internal communication of objectives",       "control": "hr_security",             "desc": "Security policies communicated to workforce"},
        # CC4 — Monitoring
        {"id": "CC4.1",  "name": "Evaluation and monitoring activities",       "control": "logging_monitoring",      "desc": "Ongoing monitoring of system operations"},
        # CC5 — Control Activities
        {"id": "CC5.2",  "name": "Technology-based control activities",        "control": "endpoint_security",       "desc": "Technology controls selected and developed"},
    ],
    "iso27001": [
        {"id": "A.5.1",  "name": "Policies for information security",          "control": "change_management",       "desc": "Management direction and support for information security"},
        {"id": "A.6.1",  "name": "Internal organization",                      "control": "hr_security",             "desc": "Information security roles and responsibilities defined"},
        {"id": "A.7.1",  "name": "Prior to employment screening",              "control": "hr_security",             "desc": "Background verification checks performed"},
        {"id": "A.7.2",  "name": "During employment obligations",              "control": "hr_security",             "desc": "Security awareness, training, and disciplinary process"},
        {"id": "A.7.3",  "name": "Termination and change of employment",       "control": "hr_security",             "desc": "Access removed upon termination or role change"},
        {"id": "A.8.1",  "name": "Responsibility for assets",                  "control": "endpoint_security",       "desc": "Asset inventory maintained and ownership assigned"},
        {"id": "A.9.1",  "name": "Business requirements for access control",   "control": "access_control",          "desc": "Access control policy established and implemented"},
        {"id": "A.9.2",  "name": "User access management",                     "control": "access_control",          "desc": "Provisioning, review, and revocation of user access"},
        {"id": "A.9.4",  "name": "System and application access control",      "control": "access_control",          "desc": "Secure log-on procedures and password management"},
        {"id": "A.12.1", "name": "Operational procedures and responsibilities","control": "logging_monitoring",      "desc": "Operating procedures documented and made available"},
        {"id": "A.12.4", "name": "Logging and monitoring",                     "control": "logging_monitoring",      "desc": "Event logs produced, protected, and regularly reviewed"},
        {"id": "A.12.6", "name": "Technical vulnerability management",         "control": "vulnerability_management","desc": "Technical vulnerabilities identified and timely remediation"},
        {"id": "A.13.1", "name": "Network security management",                "control": "network_security",        "desc": "Networks managed and controlled to protect systems"},
        {"id": "A.14.2", "name": "Security in development and support",        "control": "change_management",       "desc": "Security built into the development lifecycle"},
        {"id": "A.15.1", "name": "Information security in supplier relationships","control":"change_management",     "desc": "Supplier access agreements include security requirements"},
        {"id": "A.16.1", "name": "Management of security incidents",           "control": "logging_monitoring",      "desc": "Incidents reported, assessed, and responded to"},
        {"id": "A.18.1", "name": "Compliance with legal requirements",         "control": "change_management",       "desc": "All relevant legislative and contractual requirements identified"},
    ],
    "hipaa": [
        {"id": "§164.308(a)(1)", "name": "Risk analysis and management",       "control": "vulnerability_management","desc": "Accurate and thorough assessment of security risks"},
        {"id": "§164.308(a)(3)", "name": "Workforce security",                 "control": "hr_security",             "desc": "Appropriate authorization and supervision of workforce"},
        {"id": "§164.308(a)(4)", "name": "Information access management",      "control": "access_control",          "desc": "Access to PHI authorized on need-to-know basis"},
        {"id": "§164.308(a)(5)", "name": "Security awareness training",        "control": "hr_security",             "desc": "Training on PHI protection and malicious software"},
        {"id": "§164.308(a)(6)", "name": "Security incident procedures",       "control": "logging_monitoring",      "desc": "Identifying and responding to security incidents"},
        {"id": "§164.312(a)(1)", "name": "Access control (technical)",         "control": "access_control",          "desc": "Unique user identification and emergency access"},
        {"id": "§164.312(b)",    "name": "Audit controls",                     "control": "logging_monitoring",      "desc": "Hardware, software, and procedural audit mechanisms"},
        {"id": "§164.312(c)",    "name": "Integrity controls",                 "control": "change_management",       "desc": "PHI not improperly altered or destroyed"},
        {"id": "§164.312(e)",    "name": "Transmission security",              "control": "network_security",        "desc": "Technical measures guarding against unauthorized access in transit"},
        {"id": "§164.310(a)",    "name": "Facility access controls",           "control": "endpoint_security",       "desc": "Physical access to systems containing PHI controlled"},
    ],
    "gdpr": [
        {"id": "Art. 5",    "name": "Principles of processing",                "control": "change_management",       "desc": "Lawfulness, fairness, transparency, purpose limitation, data minimisation"},
        {"id": "Art. 25",   "name": "Data protection by design",               "control": "change_management",       "desc": "Privacy-by-design and privacy-by-default measures"},
        {"id": "Art. 30",   "name": "Records of processing activities",        "control": "change_management",       "desc": "Comprehensive RoPA maintained"},
        {"id": "Art. 32",   "name": "Security of processing",                  "control": "access_control",          "desc": "Appropriate technical and organizational security measures"},
        {"id": "Art. 33",   "name": "Breach notification (72h)",               "control": "logging_monitoring",      "desc": "Personal data breaches reported to supervisory authority"},
        {"id": "Art. 35",   "name": "Data protection impact assessment",       "control": "vulnerability_management","desc": "DPIA conducted for high-risk processing activities"},
    ],
    "pci_dss": [
        {"id": "Req. 1",  "name": "Install and maintain network security controls","control": "network_security",     "desc": "Firewalls and network controls protect cardholder data"},
        {"id": "Req. 2",  "name": "Apply secure configurations",               "control": "endpoint_security",       "desc": "Vendor defaults changed; unnecessary services removed"},
        {"id": "Req. 6",  "name": "Develop and maintain secure systems",       "control": "change_management",       "desc": "Vulnerabilities patched; secure development lifecycle"},
        {"id": "Req. 7",  "name": "Restrict access by business need-to-know",  "control": "access_control",          "desc": "Access to cardholder data restricted to authorized personnel"},
        {"id": "Req. 8",  "name": "Identify users and authenticate access",    "control": "access_control",          "desc": "Unique IDs, MFA, and strong authentication controls"},
        {"id": "Req. 10", "name": "Log and monitor all access",                "control": "logging_monitoring",      "desc": "Audit logs captured, protected, and reviewed"},
        {"id": "Req. 11", "name": "Test security of systems and networks",     "control": "vulnerability_management","desc": "Regular scanning, penetration testing, and IDS/IPS"},
        {"id": "Req. 12", "name": "Support information security with policies","control": "hr_security",             "desc": "Information security policy documented and communicated"},
    ],
    "nist_csf": [
        {"id": "ID.AM",  "name": "Asset Management",                           "control": "endpoint_security",       "desc": "Inventory of systems, software, and data assets"},
        {"id": "ID.RA",  "name": "Risk Assessment",                            "control": "vulnerability_management","desc": "Threats, vulnerabilities, likelihoods, and impacts identified"},
        {"id": "PR.AC",  "name": "Identity Management & Access Control",       "control": "access_control",          "desc": "Access to assets managed consistent with risk"},
        {"id": "PR.AT",  "name": "Awareness and Training",                     "control": "hr_security",             "desc": "Users and partners aware of cybersecurity risks"},
        {"id": "PR.DS",  "name": "Data Security",                              "control": "change_management",       "desc": "Information and records managed per risk strategy"},
        {"id": "PR.IP",  "name": "Information Protection Processes",           "control": "change_management",       "desc": "Security policies, processes, and procedures maintained"},
        {"id": "DE.AE",  "name": "Anomalies and Events",                       "control": "logging_monitoring",      "desc": "Anomalous activity detected and potential impact understood"},
        {"id": "DE.CM",  "name": "Security Continuous Monitoring",             "control": "logging_monitoring",      "desc": "Information systems and assets monitored at discrete intervals"},
        {"id": "RS.RP",  "name": "Response Planning",                          "control": "logging_monitoring",      "desc": "Response processes executed and maintained"},
        {"id": "RC.RP",  "name": "Recovery Planning",                          "control": "change_management",       "desc": "Recovery processes executed and maintained"},
    ],
}

# ── Evidence display schema ────────────────────────────────────────────────────
# Maps evidence_type -> interleaved (col_header, data_key, col_header, data_key, ...)
_EV_SCHEMA: dict[str, tuple] = {
    "iam_users":              ("Username",     "username",          "Active",     "active",               "MFA Enabled",  "mfa_enabled"),
    "iam_policies":           ("Policy Name",  "name",              "Type",       "type",                 "Entities",     "entities_count"),
    "github_members":         ("Username",     "username",          "Role",       "role",                 "MFA",          "two_factor_authentication"),
    "github_admin_members":   ("Username",     "username",          "Role",       "role"),
    "repositories":           ("Repository",   "name",              "Private",    "private",              "Default Branch","default_branch"),
    "github_repos":           ("Repository",   "name",              "Visibility", "visibility",           "Protected",    "branch_protection"),
    "slack_users":            ("Name",         "name",              "Email",      "email",                "Admin",        "is_admin"),
    "slack_workspace":        ("Workspace",    "name",              "Domain",     "domain"),
    "workspace_users":        ("Email",        "email",             "Admin",      "admin",                "Suspended",    "suspended"),
    "workspace_admin_members":("Email",        "email",             "Role",       "role"),
    "okta_users":             ("Login",        "login",             "Status",     "status",               "MFA",          "mfa_enrolled"),
    "okta_groups":            ("Group Name",   "name",              "Type",       "type"),
    "azure_users":            ("UPN",          "user_principal_name","Enabled",   "account_enabled"),
    "azure_roles":            ("Role",         "role_name",         "Scope",      "scope"),
    "jira_users":             ("Display Name", "display_name",      "Email",      "email_address",        "Active",       "active"),
    "jira_projects":          ("Name",         "name",              "Key",        "key",                  "Type",         "project_type"),
    "cloudtrail_logs":        ("Event Count",  "event_count",       "Log Group",  "log_group"),
    "gitlab_repos":           ("Name",         "name",              "Visibility", "visibility",           "Branch Prot.", "default_branch_protection"),
    "gitlab_members":         ("Username",     "username",          "Access Level","access_level"),
    "linear_issues":          ("Title",        "title",             "State",      "state",                "Priority",     "priority"),
    "datadog_monitors":       ("Monitor Name", "name",              "Type",       "type",                 "Status",       "status"),
    "datadog_users":          ("Name",         "name",              "Email",      "email",                "Role",         "role"),
    "pagerduty_users":        ("Name",         "name",              "Email",      "email",                "Role",         "role"),
    "pagerduty_incidents":    ("Number",       "incident_number",   "Status",     "status",               "Urgency",      "urgency"),
    "sentry_members":         ("Name",         "name",              "Email",      "email",                "Role",         "role"),
    "crowdstrike_agents":     ("Hostname",     "hostname",          "OS",         "os_version",           "Status",       "status"),
    "crowdstrike_detections": ("Hostname",     "hostname",          "Severity",   "severity",             "Status",       "status"),
    "jamf_computers":         ("Name",         "name",              "OS",         "operating_system",     "Managed",      "managed"),
    "sentinelone_agents":     ("Hostname",     "computerName",      "OS",         "osName",               "Active",       "isActive"),
    "kandji_devices":         ("Name",         "name",              "Platform",   "platform",             "Status",       "status"),
    "kolide_devices":         ("Name",         "name",              "Platform",   "platform",             "Enrolled",     "enrolled"),
    "snyk_projects":          ("Name",         "name",              "Type",       "type",                 "Status",       "status"),
    "hackerone_reports":      ("Report ID",    "id",                "State",      "state",                "Severity",     "severity_rating"),
    "wiz_issues":             ("Severity",     "severity",          "Status",     "status",               "Type",         "type"),
    "servicenow_incidents":   ("Number",       "number",            "State",      "state",                "Priority",     "priority"),
    "servicenow_changes":     ("Number",       "number",            "Type",       "type",                 "State",        "state"),
    "servicenow_users":       ("Username",     "username",          "Active",     "active",               "Dept.",        "department"),
    "bamboohr_employees":     ("Name",         "displayName",       "Department", "department",           "Status",       "status"),
    "rippling_employees":     ("Name",         "name",              "Department", "department",           "Status",       "status"),
    "notion_users":           ("Name",         "name",              "Type",       "type",                 "Email",        "email"),
    "confluence_spaces":      ("Name",         "name",              "Type",       "type",                 "Status",       "status"),
    "confluence_groups":      ("Group Name",   "name",              "Type",       "type"),
    "confluence_pages":       ("Title",        "title",             "Space",      "space",                "Created By",   "created_by"),
    "duo_users":              ("Username",     "username",          "Status",     "status",               "Email",        "email"),
    "splunk_alerts":          ("Name",         "name",              "Actions",    "actions"),
    "stripe_webhooks":        ("URL",          "url",               "Status",     "status"),
    "terraform_workspaces":   ("Name",         "name",              "Status",     "status",               "Locked",       "locked"),
    "vercel_projects":        ("Name",         "name",              "Framework",  "framework"),
    "cloudflare_zones":       ("Zone",         "name",              "Status",     "status",               "Plan",         "plan"),
    "microsoft_teams_users":  ("Name",         "displayName",       "UPN",        "userPrincipalName"),
    "microsoft_teams_teams":  ("Name",         "displayName",       "Members",    "memberCount"),
}

_INTEGRATION_COLORS: dict[str, object] = {
    "aws":              colors.HexColor("#FF9900"),
    "github":           colors.HexColor("#24292e"),
    "slack":            colors.HexColor("#4A154B"),
    "google_workspace": colors.HexColor("#4285F4"),
    "jira":             colors.HexColor("#0052CC"),
    "okta":             colors.HexColor("#007DC1"),
    "azure_ad":         colors.HexColor("#0078D4"),
    "gitlab":           colors.HexColor("#FC6D26"),
    "datadog":          colors.HexColor("#632CA6"),
    "pagerduty":        colors.HexColor("#06AC38"),
    "crowdstrike":      colors.HexColor("#E42A24"),
    "sentinelone":      colors.HexColor("#5B24FA"),
    "sentry":           colors.HexColor("#362D59"),
    "snyk":             colors.HexColor("#4C4A73"),
    "cloudflare":       colors.HexColor("#F38020"),
    "stripe":           colors.HexColor("#635BFF"),
}


# ── Score / status helpers ─────────────────────────────────────────────────────

def _score_color(score: int):
    if score >= 80:
        return GREEN
    if score >= 50:
        return AMBER
    return RED


def _status_colors(status: str):
    mapping = {
        "passing":    (GREEN_LIGHT,  colors.HexColor("#065f46")),
        "warning":    (AMBER_LIGHT,  colors.HexColor("#92400e")),
        "failing":    (RED_LIGHT,    colors.HexColor("#991b1b")),
        "no_evidence":(GRAY_100,     GRAY_500),
    }
    return mapping.get(status, (GRAY_100, GRAY_500))


# ── Style sheet ───────────────────────────────────────────────────────────────

def _styles() -> dict:
    return {
        "h1":            ParagraphStyle("h1",  fontName="Helvetica-Bold", fontSize=26, textColor=GRAY_900, leading=32, spaceAfter=4),
        "h2":            ParagraphStyle("h2",  fontName="Helvetica-Bold", fontSize=16, textColor=GRAY_900, leading=20, spaceBefore=14, spaceAfter=8),
        "h3":            ParagraphStyle("h3",  fontName="Helvetica-Bold", fontSize=11, textColor=GRAY_900, leading=15, spaceBefore=8, spaceAfter=5),
        "h4":            ParagraphStyle("h4",  fontName="Helvetica-Bold", fontSize=9,  textColor=GRAY_700, leading=13, spaceBefore=6, spaceAfter=3),
        "body":          ParagraphStyle("body",  fontName="Helvetica", fontSize=10, textColor=GRAY_900, leading=15),
        "body_sm":       ParagraphStyle("body_sm", fontName="Helvetica", fontSize=9, textColor=GRAY_700, leading=13),
        "small":         ParagraphStyle("small",   fontName="Helvetica", fontSize=8,  textColor=GRAY_500, leading=12),
        "label":         ParagraphStyle("label",   fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=11, spaceAfter=2),
        "cover_eyebrow": ParagraphStyle("cover_eyebrow", fontName="Helvetica-Bold", fontSize=10, textColor=TEAL, leading=14, spaceAfter=8),
        "cover_subtitle":ParagraphStyle("cover_subtitle", fontName="Helvetica", fontSize=12, textColor=GRAY_500, leading=17),
        "meta_label":    ParagraphStyle("meta_label", fontName="Helvetica-Bold", fontSize=8, textColor=GRAY_500, leading=12),
        "meta_value":    ParagraphStyle("meta_value", fontName="Helvetica-Bold", fontSize=12, textColor=GRAY_900, leading=16),
        "th":            ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8, textColor=TEAL, leading=11),
        "td":            ParagraphStyle("td", fontName="Helvetica", fontSize=9, textColor=GRAY_900, leading=12),
        "td_sm":         ParagraphStyle("td_sm", fontName="Helvetica", fontSize=8, textColor=GRAY_700, leading=11),
        "td_mono":       ParagraphStyle("td_mono", fontName="Courier", fontSize=8, textColor=GRAY_500, leading=11),
        "right":         ParagraphStyle("right", fontName="Helvetica", fontSize=8, textColor=GRAY_500, leading=11, alignment=TA_RIGHT),
    }


# ── Page template ─────────────────────────────────────────────────────────────

class _PageTemplate:
    """Adds brand header/footer to every page; renders cover header on page 1."""

    def __init__(self, context: dict, styles: dict):
        self.ctx = context
        self.st = styles
        self._is_first = True

    def __call__(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        if self._is_first:
            # Cover: full-bleed teal header band
            canvas.setFillColor(TEAL)
            canvas.rect(0, h - 80*mm, w, 80*mm, fill=1, stroke=0)
            canvas.setFillColor(WHITE)
            canvas.setFont("Helvetica-Bold", 28)
            canvas.drawString(20*mm, h - 44*mm, "TraceLayer")
            canvas.setFont("Helvetica", 11)
            canvas.setFillColor(colors.HexColor("#99f6e4"))
            canvas.drawString(20*mm, h - 56*mm, "Continuous Compliance Evidence Platform")
            self._is_first = False
        else:
            # Content pages: teal left bar
            canvas.setFillColor(TEAL)
            canvas.rect(0, 0, 4, h, fill=1, stroke=0)
            # Top micro-header
            canvas.setFillColor(GRAY_100)
            canvas.rect(0, h - 10*mm, w, 10*mm, fill=1, stroke=0)
            canvas.setFillColor(GRAY_500)
            canvas.setFont("Helvetica", 7)
            canvas.drawString(15*mm, h - 6*mm, "TraceLayer · Compliance Evidence Report")
            canvas.drawRightString(w - 15*mm, h - 6*mm,
                f"{self.ctx['company_name']} · {FRAMEWORK_LABELS.get(self.ctx['framework'], self.ctx['framework'].upper())}")
            # Footer line
            canvas.setFillColor(GRAY_300)
            canvas.rect(15*mm, 12*mm, w - 30*mm, 0.4, fill=1, stroke=0)
            canvas.setFillColor(GRAY_500)
            canvas.setFont("Helvetica", 8)
            canvas.drawString(15*mm, 8*mm,
                f"CONFIDENTIAL — {self.ctx['company_name']} — {self.ctx['framework'].upper()} Report")
            canvas.drawRightString(w - 15*mm, 8*mm, f"Page {doc.page}")

        canvas.restoreState()


# ── Evidence data helpers ─────────────────────────────────────────────────────

def _trunc(val, max_len: int = 38) -> str:
    s = str(val) if val is not None else "—"
    return s[:max_len] + "…" if len(s) > max_len else s


def _bool_label(val) -> str:
    if val is True or str(val).lower() in ("true", "yes", "1", "enabled", "active"):
        return "Yes"
    if val is False or str(val).lower() in ("false", "no", "0", "disabled", "inactive"):
        return "No"
    return str(val) if val is not None else "—"


def _is_truthy(val) -> bool:
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return str(val).lower() in ("true", "yes", "1", "active", "enabled", "online", "managed")


def _get_table_cols(evidence_type: str) -> list[tuple[str, str]]:
    schema = _EV_SCHEMA.get(evidence_type)
    if not schema:
        return [("Source ID", "__source_id__"), ("Summary", "__preview__")]
    it = iter(schema)
    return [(lbl, next(it)) for lbl in it]


def _get_cell_value(rec: dict, key: str) -> str:
    if key == "__source_id__":
        return _trunc(rec.get("source_id", ""), 38)
    if key == "__preview__":
        d = rec.get("data", {})
        if isinstance(d, dict):
            return ", ".join(f"{k}: {v}" for k, v in list(d.items())[:2])[:40]
        return ""
    d = rec.get("data", {})
    if not isinstance(d, dict):
        return "—"
    val = d.get(key)
    if val is None:
        return "—"
    if isinstance(val, bool):
        return _bool_label(val)
    return _trunc(str(val), 35)


def _fmt_n(n: int) -> str:
    return f"{n // 1000}k+" if n >= 1000 else str(n)


def _extract_insights(ev_type: str, records: list[dict]) -> list[tuple[str, str, object]]:
    """Return up to 4 (value_str, label, color) insight tuples for a given evidence type."""
    data_list = [r.get("data", {}) for r in records if isinstance(r.get("data"), dict)]
    n = len(data_list)
    insights: list[tuple[str, str, object]] = [(_fmt_n(n), "Records", INDIGO)]

    # User/employee-like types
    if ev_type in ("iam_users", "workspace_users", "okta_users", "azure_users", "jira_users",
                   "slack_users", "microsoft_teams_users", "servicenow_users",
                   "bamboohr_employees", "rippling_employees", "notion_users", "duo_users"):
        active = sum(1 for d in data_list if _is_truthy(
            d.get("active") or d.get("account_enabled") or d.get("isActive") or
            d.get("status") == "ACTIVE"))
        insights.append((_fmt_n(active), "Active", GREEN if active > 0 else RED))
        # MFA
        mfa_key = next((k for k in ("mfa_enabled", "mfa_enrolled") if k in (data_list[0] if data_list else {})), None)
        if mfa_key:
            mfa_count = sum(1 for d in data_list if _is_truthy(d.get(mfa_key)))
            insights.append((_fmt_n(mfa_count), "MFA On", GREEN if mfa_count == n else AMBER))

    # Member / admin types
    elif ev_type in ("github_members", "gitlab_members", "workspace_admin_members", "pagerduty_users",
                     "sentry_members", "datadog_users", "confluence_groups"):
        admins = sum(1 for d in data_list if str(d.get("role", d.get("access_level", ""))).lower()
                     in ("admin", "owner", "50", "manager"))
        insights.append((_fmt_n(admins), "Admins", AMBER))
        mfa_count = sum(1 for d in data_list if _is_truthy(d.get("two_factor_authentication")))
        if mfa_count > 0:
            insights.append((_fmt_n(mfa_count), "MFA On", GREEN))

    # Repository types
    elif ev_type in ("repositories", "github_repos", "gitlab_repos"):
        private = sum(1 for d in data_list if _is_truthy(d.get("private") or (d.get("visibility") == "private")))
        insights.append((_fmt_n(private), "Private", INDIGO))
        protected = sum(1 for d in data_list if _is_truthy(
            d.get("branch_protection") or d.get("default_branch_protection")))
        insights.append((_fmt_n(protected), "Protected", GREEN if protected == n else AMBER))

    # Incident / issue types
    elif ev_type in ("pagerduty_incidents", "servicenow_incidents", "wiz_issues", "hackerone_reports"):
        open_c = sum(1 for d in data_list if str(d.get("status", "")).lower() in ("triggered", "open", "new", "active"))
        insights.append((_fmt_n(open_c), "Open", RED if open_c > 0 else GREEN))
        crit = sum(1 for d in data_list if str(d.get("severity", d.get("severity_rating", ""))).lower()
                   in ("critical", "p1", "1", "high"))
        if crit > 0:
            insights.append((_fmt_n(crit), "Critical/High", RED))

    # Endpoint / device types
    elif ev_type in ("crowdstrike_agents", "sentinelone_agents", "kandji_devices", "kolide_devices", "jamf_computers"):
        managed = sum(1 for d in data_list if _is_truthy(
            d.get("managed") or d.get("isActive") or d.get("enrolled") or (d.get("status") == "online")))
        insights.append((_fmt_n(managed), "Managed/Active", GREEN))
        pct = int(managed / n * 100) if n else 0
        insights.append((f"{pct}%", "Coverage", GREEN if pct >= 90 else AMBER))

    # Monitor types
    elif ev_type == "datadog_monitors":
        ok_c = sum(1 for d in data_list if str(d.get("status", "")).lower() == "ok")
        alert_c = sum(1 for d in data_list if str(d.get("status", "")).lower() in ("alert", "warn", "no data"))
        insights.append((_fmt_n(ok_c), "OK", GREEN))
        if alert_c > 0:
            insights.append((_fmt_n(alert_c), "Alerting", RED))

    return insights[:4]


# ── Building blocks ───────────────────────────────────────────────────────────

def _insight_strip(insights: list[tuple], W: float) -> Table:
    """A row of colored metric boxes."""
    n = len(insights)
    col_w = W / n
    cells = []
    for val, lbl, color in insights:
        cell = Table([
            [Paragraph(val,  ParagraphStyle(f"iv_{lbl}", fontName="Helvetica-Bold", fontSize=18,
                                             textColor=color, alignment=TA_CENTER))],
            [Paragraph(lbl,  ParagraphStyle(f"il_{lbl}", fontName="Helvetica", fontSize=7,
                                             textColor=GRAY_500, alignment=TA_CENTER))],
        ], colWidths=[col_w - 2*mm])
        cells.append(cell)
    row = Table([cells], colWidths=[col_w] * n)
    row.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), INDIGO_LIGHT),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
        ("LINEAFTER",     (0, 0), (-2, -1), 0.5, colors.HexColor("#c7d2fe")),
        ("TOPPADDING",    (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return row


def _ev_table(recs: list[dict], ev_type: str, W: float, st: dict) -> Table:
    """Evidence table showing actual data fields with evidence freshness column."""
    cols = _get_table_cols(ev_type)
    max_show = 20
    display = recs[:max_show]

    # Add "Collected" age column
    header_row = [Paragraph(lbl, st["th"]) for lbl, _ in cols]
    header_row.append(Paragraph("Collected", st["th"]))
    rows = [header_row]

    style_cmds: list = [
        ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.2, TEAL),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.3, GRAY_100),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#f8fafb")]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]

    for row_i, rec in enumerate(display, start=1):
        age_label, age_color = _evidence_age(rec.get("timestamp", ""))
        data_cells = [Paragraph(_get_cell_value(rec, key), st["td_sm"]) for _, key in cols]
        data_cells.append(
            Paragraph(age_label, ParagraphStyle(f"age_{row_i}", fontName="Helvetica-Bold",
                                                 fontSize=7, textColor=age_color, leading=10))
        )
        rows.append(data_cells)
        # Color the age cell background if stale (> 30 days → red tint)
        if age_color == RED:
            style_cmds.append(("BACKGROUND", (-1, row_i), (-1, row_i), RED_LIGHT))
        elif age_color == AMBER:
            style_cmds.append(("BACKGROUND", (-1, row_i), (-1, row_i), AMBER_LIGHT))

    if len(recs) > max_show:
        # 1 text cell + (len(cols) - 1) empty data cells + 1 empty age cell = len(cols) + 1 total
        more = [Paragraph(f"… and {len(recs) - max_show} more records", st["small"])]
        more += [""] * len(cols)  # fills remaining data cols + age col slot
        rows.append(more)

    # Age column gets a narrower fixed width; data columns split the rest
    age_col_w = 18*mm
    data_col_w = (W - age_col_w) / len(cols)
    col_w = [data_col_w] * len(cols) + [age_col_w]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds))  # uses style_cmds which includes age-cell highlights
    return tbl


def _control_card(c: dict, W: float, st: dict, framework: str = "") -> Table:
    bg, fg = _status_colors(c["status"])
    status_label = c["status"].replace("_", " ").title()
    last = (c.get("last_collected") or "")[:10] or "Never"
    missing = c.get("missing_types", [])
    missing_str = ", ".join(missing) if missing else "All evidence types covered"
    desc = CONTROL_DESCRIPTIONS.get(c["category"], "")

    # Criteria reference line
    criteria_refs = _criteria_for_control(framework, c["category"])
    crit_ids = " · ".join(cr["id"] for cr in criteria_refs[:6])
    crit_line = f"Maps to: {crit_ids}" if crit_ids else ""

    left = Table([
        [Paragraph(c["name"], st["h3"])],
        [Paragraph(desc, st["small"])] if desc else [Spacer(1, 1)],
        [Paragraph(crit_line, ParagraphStyle(f"crit_ref_{c['category']}", fontName="Courier", fontSize=7,
                                              textColor=INDIGO, leading=10))] if crit_line else [Spacer(1, 1)],
        [Paragraph(
            f"Evidence records: <b>{c['evidence_count']}</b>   ·   Last collected: <b>{last}</b>",
            st["small"],
        )],
        [Paragraph(
            ("Missing: " + missing_str) if missing else "All evidence types covered",
            ParagraphStyle("miss", fontName="Helvetica", fontSize=8,
                           textColor=RED if missing else GREEN, leading=11),
        )],
    ], colWidths=[W - 34*mm])

    right = Table([
        [Paragraph(status_label, ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=7,
                                                 textColor=fg, backColor=bg, leading=10,
                                                 alignment=TA_CENTER))],
        [Spacer(1, 2*mm)],
        [Paragraph(f"{c['score']}%", ParagraphStyle("cscore", fontName="Helvetica-Bold",
                                                      fontSize=22, textColor=_score_color(c["score"]),
                                                      alignment=TA_CENTER, leading=26))],
    ], colWidths=[28*mm])

    card = Table([[left, right]], colWidths=[W - 34*mm, 34*mm])
    card.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX",          (0, 0), (-1, -1), 0.5, GRAY_300),
        ("LINEBEFORE",   (0, 0), (0, -1), 3, TEAL),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return card


def _recommendation(control: str, missing: list[str]) -> str:
    RECS = {
        "access_control":          "Connect Okta or Azure AD for user access records. Enforce MFA on all accounts. Review admin privileges quarterly.",
        "change_management":       "Enable branch protection on all repos. Require pull request reviews. Connect Jira for change ticket tracking.",
        "logging_monitoring":      "Enable CloudTrail in all AWS regions. Connect Datadog or Splunk for centralized log aggregation and alerting.",
        "endpoint_security":       "Deploy CrowdStrike or SentinelOne to all endpoints. Enroll all devices in Jamf or Kandji MDM.",
        "vulnerability_management":"Connect Snyk for automated code scanning. Schedule quarterly penetration tests. Track findings in HackerOne.",
        "hr_security":             "Connect BambooHR or Rippling for employee records. Document security training completion. Review offboarding procedures.",
        "network_security":        "Configure Cloudflare WAF. Review and document firewall rules. Implement network segmentation documentation.",
        "operations_security":     "Enable CloudTrail. Connect PagerDuty for incident management. Document operational runbooks in Confluence.",
        "communications_security": "Ensure Slack workspace has enterprise security features enabled. Enforce TLS for all communications.",
        "audit_controls":          "Enable CloudTrail with log file validation. Set up log retention policy minimum 1 year. Review log access controls.",
        "workforce_security":      "Connect HR system for employee lifecycle management. Implement quarterly access reviews.",
    }
    for k, v in RECS.items():
        if k in control.lower():
            return v
    if missing:
        return f"Collect missing evidence types: {', '.join(missing[:2])}. Connect relevant integrations in TraceLayer."
    return "Re-collect evidence to improve recency score. Schedule automated weekly collections."


# ── Criteria & freshness helpers ──────────────────────────────────────────────

def _criteria_for_control(framework: str, control_category: str) -> list[dict]:
    """Return all criteria for a given framework control category."""
    return [c for c in FRAMEWORK_CRITERIA.get(framework, []) if c["control"] == control_category]


def _evidence_age(timestamp_str: str) -> tuple[str, object]:
    """Return (label, color) for evidence age based on timestamp."""
    from datetime import datetime, timezone
    try:
        ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - ts).days
        if age <= 7:
            return f"{age}d ago", GREEN
        if age <= 30:
            return f"{age}d ago", AMBER
        return f"{age}d ago", RED
    except Exception:
        return "—", GRAY_500


def _criteria_section(framework: str, control_scores: list[dict], W: float, st: dict) -> list:
    """Render a full framework-criteria coverage table."""
    criteria_list = FRAMEWORK_CRITERIA.get(framework, [])
    if not criteria_list:
        return []

    # Build control_category → status lookup
    status_map = {c["category"]: c for c in control_scores}

    elements = []
    elements.append(Paragraph("Framework Requirements Coverage", st["h3"]))
    elements.append(Paragraph(
        f"The following table maps each {FRAMEWORK_LABELS.get(framework, framework.upper())} "
        f"requirement to the control domain providing evidence. "
        f"This mapping is used by auditors to verify coverage.",
        st["body_sm"],
    ))
    elements.append(Spacer(1, 3*mm))

    header = [
        Paragraph("Criteria", st["th"]),
        Paragraph("Requirement", st["th"]),
        Paragraph("Control Domain", st["th"]),
        Paragraph("Status", st["th"]),
        Paragraph("Evidence", st["th"]),
    ]
    rows = [header]
    style_cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, TEAL),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 7),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 7),
    ]

    for row_i, crit in enumerate(criteria_list, start=1):
        ctrl = status_map.get(crit["control"])
        if ctrl:
            status = ctrl["status"]
            ev_count = str(ctrl["evidence_count"])
            bg, fg = _status_colors(status)
            status_label = status.replace("_", " ").title()
        else:
            status = "no_evidence"
            ev_count = "0"
            bg, fg = _status_colors("no_evidence")
            status_label = "No Evidence"

        # Alternate row background
        if row_i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, row_i), (-1, row_i), colors.HexColor("#fafafa")))

        rows.append([
            Paragraph(crit["id"],   ParagraphStyle(f"crid_{row_i}", fontName="Courier", fontSize=7,
                                                    textColor=INDIGO, leading=10)),
            Paragraph(crit["name"], st["td_sm"]),
            Paragraph(ctrl["name"] if ctrl else crit["control"].replace("_", " ").title(), st["td_sm"]),
            Paragraph(status_label, ParagraphStyle(f"crb_{row_i}", fontName="Helvetica-Bold", fontSize=7,
                                                    textColor=fg, backColor=bg, leading=10)),
            Paragraph(ev_count,     st["td_sm"]),
        ])

    tbl = Table(rows, colWidths=[W*0.13, W*0.36, W*0.24, W*0.15, W*0.12], repeatRows=1)
    tbl.setStyle(TableStyle(style_cmds + [
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, GRAY_100),
    ]))
    elements.append(tbl)
    return elements


def _scope_box(company_name: str, framework: str, W: float, st: dict) -> Table:
    """A scope/system description callout box."""
    fw = FRAMEWORK_LABELS.get(framework, framework.upper())
    text = (
        f"<b>Scope Statement:</b> This report covers the {company_name} production environment, "
        f"including all cloud infrastructure, SaaS application services, access management systems, "
        f"and supporting tools in scope for {fw} compliance. Evidence was collected automatically "
        f"via TraceLayer integrations and reflects the state of controls at the time of generation."
    )
    inner = Table([[Paragraph(text, st["body_sm"])]], colWidths=[W - 16*mm])
    inner.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), TEAL_LIGHT),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    wrapper = Table([[inner]], colWidths=[W])
    wrapper.setStyle(TableStyle([
        ("BOX",       (0, 0), (-1, -1), 0.5, TEAL),
        ("LINEBEFORE",(0, 0), (0, -1), 3,   TEAL),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return wrapper


# ── Main renderer ─────────────────────────────────────────────────────────────

def render_pdf(context: dict) -> bytes:
    buf = BytesIO()
    st  = _styles()
    pt  = _PageTemplate(context, st)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=22*mm,  bottomMargin=22*mm,
        onPage=pt,
    )

    story = []
    W = A4[0] - 40*mm

    # ── COVER ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 84*mm))

    fw_label = FRAMEWORK_LABELS.get(context["framework"], context["framework"].upper())
    story.append(Paragraph("Compliance Evidence Report", st["cover_eyebrow"]))
    story.append(Paragraph(fw_label, st["h1"]))
    story.append(Paragraph(
        f"Automated evidence collection · {context['report_type'].title()} report",
        st["cover_subtitle"],
    ))
    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 6*mm))

    meta = [
        ("Organization",     context["company_name"]),
        ("Framework",        fw_label),
        ("Generated",        context["generated_at"]),
        ("Compliance Score", f"{context['overall_score']}%"),
    ]
    meta_data = [[
        Table([[Paragraph(lbl, st["meta_label"])], [Paragraph(val, st["meta_value"])]],
              colWidths=[W / 4 - 4*mm])
        for lbl, val in meta
    ]]
    meta_tbl = Table(meta_data, colWidths=[W / 4] * 4)
    meta_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(meta_tbl)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f"Report ID: {context['report_id']}  ·  {context['generated_at_full']}  ·  "
        f"CONFIDENTIAL — For authorized use only",
        st["small"],
    ))
    story.append(PageBreak())

    # ── SECTION 1: EXECUTIVE SUMMARY ──────────────────────────────────────────
    story.append(Paragraph("Section 1", st["label"]))
    story.append(Paragraph("Executive Summary", st["h2"]))

    score   = context["overall_score"]
    passing = sum(1 for c in context["control_scores"] if c["status"] == "passing")
    failing = sum(1 for c in context["control_scores"] if c["status"] in ("failing", "no_evidence"))
    warning = sum(1 for c in context["control_scores"] if c["status"] == "warning")

    posture = "strong" if score >= 80 else "moderate" if score >= 50 else "needs improvement"
    story.append(Paragraph(
        f"This report documents the compliance posture of <b>{context['company_name']}</b> against the "
        f"<b>{fw_label}</b> framework. Evidence was automatically collected from connected integrations "
        f"and evaluated across <b>{len(context['control_scores'])}</b> control domains. "
        f"Overall posture is assessed as <b>{posture}</b> with a score of <b>{score}/100</b>.",
        st["body_sm"],
    ))
    story.append(Spacer(1, 3*mm))
    story.append(_scope_box(context["company_name"], context["framework"], W, st))
    story.append(Spacer(1, 4*mm))

    # Summary metric strip
    story.append(_insight_strip([
        (str(score) + "%", "Compliance Score",   _score_color(score)),
        (str(context["total_records"]), "Evidence Records", INDIGO),
        (str(passing),  "Controls Passing",  GREEN),
        (str(failing),  "Controls Failing",  RED if failing > 0 else GREEN),
    ], W))
    story.append(Spacer(1, 6*mm))

    # Control breakdown table
    story.append(Paragraph("Control Domain Summary", st["h3"]))
    tbl_rows = [[
        Paragraph("Control Domain", st["th"]),
        Paragraph("Status",         st["th"]),
        Paragraph("Score",          st["th"]),
        Paragraph("Records",        st["th"]),
        Paragraph("Last Collected", st["th"]),
    ]]
    for c in context["control_scores"]:
        bg, fg = _status_colors(c["status"])
        last = (c.get("last_collected") or "")[:10] or "Never"
        tbl_rows.append([
            Paragraph(c["name"], st["td"]),
            Paragraph(c["status"].replace("_", " ").title(),
                      ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=7,
                                     textColor=fg, backColor=bg, leading=10)),
            Paragraph(f"{c['score']}%",
                      ParagraphStyle("sc_td", fontName="Helvetica-Bold", fontSize=9,
                                     textColor=_score_color(c["score"]), leading=12)),
            Paragraph(str(c["evidence_count"]), st["td"]),
            Paragraph(last, st["small"]),
        ])
    col_w = [W*0.30, W*0.16, W*0.10, W*0.18, W*0.26]
    tbl = Table(tbl_rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
        ("LINEBELOW",     (0, 0), (-1, 0), 1.5, TEAL),
        ("LINEBELOW",     (0, 1), (-1, -1), 0.4, GRAY_100),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))

    # Integration summary
    all_ev = [rec for recs in context["controls"].values() for rec in recs]
    by_integration: dict[str, int] = defaultdict(int)
    int_controls: dict[str, set] = defaultdict(set)
    for ctrl_key, recs in context["controls"].items():
        for rec in recs:
            by_integration[rec["integration"]] += 1
            int_controls[rec["integration"]].add(ctrl_key.replace("_", " ").title())

    if by_integration:
        story.append(Paragraph("Connected Integrations", st["h3"]))
        int_rows = [[
            Paragraph("Integration",      st["th"]),
            Paragraph("Records",          st["th"]),
            Paragraph("Controls Covered", st["th"]),
        ]]
        for intg, count in sorted(by_integration.items(), key=lambda x: -x[1]):
            ctrls = ", ".join(sorted(int_controls[intg]))
            if len(ctrls) > 55:
                ctrls = ctrls[:55] + "…"
            int_rows.append([
                Paragraph(intg.replace("_", " ").title(), st["td"]),
                Paragraph(str(count), st["td"]),
                Paragraph(ctrls, st["small"]),
            ])
        int_tbl = Table(int_rows, colWidths=[W*0.28, W*0.12, W*0.60], repeatRows=1)
        int_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
            ("LINEBELOW",     (0, 0), (-1, 0), 1.2, TEAL),
            ("LINEBELOW",     (0, 1), (-1, -1), 0.3, GRAY_100),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(int_tbl)

    story.append(PageBreak())

    # ── FRAMEWORK CRITERIA COVERAGE ───────────────────────────────────────────
    criteria_elements = _criteria_section(context["framework"], context["control_scores"], W, st)
    if criteria_elements:
        story.extend(criteria_elements)
        story.append(PageBreak())

    # ── CONTROL DETAIL SECTIONS ───────────────────────────────────────────────
    for i, c in enumerate(context["control_scores"], start=2):
        story.append(Paragraph(f"Section {i}", st["label"]))
        story.append(Paragraph(c["name"], st["h2"]))

        story.append(KeepTogether([_control_card(c, W, st, context["framework"]), Spacer(1, 5*mm)]))

        ev_list = context["controls"].get(c["category"], [])

        if ev_list:
            # Group by evidence_type and render each
            by_type: dict[str, list] = defaultdict(list)
            for rec in ev_list:
                by_type[rec["evidence_type"]].append(rec)

            for ev_type, recs in sorted(by_type.items()):
                story.append(Paragraph(
                    ev_type.replace("_", " ").title(),
                    st["h4"],
                ))
                # Insight strip
                insights = _extract_insights(ev_type, recs)
                if insights:
                    story.append(_insight_strip(insights, W))
                    story.append(Spacer(1, 3*mm))
                # Data table
                story.append(_ev_table(recs, ev_type, W, st))
                story.append(Spacer(1, 4*mm))
        else:
            missing_str = ", ".join(c.get("missing_types", [])) or "relevant evidence"
            story.append(Paragraph(
                f"No evidence has been collected for this control. "
                f"Connect integrations that provide: {missing_str}.",
                ParagraphStyle("no_ev", fontName="Helvetica-Oblique", fontSize=9,
                               textColor=GRAY_500, leading=13),
            ))

        story.append(PageBreak())

    # ── REMEDIATION ROADMAP ────────────────────────────────────────────────────
    story.append(Paragraph("Final Section", st["label"]))
    story.append(Paragraph("Remediation Roadmap", st["h2"]))
    story.append(Paragraph(
        "The following actions are recommended to close identified compliance gaps and improve your overall score.",
        st["body_sm"],
    ))
    story.append(Spacer(1, 4*mm))

    gaps = [c for c in context["control_scores"]
            if c["status"] in ("failing", "no_evidence", "warning")]

    if gaps:
        rec_rows = [[
            Paragraph("Priority", st["th"]),
            Paragraph("Control",  st["th"]),
            Paragraph("Gap",      st["th"]),
            Paragraph("Recommended Action", st["th"]),
        ]]
        for c in sorted(gaps, key=lambda x: x["score"]):
            missing = c.get("missing_types", [])
            gap_str = ", ".join(missing[:2]) if missing else "Evidence recency"
            action  = _recommendation(c["category"], missing)
            priority = "High" if c["score"] < 30 else "Medium"
            rec_rows.append([
                Paragraph(priority, ParagraphStyle(
                    f"pri_{c['category']}", fontName="Helvetica-Bold", fontSize=8,
                    textColor=RED if priority == "High" else AMBER, leading=11)),
                Paragraph(c["name"], st["td"]),
                Paragraph(gap_str, st["small"]),
                Paragraph(action,  st["small"]),
            ])
        rec_tbl = Table(rec_rows, colWidths=[W*0.11, W*0.20, W*0.24, W*0.45], repeatRows=1)
        rec_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), TEAL_LIGHT),
            ("LINEBELOW",     (0, 0), (-1, 0), 1.5, TEAL),
            ("LINEBELOW",     (0, 1), (-1, -1), 0.4, GRAY_100),
            ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, colors.HexColor("#fafafa")]),
            ("VALIGN",        (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ]))
        story.append(rec_tbl)
    else:
        story.append(Paragraph(
            "No critical gaps identified. Maintain evidence freshness by running collections on a weekly schedule.",
            ParagraphStyle("no_gaps", fontName="Helvetica-Oblique", fontSize=10, textColor=GREEN, leading=14),
        ))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width=W, color=GRAY_300))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph(
        f"Report generated by TraceLayer  ·  {context['generated_at_full']}  ·  "
        f"Report ID: {context['report_id']}",
        st["small"],
    ))

    doc.build(story)
    return buf.getvalue()


def save_pdf(report_id: str, pdf_bytes: bytes) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{report_id}.pdf"
    path.write_bytes(pdf_bytes)
    logger.info("Saved PDF report: %s (%d bytes)", path, len(pdf_bytes))
    return path


def load_pdf(report_id: str) -> Optional[bytes]:
    path = REPORTS_DIR / f"{report_id}.pdf"
    if not path.exists():
        return None
    return path.read_bytes()
