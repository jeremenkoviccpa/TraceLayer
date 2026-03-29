import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.policy import Policy
from models.user import User
from schemas.policy import PolicyResponse, PolicySaveRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policies", tags=["policies"])

POLICY_TEMPLATES: dict[str, dict] = {
    "information-security": {
        "title": "Information Security Policy",
        "category": "Security",
        "default_content": (
            "This Information Security Policy establishes the framework for protecting "
            "the organization's information assets against unauthorized access, disclosure, "
            "modification, or destruction. All employees, contractors, and third parties with "
            "access to company systems are required to comply with this policy. The policy is "
            "reviewed and approved by management at least annually or following any significant "
            "change in the threat landscape or business operations. Violations of this policy "
            "may result in disciplinary action up to and including termination of employment or "
            "contract. The Chief Information Security Officer (CISO) is responsible for "
            "maintaining, communicating, and enforcing this policy across the organization. "
            "Risk assessments are performed annually to ensure controls remain appropriate and "
            "proportionate to identified threats. Employees receive security awareness training "
            "upon onboarding and at least annually thereafter. This policy is supported by "
            "additional standards, procedures, and guidelines addressing specific security domains."
        ),
    },
    "access-control": {
        "title": "Access Control Policy",
        "category": "Access Control",
        "default_content": (
            "Access to company systems, applications, and data is granted on a least-privilege "
            "basis, providing users with only the permissions required to perform their job "
            "functions. Access rights are requested through a formal provisioning process and "
            "must be approved by the relevant system owner and the employee's manager. "
            "Multi-factor authentication (MFA) is enforced for all user accounts accessing "
            "production systems, administrative consoles, and cloud infrastructure. Privileged "
            "access is strictly controlled, time-limited where possible, and subject to enhanced "
            "monitoring and logging. Access rights are reviewed quarterly for critical systems "
            "and at least annually for all other systems; orphaned or excessive permissions are "
            "revoked promptly. All access is disabled within 24 hours of an employee's departure "
            "or role change. Shared accounts are prohibited except where technically unavoidable, "
            "in which case compensating controls must be documented and approved."
        ),
    },
    "incident-response": {
        "title": "Incident Response Policy",
        "category": "Incident Response",
        "default_content": (
            "This Incident Response Policy defines the organization's approach to detecting, "
            "reporting, investigating, containing, and recovering from security incidents. All "
            "employees are required to report suspected incidents to the security team immediately "
            "via the designated reporting channel. The incident response team follows a structured "
            "lifecycle: Preparation, Identification, Containment, Eradication, Recovery, and "
            "Lessons Learned. Incidents are classified by severity (Critical, High, Medium, Low) "
            "with corresponding response time objectives and escalation paths. Critical and High "
            "severity incidents require executive notification within two hours of confirmation. "
            "Data breach incidents that meet regulatory thresholds trigger mandatory notification "
            "to affected individuals and relevant authorities within legally required timeframes. "
            "Post-incident reviews are conducted for all Critical and High severity incidents, "
            "with findings used to improve detection capabilities and preventive controls. "
            "The incident response plan is tested through tabletop exercises at least annually."
        ),
    },
    "change-management": {
        "title": "Change Management Policy",
        "category": "Change Management",
        "default_content": (
            "All changes to production systems, infrastructure, and applications must follow the "
            "organization's change management process to minimize the risk of unintended disruption "
            "or security vulnerabilities. Changes are categorized as Standard (pre-approved, "
            "low-risk), Normal (requires review and approval), or Emergency (expedited path with "
            "post-implementation review). All code changes require peer code review by at least "
            "one qualified engineer before merging; changes to security-critical components require "
            "review by a senior engineer or security team member. Automated testing, including unit, "
            "integration, and security scans, must pass before any change is promoted to production. "
            "Significant changes require a rollback plan documented prior to deployment. The Change "
            "Advisory Board (CAB) reviews Normal changes weekly. Emergency changes must be "
            "retrospectively reviewed within 48 hours of implementation. All changes are logged "
            "with approver identity, rationale, and implementation details for audit purposes."
        ),
    },
    "data-classification": {
        "title": "Data Classification & Protection Policy",
        "category": "Data Protection",
        "default_content": (
            "The organization classifies all information assets into one of four tiers: Public, "
            "Internal, Confidential, and Restricted. Classification determines the handling, "
            "storage, transmission, and disposal requirements applicable to each asset. Restricted "
            "data — including personal data, payment card data, health records, and credentials — "
            "must be encrypted at rest using AES-256 and in transit using TLS 1.2 or higher. "
            "Confidential data must be encrypted in transit and access must be limited to "
            "authorized personnel with a documented business need. Data owners are responsible "
            "for classifying data within their domain and reviewing classifications annually. "
            "Retention schedules are defined per data category in accordance with legal, "
            "regulatory, and contractual obligations; data must be securely deleted or destroyed "
            "when it reaches end-of-retention. Cross-border transfers of personal data are "
            "subject to additional review to ensure compliance with applicable privacy regulations."
        ),
    },
    "vendor-management": {
        "title": "Vendor Risk Management Policy",
        "category": "Vendor Management",
        "default_content": (
            "Third-party vendors and service providers that access, process, or store company "
            "or customer data must undergo a risk assessment before engagement. Vendors are "
            "categorized as Critical, High, Medium, or Low risk based on data access, operational "
            "dependency, and regulatory exposure. Critical and High-risk vendors must provide "
            "evidence of security certifications (e.g., SOC 2, ISO 27001) or complete a security "
            "questionnaire before contracting. Contracts with vendors handling personal or "
            "confidential data must include data processing agreements, security requirements, "
            "breach notification obligations, and audit rights. Vendor risk reviews are conducted "
            "annually for Critical and High-risk vendors and biennially for Medium-risk vendors. "
            "Any vendor that experiences a security incident affecting company data must notify "
            "the organization within 24 hours. The Vendor Management team maintains an up-to-date "
            "inventory of all active vendors and their risk classifications."
        ),
    },
    "business-continuity": {
        "title": "Business Continuity & DR Policy",
        "category": "Availability",
        "default_content": (
            "The organization maintains a Business Continuity and Disaster Recovery (BC/DR) "
            "program to ensure that critical business functions and systems can be restored "
            "within defined time objectives following a disruptive event. Recovery Time "
            "Objectives (RTO) and Recovery Point Objectives (RPO) are defined for each critical "
            "system and reviewed annually. Production data is backed up daily with backups "
            "retained for a minimum of 30 days; backups are encrypted and stored in a geographically "
            "separate location from primary systems. Backup restoration is tested quarterly to "
            "verify data integrity and recoverability. The full disaster recovery plan is tested "
            "via tabletop exercise annually and via failover test at least every 18 months. "
            "Identified gaps from tests are tracked as remediation items with assigned owners "
            "and target completion dates. All BC/DR documentation is reviewed and updated "
            "annually or following significant changes to business operations or infrastructure."
        ),
    },
    "acceptable-use": {
        "title": "Acceptable Use Policy",
        "category": "Security",
        "default_content": (
            "This Acceptable Use Policy governs the use of company-owned and company-managed "
            "systems, networks, devices, and data by all employees, contractors, and authorized "
            "third parties. Company systems are provided for legitimate business purposes; "
            "incidental personal use is permitted provided it does not interfere with business "
            "operations, consume excessive resources, or violate this policy. Users must not "
            "use company systems to access, store, or transmit illegal content, engage in "
            "harassment or discrimination, circumvent security controls, or conduct personal "
            "commercial activities. Installation of unauthorized software on company devices is "
            "prohibited; all software must be approved and licensed through the IT procurement "
            "process. Users are responsible for maintaining the confidentiality of their "
            "credentials and must not share passwords or authentication tokens. Company systems "
            "are subject to monitoring and logging for security and compliance purposes, and "
            "users should have no expectation of privacy on company-owned devices or networks. "
            "Violations of this policy may result in disciplinary action up to and including termination."
        ),
    },
}


def _build_response(slug: str, saved: Policy | None) -> PolicyResponse:
    template = POLICY_TEMPLATES[slug]
    return PolicyResponse(
        slug=slug,
        title=template["title"],
        category=template["category"],
        content=saved.content if saved else template["default_content"],
        updated_at=saved.updated_at if saved else None,
    )


@router.get("", response_model=list[PolicyResponse])
async def list_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Policy).where(Policy.company_id == current_user.company_id)
    )
    saved_policies = result.scalars().all()
    saved_map = {p.slug: p for p in saved_policies}

    return [_build_response(slug, saved_map.get(slug)) for slug in POLICY_TEMPLATES]


@router.get("/{slug}", response_model=PolicyResponse)
async def get_policy(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if slug not in POLICY_TEMPLATES:
        raise HTTPException(status_code=404, detail="Policy not found")

    result = await db.execute(
        select(Policy).where(
            Policy.company_id == current_user.company_id,
            Policy.slug == slug,
        )
    )
    saved = result.scalar_one_or_none()
    return _build_response(slug, saved)


@router.put("/{slug}", response_model=PolicyResponse)
async def save_policy(
    slug: str,
    body: PolicySaveRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if slug not in POLICY_TEMPLATES:
        raise HTTPException(status_code=404, detail="Policy not found")

    result = await db.execute(
        select(Policy).where(
            Policy.company_id == current_user.company_id,
            Policy.slug == slug,
        )
    )
    policy = result.scalar_one_or_none()

    if policy:
        policy.content = body.content
        policy.updated_by_id = current_user.id
    else:
        policy = Policy(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            slug=slug,
            content=body.content,
            updated_by_id=current_user.id,
        )
        db.add(policy)

    await db.commit()
    await db.refresh(policy)
    return _build_response(slug, policy)


@router.post("/{slug}/generate")
async def generate_policy(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-generate a full policy document for the given slug."""
    if slug not in POLICY_TEMPLATES:
        raise HTTPException(status_code=404, detail="Policy not found")

    from models.company import Company
    from models.integration import Integration
    from services.ai_service import generate_policy_template

    company_result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "Our Company"

    integrations_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    connected = [row[0] for row in integrations_result.all()]

    policy_name = POLICY_TEMPLATES[slug]["title"]
    content = await generate_policy_template(slug, policy_name, company_name, connected)
    return {"content": content}
