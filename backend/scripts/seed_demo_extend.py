"""
Extend the demo account with more integrations and richer evidence data.

Adds Okta, Google Workspace, Jira, and Azure AD to admin@tracelayer.it.com.
Also enriches existing AWS, GitHub, and Slack with more records.

Usage (from backend/ directory):
    python scripts/seed_demo_extend.py

Safe to re-run — uses upsert so existing records are updated, not duplicated.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from core.config import settings
from core.database import AsyncSessionLocal
from models import Company, Integration, User
from models.evidence import Evidence

DEMO_EMAIL = "admin@tracelayer.it.com"
NOW = datetime.now(timezone.utc)
DAY = timedelta(days=1)


def _enc(data: dict) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


def _ev(company_id, integration, control, evidence_type, source_id, data, age_days=1):
    return {
        "id": uuid.uuid4(),
        "company_id": company_id,
        "integration": integration,
        "control": control,
        "evidence_type": evidence_type,
        "source_id": source_id,
        "timestamp": NOW - timedelta(days=age_days),
        "data": data,
    }


# ── AWS (extended) ────────────────────────────────────────────────────────────

def _aws_extra(cid):
    records = []

    # More IAM users — contractors, service accounts, some without MFA
    extra_users = [
        ("frank@acme.com",     "AIDA666666666666F", False, True),
        ("grace@acme.com",     "AIDA777777777777G", False, True),
        ("henry@acme.com",     "AIDA888888888888H", False, False),  # MFA missing
        ("contractor-jdoe",    "AIDA999999999999I", False, False),  # no MFA
        ("svc-data-pipeline",  "AIDAAAAAAAAAAAAAAJ", False, False),
        ("svc-monitoring",     "AIDABBBBBBBBBBBBBK", False, True),
        ("svc-backup",         "AIDACCCCCCCCCCCCL", False, False),
        ("ivan@acme.com",      "AIDADDDDDDDDDDDDDM", True,  True),  # admin
    ]
    for email, uid, admin, mfa in extra_users:
        records.append(_ev(cid, "aws", "access_control", "iam_users", uid, {
            "username": email,
            "arn": f"arn:aws:iam::123456789012:user/{email}",
            "admin": admin,
            "mfa_active": mfa,
            "password_last_used": (NOW - timedelta(days=3)).isoformat(),
            "last_activity": (NOW - timedelta(days=2)).isoformat(),
        }))

    # More IAM policies
    extra_policies = [
        ("EC2FullAccess",           "Customer managed", False, 4),
        ("RDSReadOnly",             "Customer managed", False, 2),
        ("SecretsManagerReadOnly",  "AWS managed",      False, 3),
        ("SecurityAudit",           "AWS managed",      False, 2),
        ("PowerUserAccess",         "AWS managed",      True,  1),
        ("IAMFullAccess",           "Customer managed", True,  1),
    ]
    for name, scope, admin, count in extra_policies:
        records.append(_ev(cid, "aws", "access_control", "iam_policies", f"policy_{name}", {
            "policy_name": name, "scope": scope,
            "attached_users": count, "admin_policy": admin,
        }, age_days=2))

    # More CloudTrail events — security-relevant
    extra_events = [
        ("ConsoleLogin",                "signin.amazonaws.com",      "frank@acme.com",   "us-east-1"),
        ("DeleteTrail",                 "cloudtrail.amazonaws.com",  "ivan@acme.com",    "us-east-1"),
        ("StopLogging",                 "cloudtrail.amazonaws.com",  "ivan@acme.com",    "us-east-1"),
        ("PutBucketPolicy",             "s3.amazonaws.com",          "svc-data-pipeline","us-east-1"),
        ("CreateAccessKey",             "iam.amazonaws.com",         "carol@acme.com",   "us-east-1"),
        ("AttachUserPolicy",            "iam.amazonaws.com",         "ivan@acme.com",    "us-east-1"),
        ("AuthorizeSecurityGroupIngress","ec2.amazonaws.com",         "deploy-bot",       "us-east-1"),
        ("CreateBucket",                "s3.amazonaws.com",          "grace@acme.com",   "eu-west-1"),
        ("PutBucketPublicAccessBlock",  "s3.amazonaws.com",          "grace@acme.com",   "eu-west-1"),
        ("GetSecretValue",              "secretsmanager.amazonaws.com","ci-runner",       "us-east-1"),
    ]
    for event, source, actor, region in extra_events:
        records.append(_ev(cid, "aws", "logging_monitoring", "cloudtrail_logs",
                           f"ct_extra_{event}_{actor}", {
            "event_name": event, "event_source": source,
            "user": actor, "region": region,
            "event_time": (NOW - timedelta(hours=12)).isoformat(),
        }, age_days=0))

    return records


# ── GitHub (extended) ─────────────────────────────────────────────────────────

def _github_extra(cid):
    records = []

    # More repos
    extra_repos = [
        ("mobile",        True,  "main",   True),
        ("data-pipeline", True,  "main",   True),
        ("compliance-bot",True,  "main",   True),
        ("marketing-site",False, "main",   False),
        ("internal-tools",True,  "develop",False),
    ]
    for name, private, branch, protected in extra_repos:
        records.append(_ev(cid, "github", "change_management", "repositories",
                           f"gh_repo_{name}", {
            "name": name, "full_name": f"acme-corp/{name}",
            "private": private, "default_branch": branch,
            "visibility": "private" if private else "public",
            "archived": False,
            "branch_protection_enabled": protected,
            "updated_at": (NOW - DAY).isoformat(),
        }, age_days=3))

    # More org members
    extra_members = ["frank", "grace", "henry", "ivan", "julia"]
    for login in extra_members:
        records.append(_ev(cid, "github", "access_control", "github_members",
                           login, {
            "login": login, "id": abs(hash(login)) % 99999,
            "type": "User", "site_admin": False,
        }))

    # One more admin
    records.append(_ev(cid, "github", "access_control", "github_admin_members",
                       "admin_ivan", {
        "login": "ivan", "id": abs(hash("ivan")) % 99999, "role": "admin",
    }))

    return records


# ── Slack (extended) ──────────────────────────────────────────────────────────

def _slack_extra(cid):
    records = []

    extra_users = [
        ("frank@acme.com",  "U006", False, True),
        ("grace@acme.com",  "U007", False, True),
        ("henry@acme.com",  "U008", False, False),   # no 2FA
        ("ivan@acme.com",   "U009", True,  True),
        ("julia@acme.com",  "U010", False, False),   # no 2FA
        ("svc-bot@acme.com","U011", False, False),
    ]
    for email, uid, admin, tfa in extra_users:
        records.append(_ev(cid, "slack", "access_control", "slack_users", uid, {
            "id": uid, "email": email,
            "is_admin": admin, "is_bot": uid == "U011",
            "two_factor_enabled": tfa,
            "deleted": False,
        }))

    return records


# ── Okta ──────────────────────────────────────────────────────────────────────

def _okta_evidence(cid):
    records = []

    users = [
        ("alice@acme.com",   "00u1", "ACTIVE",   True,  "2026-03-15T09:00:00Z"),
        ("bob@acme.com",     "00u2", "ACTIVE",   True,  "2026-03-14T14:20:00Z"),
        ("carol@acme.com",   "00u3", "ACTIVE",   True,  "2026-03-15T11:00:00Z"),
        ("dave@acme.com",    "00u4", "ACTIVE",   False, "2026-03-10T08:00:00Z"),  # no MFA
        ("eve@acme.com",     "00u5", "ACTIVE",   True,  "2026-03-15T07:30:00Z"),
        ("frank@acme.com",   "00u6", "ACTIVE",   False, "2026-03-01T12:00:00Z"),  # no MFA, old login
        ("grace@acme.com",   "00u7", "ACTIVE",   True,  "2026-03-15T10:15:00Z"),
        ("henry@acme.com",   "00u8", "SUSPENDED","False","2026-02-20T09:00:00Z"),  # suspended
        ("ivan@acme.com",    "00u9", "ACTIVE",   True,  "2026-03-15T08:45:00Z"),
        ("julia@acme.com",   "00u10","ACTIVE",   True,  "2026-03-13T16:00:00Z"),
    ]
    for email, uid, status, mfa, last_login in users:
        records.append(_ev(cid, "okta", "access_control", "okta_users", uid, {
            "login": email, "email": email,
            "first_name": email.split("@")[0].capitalize(),
            "last_name": "Smith",
            "status": status,
            "last_login": last_login,
            "mfa_enrolled": mfa,
            "created": "2025-01-15T10:00:00Z",
        }))

    groups = [
        ("Engineering",  "00g1", "Everyone in engineering",      8),
        ("Sales",        "00g2", "Sales and account management",  5),
        ("Finance",      "00g3", "Finance and accounting",        4),
        ("HR",           "00g4", "Human resources",               3),
        ("Leadership",   "00g5", "Executive leadership team",     3),
        ("Contractors",  "00g6", "External contractors",          2),
    ]
    for name, gid, desc, count in groups:
        records.append(_ev(cid, "okta", "access_control", "okta_groups", gid, {
            "name": name, "description": desc,
            "type": "OKTA_GROUP", "member_count": count,
        }, age_days=2))

    policies = [
        ("Default Policy",     "pol1", "PASSWORD", "ACTIVE",
         "Minimum 12 chars, complexity required, 90-day rotation"),
        ("MFA Enrollment",     "pol2", "MFA_ENROLL","ACTIVE",
         "All users must enroll in MFA within 24 hours of account creation"),
        ("Session Management", "pol3", "SIGN_ON",  "ACTIVE",
         "8-hour max session, re-auth on sensitive operations"),
    ]
    for name, pid, ptype, status, desc in policies:
        records.append(_ev(cid, "okta", "access_control", "okta_policies", pid, {
            "name": name, "type": ptype, "status": status, "description": desc,
        }, age_days=3))

    return records


# ── Google Workspace ──────────────────────────────────────────────────────────

def _workspace_evidence(cid):
    records = []

    users = [
        ("alice@acme.com",  "gw_001", True,  False, "/Engineering", "2026-03-15T09:00:00Z"),
        ("bob@acme.com",    "gw_002", False, False, "/Engineering", "2026-03-14T12:00:00Z"),
        ("carol@acme.com",  "gw_003", True,  False, "/Engineering", "2026-03-15T10:00:00Z"),
        ("dave@acme.com",   "gw_004", False, False, "/Sales",       "2026-03-12T08:00:00Z"),
        ("eve@acme.com",    "gw_005", False, False, "/Sales",       "2026-03-15T07:00:00Z"),
        ("frank@acme.com",  "gw_006", False, False, "/Finance",     "2026-03-10T11:00:00Z"),
        ("grace@acme.com",  "gw_007", False, False, "/Engineering", "2026-03-15T09:30:00Z"),
        ("henry@acme.com",  "gw_008", False, True,  "/Engineering", "2026-02-28T14:00:00Z"),  # suspended
        ("ivan@acme.com",   "gw_009", True,  False, "/Leadership",  "2026-03-15T08:00:00Z"),
        ("julia@acme.com",  "gw_010", False, False, "/HR",          "2026-03-13T15:00:00Z"),
    ]
    for email, uid, admin, suspended, org_unit, last_login in users:
        records.append(_ev(cid, "google_workspace", "access_control", "workspace_users", uid, {
            "email": email,
            "full_name": email.split("@")[0].replace(".", " ").title(),
            "is_admin": admin,
            "suspended": suspended,
            "org_unit": org_unit,
            "last_login_time": last_login,
            "two_step_verification": not suspended,
        }))

    for uid, email, super_admin in [("gw_001","alice@acme.com",True), ("gw_003","carol@acme.com",False), ("gw_009","ivan@acme.com",True)]:
        records.append(_ev(cid, "google_workspace", "access_control", "workspace_admin_members",
                           f"admin_{uid}", {
            "email": email,
            "is_super_admin": super_admin,
            "is_delegated_admin": not super_admin,
        }))

    groups = [
        ("ggl_001", "engineering@acme.com",  "Engineering",    "All engineering staff",             8),
        ("ggl_002", "sales@acme.com",        "Sales",          "Sales and account management",       5),
        ("ggl_003", "all-hands@acme.com",    "All Hands",      "All company members",               10),
        ("ggl_004", "security@acme.com",     "Security",       "Security team and reviewers",        3),
        ("ggl_005", "leadership@acme.com",   "Leadership",     "Executive leadership team",          3),
    ]
    for gid, email, name, desc, count in groups:
        records.append(_ev(cid, "google_workspace", "access_control", "workspace_groups", gid, {
            "name": name, "email": email,
            "description": desc, "member_count": count,
        }, age_days=2))

    return records


# ── Jira ──────────────────────────────────────────────────────────────────────

def _jira_evidence(cid):
    records = []

    projects = [
        ("BACK",  "Backend Services",    "alice@acme.com",  "software", "classic",  False),
        ("FRONT", "Frontend App",        "carol@acme.com",  "software", "next-gen", False),
        ("MOB",   "Mobile Apps",         "bob@acme.com",    "software", "next-gen", False),
        ("OPS",   "Infrastructure & Ops","ivan@acme.com",   "service_desk","classic",False),
        ("SEC",   "Security & Compliance","carol@acme.com", "software", "classic",  False),
        ("DATA",  "Data & Analytics",    "grace@acme.com",  "software", "next-gen", False),
        ("MKTG",  "Marketing",           "julia@acme.com",  "business", "classic",  False),
    ]
    for key, name, lead, ptype, style, private in projects:
        records.append(_ev(cid, "jira", "change_management", "jira_projects",
                           f"jira_{key}", {
            "key": key, "name": name,
            "project_type": ptype, "style": style,
            "lead_email": lead,
            "is_private": private,
            "issue_count": abs(hash(key)) % 150 + 10,
        }, age_days=2))

    jira_users = [
        ("alice@acme.com",  "jira_u1", "Alice Smith",  True,  "atlassian"),
        ("bob@acme.com",    "jira_u2", "Bob Jones",    True,  "atlassian"),
        ("carol@acme.com",  "jira_u3", "Carol White",  True,  "atlassian"),
        ("dave@acme.com",   "jira_u4", "Dave Brown",   True,  "atlassian"),
        ("eve@acme.com",    "jira_u5", "Eve Davis",    True,  "atlassian"),
        ("frank@acme.com",  "jira_u6", "Frank Miller", True,  "atlassian"),
        ("grace@acme.com",  "jira_u7", "Grace Wilson", True,  "atlassian"),
        ("henry@acme.com",  "jira_u8", "Henry Moore",  False, "atlassian"),  # inactive
        ("contractor-jdoe@ext.com","jira_u9","J. Doe",True, "atlassian"),
    ]
    for email, uid, name, active, acct_type in jira_users:
        records.append(_ev(cid, "jira", "access_control", "jira_users", uid, {
            "email": email, "display_name": name,
            "active": active, "account_type": acct_type,
        }))

    return records


# ── Azure AD ──────────────────────────────────────────────────────────────────

def _azure_evidence(cid):
    records = []

    users = [
        ("alice@acme.onmicrosoft.com",  "az_001", "Alice Smith",   True,  True,  "2026-03-15T09:00:00Z"),
        ("bob@acme.onmicrosoft.com",    "az_002", "Bob Jones",     True,  True,  "2026-03-14T14:00:00Z"),
        ("carol@acme.onmicrosoft.com",  "az_003", "Carol White",   True,  True,  "2026-03-15T11:00:00Z"),
        ("dave@acme.onmicrosoft.com",   "az_004", "Dave Brown",    True,  False, "2026-03-10T08:00:00Z"),  # no license
        ("eve@acme.onmicrosoft.com",    "az_005", "Eve Davis",     True,  True,  "2026-03-15T07:30:00Z"),
        ("frank@acme.onmicrosoft.com",  "az_006", "Frank Miller",  True,  True,  "2026-03-13T12:00:00Z"),
        ("grace@acme.onmicrosoft.com",  "az_007", "Grace Wilson",  True,  True,  "2026-03-15T10:15:00Z"),
        ("henry@acme.onmicrosoft.com",  "az_008", "Henry Moore",   False, True,  "2026-02-20T09:00:00Z"),  # disabled
        ("ivan@acme.onmicrosoft.com",   "az_009", "Ivan Clark",    True,  True,  "2026-03-15T08:45:00Z"),
        ("svc-pipeline@acme.onmicrosoft.com","az_010","SVC Pipeline",True, False,"2026-03-15T06:00:00Z"),
    ]
    for upn, uid, name, enabled, licensed, last_sign in users:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_users", uid, {
            "displayName": name,
            "userPrincipalName": upn,
            "accountEnabled": enabled,
            "lastSignInDateTime": last_sign,
            "assignedLicenses": [{"skuId": "M365_E3"}] if licensed else [],
            "mfaRegistered": enabled,
        }))

    groups = [
        ("az_g1", "IT-Admins",     "IT administration group",        True,  ["Global Admin"]),
        ("az_g2", "Developers",    "Software development team",      True,  []),
        ("az_g3", "Finance",       "Finance and accounting",         True,  []),
        ("az_g4", "HR",            "Human resources",                True,  []),
        ("az_g5", "Security",      "Security and compliance team",   True,  ["Security Reader"]),
        ("az_g6", "All-Users",     "All company employees",          False, []),
    ]
    for gid, name, desc, sec_enabled, roles in groups:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_groups", gid, {
            "displayName": name, "description": desc,
            "securityEnabled": sec_enabled,
            "groupTypes": [],
            "assignedRoles": roles,
        }, age_days=2))

    roles = [
        ("az_r1", "62e90394-69f5-4237-9190-012177145e10", "Global Administrator",    "az_001", "alice@acme.onmicrosoft.com",  "Alice Smith"),
        ("az_r2", "62e90394-69f5-4237-9190-012177145e10", "Global Administrator",    "az_009", "ivan@acme.onmicrosoft.com",   "Ivan Clark"),
        ("az_r3", "194ae4cb-b126-40b2-bd5b-6091b380977d", "Security Administrator",  "az_003", "carol@acme.onmicrosoft.com",  "Carol White"),
        ("az_r4", "fe930be7-5e62-47db-91af-98c3a49a38b1", "User Administrator",      "az_003", "carol@acme.onmicrosoft.com",  "Carol White"),
        ("az_r5", "9b895d92-2cd3-44c7-9d02-a6ac2d5ea5c3", "Application Administrator","az_007","grace@acme.onmicrosoft.com","Grace Wilson"),
    ]
    for rid, role_id, role_name, member_id, member_upn, member_name in roles:
        records.append(_ev(cid, "azure_ad", "access_control", "azure_roles", rid, {
            "roleDefinitionId": role_id,
            "roleName": role_name,
            "memberId": member_id,
            "memberUpn": member_upn,
            "memberDisplayName": member_name,
        }, age_days=1))

    return records


# ── Main ──────────────────────────────────────────────────────────────────────

async def extend():
    async with AsyncSessionLocal() as db:
        # Find the admin user
        result = await db.execute(select(User).where(User.email == DEMO_EMAIL))
        user = result.scalar_one_or_none()
        if not user:
            print(f"✗ User {DEMO_EMAIL} not found. Run seed_demo.py first.")
            return

        company_id = user.company_id
        print(f"✓ Found demo account: {DEMO_EMAIL} (company_id={company_id})")

        # ── Add new integrations (skip if already connected) ────────────────
        collected = NOW - timedelta(hours=1)
        new_integrations = [
            ("okta",              {"domain": "acme.okta.com",        "api_token": "DEMO"}),
            ("google_workspace",  {"service_account_json": "{\"type\":\"service_account\",\"project_id\":\"acme-demo\"}", "admin_email": "admin@acme.com"}),
            ("jira",              {"domain": "acme.atlassian.net",   "email": "admin@acme.com", "api_token": "DEMO"}),
            ("azure_ad",          {"tenant_id": "DEMO",              "client_id": "DEMO",       "client_secret": "DEMO"}),
        ]
        added_integrations = []
        for itype, creds in new_integrations:
            existing = await db.execute(
                select(Integration).where(
                    Integration.company_id == company_id,
                    Integration.integration_type == itype,
                )
            )
            if existing.scalar_one_or_none():
                print(f"  · {itype}: already connected — skipping")
            else:
                db.add(Integration(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    integration_type=itype,
                    credentials_enc=_enc(creds),
                    status="active",
                    last_collected_at=collected,
                ))
                added_integrations.append(itype)

        await db.flush()

        # ── Upsert evidence ──────────────────────────────────────────────────
        all_records = (
            _aws_extra(company_id)
            + _github_extra(company_id)
            + _slack_extra(company_id)
            + _okta_evidence(company_id)
            + _workspace_evidence(company_id)
            + _jira_evidence(company_id)
            + _azure_evidence(company_id)
        )

        upserted = 0
        for r in all_records:
            stmt = (
                pg_insert(Evidence.__table__)
                .values(
                    id=r["id"],
                    company_id=r["company_id"],
                    integration=r["integration"],
                    control=r["control"],
                    evidence_type=r["evidence_type"],
                    source_id=r["source_id"],
                    timestamp=r["timestamp"],
                    data=r["data"],
                )
                .on_conflict_do_update(
                    index_elements=["company_id", "integration", "evidence_type", "source_id"],
                    set_={"data": r["data"], "timestamp": r["timestamp"]},
                )
            )
            await db.execute(stmt)
            upserted += 1

        await db.commit()

    print()
    print(f"✓ Evidence upserted: {upserted} records")
    if added_integrations:
        print(f"✓ New integrations added: {', '.join(added_integrations)}")
    print()
    print("  Integrations now active:")
    print("    AWS · GitHub · Slack · Okta · Google Workspace · Jira · Azure AD")
    print()
    print("  Evidence coverage:")
    print("    access_control     — IAM, Okta, GitHub members, Slack, Workspace, Jira users, Azure users/groups/roles")
    print("    logging_monitoring — CloudTrail (15+ events incl. security-critical)")
    print("    change_management  — GitHub repos (10), Jira projects (7)")


if __name__ == "__main__":
    asyncio.run(extend())
