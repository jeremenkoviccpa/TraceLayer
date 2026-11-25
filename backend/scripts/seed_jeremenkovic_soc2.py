"""
Demo seed for jeremenkovic23@gmail.com — SOC 2 fully green.

Covers ALL 12 SOC 2 Trust Service Criteria control categories with every
expected evidence type, fresh timestamps, and 10+ records per category so
the compliance score engine returns 100% (passing) on every control.

Usage (from backend/ directory):
    python scripts/seed_jeremenkovic_soc2.py

Safe to re-run — deletes and re-inserts all demo data for this account.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.fernet import Fernet
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.config import settings
from core.database import AsyncSessionLocal
from models import Evidence, Integration
from models.access_review import AccessReview
from models.manual_control import ManualControl
from models.pen_test import PenTest
from models.policy import Policy
from models.risk import Risk
from models.score_snapshot import ScoreSnapshot
from models.training import TrainingRecord
from models.user import User
from models.vendor import Vendor

TARGET_EMAIL = "jeremenkovic23@gmail.com"
NOW = datetime.now(timezone.utc)


def _enc(data: dict) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


def _ev(cid, integration, control, evidence_type, source_id, data, age_days=0):
    return {
        "id": uuid.uuid4(),
        "company_id": cid,
        "integration": integration,
        "control": control,
        "evidence_type": evidence_type,
        "source_id": str(source_id),
        "timestamp": NOW - timedelta(days=age_days),
        "data": data,
    }


# ── INTEGRATIONS ──────────────────────────────────────────────────────────────

INTEGRATIONS = [
    ("aws",              {"access_key_id": "AKIADEMO123", "secret_access_key": "DEMO_SECRET", "region": "us-east-1"}),
    ("github",           {"token": "ghp_DEMO_TOKEN", "org": "tracelayer-demo"}),
    ("okta",             {"domain": "tracelayer.okta.com", "api_token": "DEMO_OKTA_TOKEN"}),
    ("azure_ad",         {"tenant_id": "DEMO-TENANT-ID", "client_id": "DEMO-CLIENT-ID", "client_secret": "DEMO_SECRET"}),
    ("datadog",          {"api_key": "DEMO_DD_API_KEY", "app_key": "DEMO_DD_APP_KEY", "site": "datadoghq.com"}),
    ("jira",             {"domain": "tracelayer.atlassian.net", "email": "admin@tracelayer.io", "api_token": "DEMO_JIRA_TOKEN"}),
    ("slack",            {"bot_token": "xoxb-DEMO-SLACK-TOKEN"}),
    ("google_workspace", {"admin_email": "admin@tracelayer.io", "service_account_json": '{"type":"service_account","project_id":"tracelayer-demo"}'}),
    ("pagerduty",        {"api_key": "DEMO_PD_KEY"}),
    ("crowdstrike",      {"client_id": "DEMO_CS_CLIENT", "client_secret": "DEMO_CS_SECRET", "base_url": "https://api.crowdstrike.com"}),
    ("snyk",             {"api_token": "DEMO_SNYK_TOKEN", "org_id": "tracelayer-demo"}),
    ("jamf",             {"domain": "tracelayer.jamfcloud.com", "username": "api-user", "password": "DEMO_JAMF_PW"}),
    ("sentinelone",      {"api_token": "DEMO_S1_TOKEN", "site_id": "DEMO-SITE-123"}),
    ("wiz",              {"client_id": "DEMO_WIZ_CLIENT", "client_secret": "DEMO_WIZ_SECRET"}),
    ("hackerone",        {"api_token": "DEMO_H1_TOKEN", "program_handle": "tracelayer"}),
    ("kandji",           {"api_token": "DEMO_KANDJI_TOKEN", "subdomain": "tracelayer"}),
    ("vault",            {"address": "https://vault.tracelayer.io", "token": "DEMO_VAULT_TOKEN"}),
    ("gitlab",           {"token": "glpat-DEMO_GL_TOKEN", "domain": "gitlab.com"}),
    ("servicenow",       {"instance": "tracelayer.service-now.com", "username": "api-user", "password": "DEMO_SNOW_PW"}),
    ("opsgenie",         {"api_key": "DEMO_OG_KEY"}),
    ("splunk",           {"host": "splunk.tracelayer.io", "port": 8089, "token": "DEMO_SPLUNK_TOKEN"}),
]


# ── EVIDENCE BUILDER ──────────────────────────────────────────────────────────
# UniqueConstraint: (company_id, integration, evidence_type, source_id)
# Each SOC 2 control category needs: 100% type coverage + 10+ records + age 0-1d

def _build_evidence(cid: uuid.UUID) -> list[dict]:
    records: list[dict] = []

    employees = [
        "alice@tracelayer.io", "bob@tracelayer.io", "carol@tracelayer.io",
        "dave@tracelayer.io", "eve@tracelayer.io", "frank@tracelayer.io",
        "grace@tracelayer.io", "ivan@tracelayer.io", "julia@tracelayer.io",
        "henry@tracelayer.io",
    ]

    # ── control_environment ─────────────────────────────────────────────────
    # expected: iam_policies, okta_policies, github_repositories, azure_roles
    for n, name, admin in [
        (1, "AdministratorAccess", True), (2, "ReadOnlyAccess", False),
        (3, "SecurityAudit", False), (4, "IAMFullAccess", True),
    ]:
        records.append(_ev(cid, "aws", "control_environment", "iam_policies", f"ce_iam_{n}", {
            "policy_name": name, "admin_policy": admin, "scope": "control_environment",
            "attached_entities": n * 2,
        }))
    for n, name in [(1, "MFA-Enforcement"), (2, "Password-Policy"), (3, "Session-Policy")]:
        records.append(_ev(cid, "okta", "control_environment", "okta_policies", f"ce_okta_{n}", {
            "name": name, "status": "ACTIVE", "type": "PASSWORD", "priority": n,
        }))
    for n, name in [(1, "backend"), (2, "infrastructure"), (3, "security-tooling")]:
        records.append(_ev(cid, "github", "control_environment", "github_repositories", f"ce_repo_{n}", {
            "name": name, "full_name": f"tracelayer-demo/{name}", "private": True,
            "branch_protection": True, "default_branch": "main",
        }))
    for n, name in [(1, "GlobalAdmin"), (2, "SecurityReader"), (3, "ComplianceManager")]:
        records.append(_ev(cid, "azure_ad", "control_environment", "azure_roles", f"ce_azr_{n}", {
            "displayName": name, "isBuiltIn": n == 1, "isEnabled": True, "memberCount": n * 3,
        }))

    # ── risk_assessment ─────────────────────────────────────────────────────
    # expected: vulnerability_scans, wiz_issues, snyk_projects, iam_policies
    for n in range(1, 4):
        records.append(_ev(cid, "aws", "risk_assessment", "iam_policies", f"ra_iam_{n}", {
            "policy_name": f"RiskPolicy-{n}", "risk_reviewed": True, "last_reviewed": NOW.isoformat(),
        }))
    for n, sev, title in [
        (1, "LOW", "S3 bucket public read"), (2, "MEDIUM", "IAM key rotation overdue"),
        (3, "LOW", "Security group allows all egress"), (4, "MEDIUM", "CloudTrail missing in region"),
    ]:
        records.append(_ev(cid, "aws", "risk_assessment", "vulnerability_scans", f"ra_scan_{n}", {
            "finding_id": f"SCAN-{n:04d}", "severity": sev, "title": title,
            "status": "resolved", "resolved_at": NOW.isoformat(),
        }))
    for n, pkg, sev in [
        (1, "lodash", "HIGH"), (2, "express", "MEDIUM"), (3, "axios", "LOW"), (4, "react", "LOW"),
    ]:
        records.append(_ev(cid, "snyk", "risk_assessment", "snyk_projects", f"ra_snyk_{n}", {
            "project_name": f"tracelayer-demo/{pkg}", "severity": sev,
            "issue_count": n, "last_tested": NOW.isoformat(),
        }))
    for n, title, sev in [
        (1, "Overly permissive IAM role", "HIGH"),
        (2, "Unencrypted S3 bucket", "MEDIUM"),
        (3, "Missing MFA on privileged account", "CRITICAL"),
    ]:
        records.append(_ev(cid, "wiz", "risk_assessment", "wiz_issues", f"ra_wiz_{n}", {
            "issue_id": f"WIZ-RA-{n:04d}", "title": title, "severity": sev,
            "status": "RESOLVED", "resolved_at": NOW.isoformat(),
        }))

    # ── access_control ──────────────────────────────────────────────────────
    # expected: iam_users, iam_policies, github_members, github_admin_members,
    #           slack_users, workspace_users, workspace_admin_members,
    #           okta_users, okta_groups, okta_policies, azure_users, azure_roles, jira_users
    for i, email in enumerate(employees):
        uid = f"AIDA{'0'*(12-len(str(i+1)))}{i+1}"
        records.append(_ev(cid, "aws", "access_control", "iam_users", uid, {
            "username": email, "arn": f"arn:aws:iam::123456789012:user/{email}",
            "admin": i < 2, "mfa_active": True,
            "last_activity": NOW.isoformat(),
        }))
    for n, name, admin in [
        (1, "AdministratorAccess", True), (2, "DeveloperAccess", False),
        (3, "ReadOnlyAccess", False), (4, "SecurityAudit", False),
    ]:
        records.append(_ev(cid, "aws", "access_control", "iam_policies", f"ac_iam_{n}", {
            "policy_name": name, "admin_policy": admin, "attached_users": n,
        }))
    for login in ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "ivan"]:
        records.append(_ev(cid, "github", "access_control", "github_members", login, {
            "login": login, "id": abs(hash(login)) % 99999,
            "type": "User", "site_admin": False,
        }))
    for n, login in enumerate(["carol", "ivan"]):
        records.append(_ev(cid, "github", "access_control", "github_admin_members", f"admin_{login}", {
            "login": login, "id": abs(hash(login)) % 99999, "role": "admin",
        }))
    for uid, email, admin in [
        ("U001", "alice@tracelayer.io", True), ("U002", "bob@tracelayer.io", False),
        ("U003", "carol@tracelayer.io", True), ("U004", "dave@tracelayer.io", False),
        ("U005", "eve@tracelayer.io", False), ("U006", "frank@tracelayer.io", False),
        ("U007", "grace@tracelayer.io", False), ("U008", "ivan@tracelayer.io", True),
    ]:
        records.append(_ev(cid, "slack", "access_control", "slack_users", uid, {
            "id": uid, "email": email, "is_admin": admin, "is_bot": False,
            "two_factor_enabled": True,
        }))
    for uid, email, role in [
        ("ws_001", "alice@tracelayer.io", "ADMIN"), ("ws_002", "bob@tracelayer.io", "MEMBER"),
        ("ws_003", "carol@tracelayer.io", "ADMIN"), ("ws_004", "dave@tracelayer.io", "MEMBER"),
        ("ws_005", "eve@tracelayer.io", "MEMBER"), ("ws_006", "frank@tracelayer.io", "MEMBER"),
        ("ws_007", "grace@tracelayer.io", "MEMBER"), ("ws_008", "ivan@tracelayer.io", "ADMIN"),
    ]:
        records.append(_ev(cid, "google_workspace", "access_control", "workspace_users", uid, {
            "primaryEmail": email, "isAdmin": role == "ADMIN", "suspended": False,
            "lastLoginTime": NOW.isoformat(),
        }))
    for n, email in enumerate(["alice@tracelayer.io", "carol@tracelayer.io"]):
        records.append(_ev(cid, "google_workspace", "access_control", "workspace_admin_members", f"ws_adm_{n+1}", {
            "primaryEmail": email, "isAdmin": True, "isSuperAdmin": n == 0,
        }))
    for uid, email, status, mfa in [
        ("ok1", "alice@tracelayer.io", "ACTIVE", True), ("ok2", "bob@tracelayer.io", "ACTIVE", True),
        ("ok3", "carol@tracelayer.io", "ACTIVE", True), ("ok4", "dave@tracelayer.io", "ACTIVE", True),
        ("ok5", "eve@tracelayer.io", "ACTIVE", True), ("ok6", "frank@tracelayer.io", "ACTIVE", True),
        ("ok7", "grace@tracelayer.io", "ACTIVE", True), ("ok8", "ivan@tracelayer.io", "ACTIVE", True),
        ("ok9", "julia@tracelayer.io", "ACTIVE", True), ("ok10", "henry@tracelayer.io", "SUSPENDED", False),
    ]:
        records.append(_ev(cid, "okta", "access_control", "okta_users", uid, {
            "login": email, "status": status, "mfa_enrolled": mfa,
            "last_login": NOW.isoformat(),
        }))
    for n, name, members in [
        (1, "engineering", 8), (2, "security", 3), (3, "admins", 2), (4, "read-only", 5),
    ]:
        records.append(_ev(cid, "okta", "access_control", "okta_groups", f"ac_ogrp_{n}", {
            "id": f"grp_{n:04d}", "name": name, "member_count": members,
        }))
    for n, name in [(1, "MFA-Enforcement"), (2, "Password-Policy"), (3, "SSO-Policy")]:
        records.append(_ev(cid, "okta", "access_control", "okta_policies", f"ac_opol_{n}", {
            "name": name, "status": "ACTIVE", "type": "PASSWORD",
        }))
    for n, name, member_count in [(1, "GlobalAdmin", 2), (2, "Contributor", 8), (3, "Reader", 12)]:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_roles", f"ac_azr_{n}", {
            "displayName": name, "isBuiltIn": True, "isEnabled": True, "memberCount": member_count,
        }))
    for uid, email, dept in [
        ("az1", "alice@tracelayer.io", "Engineering"), ("az2", "bob@tracelayer.io", "Engineering"),
        ("az3", "carol@tracelayer.io", "Security"), ("az4", "dave@tracelayer.io", "Product"),
        ("az5", "eve@tracelayer.io", "Engineering"), ("az6", "frank@tracelayer.io", "Operations"),
        ("az7", "grace@tracelayer.io", "Engineering"), ("az8", "ivan@tracelayer.io", "Security"),
    ]:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_users", uid, {
            "displayName": email.split("@")[0].title(), "userPrincipalName": email,
            "accountEnabled": True, "department": dept,
        }))
    for n, email in enumerate(employees[:8]):
        records.append(_ev(cid, "jira", "access_control", "jira_users", f"jira_u_{n+1}", {
            "accountId": f"jira_{n+1:04d}", "emailAddress": email,
            "displayName": email.split("@")[0].title(), "active": True,
        }))

    # ── privileged_access ───────────────────────────────────────────────────
    # expected: iam_policies, okta_groups, azure_roles, github_admin_members,
    #           vault_policy, vault_auth_method
    for n, name in [(1, "AdministratorAccess"), (2, "IAMFullAccess")]:
        records.append(_ev(cid, "aws", "privileged_access", "iam_policies", f"pa_iam_{n}", {
            "policy_name": name, "admin_policy": True, "attached_entities": 2,
            "privileged": True,
        }))
    for n, name in [(1, "admins"), (2, "security-ops")]:
        records.append(_ev(cid, "okta", "privileged_access", "okta_groups", f"pa_ogrp_{n}", {
            "id": f"pa_grp_{n:04d}", "name": name, "privileged": True, "member_count": n,
        }))
    for n, name in [(1, "GlobalAdmin"), (2, "PrivilegedRoleAdmin")]:
        records.append(_ev(cid, "azure_ad", "privileged_access", "azure_roles", f"pa_azr_{n}", {
            "displayName": name, "isBuiltIn": True, "isEnabled": True, "memberCount": n,
        }))
    for n, login in enumerate(["carol", "ivan"]):
        records.append(_ev(cid, "github", "privileged_access", "github_admin_members", f"pa_admin_{n+1}", {
            "login": login, "role": "admin", "site_admin": False,
        }))
    for n, name, paths in [(1, "engineering", "/secret/prod/*"), (2, "security", "/secret/*")]:
        records.append(_ev(cid, "vault", "privileged_access", "vault_policy", f"pa_vpol_{n}", {
            "name": name, "policies": [paths], "capabilities": ["read", "list"],
        }))
    for n, method in [(1, "github"), (2, "kubernetes")]:
        records.append(_ev(cid, "vault", "privileged_access", "vault_auth_method", f"pa_vauth_{n}", {
            "type": method, "path": f"{method}/", "enabled": True,
        }))

    # ── logging_monitoring ──────────────────────────────────────────────────
    # expected: cloudtrail_logs, datadog_monitors, datadog_logs,
    #           splunk_saved_searches, splunk_alerts,
    #           crowdstrike_detections, sentinelone_threats, wiz_issues
    for event, source, actor in [
        ("ConsoleLogin", "signin.amazonaws.com", "alice@tracelayer.io"),
        ("CreateTrail", "cloudtrail.amazonaws.com", "carol@tracelayer.io"),
        ("PutBucketPolicy", "s3.amazonaws.com", "deploy-bot"),
        ("CreateAccessKey", "iam.amazonaws.com", "carol@tracelayer.io"),
        ("AuthorizeSecurityGroupIngress", "ec2.amazonaws.com", "ivan@tracelayer.io"),
        ("AttachUserPolicy", "iam.amazonaws.com", "ivan@tracelayer.io"),
        ("GetSecretValue", "secretsmanager.amazonaws.com", "ci-runner"),
        ("PutBucketPublicAccessBlock", "s3.amazonaws.com", "grace@tracelayer.io"),
        ("DescribeInstances", "ec2.amazonaws.com", "bob@tracelayer.io"),
        ("UpdateTrail", "cloudtrail.amazonaws.com", "carol@tracelayer.io"),
    ]:
        records.append(_ev(cid, "aws", "logging_monitoring", "cloudtrail_logs", f"lm_ct_{event}_{actor[:4]}", {
            "event_name": event, "event_source": source, "user": actor,
            "region": "us-east-1", "event_time": NOW.isoformat(),
        }))
    for n, name, kind in [
        (1, "High CPU Utilization", "metric"), (2, "Error Rate Spike", "metric"),
        (3, "Availability Monitor", "service check"), (4, "Latency P99", "metric"),
        (5, "Memory Usage Critical", "metric"),
    ]:
        records.append(_ev(cid, "datadog", "logging_monitoring", "datadog_monitors", f"lm_ddmon_{n}", {
            "id": n * 1000, "name": name, "type": kind,
            "status": "OK", "created": NOW.isoformat(),
        }))
    for n, service, level in [
        (1, "api-server", "INFO"), (2, "auth-service", "WARN"),
        (3, "data-pipeline", "INFO"), (4, "worker", "INFO"),
        (5, "gateway", "INFO"),
    ]:
        records.append(_ev(cid, "datadog", "logging_monitoring", "datadog_logs", f"lm_ddlog_{n}", {
            "service": service, "status": level, "count_24h": n * 1200,
            "indexed": True,
        }))
    for n, name, schedule in [
        (1, "Security Event Summary", "cron(0 */6 * * *)"),
        (2, "Auth Failures", "cron(*/15 * * * *)"),
        (3, "Privileged Access Audit", "cron(0 0 * * *)"),
        (4, "Data Exfil Detection", "cron(*/5 * * * *)"),
    ]:
        records.append(_ev(cid, "splunk", "logging_monitoring", "splunk_saved_searches", f"lm_spsearch_{n}", {
            "name": name, "search": f"index=main | stats count", "cron_schedule": schedule,
            "is_scheduled": True,
        }))
    for n, name, severity in [
        (1, "Multiple Failed Logins", "high"),
        (2, "Data Exfiltration Risk", "critical"),
        (3, "Privilege Escalation Attempt", "critical"),
    ]:
        records.append(_ev(cid, "splunk", "logging_monitoring", "splunk_alerts", f"lm_spalert_{n}", {
            "name": name, "severity": severity, "enabled": True,
            "trigger_count_24h": n,
        }))
    for n, host, sev in [
        (1, "web-server-01", "medium"), (2, "worker-02", "low"),
        (3, "db-replica-01", "low"), (4, "api-server-03", "low"),
    ]:
        records.append(_ev(cid, "crowdstrike", "logging_monitoring", "crowdstrike_detections", f"lm_csdet_{n}", {
            "detection_id": f"ldt:{n:04d}", "hostname": host, "severity": sev,
            "status": "closed", "resolved": True, "timestamp": NOW.isoformat(),
        }))
    for n, host, threat in [
        (1, "endpoint-mac-001", "PUP.Optional"), (2, "endpoint-mac-002", "Adware.Gen"),
    ]:
        records.append(_ev(cid, "sentinelone", "logging_monitoring", "sentinelone_threats", f"lm_s1thr_{n}", {
            "threat_id": f"s1thr_{n}", "agent_computer_name": host,
            "classification": threat, "mitigated": True, "resolved_at": NOW.isoformat(),
        }))
    for n, title, sev in [
        (1, "Publicly exposed S3 bucket (remediated)", "HIGH"),
        (2, "Unpatched library in container image", "MEDIUM"),
    ]:
        records.append(_ev(cid, "wiz", "logging_monitoring", "wiz_issues", f"lm_wiz_{n}", {
            "issue_id": f"WIZ-LM-{n:04d}", "title": title, "severity": sev,
            "status": "RESOLVED", "resolved_at": NOW.isoformat(),
        }))

    # ── incident_response ───────────────────────────────────────────────────
    # expected: pagerduty_incidents, pagerduty_services, pagerduty_escalation_policies,
    #           servicenow_incidents, opsgenie_alerts, opsgenie_schedules, opsgenie_escalations
    for n, title, urgency in [
        (1, "API latency spike — degraded performance", "low"),
        (2, "Database failover triggered", "high"),
        (3, "Certificate expiry warning", "low"),
        (4, "Deployment failure — auto-rollback completed", "high"),
        (5, "Scheduled maintenance — no impact", "low"),
    ]:
        records.append(_ev(cid, "pagerduty", "incident_response", "pagerduty_incidents", f"ir_pdinc_{n}", {
            "id": f"P{n:06d}", "title": title, "urgency": urgency,
            "status": "resolved", "resolved_at": NOW.isoformat(),
        }))
    for n, name, kind in [
        (1, "API Gateway", "web"), (2, "Auth Service", "web"), (3, "Background Workers", "worker"),
    ]:
        records.append(_ev(cid, "pagerduty", "incident_response", "pagerduty_services", f"ir_pdsvc_{n}", {
            "id": f"SVC{n:04d}", "name": name, "type": kind,
            "status": "active", "integrations": ["cloudwatch", "datadog"],
        }))
    for n, name in [(1, "Engineering On-Call"), (2, "Security Incident Response")]:
        records.append(_ev(cid, "pagerduty", "incident_response", "pagerduty_escalation_policies", f"ir_pdesc_{n}", {
            "id": f"ESC{n:04d}", "name": name, "num_loops": 3,
            "escalation_rules": [{"targets": [{"type": "schedule"}], "escalation_delay_in_minutes": 30}],
        }))
    for n, short, category in [
        (1, "INC0001234", "inquiry"), (2, "INC0001235", "security"),
        (3, "INC0001236", "network"), (4, "INC0001237", "application"),
    ]:
        records.append(_ev(cid, "servicenow", "incident_response", "servicenow_incidents", f"ir_sninc_{n}", {
            "number": short, "category": category, "state": "closed",
            "resolved_at": NOW.isoformat(), "priority": "3 - Moderate",
        }))
    for n, message, priority in [
        (1, "High CPU on api-server-01", "P3"),
        (2, "Memory threshold exceeded on worker-02", "P4"),
        (3, "SSL cert expiry in 14 days", "P4"),
        (4, "Disk usage above 85% on db-01", "P3"),
    ]:
        records.append(_ev(cid, "opsgenie", "incident_response", "opsgenie_alerts", f"ir_ogalert_{n}", {
            "id": f"og_alert_{n}", "message": message, "priority": priority,
            "status": "closed", "responders": ["alice@tracelayer.io"],
        }))
    for n, name in [(1, "Engineering Rotation"), (2, "Security On-Call")]:
        records.append(_ev(cid, "opsgenie", "incident_response", "opsgenie_schedules", f"ir_ogsched_{n}", {
            "id": f"og_sched_{n}", "name": name, "enabled": True,
            "timezone": "UTC", "rotation_period": "weekly",
        }))
    for n, name in [(1, "Default Escalation"), (2, "Security Escalation")]:
        records.append(_ev(cid, "opsgenie", "incident_response", "opsgenie_escalations", f"ir_ogesc_{n}", {
            "id": f"og_esc_{n}", "name": name, "rules": [
                {"condition": "if-not-acked", "notify_type": "default", "delay": 10}
            ],
        }))

    # ── change_management ───────────────────────────────────────────────────
    # expected: github_repositories, jira_projects, servicenow_changes, gitlab_repositories
    for n, name, private in [
        (1, "backend", True), (2, "frontend", True),
        (3, "infrastructure", True), (4, "data-platform", True),
    ]:
        records.append(_ev(cid, "github", "change_management", "github_repositories", f"cm_ghrepo_{n}", {
            "name": name, "full_name": f"tracelayer-demo/{name}", "private": private,
            "default_branch": "main", "branch_protection_enabled": True,
            "updated_at": NOW.isoformat(),
        }))
    for n, key, name in [
        (1, "BACK", "Backend"), (2, "FRONT", "Frontend"),
        (3, "OPS", "Infrastructure"), (4, "SEC", "Security"), (5, "DATA", "Data"),
    ]:
        records.append(_ev(cid, "jira", "change_management", "jira_projects", f"cm_jira_{n}", {
            "key": key, "name": name, "lead_email": "carol@tracelayer.io",
            "issue_count": n * 22 + 15,
        }))
    for n, number, category in [
        (1, "CHG0000456", "normal"), (2, "CHG0000457", "standard"),
        (3, "CHG0000458", "emergency"), (4, "CHG0000459", "normal"),
    ]:
        records.append(_ev(cid, "servicenow", "change_management", "servicenow_changes", f"cm_snchg_{n}", {
            "number": number, "category": category, "state": "closed",
            "cab_approval": n != 3, "implemented_at": NOW.isoformat(),
        }))
    for n, name, private in [
        (1, "mobile-app", True), (2, "devops-scripts", True),
    ]:
        records.append(_ev(cid, "gitlab", "change_management", "gitlab_repositories", f"cm_glrepo_{n}", {
            "name": name, "path_with_namespace": f"tracelayer-demo/{name}",
            "visibility": "private" if private else "internal",
            "default_branch": "main", "last_activity_at": NOW.isoformat(),
        }))

    # ── endpoint_security ───────────────────────────────────────────────────
    # expected: crowdstrike_devices, crowdstrike_policies, sentinelone_agents,
    #           jamf_computers, jamf_policies, kandji_devices, kandji_blueprints
    # (kolide skipped — 7/8 types = 87.5% * 70 + 30 = 91 → PASSING)
    for n, host, status in [
        (1, "macbook-alice", "normal"), (2, "macbook-bob", "normal"),
        (3, "macbook-carol", "normal"), (4, "macbook-dave", "normal"),
        (5, "macbook-eve", "normal"), (6, "linux-server-01", "normal"),
        (7, "linux-server-02", "normal"), (8, "linux-worker-01", "normal"),
    ]:
        records.append(_ev(cid, "crowdstrike", "endpoint_security", "crowdstrike_devices", f"ep_csdev_{n}", {
            "device_id": f"cs_{n:04d}", "hostname": host, "status": status,
            "os_version": "macOS 14.4" if "mac" in host else "Ubuntu 22.04",
            "last_seen": NOW.isoformat(), "prevention_policy_applied": True,
        }))
    for n, name in [(1, "Prevention Policy - Mac"), (2, "Prevention Policy - Linux"), (3, "Detection Policy")]:
        records.append(_ev(cid, "crowdstrike", "endpoint_security", "crowdstrike_policies", f"ep_cspol_{n}", {
            "id": f"csp_{n:04d}", "name": name, "enabled": True,
            "platform": "Mac" if "Mac" in name else "Linux",
        }))
    for n, host in enumerate(["macbook-alice", "macbook-bob", "macbook-carol",
                               "macbook-dave", "macbook-eve", "macbook-frank",
                               "macbook-grace", "macbook-ivan"], 1):
        records.append(_ev(cid, "sentinelone", "endpoint_security", "sentinelone_agents", f"ep_s1agent_{n}", {
            "agent_id": f"s1_{n:04d}", "computer_name": host,
            "os_type": "macos", "agent_version": "23.4.2",
            "is_active": True, "last_active": NOW.isoformat(),
        }))
    for n, serial, model in [
        (1, "C02XDEMO0001", "MacBook Pro 16\""), (2, "C02XDEMO0002", "MacBook Pro 14\""),
        (3, "C02XDEMO0003", "MacBook Air M2"), (4, "C02XDEMO0004", "MacBook Pro 16\""),
        (5, "C02XDEMO0005", "MacBook Pro 14\""), (6, "C02XDEMO0006", "MacBook Air M2"),
        (7, "C02XDEMO0007", "MacBook Pro 16\""), (8, "C02XDEMO0008", "MacBook Pro 14\""),
    ]:
        records.append(_ev(cid, "jamf", "endpoint_security", "jamf_computers", serial, {
            "serialNumber": serial, "model": model, "managed": True,
            "udid": f"UDID-{n:04d}", "username": employees[n - 1] if n <= len(employees) else "",
            "lastContactTime": NOW.isoformat(),
        }))
    for n, name in [(1, "Security Baseline"), (2, "Encryption Policy"), (3, "Screen Lock Policy")]:
        records.append(_ev(cid, "jamf", "endpoint_security", "jamf_policies", f"ep_jamfpol_{n}", {
            "id": n * 100, "name": name, "enabled": True,
            "frequency": "Once every day", "scope_all_computers": True,
        }))
    for n, serial, user in [
        (1, "KANDJI-001", "alice@tracelayer.io"), (2, "KANDJI-002", "bob@tracelayer.io"),
        (3, "KANDJI-003", "carol@tracelayer.io"), (4, "KANDJI-004", "dave@tracelayer.io"),
        (5, "KANDJI-005", "eve@tracelayer.io"), (6, "KANDJI-006", "frank@tracelayer.io"),
        (7, "KANDJI-007", "grace@tracelayer.io"), (8, "KANDJI-008", "ivan@tracelayer.io"),
    ]:
        records.append(_ev(cid, "kandji", "endpoint_security", "kandji_devices", serial, {
            "device_id": serial, "serial_number": serial, "model": "MacBook Pro",
            "user": user, "blueprints": ["Security Baseline"],
            "is_missing": False, "last_check_in": NOW.isoformat(),
        }))
    for n, name in [(1, "Security Baseline"), (2, "Engineering Devices")]:
        records.append(_ev(cid, "kandji", "endpoint_security", "kandji_blueprints", f"ep_kbp_{n}", {
            "id": f"kbp_{n:04d}", "name": name, "device_count": n * 5,
            "is_default": n == 1,
        }))

    # ── vulnerability_management ────────────────────────────────────────────
    # expected: snyk_projects, vulnerability_scans, wiz_issues,
    #           crowdstrike_detections, hackerone_reports, detectify_findings
    # (detectify skipped — 5/6 = 83% * 70 + 30 = 88 → PASSING)
    for n, pkg, sev in [
        (1, "backend/api", "LOW"), (2, "backend/worker", "MEDIUM"),
        (3, "frontend/next", "LOW"), (4, "infra/terraform", "LOW"),
    ]:
        records.append(_ev(cid, "snyk", "vulnerability_management", "snyk_projects", f"vm_snyk_{n}", {
            "id": f"snyk_{n:04d}", "name": f"tracelayer-demo/{pkg}",
            "high_severity_count": 0, "medium_severity_count": 1 if sev == "MEDIUM" else 0,
            "last_tested_date": NOW.isoformat(), "status": "active",
        }))
    for n, title, sev in [
        (1, "OpenSSL CVE-2023-xxxx", "MEDIUM"), (2, "Log4j follow-up scan", "LOW"),
        (3, "Container image scan — base layer", "LOW"), (4, "Infrastructure scan — EC2", "LOW"),
    ]:
        records.append(_ev(cid, "aws", "vulnerability_management", "vulnerability_scans", f"vm_scan_{n}", {
            "finding_id": f"VSCAN-{n:04d}", "title": title, "severity": sev,
            "status": "resolved", "resolved_at": NOW.isoformat(),
        }))
    for n, title, sev in [
        (1, "Container with root privileges", "HIGH"),
        (2, "Exposed internal service", "CRITICAL"),
        (3, "Missing network segmentation", "MEDIUM"),
    ]:
        records.append(_ev(cid, "wiz", "vulnerability_management", "wiz_issues", f"vm_wiz_{n}", {
            "issue_id": f"WIZ-VM-{n:04d}", "title": title, "severity": sev,
            "status": "RESOLVED", "resolved_at": NOW.isoformat(),
        }))
    for n, host, sev in [(1, "api-server-02", "medium"), (2, "worker-03", "low")]:
        records.append(_ev(cid, "crowdstrike", "vulnerability_management", "crowdstrike_detections", f"vm_csdet_{n}", {
            "detection_id": f"vm_ldt:{n:04d}", "hostname": host, "severity": sev,
            "status": "closed", "resolved": True,
        }))
    for n, title, sev, state in [
        (1, "XSS in admin panel (fixed)", "medium", "resolved"),
        (2, "Rate limiting bypass (fixed)", "high", "resolved"),
        (3, "SQL injection edge case (fixed)", "critical", "resolved"),
    ]:
        records.append(_ev(cid, "hackerone", "vulnerability_management", "hackerone_reports", f"vm_h1_{n}", {
            "id": n * 100000, "title": title, "severity": sev, "state": state,
            "bounty_awarded_amount": n * 500, "disclosed_at": None,
        }))

    # ── vendor_risk ─────────────────────────────────────────────────────────
    # expected: github_repositories, snyk_projects, wiz_issues, cloudtrail_logs
    for n, name in [(1, "backend-vendor-sdk"), (2, "third-party-api-client"),
                    (3, "compliance-data-pipeline"), (4, "analytics-module")]:
        records.append(_ev(cid, "github", "vendor_risk", "github_repositories", f"vr_ghrepo_{n}", {
            "name": name, "full_name": f"tracelayer-demo/{name}", "private": True,
            "vendor_owned": True, "last_audit": NOW.isoformat(),
        }))
    for n, pkg in [(1, "vendor-sdk/payments"), (2, "vendor-sdk/auth"), (3, "vendor-sdk/data")]:
        records.append(_ev(cid, "snyk", "vendor_risk", "snyk_projects", f"vr_snyk_{n}", {
            "id": f"vr_snyk_{n:04d}", "name": pkg, "last_tested_date": NOW.isoformat(),
            "high_severity_count": 0, "vendor_dependency": True,
        }))
    for n, title in [(1, "Third-party API with excessive permissions"),
                     (2, "Vendor container with outdated base image")]:
        records.append(_ev(cid, "wiz", "vendor_risk", "wiz_issues", f"vr_wiz_{n}", {
            "issue_id": f"WIZ-VR-{n:04d}", "title": title, "severity": "MEDIUM",
            "status": "RESOLVED", "vendor_related": True,
        }))
    for n, event in [(1, "GetSecretValue_vendor"), (2, "AssumeRole_vendor"),
                     (3, "ListBuckets_vendor"), (4, "PutObject_vendor")]:
        records.append(_ev(cid, "aws", "vendor_risk", "cloudtrail_logs", f"vr_ct_{n}", {
            "event_name": event.split("_")[0], "user_agent": "vendor-sdk/1.0",
            "source_ip": "10.0.1.100", "event_time": NOW.isoformat(),
        }))

    # ── availability ────────────────────────────────────────────────────────
    # expected: pagerduty_services, datadog_slos, datadog_monitors,
    #           servicenow_changes, vault_secrets_engine
    for n, name, kind in [
        (1, "API Gateway", "web"), (2, "Auth Service", "web"), (3, "Background Workers", "worker"),
    ]:
        records.append(_ev(cid, "pagerduty", "availability", "pagerduty_services", f"av_pdsvc_{n}", {
            "id": f"AV_SVC{n:04d}", "name": name, "type": kind,
            "status": "active", "uptime_last_30d": 99.95,
        }))
    for n, name, slo in [(1, "API Availability SLO", 99.9), (2, "Auth SLO", 99.95), (3, "Data Pipeline SLO", 99.5)]:
        records.append(_ev(cid, "datadog", "availability", "datadog_slos", f"av_ddslo_{n}", {
            "id": f"slo_{n:04d}", "name": name, "target": slo,
            "current": slo + 0.04, "status": "ok",
        }))
    for n, name in [(1, "API P99 Latency"), (2, "Error Rate"), (3, "Service Availability")]:
        records.append(_ev(cid, "datadog", "availability", "datadog_monitors", f"av_ddmon_{n}", {
            "id": n * 2000, "name": name, "type": "metric alert",
            "status": "OK",
        }))
    for n, number in [(1, "CHG0000460"), (2, "CHG0000461"), (3, "CHG0000462")]:
        records.append(_ev(cid, "servicenow", "availability", "servicenow_changes", f"av_snchg_{n}", {
            "number": number, "category": "normal", "state": "closed",
            "availability_impact": "none", "implemented_at": NOW.isoformat(),
        }))
    for n, name in [(1, "database"), (2, "application"), (3, "certificates")]:
        records.append(_ev(cid, "vault", "availability", "vault_secrets_engine", f"av_vse_{n}", {
            "type": "kv-v2", "path": f"{name}/", "options": {"version": "2"},
            "seal_status": "unsealed", "ha_enabled": True,
        }))

    # ── confidentiality ─────────────────────────────────────────────────────
    # expected: iam_policies, vault_secrets_engine, vault_policy,
    #           cloudtrail_logs, wiz_issues
    for n, name in [(1, "KMSFullAccess"), (2, "S3EncryptionEnforcement")]:
        records.append(_ev(cid, "aws", "confidentiality", "iam_policies", f"conf_iam_{n}", {
            "policy_name": name, "encryption_related": True, "admin_policy": False,
        }))
    for n, path in [(1, "pki/"), (2, "transit/")]:
        records.append(_ev(cid, "vault", "confidentiality", "vault_secrets_engine", f"conf_vse_{n}", {
            "type": "transit" if n == 2 else "pki", "path": path,
            "encryption_enabled": True, "auto_rotate": True,
        }))
    for n, name in [(1, "encryption-policy"), (2, "tls-management")]:
        records.append(_ev(cid, "vault", "confidentiality", "vault_policy", f"conf_vpol_{n}", {
            "name": name, "policies": [f"/{name}/*"],
            "capabilities": ["read", "update", "create"],
        }))
    for n, event in [(1, "PutBucketEncryption"), (2, "CreateKey"),
                     (3, "EnableEncryption"), (4, "UpdateEncryption")]:
        records.append(_ev(cid, "aws", "confidentiality", "cloudtrail_logs", f"conf_ct_{n}", {
            "event_name": event, "encryption_event": True,
            "region": "us-east-1", "event_time": NOW.isoformat(),
        }))
    for n, title in [(1, "Unencrypted EBS volume (remediated)"),
                     (2, "RDS encryption not enabled (remediated)")]:
        records.append(_ev(cid, "wiz", "confidentiality", "wiz_issues", f"conf_wiz_{n}", {
            "issue_id": f"WIZ-CONF-{n:04d}", "title": title, "severity": "HIGH",
            "status": "RESOLVED", "resolved_at": NOW.isoformat(),
        }))

    return records


# ── SCORE SNAPSHOTS (90-day upward trend) ────────────────────────────────────

def _build_score_history(cid: uuid.UUID, framework: str = "soc2") -> list[dict]:
    snapshots = []
    progression = [
        (90, 41), (83, 48), (76, 54), (69, 59), (62, 64),
        (55, 68), (48, 73), (41, 79), (34, 83), (27, 87),
        (20, 91), (13, 95), (7, 97), (3, 99), (1, 100),
    ]
    for days_ago, score in progression:
        snapshots.append({
            "id": uuid.uuid4(),
            "company_id": cid,
            "framework": framework,
            "overall_score": score,
            "snapshot_at": NOW - timedelta(days=days_ago),
        })
    return snapshots


# ── SUPPORTING DATA ───────────────────────────────────────────────────────────

def _build_policies(cid: uuid.UUID) -> list[dict]:
    return [
        {"id": uuid.uuid4(), "company_id": cid, "slug": "information-security",
         "content": "TraceLayer maintains a comprehensive Information Security Policy approved by executive management. All personnel must comply with security standards. Policy reviewed annually."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "access-control",
         "content": "Access to systems is granted on a need-to-know, least-privilege basis. MFA is mandatory for all employees. Access reviews are conducted quarterly. Privileged access requires documented approval."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "incident-response",
         "content": "Security incidents must be reported immediately. The incident response team follows a defined playbook: detect, contain, eradicate, recover, post-mortem. PagerDuty is used for alerting and escalation."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "change-management",
         "content": "All changes to production environments require peer review via pull request and CAB approval for high-risk changes. Emergency changes must be retroactively approved within 24 hours."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "data-classification",
         "content": "Data is classified as Public, Internal, Confidential, or Restricted. Confidential and Restricted data must be encrypted at rest and in transit. Data retention schedules apply by classification."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "vendor-management",
         "content": "Third-party vendors are assessed for security risk annually. Critical vendors must provide SOC 2 Type II reports. Vendor access is reviewed quarterly and revoked immediately upon contract termination."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "vulnerability-management",
         "content": "Vulnerability scans are conducted weekly. Critical and high findings must be remediated within 7 and 30 days respectively. Penetration tests are conducted annually by an independent firm."},
        {"id": uuid.uuid4(), "company_id": cid, "slug": "business-continuity",
         "content": "Business continuity plans define RTO of 4 hours and RPO of 1 hour for critical systems. DR drills are conducted bi-annually. Backup integrity is verified monthly."},
    ]


def _build_risks(cid: uuid.UUID) -> list[dict]:
    items = [
        ("Third-party data breach via vendor API", "vendor", 2, 4, "mitigated"),
        ("Privileged credential compromise", "access", 2, 5, "mitigated"),
        ("Ransomware attack on endpoints", "endpoint", 2, 5, "mitigated"),
        ("Unpatched critical vulnerability in production", "vulnerability", 1, 5, "closed"),
        ("Misconfigured cloud storage bucket", "cloud", 1, 4, "closed"),
        ("Insider threat — excessive data access", "access", 2, 3, "mitigated"),
        ("DDoS attack on API gateway", "availability", 3, 3, "open"),
        ("Social engineering / phishing campaign", "hr", 3, 3, "open"),
        ("Regulatory non-compliance — data residency", "compliance", 1, 4, "closed"),
        ("Key person dependency — security team", "operational", 2, 3, "mitigated"),
    ]
    return [
        {
            "id": uuid.uuid4(), "company_id": cid, "title": title, "category": cat,
            "likelihood": lh, "impact": imp, "status": status,
            "description": f"Risk identified during quarterly review. Mitigation controls applied.",
        }
        for title, cat, lh, imp, status in items
    ]


def _build_vendors(cid: uuid.UUID) -> list[dict]:
    items = [
        ("Amazon Web Services", "cloud", "low", True, True, True),
        ("Datadog Inc.", "security", "low", True, True, False),
        ("Okta Inc.", "identity", "low", True, True, False),
        ("GitHub Inc. (Microsoft)", "cloud", "low", True, True, False),
        ("PagerDuty Inc.", "communication", "low", True, False, False),
        ("Snyk Ltd.", "security", "medium", True, True, False),
        ("CrowdStrike Holdings", "security", "low", True, True, False),
        ("HashiCorp (IBM)", "cloud", "low", True, True, False),
    ]
    return [
        {
            "id": uuid.uuid4(), "company_id": cid, "name": name,
            "category": cat, "risk_level": risk,
            "soc2_certified": soc2, "iso27001_certified": iso27001, "hipaa_certified": hipaa,
            "review_date": NOW - timedelta(days=45),
            "notes": "Annual vendor security review completed. SOC 2 Type II report reviewed.",
        }
        for name, cat, risk, soc2, iso27001, hipaa in items
    ]


def _build_training(cid: uuid.UUID) -> list[dict]:
    employees = [
        "alice@tracelayer.io", "bob@tracelayer.io", "carol@tracelayer.io",
        "dave@tracelayer.io", "eve@tracelayer.io", "frank@tracelayer.io",
        "grace@tracelayer.io", "ivan@tracelayer.io", "julia@tracelayer.io",
        "henry@tracelayer.io",
    ]
    courses = [
        ("Security Awareness Training", True),
        ("GDPR & Data Protection", True),
        ("Phishing Awareness", True),
    ]
    records = []
    for email in employees:
        for title, annual in courses:
            records.append({
                "id": uuid.uuid4(), "company_id": cid,
                "assignee_email": email, "title": title,
                "status": "completed", "annual": annual,
                "completed_at": NOW - timedelta(days=30),
                "due_date": NOW - timedelta(days=15),
            })
    return records


def _build_access_reviews(cid: uuid.UUID) -> list[dict]:
    return [
        {
            "id": uuid.uuid4(), "company_id": cid,
            "title": "Q4 2025 Access Review", "period": "Q4 2025",
            "status": "completed", "users_reviewed": 47, "access_changes": 6,
            "completed_at": NOW - timedelta(days=95),
            "findings": "6 stale accounts revoked. All privileged access confirmed appropriate.",
        },
        {
            "id": uuid.uuid4(), "company_id": cid,
            "title": "Q1 2026 Access Review", "period": "Q1 2026",
            "status": "completed", "users_reviewed": 52, "access_changes": 4,
            "completed_at": NOW - timedelta(days=10),
            "findings": "4 role changes implemented. No unauthorized access identified.",
        },
    ]


def _build_pen_tests(cid: uuid.UUID) -> list[dict]:
    return [
        {
            "id": uuid.uuid4(), "company_id": cid,
            "vendor_name": "Bishop Fox", "status": "remediated",
            "scope": "Full external attack surface — API, web application, cloud infrastructure",
            "conducted_at": NOW - timedelta(days=120),
            "critical_count": 0, "high_count": 2, "medium_count": 5, "low_count": 8,
            "summary": (
                "Bishop Fox conducted a comprehensive penetration test over a 10-day period. "
                "Two high-severity findings were identified: an IDOR vulnerability in the admin API "
                "and insufficient rate limiting on the authentication endpoint. Both findings have been "
                "fully remediated and verified. Five medium findings were addressed within SLA."
            ),
            "remediation_notes": "All critical and high findings remediated within 7 days. Medium findings remediated within 30 days.",
        },
        {
            "id": uuid.uuid4(), "company_id": cid,
            "vendor_name": "NCC Group", "status": "completed",
            "scope": "Cloud infrastructure and container security review",
            "conducted_at": NOW - timedelta(days=30),
            "critical_count": 0, "high_count": 0, "medium_count": 2, "low_count": 4,
            "summary": (
                "NCC Group conducted a focused cloud security assessment. No critical or high findings. "
                "Two medium findings: overly permissive S3 bucket CORS policy and unused IAM roles. "
                "Remediation in progress."
            ),
            "remediation_notes": "CORS policy remediated. IAM role cleanup scheduled for next sprint.",
        },
    ]


def _build_manual_controls(cid: uuid.UUID) -> list[dict]:
    controls = [
        ("CC1.1", "Board-level security oversight documented"),
        ("CC5.2", "Risk tolerance thresholds defined and approved"),
        ("CC9.2", "Vendor risk assessments completed for all critical vendors"),
        ("A1.1", "Business continuity plan tested and approved"),
        ("C1.1", "Data classification policy adopted by all staff"),
    ]
    return [
        {
            "id": uuid.uuid4(), "company_id": cid, "framework": "soc2",
            "control_id": ctrl_id, "status": "compliant",
            "notes": f"{desc}. Evidence on file. Last reviewed {(NOW - timedelta(days=14)).strftime('%Y-%m-%d')}.",
        }
        for ctrl_id, desc in controls
    ]


# ── MAIN ──────────────────────────────────────────────────────────────────────

async def main():
    async with AsyncSessionLocal() as db:
        # Find user and company
        user = (await db.execute(
            select(User).where(User.email == TARGET_EMAIL)
        )).scalar_one_or_none()

        if not user:
            print(f"ERROR: User {TARGET_EMAIL} not found. Create the account first.")
            sys.exit(1)

        cid = user.company_id
        print(f"Found company_id={cid} for {TARGET_EMAIL}")

        # ── Clear existing data ────────────────────────────────────────────
        print("Clearing existing data...")
        await db.execute(delete(Evidence).where(Evidence.company_id == cid))
        await db.execute(delete(Integration).where(Integration.company_id == cid))
        await db.execute(delete(ScoreSnapshot).where(ScoreSnapshot.company_id == cid))
        await db.execute(delete(Risk).where(Risk.company_id == cid))
        await db.execute(delete(Vendor).where(Vendor.company_id == cid))
        await db.execute(delete(Policy).where(Policy.company_id == cid))
        await db.execute(delete(TrainingRecord).where(TrainingRecord.company_id == cid))
        await db.execute(delete(AccessReview).where(AccessReview.company_id == cid))
        await db.execute(delete(PenTest).where(PenTest.company_id == cid))
        await db.execute(delete(ManualControl).where(ManualControl.company_id == cid))
        await db.commit()

        # ── Integrations ───────────────────────────────────────────────────
        print(f"Seeding {len(INTEGRATIONS)} integrations...")
        for int_type, creds in INTEGRATIONS:
            db.add(Integration(
                id=uuid.uuid4(),
                company_id=cid,
                integration_type=int_type,
                credentials_enc=_enc(creds),
                status="active",
                last_collected_at=NOW - timedelta(hours=2),
            ))
        await db.commit()

        # ── Evidence ───────────────────────────────────────────────────────
        evidence = _build_evidence(cid)
        print(f"Seeding {len(evidence)} evidence records across 12 SOC 2 control categories...")
        for batch_start in range(0, len(evidence), 100):
            batch = evidence[batch_start:batch_start + 100]
            stmt = pg_insert(Evidence).values(batch)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["company_id", "integration", "evidence_type", "source_id"]
            )
            await db.execute(stmt)
        await db.commit()

        # ── Score snapshots ────────────────────────────────────────────────
        snaps = _build_score_history(cid, "soc2")
        print(f"Seeding {len(snaps)} SOC 2 score snapshots...")
        for snap in snaps:
            db.add(ScoreSnapshot(**snap))
        await db.commit()

        # ── Policies ──────────────────────────────────────────────────────
        policies = _build_policies(cid)
        print(f"Seeding {len(policies)} policies...")
        for p in policies:
            db.add(Policy(**p))
        await db.commit()

        # ── Risks ─────────────────────────────────────────────────────────
        risks = _build_risks(cid)
        print(f"Seeding {len(risks)} risks...")
        for r in risks:
            db.add(Risk(**r))
        await db.commit()

        # ── Vendors ───────────────────────────────────────────────────────
        vendors = _build_vendors(cid)
        print(f"Seeding {len(vendors)} vendors...")
        for v in vendors:
            db.add(Vendor(**v))
        await db.commit()

        # ── Training ──────────────────────────────────────────────────────
        training = _build_training(cid)
        print(f"Seeding {len(training)} training records...")
        for t in training:
            db.add(TrainingRecord(**t))
        await db.commit()

        # ── Access reviews ─────────────────────────────────────────────────
        reviews = _build_access_reviews(cid)
        print(f"Seeding {len(reviews)} access reviews...")
        for r in reviews:
            db.add(AccessReview(**r))
        await db.commit()

        # ── Pen tests ──────────────────────────────────────────────────────
        pen_tests = _build_pen_tests(cid)
        print(f"Seeding {len(pen_tests)} pen tests...")
        for p in pen_tests:
            db.add(PenTest(**p))
        await db.commit()

        # ── Manual controls ────────────────────────────────────────────────
        manual = _build_manual_controls(cid)
        print(f"Seeding {len(manual)} manual controls...")
        for m in manual:
            db.add(ManualControl(**m))
        await db.commit()

        print()
        print("=" * 60)
        print("SEED COMPLETE")
        print(f"  Account : {TARGET_EMAIL}")
        print(f"  Company : {cid}")
        print(f"  Framework: SOC 2 (all 12 categories → expected score: 91–100%)")
        print(f"  Integrations: {len(INTEGRATIONS)}")
        print(f"  Evidence records: {len(evidence)}")
        print(f"  Score snapshots: {len(snaps)} (90-day trend: 41% → 100%)")
        print(f"  Policies: {len(policies)}")
        print(f"  Risks: {len(risks)} (8 mitigated/closed, 2 open-low)")
        print(f"  Vendors: {len(vendors)}")
        print(f"  Training: {len(training)}")
        print(f"  Access reviews: {len(reviews)}")
        print(f"  Pen tests: {len(pen_tests)}")
        print(f"  Manual controls: {len(manual)}")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
