"""
Full demo seed — populates admin@tracelayer.it.com with ALL integrations connected
and rich data across every module.

Usage (from backend/ directory):
    python scripts/seed_demo_full.py

Safe to re-run — uses upsert for evidence, skips existing rows for everything else.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.fernet import Fernet
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.config import settings
from core.database import AsyncSessionLocal
from core.security import hash_password
from models import Company, Evidence, Integration, User
from models.access_review import AccessReview
from models.asset import Asset
from models.background_check import BackgroundCheck
from models.bcp_record import BcpRecord
from models.data_breach import DataBreach
from models.incident import Incident
from models.management_review import ManagementReview
from models.offboarding import Offboarding
from models.pen_test import PenTest
from models.risk import Risk
from models.ropa_record import RopaRecord
from models.soa_item import SoaItem
from models.subject_request import SubjectRequest
from models.training import TrainingRecord
from models.vendor import Vendor
from models.vulnerability import Vulnerability

DEMO_EMAIL = "admin@tracelayer.it.com"
DEMO_PASSWORD = "admin"
DEMO_COMPANY = "Acme Corp (Demo)"

NOW = datetime.now(timezone.utc)
D = timedelta(days=1)


def _enc(data: dict) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


def _ev(cid, integration, control, evidence_type, source_id, data, age_days=1):
    return {
        "id": uuid.uuid4(),
        "company_id": cid,
        "integration": integration,
        "control": control,
        "evidence_type": evidence_type,
        "source_id": source_id,
        "timestamp": NOW - timedelta(days=age_days),
        "data": data,
    }


# ── ALL INTEGRATIONS ──────────────────────────────────────────────────────────

ALL_INTEGRATIONS = [
    ("aws",              {"access_key_id": "AKIADEMO", "secret_access_key": "DEMO", "region": "us-east-1"}),
    ("github",           {"token": "ghp_DEMO", "org": "acme-corp"}),
    ("slack",            {"bot_token": "xoxb-DEMO"}),
    ("okta",             {"domain": "acme.okta.com", "api_token": "DEMO"}),
    ("google_workspace", {"admin_email": "admin@acme.com", "service_account_json": '{"type":"service_account","project_id":"acme-demo"}'}),
    ("jira",             {"domain": "acme.atlassian.net", "email": "admin@acme.com", "api_token": "DEMO"}),
    ("azure_ad",         {"tenant_id": "DEMO-TENANT", "client_id": "DEMO-CLIENT", "client_secret": "DEMO"}),
    ("gitlab",           {"token": "glpat-DEMO", "domain": "gitlab.com"}),
    ("linear",           {"api_key": "lin_api_DEMO"}),
    ("notion",           {"api_key": "secret_DEMO"}),
    ("microsoft_teams",  {"tenant_id": "DEMO-TENANT", "client_id": "DEMO-CLIENT", "client_secret": "DEMO"}),
    ("cloudflare",       {"api_token": "DEMO", "account_id": "DEMO-ACCOUNT"}),
    ("crowdstrike",      {"client_id": "DEMO-CLIENT", "client_secret": "DEMO", "base_url": "https://api.crowdstrike.com"}),
    ("jamf",             {"domain": "acme.jamfcloud.com", "username": "api-user", "password": "DEMO"}),
    ("datadog",          {"api_key": "DEMO", "app_key": "DEMO", "site": "datadoghq.com"}),
    ("pagerduty",        {"api_key": "DEMO"}),
    ("sentry",           {"auth_token": "DEMO", "org_slug": "acme-corp"}),
    ("stripe",           {"api_key": "rk_live_DEMO"}),
    ("bamboohr",         {"subdomain": "acmecorp", "api_key": "DEMO"}),
    ("vercel",           {"api_token": "DEMO", "team_id": "team_DEMO"}),
    ("terraform_cloud",  {"api_token": "DEMO", "org_name": "acme-corp"}),
    ("1password",        {"service_account_token": "ops_DEMO"}),
    ("rippling",         {"api_key": "DEMO"}),
    ("google_cloud",     {"service_account_json": '{"type":"service_account","project_id":"acme-prod"}', "project_id": "acme-prod-123"}),
]


# ── EVIDENCE ──────────────────────────────────────────────────────────────────

def _evidence(cid):
    records = []
    employees = ["alice@acme.com", "bob@acme.com", "carol@acme.com", "dave@acme.com", "eve@acme.com",
                 "frank@acme.com", "grace@acme.com", "ivan@acme.com", "julia@acme.com", "henry@acme.com"]

    # AWS
    for i, email in enumerate(employees):
        uid = f"AIDA{'0'*(16-len(str(i+1)))}{i+1}"
        records.append(_ev(cid, "aws", "access_control", "iam_users", uid, {
            "username": email, "arn": f"arn:aws:iam::123456789012:user/{email}",
            "admin": email in ["carol@acme.com", "ivan@acme.com"],
            "mfa_active": email not in ["henry@acme.com", "frank@acme.com"],
            "last_activity": (NOW - timedelta(days=2)).isoformat(),
        }))
    for name, admin in [("AdministratorAccess", True), ("ReadOnlyAccess", False), ("S3FullAccess", False),
                        ("CloudTrailFullAccess", False), ("EC2FullAccess", False), ("SecurityAudit", False)]:
        records.append(_ev(cid, "aws", "access_control", "iam_policies", f"policy_{name}", {
            "policy_name": name, "admin_policy": admin, "attached_users": 2 if admin else 5,
        }, age_days=2))
    for event, source, actor in [
        ("ConsoleLogin", "signin.amazonaws.com", "alice@acme.com"),
        ("CreateTrail", "cloudtrail.amazonaws.com", "carol@acme.com"),
        ("PutBucketPolicy", "s3.amazonaws.com", "deploy-bot"),
        ("CreateAccessKey", "iam.amazonaws.com", "carol@acme.com"),
        ("AuthorizeSecurityGroupIngress", "ec2.amazonaws.com", "ivan@acme.com"),
        ("AttachUserPolicy", "iam.amazonaws.com", "ivan@acme.com"),
        ("GetSecretValue", "secretsmanager.amazonaws.com", "ci-runner"),
        ("PutBucketPublicAccessBlock", "s3.amazonaws.com", "grace@acme.com"),
    ]:
        records.append(_ev(cid, "aws", "logging_monitoring", "cloudtrail_logs", f"ct_{event}_{actor}", {
            "event_name": event, "event_source": source, "user": actor, "region": "us-east-1",
            "event_time": (NOW - timedelta(hours=6)).isoformat(),
        }, age_days=0))

    # GitHub
    for name, private in [("backend", True), ("frontend", True), ("infra", True), ("mobile", True),
                           ("data-pipeline", True), ("docs", False), ("marketing-site", False)]:
        records.append(_ev(cid, "github", "change_management", "repositories", f"gh_{name}", {
            "name": name, "full_name": f"acme-corp/{name}", "private": private,
            "default_branch": "main", "branch_protection_enabled": private,
            "updated_at": (NOW - D).isoformat(),
        }, age_days=2))
    for login in ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "ivan", "julia"]:
        records.append(_ev(cid, "github", "access_control", "github_members", login, {
            "login": login, "id": abs(hash(login)) % 99999, "type": "User", "site_admin": False,
        }))

    # Slack
    for email, uid, admin in [("alice@acme.com","U001",True), ("bob@acme.com","U002",False),
                               ("carol@acme.com","U003",True), ("dave@acme.com","U004",False),
                               ("eve@acme.com","U005",False), ("frank@acme.com","U006",False),
                               ("grace@acme.com","U007",False), ("ivan@acme.com","U008",True)]:
        records.append(_ev(cid, "slack", "access_control", "slack_users", uid, {
            "id": uid, "email": email, "is_admin": admin, "is_bot": False,
            "two_factor_enabled": admin,
        }))

    # Okta
    for email, uid, mfa, status in [
        ("alice@acme.com","ok1",True,"ACTIVE"), ("bob@acme.com","ok2",True,"ACTIVE"),
        ("carol@acme.com","ok3",True,"ACTIVE"), ("dave@acme.com","ok4",False,"ACTIVE"),
        ("eve@acme.com","ok5",True,"ACTIVE"), ("frank@acme.com","ok6",False,"ACTIVE"),
        ("grace@acme.com","ok7",True,"ACTIVE"), ("henry@acme.com","ok8",False,"SUSPENDED"),
        ("ivan@acme.com","ok9",True,"ACTIVE"), ("julia@acme.com","ok10",True,"ACTIVE"),
    ]:
        records.append(_ev(cid, "okta", "access_control", "okta_users", uid, {
            "login": email, "status": status, "mfa_enrolled": mfa,
            "last_login": (NOW - timedelta(days=2)).isoformat(),
        }))

    # Jira
    for key, name in [("BACK","Backend"), ("FRONT","Frontend"), ("MOB","Mobile"),
                      ("OPS","Infrastructure"), ("SEC","Security"), ("DATA","Data")]:
        records.append(_ev(cid, "jira", "change_management", "jira_projects", f"jira_{key}", {
            "key": key, "name": name, "lead_email": "carol@acme.com",
            "issue_count": abs(hash(key)) % 120 + 20,
        }, age_days=2))

    # Azure AD
    for upn, uid, enabled in [
        ("alice@acme.onmicrosoft.com","az1",True), ("carol@acme.onmicrosoft.com","az2",True),
        ("ivan@acme.onmicrosoft.com","az3",True), ("henry@acme.onmicrosoft.com","az4",False),
        ("grace@acme.onmicrosoft.com","az5",True),
    ]:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_users", uid, {
            "userPrincipalName": upn, "accountEnabled": enabled,
            "mfaRegistered": enabled, "lastSignInDateTime": (NOW - timedelta(days=1)).isoformat(),
        }))

    # Datadog monitoring
    for check, status in [("CPU usage < 80%", "OK"), ("Memory usage < 85%", "OK"),
                          ("Error rate < 1%", "ALERT"), ("API p99 latency < 500ms", "OK"),
                          ("DB connection pool healthy", "OK")]:
        records.append(_ev(cid, "datadog", "logging_monitoring", "datadog_monitors", f"dd_{hash(check)%9999}", {
            "name": check, "status": status, "type": "metric alert",
        }, age_days=0))

    # Cloudflare WAF
    records.append(_ev(cid, "cloudflare", "logging_monitoring", "cloudflare_waf", "cf_waf_001", {
        "zone": "acme.com", "waf_enabled": True, "ddos_protection": True,
        "firewall_rules": 12, "page_rules": 5,
    }, age_days=1))

    return records


# ── MODULE DATA ───────────────────────────────────────────────────────────────

def _risks(cid):
    return [
        Risk(id=uuid.uuid4(), company_id=cid, title="Unauthorized access to production systems",
             description="Risk of unauthorized access via compromised credentials or misconfigured permissions.",
             category="Access Control", likelihood=3, impact=5, status="open",
             notes="MFA enforced for all production access. Quarterly access reviews scheduled."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Third-party vendor data breach",
             description="A critical vendor suffers a data breach affecting customer PII shared under DPA.",
             category="Third-Party", likelihood=2, impact=5, status="mitigated",
             notes="SOC 2 reports collected for all Tier 1 vendors. DPAs in place."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Ransomware attack on internal systems",
             description="Ransomware could encrypt critical business data and disrupt operations.",
             category="Cyber Threat", likelihood=2, impact=5, status="mitigated",
             notes="EDR deployed on all endpoints. Offline backups tested quarterly."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Inadequate employee security awareness",
             description="Phishing attacks succeed due to insufficient security training.",
             category="People", likelihood=3, impact=3, status="open",
             notes="Annual security awareness training mandatory. Phishing simulations run quarterly."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Cloud misconfiguration exposing S3 buckets",
             description="Misconfigured S3 bucket policies could expose sensitive customer data.",
             category="Cloud Security", likelihood=2, impact=4, status="mitigated",
             notes="AWS Config rules enforce bucket policies. CloudTrail monitors all S3 events."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Loss of key personnel",
             description="Critical knowledge concentrated in a small number of individuals.",
             category="Operational", likelihood=3, impact=3, status="accepted",
             notes="Documentation and runbooks maintained. Cross-training in progress."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Unpatched software vulnerabilities",
             description="Known CVEs remain unpatched beyond SLA due to resource constraints.",
             category="Vulnerability Management", likelihood=3, impact=4, status="open",
             notes="30-day SLA for critical CVEs. Vulnerability scanner runs weekly."),
        Risk(id=uuid.uuid4(), company_id=cid, title="Insufficient audit log retention",
             description="Audit logs purged before the 12-month retention period required by ISO 27001.",
             category="Compliance", likelihood=1, impact=3, status="mitigated",
             notes="CloudWatch log retention set to 13 months. Verified by last audit."),
    ]


def _incidents(cid):
    return [
        Incident(id=uuid.uuid4(), company_id=cid, title="Phishing email campaign targeting engineering",
                 description="Targeted spear-phishing emails sent to 8 engineers. 1 user clicked link.",
                 severity="high", status="resolved",
                 detected_at=NOW - timedelta(days=45), resolved_at=NOW - timedelta(days=43),
                 affected_systems="Email (Google Workspace)", root_cause="Social engineering via LinkedIn-harvested names",
                 lessons_learned="Added phishing simulation training. Deployed email link scanning."),
        Incident(id=uuid.uuid4(), company_id=cid, title="Elevated API error rate (5xx spike)",
                 description="Production API returned 5xx errors for 14 minutes due to DB connection pool exhaustion.",
                 severity="medium", status="resolved",
                 detected_at=NOW - timedelta(days=21), resolved_at=NOW - timedelta(days=21),
                 affected_systems="Backend API, PostgreSQL RDS",
                 root_cause="Connection pool limit not scaled with recent traffic growth.",
                 lessons_learned="Increased pool size. Added connection pool monitoring alert."),
        Incident(id=uuid.uuid4(), company_id=cid, title="Contractor account not deprovisioned",
                 description="Former contractor retained active Okta account 11 days after contract end.",
                 severity="medium", status="resolved",
                 detected_at=NOW - timedelta(days=15), resolved_at=NOW - timedelta(days=14),
                 affected_systems="Okta, GitHub, Jira",
                 root_cause="Offboarding checklist not followed by HR.",
                 lessons_learned="Automated offboarding trigger connected to HR system."),
        Incident(id=uuid.uuid4(), company_id=cid, title="Suspected credential stuffing attempt",
                 description="1,200 failed login attempts from 40 IP addresses over 3 hours.",
                 severity="low", status="closed",
                 detected_at=NOW - timedelta(days=8), resolved_at=NOW - timedelta(days=8),
                 affected_systems="Auth service",
                 root_cause="Automated bot using previously leaked credential list.",
                 lessons_learned="Rate limiting tightened. CAPTCHA added after 5 failed attempts."),
        Incident(id=uuid.uuid4(), company_id=cid, title="Accidental public S3 bucket exposure",
                 description="Staging bucket accidentally set to public-read for 2 hours during infrastructure change.",
                 severity="high", status="resolved",
                 detected_at=NOW - timedelta(days=62), resolved_at=NOW - timedelta(days=62),
                 affected_systems="AWS S3 (staging)",
                 root_cause="Terraform change missing `block_public_access` flag.",
                 lessons_learned="Added AWS Config rule to alert on public buckets within 60 seconds."),
    ]


def _vulnerabilities(cid):
    return [
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="Log4Shell in legacy reporting service",
                      cve_id="CVE-2021-44228", severity="critical", status="resolved",
                      affected_system="reporting-service v1.2.3",
                      discovered_at=NOW - timedelta(days=90),
                      resolved_at=NOW - timedelta(days=85),
                      description="Log4j 2.x RCE vulnerability in legacy reporting microservice.",
                      remediation_notes="Upgraded Log4j to 2.17.1. Service rebuilt and redeployed."),
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="OpenSSL heap buffer overflow",
                      cve_id="CVE-2022-0778", severity="high", status="resolved",
                      affected_system="API gateway, 3 backend services",
                      discovered_at=NOW - timedelta(days=60), resolved_at=NOW - timedelta(days=55),
                      description="Infinite loop in BN_mod_sqrt() for non-prime moduli.",
                      remediation_notes="Updated OpenSSL to 3.0.2 across all affected containers."),
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="Outdated nginx with HTTP/2 vuln",
                      cve_id="CVE-2023-44487", severity="high", status="in_remediation",
                      affected_system="Load balancer nginx 1.22.0",
                      discovered_at=NOW - timedelta(days=10),
                      due_date=NOW + timedelta(days=5),
                      description="HTTP/2 Rapid Reset Attack vulnerability allowing DoS.",
                      remediation_notes="Upgrade scheduled for next maintenance window."),
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="pip dependency with prototype pollution",
                      cve_id="CVE-2023-26115", severity="medium", status="open",
                      affected_system="data-pipeline service",
                      discovered_at=NOW - timedelta(days=5),
                      due_date=NOW + timedelta(days=25),
                      description="Prototype pollution in word-wrap npm package.",
                      remediation_notes="Pending dependency update in next sprint."),
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="Weak TLS 1.0/1.1 still enabled",
                      severity="medium", status="in_remediation",
                      affected_system="Legacy customer portal",
                      discovered_at=NOW - timedelta(days=30),
                      due_date=NOW + timedelta(days=2),
                      description="TLS 1.0 and 1.1 remain enabled on legacy portal endpoint.",
                      remediation_notes="ALB config update in progress. ETA 2 days."),
        Vulnerability(id=uuid.uuid4(), company_id=cid, title="Default admin credentials on internal Grafana",
                      severity="high", status="resolved",
                      affected_system="Grafana monitoring dashboard",
                      discovered_at=NOW - timedelta(days=20), resolved_at=NOW - timedelta(days=19),
                      description="Internal Grafana instance had default admin/admin credentials.",
                      remediation_notes="Password rotated. SSO via Okta enforced."),
    ]


def _vendors(cid):
    return [
        Vendor(id=uuid.uuid4(), company_id=cid, name="Amazon Web Services", category="cloud",
               risk_level="high", website="https://aws.amazon.com", contact_email="aws-support@amazon.com",
               soc2_certified=True, iso27001_certified=True, hipaa_certified=True,
               review_date=NOW - timedelta(days=30), notes="Primary cloud infrastructure provider. Annual review completed."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Stripe", category="payment",
               risk_level="high", website="https://stripe.com", contact_email="support@stripe.com",
               soc2_certified=True, iso27001_certified=False, hipaa_certified=False,
               review_date=NOW - timedelta(days=45), notes="Payment processing. PCI DSS Level 1 certified."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Okta", category="identity",
               risk_level="high", website="https://okta.com", contact_email="support@okta.com",
               soc2_certified=True, iso27001_certified=True, hipaa_certified=True,
               review_date=NOW - timedelta(days=60), notes="Identity provider. SOC 2 Type II reviewed."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Datadog", category="security",
               risk_level="medium", website="https://datadoghq.com",
               soc2_certified=True, iso27001_certified=False, hipaa_certified=False,
               review_date=NOW - timedelta(days=90), notes="Monitoring and observability platform."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="GitHub", category="other",
               risk_level="medium", website="https://github.com",
               soc2_certified=True, iso27001_certified=True, hipaa_certified=False,
               review_date=NOW - timedelta(days=120), notes="Source code management. Enterprise license."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Twilio SendGrid", category="communication",
               risk_level="low", website="https://sendgrid.com",
               soc2_certified=True, iso27001_certified=False, hipaa_certified=False,
               review_date=NOW - timedelta(days=150), notes="Transactional email delivery."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Intercom", category="other",
               risk_level="medium", website="https://intercom.com",
               soc2_certified=True, iso27001_certified=False, hipaa_certified=False,
               review_date=NOW - timedelta(days=180),
               notes="Customer support chat. Processes customer PII. DPA signed."),
        Vendor(id=uuid.uuid4(), company_id=cid, name="Supabase", category="cloud",
               risk_level="medium", website="https://supabase.com",
               soc2_certified=True, iso27001_certified=False, hipaa_certified=False,
               review_date=NOW - timedelta(days=200), notes="Database and storage. SOC 2 Type II."),
    ]


def _assets(cid):
    return [
        Asset(id=uuid.uuid4(), company_id=cid, name="Production API (ECS Fargate)", asset_type="cloud",
              environment="production", classification="confidential", status="active",
              vendor="Amazon Web Services", version="latest", location="us-east-1",
              description="Primary backend API running on ECS Fargate behind ALB.",
              last_reviewed_at=NOW - timedelta(days=30)),
        Asset(id=uuid.uuid4(), company_id=cid, name="PostgreSQL RDS (prod)", asset_type="cloud",
              environment="production", classification="restricted", status="active",
              vendor="Amazon Web Services", version="PostgreSQL 15.4",
              description="Primary production database. Encrypted at rest and in transit.",
              last_reviewed_at=NOW - timedelta(days=30)),
        Asset(id=uuid.uuid4(), company_id=cid, name="Customer data S3 bucket", asset_type="cloud",
              environment="production", classification="restricted", status="active",
              vendor="Amazon Web Services", location="us-east-1",
              description="S3 bucket storing customer uploaded files. Versioning and MFA delete enabled."),
        Asset(id=uuid.uuid4(), company_id=cid, name="Frontend (Vercel)", asset_type="cloud",
              environment="production", classification="public", status="active",
              vendor="Vercel", version="Next.js 14", location="Edge network",
              description="Customer-facing web application deployed on Vercel."),
        Asset(id=uuid.uuid4(), company_id=cid, name="Macbook Pro (Engineering fleet)", asset_type="hardware",
              environment="other", classification="confidential", status="active",
              vendor="Apple", version="MacOS 14 Sonoma",
              description="Engineering laptops managed via Jamf. Full disk encryption enforced.",
              last_reviewed_at=NOW - timedelta(days=90)),
        Asset(id=uuid.uuid4(), company_id=cid, name="Okta Identity Platform", asset_type="software",
              environment="production", classification="confidential", status="active",
              vendor="Okta", description="SSO and MFA for all internal applications.",
              last_reviewed_at=NOW - timedelta(days=60)),
        Asset(id=uuid.uuid4(), company_id=cid, name="GitHub Enterprise (source code)", asset_type="software",
              environment="production", classification="confidential", status="active",
              vendor="GitHub", description="All source code repositories. IP and trade secrets.",
              last_reviewed_at=NOW - timedelta(days=45)),
        Asset(id=uuid.uuid4(), company_id=cid, name="Datadog APM + SIEM", asset_type="software",
              environment="production", classification="internal", status="active",
              vendor="Datadog", description="Application performance monitoring and security event management.",
              last_reviewed_at=NOW - timedelta(days=60)),
        Asset(id=uuid.uuid4(), company_id=cid, name="Staging environment (ECS)", asset_type="cloud",
              environment="staging", classification="internal", status="active",
              vendor="Amazon Web Services", location="us-east-1",
              description="Staging environment. Contains anonymized production data snapshots."),
    ]


def _training(cid):
    records = []
    employees = [
        ("alice@acme.com", "Alice Smith"), ("bob@acme.com", "Bob Jones"),
        ("carol@acme.com", "Carol White"), ("dave@acme.com", "Dave Brown"),
        ("eve@acme.com", "Eve Davis"), ("frank@acme.com", "Frank Miller"),
        ("grace@acme.com", "Grace Wilson"), ("ivan@acme.com", "Ivan Clark"),
        ("julia@acme.com", "Julia Moore"), ("henry@acme.com", "Henry Taylor"),
    ]
    courses = [
        ("Security Awareness Training 2025", "Annual mandatory security awareness training covering phishing, social engineering, and data handling.", True),
        ("GDPR & Data Privacy Fundamentals", "Training on GDPR obligations, data subject rights, and handling personal data.", True),
        ("Incident Response Procedures", "How to identify, report, and respond to security incidents.", False),
        ("Secure Coding Practices", "OWASP Top 10, input validation, and secure development lifecycle.", False),
    ]
    for email, name in employees:
        for i, (title, desc, annual) in enumerate(courses):
            # First 2 courses: most completed, last 2: mixed
            if i < 2:
                completed = email not in ["henry@acme.com", "frank@acme.com"]
            else:
                completed = email in ["alice@acme.com", "carol@acme.com", "ivan@acme.com"]
            records.append(TrainingRecord(
                id=uuid.uuid4(), company_id=cid,
                assignee_email=email, assignee_name=name, title=title, description=desc,
                due_date=NOW - timedelta(days=60) if completed else NOW + timedelta(days=30),
                completed_at=NOW - timedelta(days=90) if completed else None,
                status="completed" if completed else ("overdue" if i < 2 else "pending"),
                annual=annual,
            ))
    return records


def _pen_tests(cid):
    return [
        PenTest(id=uuid.uuid4(), company_id=cid, vendor_name="Bishop Fox",
                status="remediated",
                scope="External web application, API endpoints, and AWS infrastructure",
                conducted_at=NOW - timedelta(days=180),
                next_scheduled_at=NOW + timedelta(days=185),
                critical_count=0, high_count=2, medium_count=5, low_count=8,
                summary="Annual penetration test found 2 high findings (both remediated): SQL injection in legacy endpoint and SSRF via image upload. All findings resolved within SLA.",
                remediation_notes="SQL injection patched in v2.3.1. SSRF mitigated by restricting outbound requests."),
        PenTest(id=uuid.uuid4(), company_id=cid, vendor_name="NCC Group",
                status="completed",
                scope="Internal network and Active Directory (M365/Azure AD)",
                conducted_at=NOW - timedelta(days=90),
                next_scheduled_at=NOW + timedelta(days=275),
                critical_count=0, high_count=1, medium_count=3, low_count=4,
                summary="Internal network pentest. High finding: Kerberoastable service account. Medium findings: weak password policy for service accounts, legacy SMBv1 on 2 hosts.",
                remediation_notes="Service account password rotated to 30-char random. SMBv1 disabled. Password policy updated."),
        PenTest(id=uuid.uuid4(), company_id=cid, vendor_name="Cobalt.io",
                status="scheduled",
                scope="Mobile application (iOS + Android) and mobile API",
                next_scheduled_at=NOW + timedelta(days=45),
                critical_count=0, high_count=0, medium_count=0, low_count=0,
                summary="Upcoming mobile app pentest scheduled for Q2 2026."),
    ]


def _access_reviews(cid):
    return [
        AccessReview(id=uuid.uuid4(), company_id=cid, title="Q1 2026 Quarterly Access Review",
                     period="Q1 2026", status="completed",
                     due_date=NOW - timedelta(days=5), completed_at=NOW - timedelta(days=3),
                     users_reviewed=47, access_changes=6,
                     scope="All production system access: AWS IAM, GitHub, Okta applications, Jira projects",
                     findings="6 access changes made: 2 contractor accounts deprovisioned, 3 excess permissions removed, 1 admin role downgraded.",
                     notes="Completed on time. No critical findings."),
        AccessReview(id=uuid.uuid4(), company_id=cid, title="Q4 2025 Quarterly Access Review",
                     period="Q4 2025", status="completed",
                     due_date=NOW - timedelta(days=95), completed_at=NOW - timedelta(days=90),
                     users_reviewed=43, access_changes=4,
                     scope="All production system access + privileged accounts",
                     findings="4 changes: 1 terminated employee access revoked (late — 8 days post-termination), 3 orphaned service accounts deleted.",
                     notes="Identified gap in offboarding process. Automated deprovisioning trigger added."),
        AccessReview(id=uuid.uuid4(), company_id=cid, title="Q2 2026 Quarterly Access Review",
                     period="Q2 2026", status="open",
                     due_date=NOW + timedelta(days=85),
                     users_reviewed=0, access_changes=0,
                     scope="All production system access, third-party integrations, and API keys",
                     notes="Scheduled. Reviewer assigned."),
    ]


def _background_checks(cid):
    employees = [
        ("Alice Smith", "alice@acme.com", "standard", "Checkr", "completed", -120, -110, 365),
        ("Bob Jones", "bob@acme.com", "standard", "Checkr", "completed", -118, -108, 365),
        ("Carol White", "carol@acme.com", "enhanced", "HireRight", "completed", -200, -185, 365),
        ("Dave Brown", "dave@acme.com", "standard", "Checkr", "completed", -150, -140, 365),
        ("Eve Davis", "eve@acme.com", "standard", "Checkr", "completed", -95, -85, 365),
        ("Frank Miller", "frank@acme.com", "standard", "Checkr", "completed", -60, -50, 365),
        ("Grace Wilson", "grace@acme.com", "enhanced", "HireRight", "completed", -55, -45, 365),
        ("Ivan Clark", "ivan@acme.com", "enhanced", "HireRight", "completed", -240, -225, 365),
        ("Julia Moore", "julia@acme.com", "standard", "Checkr", "completed", -30, -22, 365),
        ("Henry Taylor", "henry@acme.com", "standard", "Checkr", "failed", -300, -290, None),
    ]
    records = []
    for name, email, ctype, vendor, status, init, comp, valid in employees:
        records.append(BackgroundCheck(
            id=uuid.uuid4(), company_id=cid,
            employee_name=name, employee_email=email,
            check_type=ctype, vendor=vendor, status=status,
            initiated_at=NOW + timedelta(days=init),
            completed_at=NOW + timedelta(days=comp) if comp else None,
            valid_until=NOW + timedelta(days=valid) if valid else None,
            notes="Clear" if status == "completed" else "Discrepancy found in employment history. HR reviewing.",
        ))
    return records


def _offboarding(cid):
    return [
        Offboarding(id=uuid.uuid4(), company_id=cid,
                    employee_name="Henry Taylor", employee_email="henry@acme.com",
                    last_day=NOW - timedelta(days=45), department="Engineering",
                    status="completed",
                    checklist=[
                        {"item": "Revoke Okta access", "done": True},
                        {"item": "Remove GitHub org membership", "done": True},
                        {"item": "Revoke AWS IAM access", "done": True},
                        {"item": "Return MacBook Pro", "done": True},
                        {"item": "Final payroll processed", "done": True},
                        {"item": "Exit interview conducted", "done": True},
                    ],
                    completed_at=NOW - timedelta(days=44),
                    notes="Standard offboarding. All access revoked within 24 hours."),
        Offboarding(id=uuid.uuid4(), company_id=cid,
                    employee_name="Mark Johnson (Contractor)", employee_email="mark.j@ext.com",
                    last_day=NOW - timedelta(days=15), department="Marketing",
                    status="completed",
                    checklist=[
                        {"item": "Revoke Okta access", "done": True},
                        {"item": "Remove Notion workspace access", "done": True},
                        {"item": "Revoke Jira access", "done": True},
                        {"item": "Return equipment", "done": False},
                    ],
                    completed_at=NOW - timedelta(days=13),
                    notes="Equipment return pending. All system access revoked."),
    ]


def _bcp(cid):
    return [
        BcpRecord(id=uuid.uuid4(), company_id=cid, title="Business Continuity Plan — Production Platform",
                  record_type="both", status="passed",
                  last_tested_at=NOW - timedelta(days=90),
                  next_test_due=NOW + timedelta(days=275),
                  rto_minutes=240, rpo_minutes=60,
                  scope="Production API, PostgreSQL RDS, S3 storage, and supporting AWS services",
                  test_results="Full failover test completed in 3h 12min (RTO met). Data loss simulated at 47 minutes (RPO met). All services restored. 2 runbook gaps identified and resolved.",
                  notes="Next test: simulate full AWS region outage with failover to eu-west-1."),
        BcpRecord(id=uuid.uuid4(), company_id=cid, title="Disaster Recovery Plan — Database",
                  record_type="drp", status="tested",
                  last_tested_at=NOW - timedelta(days=30),
                  next_test_due=NOW + timedelta(days=150),
                  rto_minutes=60, rpo_minutes=15,
                  scope="PostgreSQL RDS production database. Automated backups to S3 + cross-region replication.",
                  test_results="Point-in-time restore completed in 52 minutes. 11-minute data loss (RPO target 15min — met).",
                  notes="RDS automated backups run every 5 minutes. Retention 35 days."),
        BcpRecord(id=uuid.uuid4(), company_id=cid, title="Incident Response Plan",
                  record_type="bcp", status="passed",
                  last_tested_at=NOW - timedelta(days=60),
                  next_test_due=NOW + timedelta(days=120),
                  rto_minutes=30, rpo_minutes=0,
                  scope="Security incident response: detection, containment, eradication, recovery, post-incident review",
                  test_results="Tabletop exercise conducted with 6 participants. Response runbook followed successfully. Notification to DPA would have been within 72 hours.",
                  notes="Next exercise: ransomware simulation with IT and executive team."),
    ]


def _soa_items(cid):
    """ISO 27001:2022 Annex A — representative set of controls."""
    items = [
        ("5.1","Organizational","Policies for information security","implemented","Information security policy approved by board. Published in Notion. Annual review cycle."),
        ("5.2","Organizational","Information security roles and responsibilities","implemented","CISO role assigned (Carol White). RACI matrix documented."),
        ("5.7","Organizational","Threat intelligence","in_progress","Subscribed to CISA advisories and NCSC threat feeds. Formal process being documented."),
        ("6.1","Organizational","Actions to address risks and opportunities","implemented","Risk register maintained. Quarterly risk review meetings with leadership."),
        ("6.2","Organizational","Information security risk assessment","implemented","Annual risk assessment using ISO 27005 methodology. Last completed Q4 2025."),
        ("8.2","Organizational","Information security risk treatment","implemented","Risk treatment plan documented. 8 risks tracked in TraceLayer."),
        ("5.10","Organizational","Acceptable use of information and other associated assets","implemented","Acceptable Use Policy published and acknowledged by all staff."),
        ("5.15","Organizational","Access control","implemented","Role-based access control enforced via Okta. Quarterly access reviews."),
        ("5.31","Organizational","Legal, statutory, regulatory and contractual requirements","implemented","Legal register maintained. GDPR DPA signed with all processors."),
        ("6.3","People","Information security awareness, education and training","implemented","Annual security awareness training. 85% completion rate Q1 2026."),
        ("6.4","People","Disciplinary process","implemented","HR disciplinary process includes information security violations."),
        ("6.5","People","Responsibilities after termination or change of employment","implemented","Offboarding procedure enforced. Access revoked within 24 hours."),
        ("7.1","Physical","Physical security perimeters","implemented","Office access controlled via key card. Server infrastructure in AWS (no physical DC)."),
        ("7.6","Physical","Working in secure areas","implemented","Clean desk policy. No sensitive data on whiteboards or printed documents."),
        ("8.7","Technological","Protection against malware","implemented","CrowdStrike Falcon deployed on all endpoints. Auto-update enforced."),
        ("8.8","Technological","Management of technical vulnerabilities","in_progress","Weekly vulnerability scans. 30-day SLA for critical CVEs. 6 open vulnerabilities tracked."),
        ("8.12","Technological","Data leakage prevention","in_progress","DLP policy being evaluated. Email DLP active via Google Workspace."),
        ("8.15","Technological","Logging","implemented","CloudTrail enabled. Application logs shipped to Datadog (13-month retention)."),
        ("8.16","Technological","Monitoring activities","implemented","Datadog APM + alerting. PagerDuty on-call rotation for P1/P2 incidents."),
        ("8.24","Technological","Use of cryptography","implemented","TLS 1.2+ enforced. Data encrypted at rest (AES-256). Secrets in AWS Secrets Manager."),
        ("8.28","Technological","Secure coding","implemented","Secure coding guidelines documented. SAST in CI pipeline (Snyk). Code review required."),
    ]
    return [
        SoaItem(id=uuid.uuid4(), company_id=cid, annex_ref=ref, annex_theme=theme,
                title=title, included=True, implementation_status=status,
                implementation_notes=notes)
        for ref, theme, title, status, notes in items
    ]


def _ropa(cid):
    return [
        RopaRecord(id=uuid.uuid4(), company_id=cid, name="Customer Account Management",
                   role="controller", purpose="Manage customer accounts, authentication, and subscription billing",
                   legal_basis="contract",
                   data_categories="Name, email, company name, payment card data (tokenised), usage data",
                   data_subjects="Customers (B2B — company admins and users)",
                   recipients="Stripe (payment processing), Intercom (support), AWS (hosting)",
                   third_country_transfers="US — Stripe and AWS us-east-1. SCCs in place.",
                   retention_period="7 years post contract end (financial records); 2 years inactive account",
                   security_measures="Encryption at rest and in transit, MFA, access controls, annual pentest",
                   notes="Primary processing activity. DPAs signed with all processors."),
        RopaRecord(id=uuid.uuid4(), company_id=cid, name="Employee HR Processing",
                   role="controller", purpose="Employment contract, payroll, benefits administration",
                   legal_basis="contract",
                   data_categories="Full name, NI/SSN, address, bank details, performance data, health data",
                   data_subjects="Employees and contractors",
                   recipients="Rippling (HR/payroll), BambooHR (HR), background check providers",
                   third_country_transfers="US — Rippling. SCCs in place.",
                   retention_period="6 years post employment end (UK requirement)",
                   security_measures="Role-based access, encrypted storage, minimal access principle"),
        RopaRecord(id=uuid.uuid4(), company_id=cid, name="Marketing & Lead Generation",
                   role="controller", purpose="Email marketing, webinar registrations, lead nurturing",
                   legal_basis="consent",
                   data_categories="Name, email, company, job title, marketing interaction data",
                   data_subjects="Prospects and leads",
                   recipients="HubSpot (CRM/email), LinkedIn (ads)",
                   third_country_transfers="US — HubSpot, LinkedIn. SCCs in place.",
                   retention_period="3 years from last interaction, or until consent withdrawn",
                   security_measures="Consent management platform, opt-out mechanism, data minimisation"),
        RopaRecord(id=uuid.uuid4(), company_id=cid, name="Support Ticket Processing",
                   role="processor", purpose="Customer support via live chat and ticketing",
                   legal_basis="legitimate_interests",
                   data_categories="Name, email, support conversation content, product usage context",
                   data_subjects="Customers",
                   recipients="Intercom (sub-processor)",
                   retention_period="3 years from ticket close",
                   security_measures="Access limited to support team. Intercom DPA in place."),
    ]


def _data_breaches(cid):
    return [
        DataBreach(id=uuid.uuid4(), company_id=cid, title="Accidental S3 bucket public exposure",
                   occurred_at=NOW - timedelta(days=62), discovered_at=NOW - timedelta(days=62),
                   breach_type="confidentiality", severity="medium", status="closed",
                   affected_records=0,
                   affected_systems="AWS S3 staging bucket",
                   description="Staging S3 bucket briefly set to public-read during Terraform change. No customer data in bucket — only anonymised test fixtures. Exposure window: 2 hours.",
                   notification_required=False,
                   root_cause="Missing block_public_access flag in Terraform module.",
                   remediation="AWS Config rule added. All buckets audited and confirmed private. Terraform module patched.",
                   reporter_name="Carol White"),
    ]


def _subject_requests(cid):
    return [
        SubjectRequest(id=uuid.uuid4(), company_id=cid,
                       requester_name="Sarah M.", requester_email="sarah.m@example.com",
                       request_type="access", regulation="gdpr",
                       received_at=NOW - timedelta(days=25),
                       due_at=NOW + timedelta(days=5),
                       status="completed",
                       response_notes="Full data export provided covering account data, usage logs, and support tickets. Sent encrypted via email.",
                       completed_at=NOW - timedelta(days=5)),
        SubjectRequest(id=uuid.uuid4(), company_id=cid,
                       requester_name="James P.", requester_email="jamesp@email.com",
                       request_type="deletion", regulation="gdpr",
                       received_at=NOW - timedelta(days=10),
                       due_at=NOW + timedelta(days=20),
                       status="in_progress",
                       response_notes="Deletion request received. Verifying no active subscription. Account scheduled for deletion after 30-day cooling period."),
        SubjectRequest(id=uuid.uuid4(), company_id=cid,
                       requester_name="Lena H.",
                       request_type="rectification", regulation="gdpr",
                       received_at=NOW - timedelta(days=3),
                       due_at=NOW + timedelta(days=27),
                       status="pending",
                       response_notes="Request acknowledged. Pending review of which data fields to update."),
    ]


def _management_reviews(cid):
    return [
        ManagementReview(id=uuid.uuid4(), company_id=cid,
                         review_date=NOW - timedelta(days=90),
                         attendees="CEO (Ivan Clark), CTO (Carol White), Head of Engineering (Alice Smith), HR (Julia Moore)",
                         inputs_summary="Q4 2025 compliance scores reviewed. 3 security incidents in Q4. Pentest results presented. Vendor risk register updated. Access review Q4 completed with 4 changes.",
                         decisions="1. Increase security training budget by 20%. 2. Prioritise automated offboarding integration (Q1 target). 3. Schedule external ISO 27001 gap assessment for Q2.",
                         action_items=[
                             {"item": "Implement automated offboarding trigger", "owner": "alice@acme.com", "due_date": "2026-02-28", "done": True},
                             {"item": "Schedule ISO 27001 gap assessment", "owner": "carol@acme.com", "due_date": "2026-03-31", "done": False},
                             {"item": "Update security awareness training content", "owner": "julia@acme.com", "due_date": "2026-02-15", "done": True},
                         ],
                         next_review_date=NOW + timedelta(days=2),
                         outcome="satisfactory",
                         notes="Overall compliance posture improving. Readiness score up from 71% to 84% in Q4."),
        ManagementReview(id=uuid.uuid4(), company_id=cid,
                         review_date=NOW - timedelta(days=180),
                         attendees="CEO, CTO, Head of Engineering, Head of Sales",
                         inputs_summary="Q3 2025 first full management review post-TraceLayer implementation. SOC 2 readiness at 68%. 5 open risks. First pentest results reviewed.",
                         decisions="1. Adopt TraceLayer for continuous compliance monitoring. 2. Aim for SOC 2 Type I by end of Q1 2026. 3. Conduct quarterly reviews going forward.",
                         action_items=[
                             {"item": "Complete controls gap analysis", "owner": "carol@acme.com", "due_date": "2025-10-31", "done": True},
                             {"item": "Remediate high pentest findings", "owner": "alice@acme.com", "due_date": "2025-11-15", "done": True},
                         ],
                         next_review_date=NOW - timedelta(days=90),
                         outcome="needs_improvement",
                         notes="Significant gaps in documentation and vendor management identified. Action plan agreed."),
    ]


# ── MAIN ─────────────────────────────────────────────────────────────────────

async def seed():
    async with AsyncSessionLocal() as db:
        # ── Ensure company + user exist ──────────────────────────────────────
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()

        if not user:
            company = Company(
                id=uuid.uuid4(), name=DEMO_COMPANY,
                plan="growth", subscription_status="active",
                onboarding_completed=True,
            )
            db.add(company)
            await db.flush()

            user = User(
                id=uuid.uuid4(), email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                company_id=company.id, role="admin", email_verified=True,
            )
            db.add(user)
            await db.flush()
            print(f"✓ Created demo account: {DEMO_EMAIL}")
        else:
            # Ensure growth plan + onboarding done
            company_result = await db.execute(
                select(Company).where(Company.id == user.company_id)
            )
            company = company_result.scalar_one()
            await db.execute(
                update(Company)
                .where(Company.id == company.id)
                .values(plan="growth", subscription_status="active", onboarding_completed=True)
            )
            await db.flush()
            print(f"✓ Found existing demo account: {DEMO_EMAIL} — ensuring growth plan")

        cid = user.company_id

        # ── All integrations ─────────────────────────────────────────────────
        collected = NOW - timedelta(hours=1)
        added = []
        for itype, creds in ALL_INTEGRATIONS:
            existing = await db.execute(
                select(Integration).where(
                    Integration.company_id == cid,
                    Integration.integration_type == itype,
                )
            )
            if existing.scalar_one_or_none():
                continue
            db.add(Integration(
                id=uuid.uuid4(), company_id=cid,
                integration_type=itype, credentials_enc=_enc(creds),
                status="active", last_collected_at=collected,
            ))
            added.append(itype)
        await db.flush()
        print(f"✓ Integrations: {len(added)} added, {len(ALL_INTEGRATIONS)-len(added)} already existed")

        # ── Evidence (upsert) ────────────────────────────────────────────────
        ev_records = _evidence(cid)
        for r in ev_records:
            stmt = (
                pg_insert(Evidence.__table__)
                .values(id=r["id"], company_id=r["company_id"], integration=r["integration"],
                        control=r["control"], evidence_type=r["evidence_type"],
                        source_id=r["source_id"], timestamp=r["timestamp"], data=r["data"])
                .on_conflict_do_update(
                    index_elements=["company_id", "integration", "evidence_type", "source_id"],
                    set_={"data": r["data"], "timestamp": r["timestamp"]},
                )
            )
            await db.execute(stmt)
        print(f"✓ Evidence: {len(ev_records)} records upserted")

        # ── Helper: skip if table already has rows for this company ──────────
        async def _has_rows(model):
            r = await db.execute(select(model).where(model.company_id == cid).limit(1))
            return r.scalar_one_or_none() is not None

        # ── Risks ────────────────────────────────────────────────────────────
        if not await _has_rows(Risk):
            for r in _risks(cid):
                db.add(r)
            print(f"✓ Risks: {len(_risks(cid))} added")
        else:
            print("  · Risks: already seeded")

        # ── Incidents ────────────────────────────────────────────────────────
        if not await _has_rows(Incident):
            items = _incidents(cid)
            for r in items:
                db.add(r)
            print(f"✓ Incidents: {len(items)} added")
        else:
            print("  · Incidents: already seeded")

        # ── Vulnerabilities ──────────────────────────────────────────────────
        if not await _has_rows(Vulnerability):
            items = _vulnerabilities(cid)
            for r in items:
                db.add(r)
            print(f"✓ Vulnerabilities: {len(items)} added")
        else:
            print("  · Vulnerabilities: already seeded")

        # ── Vendors ──────────────────────────────────────────────────────────
        if not await _has_rows(Vendor):
            items = _vendors(cid)
            for r in items:
                db.add(r)
            print(f"✓ Vendors: {len(items)} added")
        else:
            print("  · Vendors: already seeded")

        # ── Assets ───────────────────────────────────────────────────────────
        if not await _has_rows(Asset):
            items = _assets(cid)
            for r in items:
                db.add(r)
            print(f"✓ Assets: {len(items)} added")
        else:
            print("  · Assets: already seeded")

        # ── Training ─────────────────────────────────────────────────────────
        if not await _has_rows(TrainingRecord):
            items = _training(cid)
            for r in items:
                db.add(r)
            print(f"✓ Training: {len(items)} records added")
        else:
            print("  · Training: already seeded")

        # ── Pen Tests ────────────────────────────────────────────────────────
        if not await _has_rows(PenTest):
            items = _pen_tests(cid)
            for r in items:
                db.add(r)
            print(f"✓ Pen Tests: {len(items)} added")
        else:
            print("  · Pen Tests: already seeded")

        # ── Access Reviews ───────────────────────────────────────────────────
        if not await _has_rows(AccessReview):
            items = _access_reviews(cid)
            for r in items:
                db.add(r)
            print(f"✓ Access Reviews: {len(items)} added")
        else:
            print("  · Access Reviews: already seeded")

        # ── Background Checks ────────────────────────────────────────────────
        if not await _has_rows(BackgroundCheck):
            items = _background_checks(cid)
            for r in items:
                db.add(r)
            print(f"✓ Background Checks: {len(items)} added")
        else:
            print("  · Background Checks: already seeded")

        # ── Offboarding ──────────────────────────────────────────────────────
        if not await _has_rows(Offboarding):
            items = _offboarding(cid)
            for r in items:
                db.add(r)
            print(f"✓ Offboarding: {len(items)} added")
        else:
            print("  · Offboarding: already seeded")

        # ── BCP / DR ─────────────────────────────────────────────────────────
        if not await _has_rows(BcpRecord):
            items = _bcp(cid)
            for r in items:
                db.add(r)
            print(f"✓ BCP Records: {len(items)} added")
        else:
            print("  · BCP Records: already seeded")

        # ── SOA ──────────────────────────────────────────────────────────────
        if not await _has_rows(SoaItem):
            items = _soa_items(cid)
            for r in items:
                db.add(r)
            print(f"✓ SOA Items: {len(items)} added (ISO 27001:2022 Annex A)")
        else:
            print("  · SOA Items: already seeded")

        # ── RoPA ─────────────────────────────────────────────────────────────
        if not await _has_rows(RopaRecord):
            items = _ropa(cid)
            for r in items:
                db.add(r)
            print(f"✓ RoPA Records: {len(items)} added")
        else:
            print("  · RoPA Records: already seeded")

        # ── Data Breaches ────────────────────────────────────────────────────
        if not await _has_rows(DataBreach):
            items = _data_breaches(cid)
            for r in items:
                db.add(r)
            print(f"✓ Data Breaches: {len(items)} added")
        else:
            print("  · Data Breaches: already seeded")

        # ── Subject Requests ─────────────────────────────────────────────────
        if not await _has_rows(SubjectRequest):
            items = _subject_requests(cid)
            for r in items:
                db.add(r)
            print(f"✓ Subject Requests: {len(items)} added")
        else:
            print("  · Subject Requests: already seeded")

        # ── Management Reviews ───────────────────────────────────────────────
        if not await _has_rows(ManagementReview):
            items = _management_reviews(cid)
            for r in items:
                db.add(r)
            print(f"✓ Management Reviews: {len(items)} added")
        else:
            print("  · Management Reviews: already seeded")

        await db.commit()

    print()
    print("━" * 50)
    print("  Demo account fully seeded!")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print(f"  Plan:     Growth (all features)")
    print(f"  Integrations: {len(ALL_INTEGRATIONS)} connected")
    print("━" * 50)


if __name__ == "__main__":
    asyncio.run(seed())
