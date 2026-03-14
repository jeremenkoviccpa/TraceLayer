"""
Demo seed script — creates a ready-to-demo account with realistic evidence data.

Usage (from backend/ directory):
    python scripts/seed_demo.py

Demo credentials:
    Email:    admin@tracelayer.it.com
    Password: admin

Re-running is safe — skips if demo company already exists.
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Allow running from backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from cryptography.fernet import Fernet
from sqlalchemy import select

from core.database import AsyncSessionLocal
from core.config import settings
from core.security import hash_password
from models import Base, Company, Control, Evidence, Integration, User

# ── Demo constants ──────────────────────────────────────────────────────────

DEMO_EMAIL = "admin@tracelayer.it.com"
DEMO_PASSWORD = "admin"
DEMO_COMPANY = "Acme Corp (Demo)"

NOW = datetime.now(timezone.utc)
DAY = timedelta(days=1)


def _enc(data: dict) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


# ── Evidence fixtures ────────────────────────────────────────────────────────

def _aws_evidence(company_id: uuid.UUID) -> list[dict]:
    users = [
        ("alice@acme.com", "AIDA111111111111A", False),
        ("bob@acme.com",   "AIDA222222222222B", False),
        ("carol@acme.com", "AIDA333333333333C", True),
        ("deploy-bot",     "AIDA444444444444D", False),
        ("ci-runner",      "AIDA555555555555E", False),
    ]
    records = []
    for email, uid, admin in users:
        records.append({
            "company_id": company_id, "integration": "aws",
            "control": "access_control", "evidence_type": "iam_users",
            "source_id": uid, "timestamp": NOW - DAY,
            "data": {"username": email, "arn": f"arn:aws:iam::123456789012:user/{email}",
                     "admin": admin, "mfa_active": not admin,
                     "last_activity": (NOW - timedelta(days=2)).isoformat()},
        })

    policies = [
        ("AdministratorAccess", "AWS managed", True),
        ("ReadOnlyAccess",      "AWS managed", False),
        ("S3FullAccess",        "Customer managed", False),
        ("CloudTrailFullAccess","Customer managed", False),
    ]
    for name, scope, admin in policies:
        records.append({
            "company_id": company_id, "integration": "aws",
            "control": "access_control", "evidence_type": "iam_policies",
            "source_id": f"policy_{name}", "timestamp": NOW - DAY * 2,
            "data": {"policy_name": name, "scope": scope,
                     "attached_users": 1 if admin else 3, "admin_policy": admin},
        })

    trails = [
        ("management_console_login", "signin.amazonaws.com", "alice@acme.com"),
        ("iam_policy_change",        "iam.amazonaws.com",    "carol@acme.com"),
        ("s3_bucket_created",        "s3.amazonaws.com",     "deploy-bot"),
        ("ec2_instance_started",     "ec2.amazonaws.com",    "ci-runner"),
        ("cloudtrail_enabled",       "cloudtrail.amazonaws.com", "carol@acme.com"),
    ]
    for event, source, actor in trails:
        records.append({
            "company_id": company_id, "integration": "aws",
            "control": "logging_monitoring", "evidence_type": "cloudtrail_logs",
            "source_id": f"ct_{event}_{actor}", "timestamp": NOW - timedelta(hours=6),
            "data": {"event_name": event, "event_source": source,
                     "user": actor, "region": "us-east-1",
                     "event_time": (NOW - timedelta(hours=6)).isoformat()},
        })

    return records


def _github_evidence(company_id: uuid.UUID) -> list[dict]:
    repos = [
        ("backend",  True,  "main"),
        ("frontend", True,  "main"),
        ("infra",    True,  "main"),
        ("docs",     False, "main"),
        ("sdk",      False, "main"),
    ]
    records = []
    for name, private, branch in repos:
        records.append({
            "company_id": company_id, "integration": "github",
            "control": "change_management", "evidence_type": "repositories",
            "source_id": f"gh_repo_{name}", "timestamp": NOW - DAY * 3,
            "data": {"name": name, "full_name": f"acme-corp/{name}",
                     "private": private, "default_branch": branch,
                     "visibility": "private" if private else "public",
                     "archived": False, "updated_at": (NOW - DAY).isoformat()},
        })

    members = ["alice", "bob", "carol", "dave", "eve"]
    for login in members:
        records.append({
            "company_id": company_id, "integration": "github",
            "control": "access_control", "evidence_type": "github_members",
            "source_id": login, "timestamp": NOW - DAY,
            "data": {"login": login, "id": hash(login) % 99999,
                     "type": "User", "site_admin": False},
        })

    for login in ["alice", "carol"]:
        records.append({
            "company_id": company_id, "integration": "github",
            "control": "access_control", "evidence_type": "github_admin_members",
            "source_id": f"admin_{login}", "timestamp": NOW - DAY,
            "data": {"login": login, "id": hash(login) % 99999, "role": "admin"},
        })

    return records


def _slack_evidence(company_id: uuid.UUID) -> list[dict]:
    users = [
        ("alice@acme.com", "U001", True),
        ("bob@acme.com",   "U002", False),
        ("carol@acme.com", "U003", True),
        ("dave@acme.com",  "U004", False),
        ("eve@acme.com",   "U005", False),
    ]
    records = []
    for email, uid, admin in users:
        records.append({
            "company_id": company_id, "integration": "slack",
            "control": "access_control", "evidence_type": "slack_users",
            "source_id": uid, "timestamp": NOW - DAY,
            "data": {"id": uid, "email": email, "is_admin": admin,
                     "is_bot": False, "deleted": False},
        })

    records.append({
        "company_id": company_id, "integration": "slack",
        "control": "access_control", "evidence_type": "slack_workspace",
        "source_id": "T_ACMECORP_DEMO", "timestamp": NOW - DAY * 2,
        "data": {"id": "T_ACMECORP_DEMO", "name": "Acme Corp",
                 "domain": "acmecorp", "email_domain": "acme.com",
                 "member_count": 5, "plan": "pro"},
    })

    return records


# ── Main ─────────────────────────────────────────────────────────────────────

async def seed():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(
            select(Company).where(Company.name == DEMO_COMPANY)
        )
        if existing.scalar_one_or_none():
            print(f"✓ Demo account already exists — skipping.")
            print(f"  Email:    {DEMO_EMAIL}")
            print(f"  Password: {DEMO_PASSWORD}")
            await engine.dispose()
            return

        # Company
        company = Company(
            id=uuid.uuid4(),
            name=DEMO_COMPANY,
            plan="growth",
            subscription_status="active",
        )
        db.add(company)
        await db.flush()

        # User
        user = User(
            id=uuid.uuid4(),
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
            company_id=company.id,
            role="admin",
            email_verified=True,
        )
        db.add(user)

        # Integrations (fake creds, status=active, collected 1h ago)
        collected = NOW - timedelta(hours=1)
        for itype, creds in [
            ("aws",    {"access_key_id": "DEMO", "secret_access_key": "DEMO", "region": "us-east-1"}),
            ("github", {"token": "DEMO", "org": "acme-corp"}),
            ("slack",  {"bot_token": "xoxb-DEMO"}),
        ]:
            db.add(Integration(
                id=uuid.uuid4(),
                company_id=company.id,
                integration_type=itype,
                credentials_enc=_enc(creds),
                status="active",
                last_collected_at=collected,
            ))

        # Evidence
        all_records = (
            _aws_evidence(company.id)
            + _github_evidence(company.id)
            + _slack_evidence(company.id)
        )
        for r in all_records:
            db.add(Evidence(
                id=uuid.uuid4(),
                company_id=r["company_id"],
                integration=r["integration"],
                control=r["control"],
                evidence_type=r["evidence_type"],
                source_id=r["source_id"],
                timestamp=r["timestamp"],
                data=r["data"],
            ))

        await db.commit()

    print("✓ Demo account created!")
    print(f"  Company:  {DEMO_COMPANY}")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print(f"  Plan:     growth (unlimited)")
    print(f"  Evidence: {len(all_records)} records across AWS, GitHub, Slack")
    print()
    print("  Go to your app and log in with the credentials above.")


if __name__ == "__main__":
    asyncio.run(seed())
