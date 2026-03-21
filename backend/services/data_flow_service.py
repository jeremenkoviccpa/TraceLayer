"""Data Flow Mapping service — auto-detects, scores risk, and maps regulations for each connected integration."""
from __future__ import annotations

import uuid
import logging

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.data_flow import DataFlow

logger = logging.getLogger(__name__)

# ── Data type display labels ───────────────────────────────────────────────────
DATA_TYPE_LABELS: dict[str, str] = {
    "full_name":          "Full Name",
    "email_address":      "Email Address",
    "phone_number":       "Phone Number",
    "personal_address":   "Personal Address",
    "date_of_birth":      "Date of Birth",
    "employee_id":        "Employee ID",
    "salary":             "Salary / Compensation",
    "employment_status":  "Employment Status",
    "org_unit":           "Org Unit / Department",
    "username":           "Username",
    "access_roles":       "Access Roles",
    "mfa_status":         "MFA Status",
    "payment_card_data":  "Payment Card Data",
    "billing_address":    "Billing Address",
    "transaction_data":   "Transaction Data",
    "financial_records":  "Financial Records",
    "health_records":     "Health Records",
    "biometric_data":     "Biometric Data",
    "behavioral_data":    "Behavioral / Usage Data",
    "device_data":        "Device Information",
    "ip_address":         "IP Address",
    "cookie_data":        "Cookie / Tracking Data",
    "email_behavior":     "Email Behavior",
    "user_id":            "User Identifier",
    "api_usage_data":     "API Usage Data",
    "model_inputs":       "AI Model Inputs",
    "model_outputs":      "AI Model Outputs",
    "infrastructure_data":"Infrastructure Data",
    "access_logs":        "Access Logs",
    "storage_data":       "Storage Data",
    "process_data":       "Process / Endpoint Data",
    "deal_data":          "Deal / Sales Data",
    "company_name":       "Company Name",
    "candidate_data":     "Candidate Data",
    "assessment_results": "Assessment Results",
    "training_progress":  "Training Progress",
    "support_tickets":    "Support Ticket Data",
    "audit_logs":         "Audit Logs",
    "security_events":    "Security Events",
}

# ── Per-integration data type definitions ─────────────────────────────────────
INTEGRATION_DATA_MAP: dict[str, dict] = {
    # Identity & Access
    "google_workspace":       {"data_types": ["full_name", "email_address", "employee_id", "org_unit", "mfa_status"], "data_category": "personal",     "default_region": "us",     "purpose": "identity_management"},
    "okta":                   {"data_types": ["full_name", "email_address", "username", "mfa_status", "access_roles"], "data_category": "personal",    "default_region": "us",     "purpose": "identity_management"},
    "azure_ad":               {"data_types": ["full_name", "email_address", "username", "access_roles", "mfa_status"], "data_category": "personal",    "default_region": "us",     "purpose": "identity_management"},
    "okta_verify":            {"data_types": ["email_address", "mfa_status", "device_data"],                           "data_category": "personal",    "default_region": "us",     "purpose": "mfa_enforcement"},
    "microsoft_authenticator":{"data_types": ["email_address", "mfa_status", "device_data"],                           "data_category": "personal",    "default_region": "us",     "purpose": "mfa_enforcement"},
    "google_authenticator":   {"data_types": ["email_address", "mfa_status"],                                          "data_category": "personal",    "default_region": "us",     "purpose": "mfa_enforcement"},
    "1password":              {"data_types": ["access_roles", "email_address", "mfa_status"],                          "data_category": "personal",    "default_region": "us",     "purpose": "password_management"},
    "bitwarden":              {"data_types": ["access_roles", "email_address", "mfa_status"],                          "data_category": "personal",    "default_region": "eu",     "purpose": "password_management"},
    "lastpass":               {"data_types": ["access_roles", "email_address"],                                        "data_category": "personal",    "default_region": "us",     "purpose": "password_management"},
    "duo":                    {"data_types": ["email_address", "phone_number", "mfa_status", "device_data"],           "data_category": "personal",    "default_region": "us",     "purpose": "mfa_enforcement"},
    "jumpcloud":              {"data_types": ["full_name", "email_address", "username", "access_roles", "device_data"],"data_category": "personal",    "default_region": "us",     "purpose": "identity_management"},
    "tailscale":              {"data_types": ["email_address", "device_data", "ip_address"],                           "data_category": "personal",    "default_region": "us",     "purpose": "network_access"},
    "auth0":                  {"data_types": ["full_name", "email_address", "username", "behavioral_data"],            "data_category": "personal",    "default_region": "us",     "purpose": "identity_management"},
    "doppler":                {"data_types": ["access_logs", "email_address"],                                         "data_category": "operational", "default_region": "us",     "purpose": "secrets_management"},
    "ping_identity":          {"data_types": ["full_name", "email_address", "username", "access_roles"],               "data_category": "personal",    "default_region": "us",     "purpose": "identity_management"},
    "zscaler":                {"data_types": ["ip_address", "behavioral_data", "access_logs"],                         "data_category": "personal",    "default_region": "us",     "purpose": "network_security"},
    "rippling":               {"data_types": ["full_name", "email_address", "salary", "employment_status", "personal_address", "date_of_birth"], "data_category": "sensitive", "default_region": "us", "purpose": "hr_management"},
    "bamboohr":               {"data_types": ["full_name", "email_address", "salary", "employment_status", "personal_address"], "data_category": "sensitive", "default_region": "us", "purpose": "hr_management"},
    "hibob":                  {"data_types": ["full_name", "email_address", "salary", "employment_status", "date_of_birth"], "data_category": "sensitive", "default_region": "eu", "purpose": "hr_management"},
    "personio":               {"data_types": ["full_name", "email_address", "salary", "employment_status", "personal_address"], "data_category": "sensitive", "default_region": "eu", "purpose": "hr_management"},
    "deel":                   {"data_types": ["full_name", "email_address", "salary", "personal_address", "date_of_birth"], "data_category": "sensitive", "default_region": "us", "purpose": "hr_management"},
    "remote":                 {"data_types": ["full_name", "email_address", "salary", "personal_address", "date_of_birth"], "data_category": "sensitive", "default_region": "us", "purpose": "hr_management"},
    "lattice":                {"data_types": ["full_name", "email_address", "employment_status", "org_unit"],          "data_category": "personal",    "default_region": "us",     "purpose": "performance_management"},
    "greenhouse":             {"data_types": ["full_name", "email_address", "candidate_data"],                         "data_category": "personal",    "default_region": "us",     "purpose": "recruitment"},
    "lever":                  {"data_types": ["full_name", "email_address", "candidate_data"],                         "data_category": "personal",    "default_region": "us",     "purpose": "recruitment"},
    "checkr":                 {"data_types": ["full_name", "date_of_birth", "personal_address", "candidate_data"],     "data_category": "sensitive",   "default_region": "us",     "purpose": "background_checks"},
    "trainual":               {"data_types": ["full_name", "email_address", "training_progress"],                      "data_category": "personal",    "default_region": "us",     "purpose": "training"},
    "knowbe4":                {"data_types": ["full_name", "email_address", "training_progress", "behavioral_data"],   "data_category": "personal",    "default_region": "us",     "purpose": "security_training"},
    "360learning":            {"data_types": ["full_name", "email_address", "training_progress"],                      "data_category": "personal",    "default_region": "eu",     "purpose": "training"},
    "hackerrank":             {"data_types": ["email_address", "candidate_data", "assessment_results"],                "data_category": "personal",    "default_region": "us",     "purpose": "technical_assessment"},
    "leetcode":               {"data_types": ["email_address", "candidate_data", "assessment_results"],                "data_category": "personal",    "default_region": "us",     "purpose": "technical_assessment"},
    # Cloud Infrastructure
    "aws":                    {"data_types": ["infrastructure_data", "access_logs", "storage_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "google_cloud":           {"data_types": ["infrastructure_data", "access_logs", "storage_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "azure":                  {"data_types": ["infrastructure_data", "access_logs", "storage_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "vercel":                 {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "deployment"},
    "digitalocean":           {"data_types": ["infrastructure_data", "access_logs", "storage_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "heroku":                 {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "render":                 {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "flyio":                  {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "netlify":                {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "deployment"},
    "oracle_cloud":           {"data_types": ["infrastructure_data", "access_logs", "storage_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "cloud_infrastructure"},
    "terraform_cloud":        {"data_types": ["infrastructure_data", "access_logs"],                                   "data_category": "operational", "default_region": "us",     "purpose": "infrastructure_as_code"},
    "kubernetes":             {"data_types": ["infrastructure_data", "access_logs", "process_data"],                   "data_category": "operational", "default_region": "us",     "purpose": "container_orchestration"},
    # Source Control
    "github":                 {"data_types": ["email_address", "username", "access_logs", "audit_logs"],               "data_category": "personal",    "default_region": "us",     "purpose": "source_control"},
    "gitlab":                 {"data_types": ["email_address", "username", "access_logs", "audit_logs"],               "data_category": "personal",    "default_region": "eu",     "purpose": "source_control"},
    "bitbucket":              {"data_types": ["email_address", "username", "access_logs"],                             "data_category": "personal",    "default_region": "us",     "purpose": "source_control"},
    # Project Management
    "jira":                   {"data_types": ["full_name", "email_address", "audit_logs"],                             "data_category": "personal",    "default_region": "us",     "purpose": "project_management"},
    "linear":                 {"data_types": ["full_name", "email_address", "audit_logs"],                             "data_category": "personal",    "default_region": "us",     "purpose": "project_management"},
    "notion":                 {"data_types": ["full_name", "email_address", "storage_data"],                           "data_category": "personal",    "default_region": "us",     "purpose": "documentation"},
    "confluence":             {"data_types": ["full_name", "email_address", "storage_data"],                           "data_category": "personal",    "default_region": "us",     "purpose": "documentation"},
    "asana":                  {"data_types": ["full_name", "email_address"],                                           "data_category": "personal",    "default_region": "us",     "purpose": "project_management"},
    "monday":                 {"data_types": ["full_name", "email_address"],                                           "data_category": "personal",    "default_region": "us",     "purpose": "project_management"},
    # Communication
    "slack":                  {"data_types": ["full_name", "email_address", "behavioral_data", "access_logs"],         "data_category": "personal",    "default_region": "us",     "purpose": "communication"},
    "microsoft_teams":        {"data_types": ["full_name", "email_address", "behavioral_data"],                        "data_category": "personal",    "default_region": "us",     "purpose": "communication"},
    "zoom":                   {"data_types": ["full_name", "email_address", "behavioral_data"],                        "data_category": "personal",    "default_region": "us",     "purpose": "video_conferencing"},
    "webex":                  {"data_types": ["full_name", "email_address", "behavioral_data"],                        "data_category": "personal",    "default_region": "us",     "purpose": "video_conferencing"},
    "intercom":               {"data_types": ["full_name", "email_address", "behavioral_data", "support_tickets"],     "data_category": "personal",    "default_region": "us",     "purpose": "customer_support"},
    "zendesk":                {"data_types": ["full_name", "email_address", "support_tickets"],                        "data_category": "personal",    "default_region": "us",     "purpose": "customer_support"},
    # CRM & Marketing
    "hubspot":                {"data_types": ["full_name", "email_address", "phone_number", "company_name", "deal_data", "behavioral_data"], "data_category": "personal", "default_region": "us", "purpose": "marketing_crm"},
    "salesforce":             {"data_types": ["full_name", "email_address", "phone_number", "company_name", "deal_data", "personal_address"], "data_category": "personal", "default_region": "us", "purpose": "sales_crm"},
    "mailchimp":              {"data_types": ["email_address", "full_name", "email_behavior"],                         "data_category": "personal",    "default_region": "us",     "purpose": "email_marketing"},
    # Customer Data Platform
    "segment":                {"data_types": ["user_id", "email_address", "behavioral_data", "device_data", "ip_address"], "data_category": "personal", "default_region": "us",  "purpose": "analytics_routing"},
    "mixpanel":               {"data_types": ["user_id", "behavioral_data", "device_data", "ip_address"],              "data_category": "personal",    "default_region": "us",     "purpose": "product_analytics"},
    "google_analytics":       {"data_types": ["behavioral_data", "ip_address", "device_data", "cookie_data"],          "data_category": "personal",    "default_region": "us",     "purpose": "web_analytics"},
    # Payment
    "stripe":                 {"data_types": ["payment_card_data", "email_address", "billing_address", "transaction_data"], "data_category": "financial", "default_region": "us", "purpose": "payment_processing"},
    # Security
    "crowdstrike":            {"data_types": ["device_data", "process_data", "behavioral_data", "ip_address"],         "data_category": "operational", "default_region": "us",     "purpose": "endpoint_security"},
    "sentinelone":            {"data_types": ["device_data", "process_data", "behavioral_data"],                       "data_category": "operational", "default_region": "us",     "purpose": "endpoint_security"},
    "jamf":                   {"data_types": ["device_data", "employee_id", "email_address"],                          "data_category": "personal",    "default_region": "us",     "purpose": "mdm"},
    "kandji":                 {"data_types": ["device_data", "email_address"],                                         "data_category": "personal",    "default_region": "us",     "purpose": "mdm"},
    "icloud":                 {"data_types": ["device_data", "email_address", "employee_id"],                          "data_category": "personal",    "default_region": "us",     "purpose": "mdm"},
    "kolide":                 {"data_types": ["device_data", "email_address", "process_data"],                         "data_category": "personal",    "default_region": "us",     "purpose": "endpoint_security"},
    "snyk":                   {"data_types": ["access_logs", "audit_logs"],                                            "data_category": "operational", "default_region": "us",     "purpose": "security_scanning"},
    "wiz":                    {"data_types": ["infrastructure_data", "access_logs", "security_events"],                "data_category": "operational", "default_region": "us",     "purpose": "cloud_security"},
    "tenable":                {"data_types": ["ip_address", "device_data", "security_events"],                         "data_category": "operational", "default_region": "us",     "purpose": "vulnerability_management"},
    "qualys":                 {"data_types": ["ip_address", "device_data", "security_events"],                         "data_category": "operational", "default_region": "us",     "purpose": "vulnerability_management"},
    "metomic":                {"data_types": ["behavioral_data", "ip_address", "access_logs"],                         "data_category": "operational", "default_region": "eu",     "purpose": "data_security"},
    "nightfall":              {"data_types": ["security_events", "access_logs"],                                       "data_category": "operational", "default_region": "us",     "purpose": "dlp"},
    "splunk":                 {"data_types": ["access_logs", "security_events", "behavioral_data", "ip_address"],      "data_category": "operational", "default_region": "us",     "purpose": "siem"},
    "datadog":                {"data_types": ["access_logs", "security_events", "behavioral_data", "ip_address"],      "data_category": "operational", "default_region": "us",     "purpose": "monitoring"},
    "sentry":                 {"data_types": ["ip_address", "device_data", "behavioral_data", "email_address"],        "data_category": "personal",    "default_region": "us",     "purpose": "error_monitoring"},
    "pagerduty":              {"data_types": ["email_address", "phone_number", "access_logs"],                         "data_category": "personal",    "default_region": "us",     "purpose": "incident_management"},
    "opsgenie":               {"data_types": ["email_address", "phone_number"],                                        "data_category": "personal",    "default_region": "us",     "purpose": "incident_management"},
    "cloudflare":             {"data_types": ["ip_address", "behavioral_data", "access_logs"],                         "data_category": "personal",    "default_region": "global", "purpose": "network_security"},
    "hackerone":              {"data_types": ["email_address", "security_events"],                                     "data_category": "operational", "default_region": "us",     "purpose": "bug_bounty"},
    "betteruptime":           {"data_types": ["access_logs", "behavioral_data"],                                       "data_category": "operational", "default_region": "eu",     "purpose": "monitoring"},
    "new_relic":              {"data_types": ["access_logs", "behavioral_data", "ip_address"],                         "data_category": "operational", "default_region": "us",     "purpose": "monitoring"},
    # Data
    "snowflake":              {"data_types": ["storage_data", "access_logs"],                                          "data_category": "operational", "default_region": "us",     "purpose": "data_warehouse"},
    "databricks":             {"data_types": ["storage_data", "access_logs"],                                          "data_category": "operational", "default_region": "us",     "purpose": "data_platform"},
    "vault":                  {"data_types": ["access_logs", "audit_logs"],                                            "data_category": "operational", "default_region": "us",     "purpose": "secrets_management"},
    # Time Tracking
    "harvest":                {"data_types": ["full_name", "email_address", "employment_status"],                      "data_category": "personal",    "default_region": "us",     "purpose": "time_tracking"},
    # AI Vendors
    "openai":                 {"data_types": ["api_usage_data", "model_inputs", "model_outputs"],                      "data_category": "operational", "default_region": "us",     "purpose": "ai_processing"},
    "anthropic":              {"data_types": ["api_usage_data", "model_inputs", "model_outputs"],                      "data_category": "operational", "default_region": "us",     "purpose": "ai_processing"},
    "google_gemini":          {"data_types": ["api_usage_data", "model_inputs", "model_outputs"],                      "data_category": "operational", "default_region": "us",     "purpose": "ai_processing"},
}

# ── Regulation labels ──────────────────────────────────────────────────────────
REGULATION_LABELS: dict[str, str] = {
    "gdpr":    "GDPR",
    "ccpa":    "CCPA/CPRA",
    "hipaa":   "HIPAA",
    "pci_dss": "PCI DSS",
    "sox":     "SOX",
    "lgpd":    "LGPD",
}

# Data types that trigger elevated regulations
_HEALTH_TYPES = {"health_records", "biometric_data", "genetic_data", "medical_data"}
_PAYMENT_TYPES = {"payment_card_data", "cardholder_data", "transaction_data"}
_SENSITIVE_PERSONAL = {"date_of_birth", "salary", "personal_address", "candidate_data"}
_AI_PERSONAL = {"model_inputs", "model_outputs"}


def compute_risk(data_category: str, data_types: list[str], is_cross_border: bool) -> str:
    """Compute risk level from data category, types, and cross-border status."""
    if any(t in _HEALTH_TYPES for t in data_types) or any(t in _PAYMENT_TYPES for t in data_types):
        return "critical"
    base = {"sensitive": "high", "financial": "high", "personal": "medium", "operational": "low"}.get(data_category, "medium")
    if is_cross_border and base == "medium":
        return "high"
    if is_cross_border and base == "low":
        return "medium"
    return base


def compute_regulations(data_category: str, data_types: list[str], region: str) -> list[str]:
    """Determine which regulations apply based on data and region."""
    regs: set[str] = set()
    # GDPR: any personal/sensitive data (assume EU customers possible)
    if data_category in ("personal", "sensitive"):
        regs.add("gdpr")
        regs.add("ccpa")
    # AI data processing with personal inputs triggers GDPR
    if any(t in _AI_PERSONAL for t in data_types):
        regs.add("gdpr")
    # HIPAA: health data
    if any(t in _HEALTH_TYPES for t in data_types):
        regs.add("hipaa")
    # PCI DSS: payment card data
    if any(t in _PAYMENT_TYPES for t in data_types):
        regs.add("pci_dss")
    # EU region always triggers GDPR
    if region in ("eu", "eu-west", "eu-central", "eu-north"):
        regs.add("gdpr")
    return sorted(regs)


def _region_is_cross_border(region: str, home_region: str = "us") -> bool:
    eu = {"eu", "eu-west", "eu-central", "eu-north"}
    us = {"us", "us-east", "us-west"}
    if home_region in us and region in eu:
        return True
    if home_region in eu and region in us:
        return True
    return False


async def scan_and_populate(company_id: uuid.UUID, db: AsyncSession) -> list[DataFlow]:
    """
    Read all connected integrations for the company and auto-create DataFlow records.
    Existing auto-detected flows are replaced; manually-created ones are preserved.
    """
    from models.integration import Integration

    # Remove previous auto-detected flows
    await db.execute(
        delete(DataFlow).where(
            DataFlow.company_id == company_id,
            DataFlow.is_auto_detected.is_(True),
        )
    )

    integrations_result = await db.execute(
        select(Integration).where(
            Integration.company_id == company_id,
            Integration.status == "active",
        )
    )
    integrations = list(integrations_result.scalars().all())

    new_flows: list[DataFlow] = []
    for integration in integrations:
        itype = integration.integration_type
        mapping = INTEGRATION_DATA_MAP.get(itype)
        if not mapping:
            continue

        data_types: list[str] = mapping["data_types"]
        data_category: str = mapping["data_category"]
        region: str = mapping["default_region"]
        purpose: str = mapping["purpose"]

        is_cross_border = _region_is_cross_border(region)
        risk = compute_risk(data_category, data_types, is_cross_border)
        regs = compute_regulations(data_category, data_types, region)
        tool_label = itype.replace("_", " ").title()

        # Create one flow per data type for granular visibility
        for data_type in data_types:
            flow = DataFlow(
                id=uuid.uuid4(),
                company_id=company_id,
                data_type=data_type,
                data_category=data_category,
                tool=itype,
                tool_label=tool_label,
                region=region,
                risk_level=risk,
                regulations=regs,
                purpose=purpose,
                is_auto_detected=True,
                is_cross_border=is_cross_border,
            )
            db.add(flow)
            new_flows.append(flow)

    await db.commit()
    logger.info("Data flow scan: company=%s flows_created=%d", company_id, len(new_flows))
    return new_flows


async def add_flow_for_integration(company_id: uuid.UUID, integration_type: str, db: AsyncSession) -> None:
    """Called when a new integration is connected — creates auto-detected flows for it."""
    mapping = INTEGRATION_DATA_MAP.get(integration_type)
    if not mapping:
        return

    data_types: list[str] = mapping["data_types"]
    data_category: str = mapping["data_category"]
    region: str = mapping["default_region"]
    purpose: str = mapping["purpose"]
    is_cross_border = _region_is_cross_border(region)
    risk = compute_risk(data_category, data_types, is_cross_border)
    regs = compute_regulations(data_category, data_types, region)
    tool_label = integration_type.replace("_", " ").title()

    for data_type in data_types:
        flow = DataFlow(
            id=uuid.uuid4(),
            company_id=company_id,
            data_type=data_type,
            data_category=data_category,
            tool=integration_type,
            tool_label=tool_label,
            region=region,
            risk_level=risk,
            regulations=regs,
            purpose=purpose,
            is_auto_detected=True,
            is_cross_border=is_cross_border,
        )
        db.add(flow)

    await db.commit()
    logger.info("Auto-created data flows for integration=%s company=%s", integration_type, company_id)


async def remove_flows_for_integration(company_id: uuid.UUID, integration_type: str, db: AsyncSession) -> None:
    """Called when an integration is disconnected — removes its auto-detected flows."""
    await db.execute(
        delete(DataFlow).where(
            DataFlow.company_id == company_id,
            DataFlow.tool == integration_type,
            DataFlow.is_auto_detected.is_(True),
        )
    )
    await db.commit()
