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
    id: str
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

    await db.commit()

    return {
        "integrations_added": len(added),
        "integrations_skipped": len(skipped),
        "evidence_upserted": ev_count,
        "added": added,
    }
