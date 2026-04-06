"""
Super-admin API — only accessible to emails listed in INTERNAL_ADMINS env var.
Provides company and user management for internal operators.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.company import Company
from models.evidence import Evidence
from models.integration import Integration
from models.partner_directory import PartnerDirectoryEntry
from models.score_snapshot import ScoreSnapshot
from models.tool_lead import ToolLead
from models.user import User
from schemas.partner_directory import PartnerDirectoryEntryResponse
from services import audit_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/super-admin", tags=["super-admin"])


# ── Auth guard ────────────────────────────────────────────────────────────────

async def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.email not in settings.internal_admins_list:
        raise HTTPException(status_code=403, detail="Super-admin access required.")
    return current_user


# ── Schemas ───────────────────────────────────────────────────────────────────

class CompanyRow(BaseModel):
    id: str
    name: str
    plan: str
    subscription_status: Optional[str]
    is_partner_account: bool
    created_at: datetime
    user_count: int
    admin_emails: list[str]
    integration_count: int = 0
    evidence_count: int = 0

    class Config:
        from_attributes = True


class PatchCompanyBody(BaseModel):
    plan: Optional[str] = None
    is_partner_account: Optional[bool] = None
    reset_subscription: Optional[bool] = None  # wipe billing fields → free


class UserRow(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PatchUserBody(BaseModel):
    role: Optional[str] = None
    email_verified: Optional[bool] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/companies", response_model=list[CompanyRow])
async def list_companies(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all companies with user counts and admin emails."""
    result = await db.execute(select(Company).order_by(Company.created_at.desc()))
    companies = result.scalars().all()

    # Batch-load integration and evidence counts
    int_counts_result = await db.execute(
        select(Integration.company_id, func.count(Integration.id).label("cnt"))
        .group_by(Integration.company_id)
    )
    int_counts = {str(row.company_id): row.cnt for row in int_counts_result}

    ev_counts_result = await db.execute(
        select(Evidence.company_id, func.count(Evidence.id).label("cnt"))
        .group_by(Evidence.company_id)
    )
    ev_counts = {str(row.company_id): row.cnt for row in ev_counts_result}

    rows = []
    for c in companies:
        users_result = await db.execute(
            select(User).where(User.company_id == c.id)
        )
        users = users_result.scalars().all()
        admin_emails = [u.email for u in users if u.role == "admin"]
        cid = str(c.id)
        rows.append(CompanyRow(
            id=cid,
            name=c.name,
            plan=c.plan,
            subscription_status=c.subscription_status,
            is_partner_account=c.is_partner_account,
            created_at=c.created_at,
            user_count=len(users),
            admin_emails=admin_emails,
            integration_count=int_counts.get(cid, 0),
            evidence_count=ev_counts.get(cid, 0),
        ))
    return rows


@router.patch("/companies/{company_id}", response_model=CompanyRow)
async def patch_company(
    company_id: uuid.UUID,
    body: PatchCompanyBody,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a company's plan or partner status."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if body.plan is not None:
        if body.plan not in ("free", "growth"):
            raise HTTPException(status_code=400, detail="Plan must be 'free' or 'growth'")
        company.plan = body.plan

    if body.is_partner_account is not None:
        company.is_partner_account = body.is_partner_account

    if body.reset_subscription:
        company.plan = "free"
        company.subscription_status = None
        company.ls_subscription_id = None
        company.ls_customer_id = None

    await audit_service.log_action(
        db=db,
        company_id=company.id,
        action="superadmin.company_updated",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"changes": body.model_dump(exclude_none=True)},
    )
    await db.commit()
    await db.refresh(company)

    users_result = await db.execute(select(User).where(User.company_id == company.id))
    users = users_result.scalars().all()
    ic_result = await db.execute(
        select(func.count(Integration.id)).where(Integration.company_id == company.id)
    )
    ec_result = await db.execute(
        select(func.count(Evidence.id)).where(Evidence.company_id == company.id)
    )
    return CompanyRow(
        id=str(company.id),
        name=company.name,
        plan=company.plan,
        subscription_status=company.subscription_status,
        is_partner_account=company.is_partner_account,
        created_at=company.created_at,
        user_count=len(users),
        admin_emails=[u.email for u in users if u.role == "admin"],
        integration_count=ic_result.scalar_one() or 0,
        evidence_count=ec_result.scalar_one() or 0,
    )


@router.get("/companies/{company_id}/users", response_model=list[UserRow])
async def list_company_users(
    company_id: uuid.UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.company_id == company_id))
    users = result.scalars().all()
    return [
        UserRow(
            id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            email_verified=u.email_verified,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/companies/{company_id}/users/{user_id}", response_model=UserRow)
async def patch_company_user(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    body: PatchUserBody,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role within a company."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.role is not None:
        if body.role not in ("admin", "member", "viewer"):
            raise HTTPException(status_code=400, detail="Role must be admin, member, or viewer")
        user.role = body.role

    if body.email_verified is not None:
        user.email_verified = body.email_verified

    await audit_service.log_action(
        db=db,
        company_id=company_id,
        action="superadmin.user_updated",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"target_user_id": str(user_id), "changes": body.model_dump(exclude_none=True)},
    )
    await db.commit()
    await db.refresh(user)
    return UserRow(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        email_verified=user.email_verified,
        created_at=user.created_at,
    )


@router.delete("/companies/{company_id}", status_code=204)
async def delete_company(
    company_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Permanently delete a company and all its associated data."""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await audit_service.log_action(
        db=db,
        company_id=company_id,
        action="superadmin.company_deleted",
        user_id=current_user.id,
        user_email=current_user.email,
        metadata={"company_name": company.name},
    )
    await db.commit()

    # Discover all tables that have a company_id column (avoids hardcoded names)
    tbl_result = await db.execute(text("""
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'company_id'
          AND table_schema = 'public'
          AND table_name NOT IN ('companies', 'users')
        ORDER BY table_name
    """))
    child_tables = [row[0] for row in tbl_result.fetchall()]

    # 1. Delete all company-scoped child records
    for tbl in child_tables:
        await db.execute(text(f"DELETE FROM {tbl} WHERE company_id = :cid"), {"cid": company_id})  # noqa: S608

    # 2. Delete tokens/sessions that FK to users (must go before users)
    for token_tbl in ("email_verification_tokens", "password_reset_tokens", "refresh_tokens"):
        await db.execute(text(f"""
            DELETE FROM {token_tbl}
            WHERE user_id IN (SELECT id FROM users WHERE company_id = :cid)
        """), {"cid": company_id})  # noqa: S608

    # 3. Users, then the company
    await db.execute(text("DELETE FROM users WHERE company_id = :cid"), {"cid": company_id})
    await db.execute(text("DELETE FROM companies WHERE id = :cid"), {"cid": company_id})
    await db.commit()
    return Response(status_code=204)


@router.delete("/companies/{company_id}/users/{user_id}", status_code=204)
async def delete_company_user(
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a user from a company."""
    result = await db.execute(
        select(User).where(User.id == user_id, User.company_id == company_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()
    return Response(status_code=204)


# ── Partner Directory CRUD ────────────────────────────────────────────────────

class PartnerDirectoryBody(BaseModel):
    partner_type: str
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    referral_url: Optional[str] = None
    contact_email: Optional[str] = None
    frameworks: Optional[list[str]] = None
    specialties: Optional[list[str]] = None
    is_featured: bool = False
    is_active: bool = True


class PartnerDirectoryPatchBody(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    referral_url: Optional[str] = None
    contact_email: Optional[str] = None
    frameworks: Optional[list[str]] = None
    specialties: Optional[list[str]] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None


@router.get("/partner-directory", response_model=list[PartnerDirectoryEntryResponse])
async def list_partner_directory(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PartnerDirectoryEntry).order_by(
            PartnerDirectoryEntry.partner_type,
            PartnerDirectoryEntry.is_featured.desc(),
            PartnerDirectoryEntry.name,
        )
    )
    return result.scalars().all()


@router.post("/partner-directory", response_model=PartnerDirectoryEntryResponse)
async def create_partner_entry(
    body: PartnerDirectoryBody,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if body.partner_type not in ("auditor", "pen_test"):
        raise HTTPException(status_code=400, detail="partner_type must be 'auditor' or 'pen_test'")
    entry = PartnerDirectoryEntry(**body.model_dump())
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.patch("/partner-directory/{entry_id}", response_model=PartnerDirectoryEntryResponse)
async def patch_partner_entry(
    entry_id: uuid.UUID,
    body: PartnerDirectoryPatchBody,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PartnerDirectoryEntry).where(PartnerDirectoryEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(entry, k, v)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.delete("/partner-directory/{entry_id}", status_code=204)
async def delete_partner_entry(
    entry_id: uuid.UUID,
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PartnerDirectoryEntry).where(PartnerDirectoryEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await db.delete(entry)
    await db.commit()
    return Response(status_code=204)


# ── Tool leads ────────────────────────────────────────────────────────────────

class ToolLeadRow(BaseModel):
    id: uuid.UUID
    email: str
    tool: str
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/tool-leads", response_model=list[ToolLeadRow])
async def list_tool_leads(
    _: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ToolLead).order_by(ToolLead.created_at.desc()).limit(500))
    return result.scalars().all()


# ── Demo seed ─────────────────────────────────────────────────────────────────

def _enc(data: dict) -> str:
    f = Fernet(settings.fernet_key.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


_DEMO_INTEGRATIONS = [
    ("aws",              {"access_key_id": "AKIADEMO", "secret_access_key": "DEMO", "region": "us-east-1"}),
    ("github",           {"token": "ghp_DEMO", "org": "acme-corp"}),
    ("slack",            {"bot_token": "xoxb-DEMO"}),
    ("okta",             {"domain": "acme.okta.com", "api_token": "DEMO"}),
    ("google_workspace", {"admin_email": "admin@acme.com", "service_account_json": '{"type":"service_account"}'}),
    ("jira",             {"domain": "acme.atlassian.net", "email": "admin@acme.com", "api_token": "DEMO"}),
    ("azure_ad",         {"tenant_id": "DEMO", "client_id": "DEMO", "client_secret": "DEMO"}),
    ("gitlab",           {"token": "glpat-DEMO", "domain": "gitlab.com"}),
    ("bitbucket",        {"username": "api-user", "app_password": "DEMO", "workspace": "acme-corp"}),
    ("linear",           {"api_key": "lin_api_DEMO"}),
    ("notion",           {"api_key": "secret_DEMO"}),
    ("asana",            {"access_token": "as-DEMO", "workspace_gid": "acme-ws"}),
    ("datadog",          {"api_key": "DEMO", "app_key": "DEMO", "site": "datadoghq.com"}),
    ("pagerduty",        {"api_key": "DEMO"}),
    ("new_relic",        {"api_key": "NRAK-DEMO", "account_id": "1234567"}),
    ("splunk",           {"host": "splunk.acme.internal", "token": "sp-DEMO", "port": "8089"}),
    ("snyk",             {"api_token": "snyk-DEMO", "org_id": "acme-corp"}),
    ("wiz",              {"client_id": "wiz-DEMO", "client_secret": "DEMO", "tenant": "acme"}),
    ("knowbe4",          {"api_token": "kb4-DEMO", "region": "us"}),
    ("qualys",           {"username": "api-user", "password": "DEMO", "platform_url": "https://qualysapi.qualys.com"}),
    ("bamboohr",         {"subdomain": "acmecorp", "api_key": "DEMO"}),
    ("greenhouse",       {"api_key": "gh-DEMO", "subdomain": "acme"}),
    ("checkr",           {"api_key": "ck-DEMO"}),
    ("stripe",           {"api_key": "rk_live_DEMO"}),
    ("hubspot",          {"access_token": "hs-DEMO"}),
    ("salesforce",       {"client_id": "DEMO", "client_secret": "DEMO", "username": "admin@acme.com", "password": "DEMO", "security_token": "DEMO"}),
    ("zendesk",          {"subdomain": "acme", "email": "admin@acme.com", "api_token": "zd-DEMO"}),
    ("intercom",         {"access_token": "ic-DEMO"}),
    ("sendgrid",         {"api_key": "SG.DEMO"}),
    ("vercel",           {"api_token": "DEMO", "team_id": "team_DEMO"}),
    ("cloudflare",       {"api_token": "DEMO", "account_id": "DEMO-ACCOUNT"}),
    ("crowdstrike",      {"client_id": "DEMO", "client_secret": "DEMO", "base_url": "https://api.crowdstrike.com"}),
    ("jamf",             {"domain": "acme.jamfcloud.com", "username": "api-user", "password": "DEMO"}),
    ("terraform_cloud",  {"api_token": "DEMO", "org_name": "acme-corp"}),
    ("1password",        {"service_account_token": "ops_DEMO"}),
    ("rippling",         {"api_key": "DEMO"}),
    ("sentry",           {"auth_token": "DEMO", "org_slug": "acme-corp"}),
    ("google_cloud",     {"service_account_json": '{"type":"service_account","project_id":"acme-prod"}', "project_id": "acme-prod-123"}),
    # Additional integrations for SOC 2 full coverage
    ("vault",            {"address": "https://vault.acme.internal", "token": "hvs.DEMO"}),
    ("sentinelone",      {"api_token": "DEMO_S1_TOKEN", "site_id": "DEMO-SITE-001"}),
    ("kandji",           {"api_token": "DEMO_KANDJI", "subdomain": "acme"}),
    ("servicenow",       {"instance": "acme.service-now.com", "username": "api-user", "password": "DEMO"}),
    ("opsgenie",         {"api_key": "DEMO_OG_KEY"}),
    ("hackerone",        {"api_token": "DEMO_H1_TOKEN", "program_handle": "acme-security"}),
]


def _build_demo_evidence(cid: uuid.UUID) -> list[dict]:
    now = datetime.now(timezone.utc)
    employees = ["alice@acme.com", "bob@acme.com", "carol@acme.com", "dave@acme.com",
                 "eve@acme.com", "frank@acme.com", "grace@acme.com", "ivan@acme.com",
                 "julia@acme.com", "henry@acme.com"]

    def ev(integration, control, etype, source_id, data, age_days=1):
        return {
            "id": uuid.uuid4(),
            "company_id": cid,
            "integration": integration,
            "control": control,
            "evidence_type": etype,
            "source_id": source_id,
            "timestamp": now - timedelta(days=age_days),
            "data": data,
        }

    records = []

    # AWS
    for i, email in enumerate(employees):
        uid = f"AIDA{'0'*(16-len(str(i+1)))}{i+1}"
        records.append(ev("aws", "access_control", "iam_users", uid, {
            "username": email, "arn": f"arn:aws:iam::123456789012:user/{email}",
            "admin": email in ["carol@acme.com", "ivan@acme.com"],
            "mfa_active": email not in ["henry@acme.com", "frank@acme.com"],
            "last_activity": (now - timedelta(days=2)).isoformat(),
        }))
    for name, admin in [("AdministratorAccess", True), ("ReadOnlyAccess", False), ("S3FullAccess", False),
                        ("CloudTrailFullAccess", False), ("EC2FullAccess", False), ("SecurityAudit", False)]:
        records.append(ev("aws", "access_control", "iam_policies", f"policy_{name}", {
            "policy_name": name, "admin_policy": admin, "attached_users": 2 if admin else 5,
        }, age_days=2))
    for event, source, actor in [
        ("ConsoleLogin", "signin.amazonaws.com", "alice@acme.com"),
        ("CreateTrail", "cloudtrail.amazonaws.com", "carol@acme.com"),
        ("PutBucketPolicy", "s3.amazonaws.com", "deploy-bot"),
        ("CreateAccessKey", "iam.amazonaws.com", "carol@acme.com"),
        ("AuthorizeSecurityGroupIngress", "ec2.amazonaws.com", "ivan@acme.com"),
        ("GetSecretValue", "secretsmanager.amazonaws.com", "ci-runner"),
        ("DeleteTrail", "cloudtrail.amazonaws.com", "ivan@acme.com"),
        ("StopLogging", "cloudtrail.amazonaws.com", "ivan@acme.com"),
    ]:
        records.append(ev("aws", "logging_monitoring", "cloudtrail_logs", f"ct_{event}_{actor}", {
            "event_name": event, "event_source": source, "user": actor, "region": "us-east-1",
            "event_time": (now - timedelta(hours=6)).isoformat(),
        }, age_days=0))
    for name, private, protected in [
        ("backend", True, True), ("frontend", True, True), ("infra", True, True),
        ("mobile", True, True), ("data-pipeline", True, True), ("docs", False, False),
        ("marketing-site", False, False), ("compliance-bot", True, True),
    ]:
        records.append(ev("aws", "cloud_assets", "s3_buckets", f"s3-{name}", {
            "name": f"acme-{name}-bucket", "region": "us-east-1",
            "public": not private, "encrypted": private, "versioning": protected,
        }, age_days=1))
    for iid, itype, state in [
        ("i-001", "t3.medium", "running"), ("i-002", "t3.large", "running"),
        ("i-003", "c5.xlarge", "running"), ("i-004", "t3.small", "stopped"),
    ]:
        records.append(ev("aws", "cloud_assets", "ec2_instances", iid, {
            "instance_id": iid, "instance_type": itype, "state": state,
            "region": "us-east-1", "public_ip": None if state == "stopped" else "1.2.3.4",
        }, age_days=1))

    # GitHub
    for name, private, protected in [
        ("backend", True, True), ("frontend", True, True), ("infra", True, True),
        ("mobile", True, True), ("data-pipeline", True, True), ("docs", False, False),
        ("marketing-site", False, False),
    ]:
        records.append(ev("github", "change_management", "repositories", f"gh_{name}", {
            "name": name, "full_name": f"acme-corp/{name}", "private": private,
            "default_branch": "main", "branch_protection_enabled": protected,
            "updated_at": (now - timedelta(days=1)).isoformat(),
        }, age_days=2))
    for login in ["alice", "bob", "carol", "dave", "eve", "frank", "grace", "ivan", "julia"]:
        records.append(ev("github", "access_control", "github_members", login, {
            "login": login, "id": abs(hash(login)) % 99999, "type": "User", "site_admin": False,
        }))

    # Slack
    for email, uid, admin, tfa in [
        ("alice@acme.com", "U001", True, True), ("bob@acme.com", "U002", False, True),
        ("carol@acme.com", "U003", True, True), ("dave@acme.com", "U004", False, False),
        ("eve@acme.com", "U005", False, True), ("frank@acme.com", "U006", False, False),
        ("grace@acme.com", "U007", False, True), ("ivan@acme.com", "U008", True, True),
        ("henry@acme.com", "U009", False, False), ("julia@acme.com", "U010", False, True),
    ]:
        records.append(ev("slack", "access_control", "slack_users", uid, {
            "id": uid, "email": email, "is_admin": admin,
            "two_factor_enabled": tfa, "is_bot": False,
        }))

    # Okta
    for email, uid, mfa, status in [
        ("alice@acme.com", "ok1", True, "ACTIVE"), ("bob@acme.com", "ok2", True, "ACTIVE"),
        ("carol@acme.com", "ok3", True, "ACTIVE"), ("dave@acme.com", "ok4", False, "ACTIVE"),
        ("eve@acme.com", "ok5", True, "ACTIVE"), ("frank@acme.com", "ok6", False, "ACTIVE"),
        ("grace@acme.com", "ok7", True, "ACTIVE"), ("henry@acme.com", "ok8", False, "SUSPENDED"),
        ("ivan@acme.com", "ok9", True, "ACTIVE"), ("julia@acme.com", "ok10", True, "ACTIVE"),
    ]:
        records.append(ev("okta", "access_control", "okta_users", uid, {
            "login": email, "status": status, "mfa_enrolled": mfa,
            "last_login": (now - timedelta(days=2)).isoformat(),
        }))
    for name, gid, count in [
        ("Engineering", "og1", 8), ("Sales", "og2", 5), ("Finance", "og3", 4),
        ("HR", "og4", 3), ("Leadership", "og5", 3),
    ]:
        records.append(ev("okta", "access_control", "okta_groups", gid, {
            "name": name, "type": "OKTA_GROUP", "member_count": count,
        }, age_days=2))

    # Google Workspace
    for email, uid, admin, suspended in [
        ("alice@acme.com", "gw1", True, False), ("bob@acme.com", "gw2", False, False),
        ("carol@acme.com", "gw3", True, False), ("dave@acme.com", "gw4", False, False),
        ("eve@acme.com", "gw5", False, False), ("frank@acme.com", "gw6", False, False),
        ("grace@acme.com", "gw7", False, False), ("henry@acme.com", "gw8", False, True),
        ("ivan@acme.com", "gw9", True, False), ("julia@acme.com", "gw10", False, False),
    ]:
        records.append(ev("google_workspace", "access_control", "workspace_users", uid, {
            "email": email, "is_admin": admin, "suspended": suspended,
            "two_step_verification": not suspended,
            "last_login_time": (now - timedelta(days=1)).isoformat(),
        }))

    # Azure AD
    for upn, uid, enabled in [
        ("alice@acme.onmicrosoft.com", "az1", True), ("carol@acme.onmicrosoft.com", "az2", True),
        ("ivan@acme.onmicrosoft.com", "az3", True), ("henry@acme.onmicrosoft.com", "az4", False),
        ("grace@acme.onmicrosoft.com", "az5", True), ("frank@acme.onmicrosoft.com", "az6", True),
        ("julia@acme.onmicrosoft.com", "az7", True),
    ]:
        records.append(ev("azure_ad", "access_control", "azure_users", uid, {
            "userPrincipalName": upn, "accountEnabled": enabled,
            "mfaRegistered": enabled,
            "lastSignInDateTime": (now - timedelta(days=1)).isoformat(),
            "assignedLicenses": [{"skuId": "M365_E3"}] if enabled else [],
        }))

    # Jira
    for key, name in [
        ("BACK", "Backend"), ("FRONT", "Frontend"), ("MOB", "Mobile"),
        ("OPS", "Infrastructure"), ("SEC", "Security"), ("DATA", "Data"), ("MKTG", "Marketing"),
    ]:
        records.append(ev("jira", "change_management", "jira_projects", f"jira_{key}", {
            "key": key, "name": name, "lead_email": "carol@acme.com",
            "issue_count": abs(hash(key)) % 120 + 20,
        }, age_days=2))
    for email, uid, active in [
        ("alice@acme.com", "ju1", True), ("bob@acme.com", "ju2", True),
        ("carol@acme.com", "ju3", True), ("dave@acme.com", "ju4", True),
        ("eve@acme.com", "ju5", True), ("frank@acme.com", "ju6", True),
        ("henry@acme.com", "ju7", False),
    ]:
        records.append(ev("jira", "access_control", "jira_users", uid, {
            "email": email, "active": active, "account_type": "atlassian",
        }))

    # GitLab
    for name, private, protected in [
        ("ops-scripts", True, True), ("legacy-api", True, False), ("devops-tools", True, True),
    ]:
        records.append(ev("gitlab", "change_management", "repositories", f"gl_{name}", {
            "name": name, "path_with_namespace": f"acme-corp/{name}",
            "visibility": "private" if private else "public",
            "default_branch": "main", "protected_branches": [{"name": "main"}] if protected else [],
        }, age_days=2))

    # Bitbucket
    for name, private, protected in [
        ("ops-scripts", True, True), ("legacy-portal", True, False),
        ("terraform-infra", True, True), ("api-gateway", True, True),
    ]:
        records.append(ev("bitbucket", "change_management", "bitbucket_repos", f"bb_{name}", {
            "name": name, "private": private, "mainBranch": "main", "branchProtected": protected,
        }, age_days=1))

    # Datadog
    for check, status in [
        ("CPU usage < 80%", "OK"), ("Memory usage < 85%", "OK"),
        ("Error rate < 1%", "ALERT"), ("API p99 latency < 500ms", "OK"),
        ("DB connection pool healthy", "OK"), ("Disk usage < 90%", "WARN"),
    ]:
        records.append(ev("datadog", "logging_monitoring", "datadog_monitors", f"dd_{abs(hash(check))%9999}", {
            "name": check, "status": status, "type": "metric alert",
        }, age_days=0))

    # Snyk
    snyk_vulns = [
        ("snyk-1", "jsonwebtoken", "8.5.1", "Algorithm confusion attack", "critical", "backend", "open"),
        ("snyk-2", "lodash", "4.17.19", "Prototype Pollution", "high", "backend", "fixed"),
        ("snyk-3", "axios", "0.21.1", "SSRF", "high", "frontend", "fixed"),
        ("snyk-4", "semver", "5.7.1", "ReDoS", "medium", "data-pipeline", "open"),
        ("snyk-5", "pyyaml", "5.3.1", "Arbitrary Code Execution", "high", "data-pipeline", "open"),
        ("snyk-6", "word-wrap", "1.2.3", "Prototype Pollution", "medium", "mobile", "open"),
        ("snyk-7", "minimatch", "3.0.4", "ReDoS", "high", "infra", "fixed"),
        ("snyk-8", "tough-cookie", "2.5.0", "Prototype Pollution", "medium", "backend", "open"),
    ]
    for sid, pkg, version, title, severity, project, status in snyk_vulns:
        records.append(ev("snyk", "vulnerability_management", "snyk_vulnerabilities", sid, {
            "id": sid, "title": title, "packageName": pkg, "version": version,
            "severity": severity, "project": project, "status": status,
        }, age_days=1))

    # Wiz
    wiz_issues = [
        ("wiz-1", "S3 bucket allows public access", "CRITICAL", "acme-staging", "RESOLVED"),
        ("wiz-2", "EC2 instance with public IP and no WAF", "HIGH", "prod-api-01", "OPEN"),
        ("wiz-3", "RDS not encrypted at rest", "HIGH", "prod-db", "RESOLVED"),
        ("wiz-4", "IAM role with wildcard permissions", "HIGH", "ci-runner-role", "IN_PROGRESS"),
        ("wiz-5", "Container running as root", "MEDIUM", "data-pipeline", "OPEN"),
        ("wiz-6", "Secret exposed in env var", "CRITICAL", "prod-api-02", "RESOLVED"),
        ("wiz-7", "CloudTrail not enabled in all regions", "MEDIUM", "global", "RESOLVED"),
        ("wiz-8", "Network ACL allows all inbound traffic", "HIGH", "prod-vpc", "IN_PROGRESS"),
    ]
    for wid, title, severity, resource, status in wiz_issues:
        records.append(ev("wiz", "vulnerability_management", "wiz_issues", wid, {
            "id": wid, "title": title, "severity": severity,
            "resourceName": resource, "status": status, "cloudPlatform": "AWS",
        }, age_days=1))

    # KnowBe4
    for email, uid, completed, score, failures in [
        ("alice@acme.com", "kb4-1", True, 100, 0), ("bob@acme.com", "kb4-2", True, 95, 0),
        ("carol@acme.com", "kb4-3", True, 100, 0), ("dave@acme.com", "kb4-4", False, 60, 1),
        ("eve@acme.com", "kb4-5", True, 100, 0), ("frank@acme.com", "kb4-6", False, 40, 3),
        ("grace@acme.com", "kb4-7", True, 90, 1), ("henry@acme.com", "kb4-8", False, 0, 0),
        ("ivan@acme.com", "kb4-9", True, 100, 0), ("julia@acme.com", "kb4-10", True, 100, 0),
    ]:
        records.append(ev("knowbe4", "security_awareness", "knowbe4_users", uid, {
            "email": email, "trainingCompleted": completed,
            "currentTrainingScore": score, "phishingTestFailures": failures,
        }))

    # Splunk
    for sid, title, severity, status in [
        ("sp-1", "Multiple Failed Login Attempts", "HIGH", "Triggered"),
        ("sp-2", "Privileged Account Activity Outside Hours", "HIGH", "Triggered"),
        ("sp-3", "Large Data Export Detected", "MEDIUM", "Resolved"),
        ("sp-4", "New Admin Account Created", "MEDIUM", "Resolved"),
        ("sp-5", "Container Escape Attempt", "CRITICAL", "Resolved"),
        ("sp-6", "Outbound Traffic Anomaly", "HIGH", "Investigating"),
    ]:
        records.append(ev("splunk", "logging_monitoring", "splunk_alerts", sid, {
            "alertId": sid, "alertName": title, "severity": severity, "status": status,
        }, age_days=1))

    # New Relic
    for nid, name, uptime, p99, error_rate, health in [
        ("nr-1", "backend-api", 99.97, 142, 0.08, "healthy"),
        ("nr-2", "data-pipeline", 99.45, 312, 0.45, "warning"),
        ("nr-3", "auth-service", 99.99, 89, 0.02, "healthy"),
        ("nr-4", "frontend", 99.98, 68, 0.05, "healthy"),
        ("nr-5", "mobile-api", 99.91, 198, 0.18, "healthy"),
    ]:
        records.append(ev("new_relic", "logging_monitoring", "newrelic_services", nid, {
            "name": name, "uptimePercent": uptime, "responseTimeP99Ms": p99,
            "errorRate": error_rate, "healthStatus": health,
        }, age_days=0))

    # Qualys
    for qid, title, severity, host, status in [
        ("qid-1", "TLS 1.0/1.1 Protocol Detected", "CRITICAL", "legacy-portal.acme.com", "OPEN"),
        ("qid-2", "OpenSSH < 9.3 Multiple Vulnerabilities", "HIGH", "bastion-01.acme.com", "IN_PROGRESS"),
        ("qid-3", "Apache RCE CVE-2023-25690", "HIGH", "internal-wiki.acme.com", "FIXED"),
        ("qid-4", "WordPress Core XSS", "MEDIUM", "marketing.acme.com", "OPEN"),
        ("qid-5", "Expired SSL Certificate", "MEDIUM", "staging.acme.com", "OPEN"),
    ]:
        records.append(ev("qualys", "vulnerability_management", "qualys_vulnerabilities", qid, {
            "id": qid, "title": title, "severity": severity, "host": host, "status": status,
        }, age_days=1))

    # Cloudflare WAF
    records.append(ev("cloudflare", "logging_monitoring", "cloudflare_waf", "cf_waf_001", {
        "zone": "acme.com", "waf_enabled": True, "ddos_protection": True,
        "firewall_rules": 12, "blocked_requests_24h": 847,
    }, age_days=0))

    # BambooHR
    for eid, email, dept, status in [
        ("bhr-1", "alice@acme.com", "Engineering", "Active"),
        ("bhr-2", "bob@acme.com", "Engineering", "Active"),
        ("bhr-3", "carol@acme.com", "Security", "Active"),
        ("bhr-4", "henry@acme.com", "Engineering", "Terminated"),
        ("bhr-5", "julia@acme.com", "HR", "Active"),
    ]:
        records.append(ev("bamboohr", "hr", "bamboohr_employees", eid, {
            "id": eid, "email": email, "department": dept,
            "status": status, "hireDate": "2024-01-15",
        }, age_days=2))

    # Greenhouse
    for gid, title, dept, status, apps in [
        ("ghr-1", "Senior Backend Engineer", "Engineering", "open", 8),
        ("ghr-2", "Security Engineer", "Security", "open", 5),
        ("ghr-3", "Head of Customer Success", "Sales", "open", 12),
        ("ghr-4", "DevOps Engineer", "Engineering", "closed", 3),
    ]:
        records.append(ev("greenhouse", "hr", "greenhouse_jobs", gid, {
            "jobId": gid, "title": title, "department": dept,
            "status": status, "applications": apps,
        }, age_days=2))

    # Checkr
    for cid_check, email, name, status in [
        ("ck-1", "alice@acme.com", "Alice Smith", "clear"),
        ("ck-2", "bob@acme.com", "Bob Jones", "clear"),
        ("ck-3", "carol@acme.com", "Carol White", "clear"),
        ("ck-4", "frank@acme.com", "Frank Miller", "clear"),
        ("ck-5", "grace@acme.com", "Grace Wilson", "pending"),
    ]:
        records.append(ev("checkr", "hr", "checkr_reports", cid_check, {
            "reportId": cid_check, "candidateEmail": email,
            "candidateName": name, "status": status, "packageType": "employee_pro",
        }, age_days=3))

    # Stripe
    records.append(ev("stripe", "customer_data", "stripe_summary", "stripe-summary-001", {
        "totalCustomers": 47, "activeSubscriptions": 41,
        "mrr": 38400, "currency": "usd",
        "planBreakdown": {"growth": 29, "enterprise": 12},
    }, age_days=0))

    # HubSpot
    for hid, name, amount, stage in [
        ("hs-1", "Acme Corp — Enterprise Annual", 75000, "closedwon"),
        ("hs-2", "Globex Corp — Growth Plan", 18000, "closedwon"),
        ("hs-3", "Initech — Enterprise Evaluation", 60000, "presentationscheduled"),
        ("hs-4", "Hooli — Enterprise Annual", 90000, "contractsent"),
    ]:
        records.append(ev("hubspot", "customer_data", "hubspot_deals", hid, {
            "dealId": hid, "dealName": name, "amount": amount, "dealStage": stage,
        }, age_days=2))

    # Zendesk
    for tid, subject, priority, status in [
        ("zd-1", "Unable to export compliance report", "normal", "open"),
        ("zd-2", "2FA setup not working", "urgent", "solved"),
        ("zd-3", "DSAR data export request", "high", "pending"),
        ("zd-4", "Azure AD integration failing", "high", "open"),
        ("zd-5", "SOC 2 evidence package download broken", "urgent", "open"),
    ]:
        records.append(ev("zendesk", "logging_monitoring", "zendesk_tickets", tid, {
            "id": tid, "subject": subject, "priority": priority, "status": status,
        }, age_days=1))

    # Intercom
    for iid, email, name, plan, status in [
        ("ic-1", "alice@customer.com", "Alice Chen", "Enterprise", "Active"),
        ("ic-2", "bob@startup.io", "Bob Martinez", "Growth", "Active"),
        ("ic-3", "carol@corp.com", "Carol Lewis", "Enterprise", "Active"),
        ("ic-4", "eve@bigco.com", "Eve Johnson", "Enterprise", "Active"),
    ]:
        records.append(ev("intercom", "customer_data", "intercom_contacts", iid, {
            "contactId": iid, "email": email, "name": name, "plan": plan, "status": status,
        }, age_days=2))

    # SendGrid
    records.append(ev("sendgrid", "logging_monitoring", "sendgrid_stats", "sg-stats-today", {
        "requests": 1842, "delivered": 1799, "opens": 634, "clicks": 128,
        "bounces": 12, "deliveryRate": 97.7, "openRate": 35.2,
    }, age_days=0))

    # Vercel
    records.append(ev("vercel", "cloud_assets", "vercel_deployments", "vercel-deploy-001", {
        "projectName": "tracelayer-frontend",
        "deployments": 24, "lastDeployedAt": (now - timedelta(hours=3)).isoformat(),
        "status": "Ready", "framework": "nextjs",
    }, age_days=0))

    # Asana
    for aid, name, status, team in [
        ("as-1", "ISO 27001 Certification Roadmap", "in_progress", "Engineering"),
        ("as-2", "Q1 2026 Security Sprint", "completed", "Engineering"),
        ("as-3", "GDPR Data Mapping Project", "in_progress", "Legal"),
        ("as-4", "Vendor Risk Review 2026", "in_progress", "Security"),
    ]:
        records.append(ev("asana", "change_management", "asana_projects", aid, {
            "projectId": aid, "name": name, "status": status, "team": team,
        }, age_days=1))

    # Rippling (HR)
    for rid, email, dept, status in [
        ("rip-1", "alice@acme.com", "Engineering", "active"),
        ("rip-2", "carol@acme.com", "Security", "active"),
        ("rip-3", "henry@acme.com", "Engineering", "terminated"),
        ("rip-4", "ivan@acme.com", "Leadership", "active"),
        ("rip-5", "julia@acme.com", "HR", "active"),
    ]:
        records.append(ev("rippling", "hr", "rippling_employees", rid, {
            "id": rid, "email": email, "department": dept, "status": status,
        }, age_days=2))

    # Sentry
    for sid, title, level, project in [
        ("se-1", "TypeError: Cannot read properties of null", "error", "backend-api"),
        ("se-2", "UnhandledPromiseRejection in payment flow", "error", "frontend"),
        ("se-3", "Rate limit exceeded on external API", "warning", "data-pipeline"),
    ]:
        records.append(ev("sentry", "logging_monitoring", "sentry_issues", sid, {
            "id": sid, "title": title, "level": level, "project": project,
            "count": abs(hash(sid)) % 500 + 10, "firstSeen": (now - timedelta(days=5)).isoformat(),
        }, age_days=1))

    # PagerDuty
    for pid, title, severity, status in [
        ("pd-1", "API p99 latency > 500ms", "critical", "resolved"),
        ("pd-2", "Database CPU > 90%", "warning", "resolved"),
        ("pd-3", "Error rate spike in data-pipeline", "error", "resolved"),
    ]:
        records.append(ev("pagerduty", "logging_monitoring", "pagerduty_incidents", pid, {
            "id": pid, "title": title, "urgency": severity, "status": status,
        }, age_days=3))

    # Terraform Cloud
    records.append(ev("terraform_cloud", "change_management", "terraform_runs", "tf-run-001", {
        "workspaceName": "acme-production", "runId": "tf-run-001",
        "status": "applied", "triggeredBy": "carol@acme.com",
        "createdAt": (now - timedelta(days=1)).isoformat(),
        "resourcesChanged": 3,
    }, age_days=1))

    # 1Password
    records.append(ev("1password", "access_control", "onepassword_vaults", "1p-vault-001", {
        "vaultName": "Production Secrets",
        "itemCount": 142, "memberCount": 8,
        "lastActivityAt": (now - timedelta(hours=2)).isoformat(),
    }, age_days=0))

    # ── SOC 2 COMPLETENESS — covers all 12 control categories at 90%+ ─────────
    # Ensures every expected evidence type in EXPECTED_TYPES["soc2"] is present
    # with fresh timestamps (age_days=0/1) and 10+ records per category.

    # control_environment: iam_policies, okta_policies, github_repositories, azure_roles
    for n, name, admin in [(1,"AdministratorAccess",True),(2,"SecurityAudit",False),(3,"IAMReadOnly",False)]:
        records.append(ev("aws","control_environment","iam_policies",f"ce_iam_{n}",{"policy_name":name,"admin_policy":admin,"scope":"governance"},age_days=1))
    for n, name in [(1,"MFA-Enforcement"),(2,"Password-Complexity"),(3,"Session-Timeout")]:
        records.append(ev("okta","control_environment","okta_policies",f"ce_okta_{n}",{"name":name,"status":"ACTIVE","type":"PASSWORD","priority":n},age_days=1))
    for n, name in [(1,"backend"),(2,"infrastructure"),(3,"security-config")]:
        records.append(ev("github","control_environment","github_repositories",f"ce_repo_{n}",{"name":name,"full_name":f"acme-corp/{name}","private":True,"branch_protection":True,"default_branch":"main"},age_days=1))
    for n, name, count in [(1,"GlobalAdmin",2),(2,"SecurityReader",4),(3,"ComplianceManager",2),(4,"AuditReader",6)]:
        records.append(ev("azure_ad","control_environment","azure_roles",f"ce_azr_{n}",{"displayName":name,"isBuiltIn":True,"isEnabled":True,"memberCount":count},age_days=1))

    # risk_assessment: vulnerability_scans, wiz_issues, snyk_projects, iam_policies
    for n, sev, title in [(1,"LOW","S3 public read (resolved)"),(2,"MEDIUM","IAM key rotation"),(3,"LOW","Security group egress"),(4,"LOW","CloudTrail gap")]:
        records.append(ev("aws","risk_assessment","vulnerability_scans",f"ra_scan_{n}",{"finding_id":f"SCAN-{n:04d}","severity":sev,"title":title,"status":"resolved"},age_days=0))
    for n, title, sev in [(1,"Overpermissive IAM role","HIGH"),(2,"Unencrypted S3 bucket","MEDIUM"),(3,"Missing MFA privileged","CRITICAL")]:
        records.append(ev("wiz","risk_assessment","wiz_issues",f"ra_wiz_{n}",{"issue_id":f"WIZ-RA-{n:04d}","title":title,"severity":sev,"status":"RESOLVED"},age_days=0))
    for n, pkg, sev in [(1,"lodash","HIGH"),(2,"express","MEDIUM"),(3,"axios","LOW"),(4,"react","LOW")]:
        records.append(ev("snyk","risk_assessment","snyk_projects",f"ra_snyk_{n}",{"project_name":f"acme/{pkg}","severity":sev,"issue_count":n,"last_tested":now.isoformat()},age_days=0))
    for n, name in [(1,"RiskAssessmentPolicy"),(2,"SecurityBaseline"),(3,"ComplianceControls")]:
        records.append(ev("aws","risk_assessment","iam_policies",f"ra_iam_{n}",{"policy_name":name,"risk_reviewed":True,"last_reviewed":now.isoformat()},age_days=0))

    # access_control additions: github_admin_members, workspace_admin_members, okta_policies, azure_roles
    for n, login in enumerate(["carol","ivan"],1):
        records.append(ev("github","access_control","github_admin_members",f"ac_admin_{n}",{"login":login,"id":abs(hash(login))%99999,"role":"admin","site_admin":False},age_days=0))
    for n, email in enumerate(["alice@acme.com","carol@acme.com","ivan@acme.com"],1):
        records.append(ev("google_workspace","access_control","workspace_admin_members",f"ac_wsadm_{n}",{"primaryEmail":email,"isAdmin":True,"isSuperAdmin":n==1},age_days=0))
    for n, name in [(1,"MFA-Enforcement"),(2,"Password-Policy"),(3,"SSO-Policy")]:
        records.append(ev("okta","access_control","okta_policies",f"ac_opol_{n}",{"name":name,"status":"ACTIVE","type":"PASSWORD"},age_days=0))
    for n, name, count in [(1,"GlobalAdmin",2),(2,"Contributor",8),(3,"Reader",12)]:
        records.append(ev("azure_ad","access_control","azure_roles",f"ac_azr_{n}",{"displayName":name,"isBuiltIn":True,"isEnabled":True,"memberCount":count},age_days=0))

    # privileged_access: iam_policies, okta_groups, azure_roles, github_admin_members, vault_policy, vault_auth_method
    for n, name in [(1,"AdministratorAccess"),(2,"IAMFullAccess")]:
        records.append(ev("aws","privileged_access","iam_policies",f"pa_iam_{n}",{"policy_name":name,"admin_policy":True,"privileged":True,"attached_entities":2},age_days=0))
    for n, name in [(1,"admins"),(2,"security-ops"),(3,"leadership")]:
        records.append(ev("okta","privileged_access","okta_groups",f"pa_ogrp_{n}",{"id":f"pa_grp_{n}","name":name,"privileged":True,"member_count":n},age_days=0))
    for n, name in [(1,"GlobalAdmin"),(2,"PrivilegedRoleAdmin")]:
        records.append(ev("azure_ad","privileged_access","azure_roles",f"pa_azr_{n}",{"displayName":name,"isBuiltIn":True,"isEnabled":True,"memberCount":n},age_days=0))
    records.append(ev("github","privileged_access","github_admin_members","pa_admin_carol",{"login":"carol","role":"admin","site_admin":False},age_days=0))
    for n, name, path in [(1,"engineering","/secret/prod/*"),(2,"security","/secret/*"),(3,"readonly","/secret/+/config")]:
        records.append(ev("vault","privileged_access","vault_policy",f"pa_vpol_{n}",{"name":name,"policies":[path],"capabilities":["read","list"]},age_days=0))
    for n, method in [(1,"github"),(2,"kubernetes")]:
        records.append(ev("vault","privileged_access","vault_auth_method",f"pa_vauth_{n}",{"type":method,"path":f"{method}/","enabled":True},age_days=0))

    # logging_monitoring additions: datadog_logs, splunk_saved_searches, crowdstrike_detections, sentinelone_threats, wiz_issues
    for n, svc, lvl in [(1,"api-server","INFO"),(2,"auth-service","WARN"),(3,"data-pipeline","INFO"),(4,"gateway","INFO"),(5,"worker","INFO")]:
        records.append(ev("datadog","logging_monitoring","datadog_logs",f"lm_ddlog_{n}",{"service":svc,"status":lvl,"count_24h":n*1200,"indexed":True},age_days=0))
    for n, name, schedule in [(1,"Security Event Summary","cron(0 */6 * * *)"),(2,"Auth Failures","cron(*/15 * * * *)"),(3,"Privilege Audit","cron(0 0 * * *)"),(4,"Data Exfil","cron(*/5 * * * *)")]:
        records.append(ev("splunk","logging_monitoring","splunk_saved_searches",f"lm_spsearch_{n}",{"name":name,"search":"index=main | stats count","cron_schedule":schedule,"is_scheduled":True},age_days=0))
    for n, host, sev in [(1,"web-server-01","medium"),(2,"worker-02","low"),(3,"db-replica-01","low"),(4,"api-server-03","low"),(5,"batch-01","low")]:
        records.append(ev("crowdstrike","logging_monitoring","crowdstrike_detections",f"lm_csdet_{n}",{"detection_id":f"ldt:{n:04d}","hostname":host,"severity":sev,"status":"closed","resolved":True},age_days=0))
    for n, host, threat in [(1,"endpoint-mac-001","PUP.Optional"),(2,"endpoint-mac-002","Adware.Gen"),(3,"endpoint-mac-003","Potentially.Unwanted")]:
        records.append(ev("sentinelone","logging_monitoring","sentinelone_threats",f"lm_s1thr_{n}",{"threat_id":f"s1thr_{n}","agent_computer_name":host,"classification":threat,"mitigated":True},age_days=0))
    for n, title, sev in [(1,"Public S3 (remediated)","HIGH"),(2,"Unpatched container image","MEDIUM"),(3,"Network exposure resolved","HIGH")]:
        records.append(ev("wiz","logging_monitoring","wiz_issues",f"lm_wiz_{n}",{"issue_id":f"WIZ-LM-{n:04d}","title":title,"severity":sev,"status":"RESOLVED"},age_days=0))

    # incident_response: pagerduty_incidents, pagerduty_services, pagerduty_escalation_policies,
    #                    servicenow_incidents, opsgenie_alerts, opsgenie_schedules, opsgenie_escalations
    for n, title, urgency in [(1,"API latency spike","low"),(2,"DB failover triggered","high"),(3,"Cert expiry warning","low"),(4,"Deploy failure auto-rollback","high"),(5,"Scheduled maintenance","low")]:
        records.append(ev("pagerduty","incident_response","pagerduty_incidents",f"ir_pdinc_{n}",{"id":f"P{n:06d}","title":title,"urgency":urgency,"status":"resolved"},age_days=1))
    for n, name, kind in [(1,"API Gateway","web"),(2,"Auth Service","web"),(3,"Background Workers","worker")]:
        records.append(ev("pagerduty","incident_response","pagerduty_services",f"ir_pdsvc_{n}",{"id":f"SVC{n:04d}","name":name,"type":kind,"status":"active"},age_days=1))
    for n, name in [(1,"Engineering On-Call"),(2,"Security Incident Response")]:
        records.append(ev("pagerduty","incident_response","pagerduty_escalation_policies",f"ir_pdesc_{n}",{"id":f"ESC{n:04d}","name":name,"num_loops":3},age_days=1))
    for n, short, cat in [(1,"INC0001234","inquiry"),(2,"INC0001235","security"),(3,"INC0001236","network"),(4,"INC0001237","application")]:
        records.append(ev("servicenow","incident_response","servicenow_incidents",f"ir_sninc_{n}",{"number":short,"category":cat,"state":"closed","priority":"3 - Moderate"},age_days=1))
    for n, msg, pri in [(1,"High CPU on api-server-01","P3"),(2,"Memory threshold exceeded","P4"),(3,"SSL cert expiry in 14d","P4"),(4,"Disk usage above 85%","P3")]:
        records.append(ev("opsgenie","incident_response","opsgenie_alerts",f"ir_ogalert_{n}",{"id":f"og_alert_{n}","message":msg,"priority":pri,"status":"closed"},age_days=1))
    for n, name in [(1,"Engineering Rotation"),(2,"Security On-Call")]:
        records.append(ev("opsgenie","incident_response","opsgenie_schedules",f"ir_ogsched_{n}",{"id":f"og_sched_{n}","name":name,"enabled":True,"rotation_period":"weekly"},age_days=1))
    for n, name in [(1,"Default Escalation"),(2,"Security Escalation")]:
        records.append(ev("opsgenie","incident_response","opsgenie_escalations",f"ir_ogesc_{n}",{"id":f"og_esc_{n}","name":name,"rules":[{"condition":"if-not-acked","delay":10}]},age_days=1))

    # change_management additions: github_repositories, gitlab_repositories, servicenow_changes
    # (existing "repositories" type doesn't count — adding "github_repositories" and "gitlab_repositories")
    for n, name, priv in [(1,"backend",True),(2,"frontend",True),(3,"infrastructure",True),(4,"data-platform",True),(5,"mobile-app",True)]:
        records.append(ev("github","change_management","github_repositories",f"cm_ghrepo_{n}",{"name":name,"full_name":f"acme-corp/{name}","private":priv,"branch_protection_enabled":True,"default_branch":"main","updated_at":now.isoformat()},age_days=0))
    for n, name in [(1,"ops-scripts"),(2,"legacy-api"),(3,"devops-tools")]:
        records.append(ev("gitlab","change_management","gitlab_repositories",f"cm_glrepo_{n}",{"name":name,"path_with_namespace":f"acme-corp/{name}","visibility":"private","default_branch":"main","last_activity_at":now.isoformat()},age_days=0))
    for n, number, cat in [(1,"CHG0000101","normal"),(2,"CHG0000102","standard"),(3,"CHG0000103","emergency"),(4,"CHG0000104","normal")]:
        records.append(ev("servicenow","change_management","servicenow_changes",f"cm_snchg_{n}",{"number":number,"category":cat,"state":"closed","cab_approval":n!=3,"implemented_at":now.isoformat()},age_days=0))

    # endpoint_security: crowdstrike_devices, crowdstrike_policies, sentinelone_agents,
    #                    jamf_computers, jamf_policies, kandji_devices, kandji_blueprints
    for n, host, os_type in [(1,"macbook-alice","macOS 14.4"),(2,"macbook-bob","macOS 14.4"),(3,"macbook-carol","macOS 14.4"),(4,"macbook-dave","macOS 14.3"),(5,"linux-server-01","Ubuntu 22.04"),(6,"linux-server-02","Ubuntu 22.04"),(7,"linux-worker-01","Ubuntu 22.04"),(8,"linux-worker-02","Ubuntu 22.04")]:
        records.append(ev("crowdstrike","endpoint_security","crowdstrike_devices",f"ep_csdev_{n}",{"device_id":f"cs_{n:04d}","hostname":host,"status":"normal","os_version":os_type,"last_seen":now.isoformat(),"prevention_policy_applied":True},age_days=0))
    for n, name in [(1,"Prevention Policy - Mac"),(2,"Prevention Policy - Linux"),(3,"Detection Policy")]:
        records.append(ev("crowdstrike","endpoint_security","crowdstrike_policies",f"ep_cspol_{n}",{"id":f"csp_{n:04d}","name":name,"enabled":True},age_days=0))
    for n, host in enumerate(["macbook-alice","macbook-bob","macbook-carol","macbook-dave","macbook-eve","macbook-frank","macbook-grace","macbook-ivan"],1):
        records.append(ev("sentinelone","endpoint_security","sentinelone_agents",f"ep_s1agent_{n}",{"agent_id":f"s1_{n:04d}","computer_name":host,"os_type":"macos","agent_version":"23.4.2","is_active":True},age_days=0))
    for n, serial in enumerate(["C02XDEMO0001","C02XDEMO0002","C02XDEMO0003","C02XDEMO0004","C02XDEMO0005","C02XDEMO0006","C02XDEMO0007","C02XDEMO0008"],1):
        records.append(ev("jamf","endpoint_security","jamf_computers",serial,{"serialNumber":serial,"model":"MacBook Pro","managed":True,"lastContactTime":now.isoformat()},age_days=0))
    for n, name in [(1,"Security Baseline"),(2,"Encryption Policy"),(3,"Screen Lock Policy")]:
        records.append(ev("jamf","endpoint_security","jamf_policies",f"ep_jamfpol_{n}",{"id":n*100,"name":name,"enabled":True,"scope_all_computers":True},age_days=0))
    for n, serial in enumerate(["KANDJI-001","KANDJI-002","KANDJI-003","KANDJI-004","KANDJI-005","KANDJI-006","KANDJI-007","KANDJI-008"],1):
        records.append(ev("kandji","endpoint_security","kandji_devices",serial,{"device_id":serial,"serial_number":serial,"model":"MacBook Pro","blueprints":["Security Baseline"],"is_missing":False,"last_check_in":now.isoformat()},age_days=0))
    for n, name in [(1,"Security Baseline"),(2,"Engineering Devices")]:
        records.append(ev("kandji","endpoint_security","kandji_blueprints",f"ep_kbp_{n}",{"id":f"kbp_{n:04d}","name":name,"device_count":n*5,"is_default":n==1},age_days=0))

    # vulnerability_management additions: snyk_projects, vulnerability_scans, crowdstrike_detections, hackerone_reports
    # (wiz_issues already seeded above — reuse different source_ids)
    for n, pkg, sev in [(1,"backend/api","LOW"),(2,"backend/worker","MEDIUM"),(3,"frontend/next","LOW"),(4,"infra/terraform","LOW")]:
        records.append(ev("snyk","vulnerability_management","snyk_projects",f"vm_snyk_{n}",{"id":f"snyk_{n:04d}","name":f"acme/{pkg}","high_severity_count":0,"medium_severity_count":1 if sev=="MEDIUM" else 0,"last_tested_date":now.isoformat()},age_days=0))
    for n, title, sev in [(1,"OpenSSL CVE-2023-xxxx","MEDIUM"),(2,"Log4j follow-up scan","LOW"),(3,"Container base layer scan","LOW"),(4,"EC2 infrastructure scan","LOW")]:
        records.append(ev("aws","vulnerability_management","vulnerability_scans",f"vm_vscan_{n}",{"finding_id":f"VSCAN-{n:04d}","title":title,"severity":sev,"status":"resolved"},age_days=0))
    for n, host, sev in [(1,"api-server-02","medium"),(2,"worker-03","low"),(3,"batch-server","low")]:
        records.append(ev("crowdstrike","vulnerability_management","crowdstrike_detections",f"vm_csdet_{n}",{"detection_id":f"vm_ldt:{n:04d}","hostname":host,"severity":sev,"status":"closed","resolved":True},age_days=0))
    for n, title, sev, state in [(1,"XSS admin panel (fixed)","medium","resolved"),(2,"Rate limiting bypass (fixed)","high","resolved"),(3,"SQL injection edge case (fixed)","critical","resolved")]:
        records.append(ev("hackerone","vulnerability_management","hackerone_reports",f"vm_h1_{n}",{"id":n*100000,"title":title,"severity":sev,"state":state,"bounty_awarded_amount":n*500},age_days=0))

    # vendor_risk: github_repositories, snyk_projects, wiz_issues, cloudtrail_logs
    for n, name in [(1,"backend-vendor-sdk"),(2,"third-party-api-client"),(3,"analytics-module"),(4,"compliance-data-pipeline")]:
        records.append(ev("github","vendor_risk","github_repositories",f"vr_ghrepo_{n}",{"name":name,"full_name":f"acme-corp/{name}","private":True,"vendor_owned":True},age_days=0))
    for n, pkg in [(1,"vendor-sdk/payments"),(2,"vendor-sdk/auth"),(3,"vendor-sdk/data")]:
        records.append(ev("snyk","vendor_risk","snyk_projects",f"vr_snyk_{n}",{"id":f"vr_snyk_{n:04d}","name":pkg,"last_tested_date":now.isoformat(),"high_severity_count":0,"vendor_dependency":True},age_days=0))
    for n, title in [(1,"Third-party API excessive permissions"),(2,"Vendor container outdated image")]:
        records.append(ev("wiz","vendor_risk","wiz_issues",f"vr_wiz_{n}",{"issue_id":f"WIZ-VR-{n:04d}","title":title,"severity":"MEDIUM","status":"RESOLVED"},age_days=0))
    for n, event in [(1,"GetSecretValue_vendor"),(2,"AssumeRole_vendor"),(3,"ListBuckets_vendor"),(4,"PutObject_vendor")]:
        records.append(ev("aws","vendor_risk","cloudtrail_logs",f"vr_ct_{n}",{"event_name":event.split("_")[0],"user_agent":"vendor-sdk/1.0","source_ip":"10.0.1.100","event_time":now.isoformat()},age_days=0))

    # availability: pagerduty_services, datadog_slos, datadog_monitors, servicenow_changes, vault_secrets_engine
    for n, name, kind in [(1,"API Gateway","web"),(2,"Auth Service","web"),(3,"Background Workers","worker")]:
        records.append(ev("pagerduty","availability","pagerduty_services",f"av_pdsvc_{n}",{"id":f"AV_SVC{n:04d}","name":name,"type":kind,"status":"active","uptime_last_30d":99.95},age_days=0))
    for n, name, slo in [(1,"API Availability SLO",99.9),(2,"Auth SLO",99.95),(3,"Data Pipeline SLO",99.5)]:
        records.append(ev("datadog","availability","datadog_slos",f"av_ddslo_{n}",{"id":f"slo_{n:04d}","name":name,"target":slo,"current":slo+0.04,"status":"ok"},age_days=0))
    for n, name in [(1,"API P99 Latency"),(2,"Error Rate"),(3,"Service Availability")]:
        records.append(ev("datadog","availability","datadog_monitors",f"av_ddmon_{n}",{"id":n*2000,"name":name,"type":"metric alert","status":"OK"},age_days=0))
    for n, number in [(1,"CHG0000201"),(2,"CHG0000202"),(3,"CHG0000203")]:
        records.append(ev("servicenow","availability","servicenow_changes",f"av_snchg_{n}",{"number":number,"category":"normal","state":"closed","availability_impact":"none"},age_days=0))
    for n, name in [(1,"database"),(2,"application"),(3,"certificates")]:
        records.append(ev("vault","availability","vault_secrets_engine",f"av_vse_{n}",{"type":"kv-v2","path":f"{name}/","options":{"version":"2"},"seal_status":"unsealed","ha_enabled":True},age_days=0))

    # confidentiality: iam_policies, vault_secrets_engine, vault_policy, cloudtrail_logs, wiz_issues
    for n, name in [(1,"KMSFullAccess"),(2,"S3EncryptionEnforcement")]:
        records.append(ev("aws","confidentiality","iam_policies",f"conf_iam_{n}",{"policy_name":name,"encryption_related":True,"admin_policy":False},age_days=0))
    for n, path, t in [(1,"pki/","pki"),(2,"transit/","transit")]:
        records.append(ev("vault","confidentiality","vault_secrets_engine",f"conf_vse_{n}",{"type":t,"path":path,"encryption_enabled":True,"auto_rotate":True},age_days=0))
    for n, name in [(1,"encryption-policy"),(2,"tls-management")]:
        records.append(ev("vault","confidentiality","vault_policy",f"conf_vpol_{n}",{"name":name,"policies":[f"/{name}/*"],"capabilities":["read","update","create"]},age_days=0))
    for n, event in [(1,"PutBucketEncryption"),(2,"CreateKey"),(3,"EnableEncryption"),(4,"UpdateEncryption")]:
        records.append(ev("aws","confidentiality","cloudtrail_logs",f"conf_ct_{n}",{"event_name":event,"encryption_event":True,"region":"us-east-1","event_time":now.isoformat()},age_days=0))
    for n, title in [(1,"Unencrypted EBS volume (remediated)"),(2,"RDS encryption not enabled (remediated)")]:
        records.append(ev("wiz","confidentiality","wiz_issues",f"conf_wiz_{n}",{"issue_id":f"WIZ-CONF-{n:04d}","title":title,"severity":"HIGH","status":"RESOLVED"},age_days=0))

    return records


@router.post("/companies/{company_id}/seed-demo", status_code=200)
async def seed_demo_integrations(
    company_id: uuid.UUID,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Seed demo integrations + evidence for a company.
    Safe to re-run — skips existing integrations, upserts evidence.
    """
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    now = datetime.now(timezone.utc)
    added, skipped = [], []

    for itype, creds in _DEMO_INTEGRATIONS:
        existing = await db.execute(
            select(Integration).where(
                Integration.company_id == company_id,
                Integration.integration_type == itype,
            )
        )
        if existing.scalar_one_or_none():
            skipped.append(itype)
        else:
            db.add(Integration(
                id=uuid.uuid4(),
                company_id=company_id,
                integration_type=itype,
                credentials_enc=_enc(creds),
                status="active",
                last_collected_at=now - timedelta(hours=1),
            ))
            added.append(itype)

    await db.flush()

    # Upsert evidence
    evidence = _build_demo_evidence(company_id)
    ev_count = 0
    for r in evidence:
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
        ev_count += 1

    # Seed SOC 2 score history — 90-day upward trend ending at 100
    from sqlalchemy import delete as sa_delete
    await db.execute(
        sa_delete(ScoreSnapshot).where(
            ScoreSnapshot.company_id == company_id,
            ScoreSnapshot.framework == "soc2",
        )
    )
    soc2_trend = [
        (90, 38), (83, 44), (76, 51), (69, 57), (62, 63),
        (55, 68), (48, 72), (41, 78), (34, 83), (27, 88),
        (20, 92), (13, 95), (7, 98), (3, 99), (1, 100),
    ]
    for days_ago, score in soc2_trend:
        db.add(ScoreSnapshot(
            id=uuid.uuid4(),
            company_id=company_id,
            framework="soc2",
            overall_score=score,
            snapshot_at=now - timedelta(days=days_ago),
        ))

    await db.commit()

    return {
        "integrations_added": len(added),
        "integrations_skipped": len(skipped),
        "evidence_upserted": ev_count,
        "added": added,
        "soc2_score_snapshots": len(soc2_trend),
    }
