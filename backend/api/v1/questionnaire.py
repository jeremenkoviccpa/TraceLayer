import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.plan_gate import require_growth
from models.user import User
from services.ai_service import autofill_questionnaire

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/questionnaire", tags=["questionnaire"])

# ── Questionnaire definitions ─────────────────────────────────────────────────

QUESTIONNAIRE_TYPES: dict[str, dict] = {
    "soc2": {
        "name": "SOC 2 Type II",
        "questions": [
            {
                "id": "soc2_01",
                "question": "Does your organization have a documented information security policy that is reviewed and approved by management at least annually?",
                "answer_template": "Yes, {company_name} maintains a comprehensive Information Security Policy that is reviewed and formally approved by executive management on an annual basis. The policy covers all major security domains including access control, incident response, change management, and vendor risk management.",
            },
            {
                "id": "soc2_02",
                "question": "Do you enforce multi-factor authentication (MFA) for all users accessing production systems and sensitive applications?",
                "answer_template": "Yes, MFA is enforced for all user accounts accessing {company_name}'s production systems, cloud infrastructure, administrative consoles, and sensitive business applications. MFA enforcement is implemented at the identity provider level and cannot be bypassed without an approved exception.",
            },
            {
                "id": "soc2_03",
                "question": "Do you conduct formal background checks on all employees prior to granting access to production systems?",
                "answer_template": "Yes, {company_name} requires background verification for all employees and contractors prior to onboarding. Checks include criminal history, identity verification, and employment history validation, conducted by an accredited third-party screening provider.",
            },
            {
                "id": "soc2_04",
                "question": "Do you have a formal incident response plan, and is it tested at least annually?",
                "answer_template": "Yes, {company_name} maintains a documented Incident Response Plan that defines severity classifications, escalation paths, containment and recovery procedures, and post-incident review requirements. The plan is tested via tabletop exercise at least annually, and findings are tracked and remediated.",
            },
            {
                "id": "soc2_05",
                "question": "How do you manage and review access rights? Are access reviews conducted periodically?",
                "answer_template": "{company_name} conducts formal access reviews on a quarterly basis for critical systems and annually for all other systems. Reviews are performed by system owners and approved by managers. Excess or orphaned access is revoked within five business days of identification.",
            },
            {
                "id": "soc2_06",
                "question": "Do you encrypt data at rest and in transit? What encryption standards do you use?",
                "answer_template": "Yes, {company_name} encrypts all sensitive data at rest using AES-256 and in transit using TLS 1.2 or higher. Encryption key management follows industry best practices, with keys stored in a dedicated secrets management system and rotated on a defined schedule.",
            },
            {
                "id": "soc2_07",
                "question": "Do you perform vulnerability assessments or penetration tests? How frequently?",
                "answer_template": "{company_name} performs automated vulnerability scans continuously as part of the CI/CD pipeline and conducts third-party penetration tests at least annually. Critical and High findings are remediated within defined SLAs. Penetration test reports are available to customers under NDA.",
            },
            {
                "id": "soc2_08",
                "question": "Do you have a formal change management process for production deployments?",
                "answer_template": "Yes, {company_name} follows a documented Change Management Policy. All production changes require peer code review, automated testing, and approval by an authorized reviewer. Emergency changes are expedited through an alternate approval path and subject to post-implementation review within 48 hours.",
            },
            {
                "id": "soc2_09",
                "question": "Do you conduct security awareness training for employees? How often?",
                "answer_template": "Yes, all {company_name} employees complete mandatory security awareness training upon onboarding and at least annually thereafter. Training covers topics including phishing recognition, secure coding practices, data handling, and incident reporting procedures. Completion rates are tracked and reported to management.",
            },
            {
                "id": "soc2_10",
                "question": "Do you have a Business Continuity and Disaster Recovery (BC/DR) plan? When was it last tested?",
                "answer_template": "{company_name} maintains a Business Continuity and Disaster Recovery plan with defined RTOs and RPOs for all critical systems. Daily encrypted backups are stored in a geographically separate location. The plan is tested via tabletop exercise annually and a full failover test is conducted at least every 18 months.",
            },
            {
                "id": "soc2_11",
                "question": "How do you manage third-party vendor risk? Do you assess vendors before engagement?",
                "answer_template": "{company_name} conducts risk assessments for all vendors that access, process, or store company or customer data prior to engagement. Vendors are categorized by risk tier, and Critical/High-risk vendors must provide SOC 2 reports or equivalent security attestations. Contracts include data processing agreements, security obligations, and breach notification requirements.",
            },
            {
                "id": "soc2_12",
                "question": "Do you maintain audit logs for access to production systems and sensitive data? How long are logs retained?",
                "answer_template": "Yes, {company_name} maintains comprehensive audit logs covering authentication events, administrative actions, data access, and system configuration changes. Logs are retained for a minimum of 12 months in a tamper-evident, centralized logging system. Access to logs is restricted to authorized security and operations personnel.",
            },
            {
                "id": "soc2_13",
                "question": "Do you have a formal process for revoking access when employees leave the organization?",
                "answer_template": "Yes, {company_name} has an automated offboarding process that disables all system access within one business hour of an employee's departure being confirmed in HR systems. Physical access and hardware are also revoked and recovered. Access termination is verified and logged as part of the offboarding checklist.",
            },
            {
                "id": "soc2_14",
                "question": "Do you use a dedicated secrets management system for storing API keys, passwords, and cryptographic keys?",
                "answer_template": "Yes, {company_name} uses a dedicated secrets management platform to store and distribute credentials, API keys, and cryptographic material. Hardcoding secrets in source code is prohibited and enforced via automated pre-commit scanning. Secrets are rotated on a defined schedule and upon personnel changes.",
            },
            {
                "id": "soc2_15",
                "question": "Do you maintain an inventory of all information assets and systems in scope for the audit?",
                "answer_template": "{company_name} maintains a continuously updated inventory of all information assets including cloud infrastructure, applications, endpoints, and data stores. Asset ownership is assigned and reviewed quarterly. The inventory is used as the basis for risk assessments, vulnerability management, and access reviews.",
            },
        ],
    },
    "iso27001": {
        "name": "ISO 27001",
        "questions": [
            {
                "id": "iso_01",
                "question": "Has your organization established, implemented, maintained, and continually improved an Information Security Management System (ISMS)?",
                "answer_template": "Yes, {company_name} has established a formal ISMS aligned with ISO 27001 principles. The ISMS scope, objectives, and policy are documented and approved by top management. Continual improvement is driven by internal audits, management reviews, and corrective actions arising from identified nonconformities and security incidents.",
            },
            {
                "id": "iso_02",
                "question": "Has your organization completed a formal information security risk assessment covering all in-scope assets?",
                "answer_template": "{company_name} conducts a formal risk assessment at least annually and following significant changes to the business or threat environment. The assessment identifies threats and vulnerabilities, evaluates likelihood and impact, and determines appropriate treatment options. A risk register is maintained and reviewed by the CISO and management team.",
            },
            {
                "id": "iso_03",
                "question": "Has a Statement of Applicability (SoA) been produced and signed off by management?",
                "answer_template": "Yes, {company_name} has produced a Statement of Applicability covering all Annex A controls. Each control is marked as applicable or not applicable with documented justification. The SoA is reviewed and signed off by management annually and updated as the risk landscape changes.",
            },
            {
                "id": "iso_04",
                "question": "Are management reviews of the ISMS conducted at planned intervals?",
                "answer_template": "{company_name} conducts formal ISMS management reviews at least annually, typically scheduled after the completion of internal audits. Reviews assess ISMS performance, audit results, risk treatment effectiveness, and resource adequacy. Outputs include documented decisions and action items assigned to responsible owners.",
            },
            {
                "id": "iso_05",
                "question": "Has an internal audit of the ISMS been completed covering all controls?",
                "answer_template": "Yes, {company_name} conducts internal ISMS audits at least annually using qualified internal or contracted auditors who are independent of the areas being audited. Audit scope covers all in-scope controls and processes. Findings are documented, tracked, and remediated within agreed timeframes.",
            },
            {
                "id": "iso_06",
                "question": "Is an asset inventory maintained for all information assets within the ISMS scope?",
                "answer_template": "{company_name} maintains a comprehensive asset inventory covering all hardware, software, data assets, and services within the ISMS scope. Each asset has an assigned owner responsible for its classification, protection, and review. The inventory is updated continuously and formally reviewed on a quarterly basis.",
            },
            {
                "id": "iso_07",
                "question": "How does your organization manage supplier relationships and their information security risks?",
                "answer_template": "{company_name} maintains a supplier management policy and procedure requiring security assessment of all suppliers before engagement. Security requirements are embedded in contracts via data processing agreements and security addenda. Supplier security performance is reviewed annually for critical suppliers, with corrective action plans required for deficiencies.",
            },
            {
                "id": "iso_08",
                "question": "Do you have documented procedures for information classification and handling?",
                "answer_template": "Yes, {company_name} operates a four-tier data classification scheme (Public, Internal, Confidential, Restricted) with documented handling procedures for each level. All new data assets are classified upon creation. Data owners are responsible for correct classification, and employees are trained on handling requirements during onboarding.",
            },
            {
                "id": "iso_09",
                "question": "How do you ensure that information security requirements are addressed in your software development and change management processes?",
                "answer_template": "{company_name} integrates security into the software development lifecycle via security requirements definition, secure coding standards, mandatory code review, SAST/DAST scanning in CI/CD pipelines, and pre-production security testing. The change management process includes security impact assessment for all significant changes.",
            },
            {
                "id": "iso_10",
                "question": "What physical and environmental security controls are in place to protect information processing facilities?",
                "answer_template": "{company_name}'s production infrastructure is hosted in SOC 2 Type II certified cloud data centers operated by our cloud service provider, which maintains comprehensive physical security controls including perimeter security, access controls, CCTV, environmental monitoring, and redundant utilities. Physical security responsibilities and shared model details are documented in our cloud provider agreements.",
            },
        ],
    },
    "gdpr_vendor": {
        "name": "GDPR Vendor Assessment",
        "questions": [
            {
                "id": "gdpr_01",
                "question": "What personal data does your organization process, and what is the legal basis for processing?",
                "answer_template": "{company_name} processes personal data including name, email address, and usage data for the purposes of providing the contracted service. The legal basis for processing is the performance of a contract with the data subject, as well as legitimate interests where applicable. A detailed Record of Processing Activities (RoPA) is maintained.",
            },
            {
                "id": "gdpr_02",
                "question": "Do you have a Data Processing Agreement (DPA) in place that complies with GDPR Article 28 requirements?",
                "answer_template": "Yes, {company_name} provides a GDPR-compliant Data Processing Agreement that covers all requirements of Article 28, including the nature and purpose of processing, data subject rights, sub-processor obligations, security measures, and breach notification procedures. The DPA can be executed as part of the service agreement.",
            },
            {
                "id": "gdpr_03",
                "question": "Where is personal data stored and processed? Do you transfer data outside the EU/EEA?",
                "answer_template": "{company_name} stores and processes personal data within the EU/EEA by default. Any transfers outside the EU/EEA are subject to appropriate safeguards as required by GDPR Chapter V, including Standard Contractual Clauses (SCCs) or adequacy decisions. Sub-processors are subject to equivalent transfer requirements.",
            },
            {
                "id": "gdpr_04",
                "question": "How do you handle data subject rights requests (access, erasure, portability, etc.)?",
                "answer_template": "{company_name} has documented procedures for handling data subject rights requests including the right to access, rectification, erasure, restriction, and portability. Requests are processed within the statutory 30-day timeframe. A dedicated process ensures requests are verified, logged, and fulfilled or refused with documented justification.",
            },
            {
                "id": "gdpr_05",
                "question": "What is your data breach notification process, and what are your notification timescales?",
                "answer_template": "{company_name} has a documented breach notification procedure requiring internal escalation within 4 hours of a suspected breach. Confirmed breaches that meet the GDPR notification threshold are reported to the relevant supervisory authority within 72 hours. Affected data subjects are notified without undue delay where required. Breach records are maintained.",
            },
            {
                "id": "gdpr_06",
                "question": "Do you use sub-processors? How are sub-processors managed and disclosed?",
                "answer_template": "{company_name} engages a limited number of sub-processors to support service delivery, including cloud infrastructure and email delivery providers. A current list of sub-processors is published and updated with advance notice of changes. All sub-processors are contractually bound to the same data protection obligations as {company_name} under the DPA.",
            },
            {
                "id": "gdpr_07",
                "question": "How long do you retain personal data, and what is your data deletion process?",
                "answer_template": "{company_name} retains personal data only for as long as necessary to fulfill the contracted service and comply with legal obligations. Upon contract termination, personal data is deleted or returned within 30 days as specified in the DPA. Data deletion is performed securely using industry-standard methods, and a deletion certificate can be provided upon request.",
            },
            {
                "id": "gdpr_08",
                "question": "Have you appointed a Data Protection Officer (DPO)? Do you conduct Data Protection Impact Assessments (DPIAs)?",
                "answer_template": "{company_name} has assessed its processing activities against GDPR DPO appointment criteria. DPIAs are conducted for new or significantly changed processing activities that are likely to result in high risk to individuals, including large-scale processing of sensitive data. DPIA outcomes are reviewed by the privacy team and, where required, by the supervisory authority prior to processing commencing.",
            },
        ],
    },
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class QuestionnaireTypeItem(BaseModel):
    id: str
    name: str
    question_count: int


class QuestionnaireGenerateRequest(BaseModel):
    questionnaire_type: str


class QuestionAnswer(BaseModel):
    id: str
    question: str
    answer: str


class QuestionnaireGenerateResponse(BaseModel):
    questionnaire_type: str
    name: str
    company_name: str
    generated_at: str
    answers: list[QuestionAnswer]


class AutofillRequest(BaseModel):
    questions: list[str]

    @field_validator("questions")
    @classmethod
    def validate_questions(cls, v: list[str]) -> list[str]:
        v = [q.strip() for q in v if q.strip()]
        if not v:
            raise ValueError("At least one question is required")
        if len(v) > 100:
            raise ValueError("Maximum 100 questions per request")
        return v


class AutofillAnswerItem(BaseModel):
    question: str
    answer: str


class AutofillContextSummary(BaseModel):
    integrations_count: int
    policies_count: int
    vendors_count: int
    assets_count: int
    incidents_count: int
    vulnerabilities_count: int
    pen_test: bool
    training_count: int
    risks_count: int
    soa_count: int
    ropa_count: int
    breaches_count: int
    subject_requests_count: int
    bcp_count: int
    management_review: bool
    detected_type: str


class AutofillResponse(BaseModel):
    company_name: str
    generated_at: str
    detected_type: str
    context: AutofillContextSummary
    answers: list[AutofillAnswerItem]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/types", response_model=list[QuestionnaireTypeItem])
async def list_questionnaire_types(
    current_user: User = Depends(get_current_user),
):
    return [
        QuestionnaireTypeItem(
            id=key,
            name=value["name"],
            question_count=len(value["questions"]),
        )
        for key, value in QUESTIONNAIRE_TYPES.items()
    ]


@router.post("/generate", response_model=QuestionnaireGenerateResponse)
async def generate_questionnaire(
    body: QuestionnaireGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.questionnaire_type not in QUESTIONNAIRE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown questionnaire type. Valid types: {list(QUESTIONNAIRE_TYPES.keys())}",
        )

    # Load company to get the name
    from models.company import Company

    company_result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "Your Company"

    from datetime import datetime, timezone

    qt = QUESTIONNAIRE_TYPES[body.questionnaire_type]
    answers = [
        QuestionAnswer(
            id=q["id"],
            question=q["question"],
            answer=q["answer_template"].replace("{company_name}", company_name),
        )
        for q in qt["questions"]
    ]

    return QuestionnaireGenerateResponse(
        questionnaire_type=body.questionnaire_type,
        name=qt["name"],
        company_name=company_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        answers=answers,
    )


@router.post("/ai-autofill", response_model=AutofillResponse)
async def ai_autofill_questionnaire(
    body: AutofillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_growth),
):
    from datetime import datetime, timezone

    from models.company import Company

    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "Your Company"

    try:
        answers, detected_type, ctx_summary = await autofill_questionnaire(current_user.company_id, body.questions, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("AI autofill failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")

    return AutofillResponse(
        company_name=company_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        detected_type=detected_type,
        context=AutofillContextSummary(**ctx_summary),
        answers=[AutofillAnswerItem(question=a["question"], answer=a["answer"]) for a in answers],
    )
