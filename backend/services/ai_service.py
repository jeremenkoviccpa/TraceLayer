import json
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

logger = logging.getLogger(__name__)

FRAMEWORK_LABELS = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}

FRAMEWORK_LABELS_FULL = {
    "soc2":     "SOC 2 Type II",
    "iso27001": "ISO 27001",
    "hipaa":    "HIPAA",
    "gdpr":     "GDPR",
    "pci_dss":  "PCI DSS",
    "ccpa":     "CCPA",
    "nist_csf": "NIST CSF",
    "dpdp":     "DPDP Act 2023 (India)",
    "cert_in":  "CERT-In Directions 2022 (India)",
}

# Groups of integrations that are interchangeable for compliance purposes
INTEGRATION_ALTERNATIVES: dict[str, dict] = {
    "cloud_infra": {
        "label": "Cloud Infrastructure",
        "integrations": ["aws", "azure", "gcp"],
        "evidence": "infrastructure logs, IAM policies, config snapshots, storage bucket policies, network flow logs",
    },
    "identity": {
        "label": "Identity & SSO",
        "integrations": ["okta", "azure_ad", "google_workspace"],
        "evidence": "user provisioning/deprovisioning, MFA enforcement, access logs, group memberships",
    },
    "source_control": {
        "label": "Source Control & CI/CD",
        "integrations": ["github", "gitlab", "bitbucket"],
        "evidence": "code review records, branch protection rules, deployment history, PR approval audit trail",
    },
    "hrms": {
        "label": "HR & People Management",
        "integrations": ["rippling", "bamboohr", "workday", "gusto"],
        "evidence": "employee onboarding/offboarding records, employment status, org structure, background check tracking",
    },
    "monitoring": {
        "label": "Monitoring & Incident Management",
        "integrations": ["datadog", "pagerduty", "sentry", "newrelic"],
        "evidence": "uptime metrics, alert history, incident timelines, performance dashboards",
    },
    "communication": {
        "label": "Team Communication",
        "integrations": ["slack", "teams"],
        "evidence": "incident communication audit trail, access logs",
    },
    "project_mgmt": {
        "label": "Project & Issue Tracking",
        "integrations": ["jira", "linear", "asana"],
        "evidence": "vulnerability tracking tickets, change management records, remediation timelines",
    },
    "payment": {
        "label": "Payment Processing",
        "integrations": ["stripe"],
        "evidence": "payment processing logs, cardholder data environment scope",
    },
}

# Per framework: which integration categories are required vs recommended
FRAMEWORK_INTEGRATION_REQUIREMENTS: dict[str, dict] = {
    "soc2": {
        "required": ["cloud_infra", "identity", "source_control", "monitoring", "hrms"],
        "recommended": ["project_mgmt", "communication"],
        "context": (
            "SOC 2 centers on the Trust Service Criteria. Access control (CC6) needs identity + cloud IAM evidence. "
            "Change management (CC8) needs source control. Availability (A1) needs monitoring. "
            "Logical & physical access (CC6.2/CC6.3) needs HR for onboarding/offboarding."
        ),
    },
    "iso27001": {
        "required": ["cloud_infra", "identity", "source_control", "hrms", "monitoring"],
        "recommended": ["project_mgmt"],
        "context": (
            "ISO 27001 Annex A covers asset management (A.8 — cloud), access control (A.9 — identity), "
            "operations security (A.12 — monitoring), and personnel security (A.7 — HR). "
            "Source control covers A.12.1 change management and A.14 secure development."
        ),
    },
    "hipaa": {
        "required": ["cloud_infra", "identity", "monitoring", "hrms"],
        "recommended": ["source_control", "communication"],
        "context": (
            "HIPAA Technical Safeguards require audit controls (monitoring), access management (identity), "
            "and transmission security (cloud). Administrative Safeguards require workforce training/sanctions (HR). "
            "Cloud infra must be HIPAA BAA-eligible (AWS, Azure, GCP all qualify)."
        ),
    },
    "gdpr": {
        "required": ["cloud_infra", "identity", "hrms"],
        "recommended": ["monitoring", "source_control"],
        "context": (
            "GDPR evidence covers data processing records (RoPA), access controls for personal data (identity + cloud), "
            "and data subject request handling. Cloud infra determines data residency — EU region selection is critical. "
            "HR provides employee data subject access evidence."
        ),
    },
    "pci_dss": {
        "required": ["cloud_infra", "identity", "monitoring", "source_control"],
        "recommended": ["payment", "project_mgmt"],
        "context": (
            "PCI DSS Req 1-2 need network segmentation evidence (cloud). Req 7-8 need access control (identity + MFA). "
            "Req 10 needs logging (cloud + monitoring). Req 6 needs code review (source control). "
            "Req 11 needs vulnerability scanning which can be evidenced via monitoring tools."
        ),
    },
    "ccpa": {
        "required": ["cloud_infra", "identity"],
        "recommended": ["hrms", "monitoring"],
        "context": (
            "CCPA focuses on consumer rights: access, deletion, and opt-out. Cloud infra shows where data is stored "
            "and provides deletion capability evidence. Identity shows who has access to consumer data."
        ),
    },
    "nist_csf": {
        "required": ["cloud_infra", "identity", "monitoring", "source_control"],
        "recommended": ["hrms", "project_mgmt"],
        "context": (
            "NIST CSF maps to five functions: Identify (asset inventory via cloud), Protect (access control via identity, "
            "change management via source control), Detect (monitoring), Respond & Recover (incident management via monitoring + project mgmt)."
        ),
    },
    "dpdp": {
        "required": ["cloud_infra", "identity"],
        "recommended": ["hrms", "monitoring"],
        "context": (
            "DPDP Act 2023 (India) focuses on consent, data localisation (cloud region — must be India), "
            "access to personal data (identity), and breach notification within 72 hours (monitoring for detection)."
        ),
    },
    "cert_in": {
        "required": ["cloud_infra", "monitoring", "identity"],
        "recommended": ["source_control", "project_mgmt"],
        "context": (
            "CERT-In Directions require: 180-day log retention (cloud + monitoring), NTP synchronisation "
            "(cloud config evidence), vulnerability management (monitoring/scanning), and 6-hour incident reporting. "
            "Identity provides access audit trails required by Dir. 5."
        ),
    },
}


def _build_integration_gap_analysis(framework: str, connected: list[str]) -> str:
    """Produce a structured integration gap analysis for the given framework and connected integrations."""
    reqs = FRAMEWORK_INTEGRATION_REQUIREMENTS.get(framework, {})
    required_cats = reqs.get("required", [])
    recommended_cats = reqs.get("recommended", [])
    framework_context = reqs.get("context", "")

    connected_lower = {c.lower() for c in connected}

    lines = []
    if framework_context:
        lines.append(f"Framework note: {framework_context}")
    lines.append("")
    lines.append("INTEGRATION STATUS:")

    missing_required = []
    for category in required_cats:
        cat = INTEGRATION_ALTERNATIVES.get(category, {})
        connected_in_cat = [i for i in cat.get("integrations", []) if i in connected_lower]
        all_options = cat.get("integrations", [])
        if connected_in_cat:
            lines.append(f"  ✓ [REQUIRED] {cat.get('label', category)}: {', '.join(connected_in_cat)} — covers: {cat.get('evidence', '')}")
        else:
            missing_required.append(cat.get("label", category))
            lines.append(f"  ✗ [REQUIRED] {cat.get('label', category)}: NOT CONNECTED")
            lines.append(f"    → Missing evidence: {cat.get('evidence', '')}")
            lines.append(f"    → Connect any one of: {', '.join(all_options)} (they are equivalent for compliance)")

    for category in recommended_cats:
        cat = INTEGRATION_ALTERNATIVES.get(category, {})
        connected_in_cat = [i for i in cat.get("integrations", []) if i in connected_lower]
        all_options = cat.get("integrations", [])
        if connected_in_cat:
            lines.append(f"  ✓ [RECOMMENDED] {cat.get('label', category)}: {', '.join(connected_in_cat)}")
        else:
            lines.append(f"  ○ [RECOMMENDED] {cat.get('label', category)}: not connected — options: {', '.join(all_options)}")

    if missing_required:
        lines.append(f"\nCRITICAL GAPS: {len(missing_required)} required integration categories missing — {', '.join(missing_required)}")
    else:
        lines.append("\nAll required integration categories are covered.")

    return "\n".join(lines)


def _build_prompt(framework: str, score_data: dict) -> str:
    label = FRAMEWORK_LABELS.get(framework, framework.upper())

    lines = []
    for c in score_data["controls"]:
        covered = ", ".join(c["covered_types"]) if c["covered_types"] else "none"
        missing = ", ".join(c["missing_types"]) if c["missing_types"] else "none"
        lines.append(
            f"- {c['name']}: {c['score']}% ({c['status']}) | "
            f"evidence count: {c['evidence_count']} | "
            f"covered types: {covered} | "
            f"missing types: {missing}"
        )

    controls_text = "\n".join(lines)

    return f"""You are a compliance advisor helping an engineering team understand their {label} posture.

Framework: {label}
Overall Score: {score_data["overall_score"]}%

Control breakdown:
{controls_text}

Write a 3-4 sentence summary that:
1. States the overall posture plainly (good/needs work/critical gaps)
2. Calls out what is working well, if anything
3. Names the single most critical gap and gives one specific, concrete action to fix it

Rules:
- Write in flowing prose — no bullet points
- Be specific: use actual control names and evidence type names from the data
- Do not give generic compliance advice — ground everything in the numbers above
- Keep it under 90 words"""


async def generate_compliance_summary(framework: str, score_data: dict) -> str:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed — add it to requirements.txt") from exc

    client = AsyncGroq(api_key=settings.groq_api_key)
    prompt = _build_prompt(framework, score_data)

    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=220,
    )

    return completion.choices[0].message.content.strip()


# ── Advisor chat ──────────────────────────────────────────────────────────────

async def chat_with_advisor(
    framework: str,
    score_data: dict,
    message: str,
    history: list[dict],
    connected_integrations: list[str] | None = None,
) -> str:
    """Multi-turn compliance advisor chat powered by Groq."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed") from exc

    label = FRAMEWORK_LABELS_FULL.get(framework, framework.upper())
    connected = connected_integrations or []

    controls_lines = []
    for c in score_data["controls"]:
        collected = ", ".join(c["covered_types"]) or "none"
        missing   = ", ".join(c["missing_types"])  or "none"
        controls_lines.append(
            f"  - {c['name']}: {c['score']}% ({c['status']}) | "
            f"collected: {collected} | missing: {missing}"
        )
    controls_text = "\n".join(controls_lines)

    failing = [c for c in score_data["controls"] if c["status"] in ("failing", "no_evidence")]
    top_gap = failing[0]["name"] if failing else "—"

    integration_gap_text = _build_integration_gap_analysis(framework, connected)
    connected_str = ", ".join(connected) if connected else "none"

    system_prompt = f"""You are TraceLayer's AI Compliance Advisor — a direct, expert guide helping an engineering team achieve {label} compliance.

CURRENT POSTURE (live data):
- Framework: {label}
- Overall score: {score_data["overall_score"]}%
- Connected integrations: {connected_str}
- Controls:
{controls_text}
- Top priority control gap: {top_gap}

{integration_gap_text}

INTEGRATION KNOWLEDGE:
- AWS, Azure, and GCP are interchangeable for cloud infrastructure evidence — recommend the one they already use
- Okta, Azure AD, and Google Workspace are interchangeable for identity/SSO evidence
- GitHub, GitLab, and Bitbucket are interchangeable for source control evidence
- Rippling, BambooHR, Workday, and Gusto are interchangeable for HR evidence
- Datadog, PagerDuty, Sentry, and New Relic are interchangeable for monitoring evidence
- Slack and Microsoft Teams are interchangeable for communication evidence
- Jira, Linear, and Asana are interchangeable for issue tracking evidence
- When recommending an integration, always check if they already have an equivalent connected and prefer it

RULES:
- When asked "where to start" or for a plan: assess their current integrations, name exactly which categories are missing, and give a prioritized numbered list of integrations to connect (required gaps first, then recommended)
- Always offer alternatives — if they don't have AWS, mention Azure or GCP; if not Okta, mention Azure AD or Google Workspace
- Reference actual control names and missing evidence types from the data
- For failing/no_evidence controls, explain which specific integration(s) would fix them and why
- Be concise (≤200 words) unless the user asks to elaborate
- Tone: friendly, direct, expert — like a senior compliance engineer on their team
- Never give generic advice — every recommendation must be grounded in their specific stack and gaps"""

    msgs: list[dict] = [{"role": "system", "content": system_prompt}]
    for h in history[-14:]:
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": message})

    client = AsyncGroq(api_key=settings.groq_api_key)
    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        temperature=0.35,
        max_tokens=500,
    )
    return completion.choices[0].message.content.strip()


# ── General compliance advisor (global chat) ─────────────────────────────────

async def chat_with_general_advisor(
    message: str,
    history: list[dict],
    company_context: dict | None = None,
) -> str:
    """General-purpose compliance advisor chat for the global chatbot."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed") from exc

    # Build context block from company data if available
    ctx_lines = []
    if company_context:
        if company_context.get("company_name"):
            ctx_lines.append(f"Company: {company_context['company_name']}")
        if company_context.get("connected_integrations"):
            ctx_lines.append(f"Connected integrations: {', '.join(company_context['connected_integrations'])}")
        if company_context.get("active_frameworks"):
            ctx_lines.append(f"Active compliance frameworks: {', '.join(company_context['active_frameworks'])}")
        if company_context.get("scores"):
            score_lines = [f"  - {fw}: {sc}%" for fw, sc in company_context["scores"].items()]
            ctx_lines.append("Compliance scores:\n" + "\n".join(score_lines))

    context_block = ("\n\nCOMPANY CONTEXT (live data):\n" + "\n".join(ctx_lines)) if ctx_lines else ""

    system_prompt = f"""You are TraceLayer's AI Compliance Advisor — an expert guide helping teams achieve and maintain security compliance.

You have deep knowledge of:
- SOC 2 Type II (Trust Service Criteria)
- ISO 27001 (ISMS, Annex A controls)
- HIPAA (Technical, Administrative, and Physical Safeguards)
- GDPR (data subject rights, RoPA, DPA, DPIA, breach notification)
- PCI DSS (cardholder data environment, network segmentation, Req 1-12)
- CCPA (consumer rights, data deletion, opt-out)
- NIST CSF (Identify, Protect, Detect, Respond, Recover)
- DPDP Act 2023 India (consent, data localisation, 72-hour breach notification)
- CERT-In Directions 2022 (180-day log retention, NTP sync, 6-hour incident reporting)
- Evidence collection, audit preparation, policy writing, vendor risk, penetration testing
- Integration equivalencies: AWS ≈ Azure ≈ GCP, Okta ≈ Azure AD ≈ Google Workspace, GitHub ≈ GitLab ≈ Bitbucket, Rippling ≈ BambooHR ≈ Workday, Datadog ≈ PagerDuty ≈ Sentry, Slack ≈ Teams, Jira ≈ Linear ≈ Asana{context_block}

RULES:
- Be direct and specific — give concrete, actionable answers
- Reference real framework requirements (control names, article numbers, requirement IDs)
- When recommending integrations, always offer equivalent alternatives
- Keep answers concise (≤250 words) unless asked to elaborate
- Tone: expert, friendly, like a senior compliance engineer on the team
- Never give generic boilerplate — ground everything in specifics"""

    msgs: list[dict] = [{"role": "system", "content": system_prompt}]
    for h in history[-20:]:
        msgs.append({"role": h["role"], "content": h["content"]})
    msgs.append({"role": "user", "content": message})

    client = AsyncGroq(api_key=settings.groq_api_key)
    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=msgs,
        temperature=0.35,
        max_tokens=600,
    )
    return completion.choices[0].message.content.strip()


# ── Policy template generator ─────────────────────────────────────────────────

async def generate_policy_template(
    slug: str,
    policy_name: str,
    company_name: str,
    connected_integrations: list[str],
) -> str:
    """Generate a full policy document for the given policy type."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed") from exc

    integrations_str = ", ".join(connected_integrations) if connected_integrations else "standard security tools"

    prompt = f"""Generate a complete, professional {policy_name} for {company_name}.

The company uses: {integrations_str}

Requirements:
- Write a full, production-ready policy document (600-900 words)
- Use proper policy structure: Purpose, Scope, Policy Statement, Procedures, Roles & Responsibilities, Enforcement, Review Cycle
- Reference the company's actual tools where relevant (e.g., "{integrations_str}")
- Reference applicable compliance frameworks where relevant (SOC 2, ISO 27001, GDPR, HIPAA as appropriate for this policy type)
- Use {company_name} as the company name throughout
- Format in clean Markdown with headers (##), bullet points, and numbered lists where appropriate
- Make it specific and actionable — not generic boilerplate
- Include version: 1.0, effective date: {__import__('datetime').date.today().strftime('%B %d, %Y')}, and owner: Security Team in the header

Output ONLY the Markdown policy document. No preamble or explanation."""

    client = AsyncGroq(api_key=settings.groq_api_key)
    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    return completion.choices[0].message.content.strip()


# ── Questionnaire autofill ────────────────────────────────────────────────────

_INT_LABELS = {
    "aws": "AWS", "github": "GitHub", "slack": "Slack",
    "google_workspace": "Google Workspace", "okta": "Okta",
    "azure_ad": "Azure AD", "jira": "Jira", "gitlab": "GitLab",
    "gcp": "GCP", "linear": "Linear", "datadog": "Datadog",
    "pagerduty": "PagerDuty", "sentry": "Sentry", "teams": "Microsoft Teams",
    "stripe": "Stripe", "rippling": "Rippling", "bamboohr": "BambooHR",
    "notion": "Notion",
}


async def _gather_company_context(company_id: uuid.UUID, db: AsyncSession) -> dict:
    from sqlalchemy import select

    from models.access_review import AccessReview
    from models.asset import Asset
    from models.background_check import BackgroundCheck
    from models.bcp_record import BcpRecord
    from models.company import Company
    from models.data_breach import DataBreach
    from models.incident import Incident
    from models.integration import Integration
    from models.management_review import ManagementReview
    from models.manual_control import ManualControl
    from models.offboarding import Offboarding
    from models.pen_test import PenTest
    from models.policy import Policy
    from models.risk import Risk
    from models.ropa_record import RopaRecord
    from models.soa_item import SoaItem
    from models.subject_request import SubjectRequest
    from models.training import TrainingRecord
    from models.vendor import Vendor
    from models.vulnerability import Vulnerability

    async def fetch(stmt):
        return (await db.execute(stmt)).scalars().all()

    async def fetch_one(stmt):
        return (await db.execute(stmt)).scalar_one_or_none()

    company = await fetch_one(select(Company).where(Company.id == company_id))
    company_name = company.name if company else "Our Company"

    integrations = await fetch(
        select(Integration).where(Integration.company_id == company_id, Integration.status == "active")
    )
    policies = await fetch(
        select(Policy).where(Policy.company_id == company_id, Policy.content != "")
    )
    manual_controls = await fetch(select(ManualControl).where(ManualControl.company_id == company_id))
    pen_test = await fetch_one(
        select(PenTest).where(PenTest.company_id == company_id).order_by(PenTest.conducted_at.desc()).limit(1)
    )
    training = await fetch(select(TrainingRecord).where(TrainingRecord.company_id == company_id))
    risks = await fetch(select(Risk).where(Risk.company_id == company_id))
    access_review = await fetch_one(
        select(AccessReview).where(AccessReview.company_id == company_id).order_by(AccessReview.completed_at.desc()).limit(1)
    )

    # ── New data sources ──────────────────────────────────────────────────────
    vendors = await fetch(select(Vendor).where(Vendor.company_id == company_id))
    assets = await fetch(select(Asset).where(Asset.company_id == company_id))
    incidents = await fetch(select(Incident).where(Incident.company_id == company_id))
    vulnerabilities = await fetch(select(Vulnerability).where(Vulnerability.company_id == company_id))
    bcp_records = await fetch(select(BcpRecord).where(BcpRecord.company_id == company_id))
    background_checks = await fetch(select(BackgroundCheck).where(BackgroundCheck.company_id == company_id))
    offboardings = await fetch(select(Offboarding).where(Offboarding.company_id == company_id))
    soa_items = await fetch(select(SoaItem).where(SoaItem.company_id == company_id))
    ropa_records = await fetch(select(RopaRecord).where(RopaRecord.company_id == company_id))
    data_breaches = await fetch(select(DataBreach).where(DataBreach.company_id == company_id))
    subject_requests = await fetch(select(SubjectRequest).where(SubjectRequest.company_id == company_id))
    management_review = await fetch_one(
        select(ManagementReview).where(ManagementReview.company_id == company_id).order_by(ManagementReview.review_date.desc()).limit(1)
    )

    return {
        "company_name": company_name,
        # Existing
        "integrations": [_INT_LABELS.get(i.integration_type, i.integration_type) for i in integrations],
        "policies": [p.slug.replace("_", " ").replace("-", " ").title() for p in policies if p.content],
        "manual_controls": {
            "total": len(manual_controls),
            "compliant": sum(1 for m in manual_controls if m.status == "compliant"),
            "pending": sum(1 for m in manual_controls if m.status == "pending"),
        },
        "pen_test": pen_test,
        "training": {
            "total": len(training),
            "completed": sum(1 for t in training if t.status == "completed"),
            "overdue": sum(1 for t in training if t.status == "overdue"),
            "annual": sum(1 for t in training if t.annual),
        },
        "risks": {
            "total": len(risks),
            "critical": sum(1 for r in risks if r.risk_level == "critical"),
            "high": sum(1 for r in risks if r.risk_level == "high"),
            "open": sum(1 for r in risks if r.status == "open"),
            "mitigated": sum(1 for r in risks if r.status == "mitigated"),
            "accepted": sum(1 for r in risks if r.status == "accepted"),
        },
        "access_review": access_review,
        # New
        "vendors": {
            "total": len(vendors),
            "high_risk": sum(1 for v in vendors if v.risk_level in ("high", "critical")),
            "soc2_certified": sum(1 for v in vendors if v.soc2_certified),
            "iso27001_certified": sum(1 for v in vendors if v.iso27001_certified),
            "hipaa_certified": sum(1 for v in vendors if v.hipaa_certified),
            "with_dpa": sum(1 for v in vendors if v.contact_email),  # proxy for managed vendors
        },
        "assets": {
            "total": len(assets),
            "production": sum(1 for a in assets if a.environment == "production"),
            "cloud": sum(1 for a in assets if a.asset_type == "cloud"),
            "active": sum(1 for a in assets if a.status == "active"),
            "classified_restricted": sum(1 for a in assets if a.classification == "restricted"),
            "classified_confidential": sum(1 for a in assets if a.classification == "confidential"),
        },
        "incidents": {
            "total": len(incidents),
            "open": sum(1 for i in incidents if i.status in ("open", "investigating")),
            "resolved": sum(1 for i in incidents if i.status in ("resolved", "closed")),
            "critical": sum(1 for i in incidents if i.severity == "critical"),
            "high": sum(1 for i in incidents if i.severity == "high"),
        },
        "vulnerabilities": {
            "total": len(vulnerabilities),
            "open": sum(1 for v in vulnerabilities if v.status in ("open", "in_remediation")),
            "resolved": sum(1 for v in vulnerabilities if v.status == "resolved"),
            "critical": sum(1 for v in vulnerabilities if v.severity == "critical"),
            "high": sum(1 for v in vulnerabilities if v.severity == "high"),
        },
        "bcp": {
            "total": len(bcp_records),
            "tested": sum(1 for b in bcp_records if b.status in ("tested", "passed")),
            "passed": sum(1 for b in bcp_records if b.status == "passed"),
            "rto_minutes": min((b.rto_minutes for b in bcp_records if b.rto_minutes), default=None),
            "rpo_minutes": min((b.rpo_minutes for b in bcp_records if b.rpo_minutes), default=None),
        },
        "background_checks": {
            "total": len(background_checks),
            "completed": sum(1 for b in background_checks if b.status == "completed"),
            "pending": sum(1 for b in background_checks if b.status in ("pending", "in_progress")),
        },
        "offboarding": {
            "total": len(offboardings),
            "completed": sum(1 for o in offboardings if o.status == "completed"),
        },
        "soa": {
            "total": len(soa_items),
            "included": sum(1 for s in soa_items if s.included),
            "implemented": sum(1 for s in soa_items if s.implementation_status == "implemented"),
            "in_progress": sum(1 for s in soa_items if s.implementation_status == "in_progress"),
            "not_implemented": sum(1 for s in soa_items if s.implementation_status == "not_implemented"),
        },
        "ropa": {
            "total": len(ropa_records),
            "roles": list({r.role for r in ropa_records}),
        },
        "data_breaches": {
            "total": len(data_breaches),
            "open": sum(1 for b in data_breaches if b.status in ("open", "investigating")),
            "notified_dpa": sum(1 for b in data_breaches if b.dpa_notified_at),
        },
        "subject_requests": {
            "total": len(subject_requests),
            "completed": sum(1 for r in subject_requests if r.status == "completed"),
            "open": sum(1 for r in subject_requests if r.status in ("open", "in_progress")),
        },
        "management_review": management_review,
    }


def _detect_questionnaire_type(questions: list[str]) -> str:
    """Heuristic: detect questionnaire focus from keywords in questions."""
    text = " ".join(questions).lower()
    scores = {"soc2": 0, "iso27001": 0, "gdpr": 0, "hipaa": 0, "pci": 0}

    soc2_kw = ["soc 2", "soc2", "trust service", "availability", "confidentiality", "processing integrity"]
    iso_kw = ["iso 27001", "isms", "annex a", "statement of applicability", "management review", "nonconformity"]
    gdpr_kw = ["gdpr", "data subject", "dpa", "dpo", "ropa", "lawful basis", "erasure", "supervisory authority", "article 28"]
    hipaa_kw = ["hipaa", "phi", "protected health", "covered entity", "business associate", "baa", "safeguards"]
    pci_kw = ["pci", "cardholder", "payment card", "pci dss", "card data", "merchant"]

    for kw in soc2_kw:
        scores["soc2"] += text.count(kw) * 2
    for kw in iso_kw:
        scores["iso27001"] += text.count(kw) * 2
    for kw in gdpr_kw:
        scores["gdpr"] += text.count(kw) * 2
    for kw in hipaa_kw:
        scores["hipaa"] += text.count(kw) * 2
    for kw in pci_kw:
        scores["pci"] += text.count(kw) * 2

    # Generic security terms
    if "mfa" in text or "multi-factor" in text:
        scores["soc2"] += 1
    if "encryption" in text or "encrypt" in text:
        scores["soc2"] += 1
    if "personal data" in text or "personal information" in text:
        scores["gdpr"] += 1

    detected = max(scores, key=lambda k: scores[k])
    return detected if scores[detected] > 0 else "general"


def _build_autofill_prompt(ctx: dict, questions: list[str], detected_type: str = "general") -> str:
    company_name = ctx["company_name"]

    integrations_str = ", ".join(ctx["integrations"]) or "None configured"
    policies_str = ", ".join(ctx["policies"]) or "None adopted yet"

    mc = ctx["manual_controls"]
    mc_str = f"{mc['total']} controls tracked — {mc['compliant']} compliant, {mc['pending']} pending"

    pt = ctx["pen_test"]
    if pt:
        pt_str = (
            f"Conducted by {pt.vendor_name}, status: {pt.status}, "
            f"findings: {pt.critical_count} critical / {pt.high_count} high / "
            f"{pt.medium_count} medium / {pt.low_count} low"
        )
        if pt.conducted_at:
            pt_str += f", conducted: {pt.conducted_at.strftime('%B %Y')}"
    else:
        pt_str = "No penetration test on record"

    tr = ctx["training"]
    if tr["total"] > 0:
        rate = round(tr["completed"] / tr["total"] * 100)
        tr_str = f"{tr['total']} records — {tr['completed']} completed ({rate}%), {tr['overdue']} overdue, {tr['annual']} annual"
    else:
        tr_str = "No training records"

    rs = ctx["risks"]
    rs_str = (
        f"{rs['total']} identified — {rs['critical']} critical, {rs['high']} high; "
        f"{rs['open']} open, {rs['mitigated']} mitigated, {rs['accepted']} accepted"
    ) if rs["total"] > 0 else "No risks recorded"

    ar = ctx["access_review"]
    ar_str = (
        f"Most recent: '{ar.title}', period {ar.period}, status: {ar.status}, "
        f"{ar.users_reviewed} users reviewed, {ar.access_changes} access changes"
    ) if ar else "No access reviews on record"

    # New context sections
    v = ctx["vendors"]
    vendor_str = (
        f"{v['total']} vendors tracked — {v['high_risk']} high/critical risk; "
        f"{v['soc2_certified']} SOC 2 certified, {v['iso27001_certified']} ISO 27001 certified, "
        f"{v['hipaa_certified']} HIPAA certified"
    ) if v["total"] > 0 else "No vendors tracked"

    a = ctx["assets"]
    asset_str = (
        f"{a['total']} assets — {a['production']} production, {a['cloud']} cloud; "
        f"{a['classified_restricted']} restricted, {a['classified_confidential']} confidential"
    ) if a["total"] > 0 else "No assets inventoried"

    inc = ctx["incidents"]
    inc_str = (
        f"{inc['total']} incidents — {inc['open']} open, {inc['resolved']} resolved; "
        f"{inc['critical']} critical, {inc['high']} high severity"
    ) if inc["total"] > 0 else "No incidents recorded"

    vuln = ctx["vulnerabilities"]
    vuln_str = (
        f"{vuln['total']} vulnerabilities — {vuln['open']} open/in-remediation, {vuln['resolved']} resolved; "
        f"{vuln['critical']} critical, {vuln['high']} high"
    ) if vuln["total"] > 0 else "No vulnerabilities tracked"

    bcp = ctx["bcp"]
    if bcp["total"] > 0:
        bcp_str = f"{bcp['total']} BCP/DR plans — {bcp['tested']} tested, {bcp['passed']} passed"
        if bcp["rto_minutes"]:
            bcp_str += f"; RTO: {bcp['rto_minutes']} min"
        if bcp["rpo_minutes"]:
            bcp_str += f", RPO: {bcp['rpo_minutes']} min"
    else:
        bcp_str = "No BCP/DR records"

    bgc = ctx["background_checks"]
    bgc_str = (
        f"{bgc['total']} checks — {bgc['completed']} completed, {bgc['pending']} pending"
    ) if bgc["total"] > 0 else "No background checks recorded"

    soa = ctx["soa"]
    soa_str = (
        f"{soa['included']} of {soa['total']} controls included in scope; "
        f"{soa['implemented']} implemented, {soa['in_progress']} in progress, {soa['not_implemented']} not implemented"
    ) if soa["total"] > 0 else "SoA not yet completed"

    ropa = ctx["ropa"]
    ropa_str = (
        f"{ropa['total']} processing activities recorded; roles: {', '.join(ropa['roles'][:5])}"
    ) if ropa["total"] > 0 else "RoPA not yet completed"

    breaches = ctx["data_breaches"]
    breach_str = (
        f"{breaches['total']} breach events — {breaches['open']} open, {breaches['notified_dpa']} with DPA notified"
    ) if breaches["total"] > 0 else "No data breach events recorded"

    dsr = ctx["subject_requests"]
    dsr_str = (
        f"{dsr['total']} subject requests — {dsr['completed']} completed, {dsr['open']} open"
    ) if dsr["total"] > 0 else "No data subject requests recorded"

    mr = ctx["management_review"]
    mr_str = (
        f"Most recent: {mr.review_date}, outcome: {mr.outcome}, "
        f"attendees: {mr.attendees or 'not specified'}"
    ) if mr else "No management reviews on record"

    # Tailor tone hint based on detected type
    type_hints = {
        "gdpr": "Pay special attention to GDPR/privacy-related data: RoPA, breach register, subject requests, and DPA status.",
        "iso27001": "Pay special attention to ISMS-related data: SoA, management reviews, risk assessment, and asset inventory.",
        "hipaa": "Pay special attention to PHI handling, security safeguards, BAA status, and incident response.",
        "pci": "Pay special attention to cardholder data environment, vulnerability management, and access controls.",
        "soc2": "Pay special attention to trust service criteria: access controls, monitoring, incident response, and availability.",
        "general": "Answer questions professionally using the full context provided.",
    }
    type_hint = type_hints.get(detected_type, type_hints["general"])

    numbered_qs = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))

    return f"""You are a compliance expert helping {company_name} fill out a security questionnaire.

{type_hint}

Use ONLY the factual information provided below. Do not invent specific dates, tool names, or numbers not present in the context. If specific data is unavailable, write a professional answer describing what is in place and note that details can be confirmed during due diligence.

COMPANY CONTEXT:
- Company: {company_name}
- Active security integrations: {integrations_str}
- Adopted policies: {policies_str}
- Compliance controls: {mc_str}
- Penetration testing: {pt_str}
- Security training: {tr_str}
- Risk register: {rs_str}
- Access reviews: {ar_str}
- Vendor risk: {vendor_str}
- Asset inventory: {asset_str}
- Incident management: {inc_str}
- Vulnerability management: {vuln_str}
- Business continuity & DR: {bcp_str}
- Background checks: {bgc_str}
- Statement of Applicability: {soa_str}
- Data processing records (RoPA): {ropa_str}
- Data breach register: {breach_str}
- Data subject requests: {dsr_str}
- Management reviews: {mr_str}

QUESTIONS:
{numbered_qs}

Respond with a JSON array only — no markdown, no explanation outside the JSON. Format:
[
  {{"index": 1, "answer": "..."}},
  {{"index": 2, "answer": "..."}}
]

Rules:
- Each answer must be professional, 2–4 sentences, grounded in the context above
- Reference {company_name} by name in each answer
- Do not use bullet points inside answers
- Do not fabricate specific tool names, vendors, or dates not in the context
- Where data is sparse, write confidently about the processes in place and offer to provide more detail during due diligence"""


async def autofill_questionnaire(
    company_id: uuid.UUID,
    questions: list[str],
    db: AsyncSession,
) -> tuple[list[dict], str, dict]:
    """Returns (answers, detected_type, context_summary)."""
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed — add it to requirements.txt") from exc

    ctx = await _gather_company_context(company_id, db)
    detected_type = _detect_questionnaire_type(questions)
    prompt = _build_autofill_prompt(ctx, questions, detected_type)

    client = AsyncGroq(api_key=settings.groq_api_key)
    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=6000,
    )

    content = completion.choices[0].message.content.strip()

    # Extract JSON array from response
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        raise ValueError("AI response did not contain a valid JSON array")

    raw = json.loads(match.group(0))
    answer_map = {item["index"]: item["answer"] for item in raw if "index" in item and "answer" in item}
    answers = [
        {"question": q, "answer": answer_map.get(i + 1, "")}
        for i, q in enumerate(questions)
    ]

    # Build context summary for UI display
    context_summary = {
        "integrations_count": len(ctx["integrations"]),
        "policies_count": len(ctx["policies"]),
        "vendors_count": ctx["vendors"]["total"],
        "assets_count": ctx["assets"]["total"],
        "incidents_count": ctx["incidents"]["total"],
        "vulnerabilities_count": ctx["vulnerabilities"]["total"],
        "pen_test": ctx["pen_test"] is not None,
        "training_count": ctx["training"]["total"],
        "risks_count": ctx["risks"]["total"],
        "soa_count": ctx["soa"]["total"],
        "ropa_count": ctx["ropa"]["total"],
        "breaches_count": ctx["data_breaches"]["total"],
        "subject_requests_count": ctx["subject_requests"]["total"],
        "bcp_count": ctx["bcp"]["total"],
        "management_review": ctx["management_review"] is not None,
        "detected_type": detected_type,
    }

    return answers, detected_type, context_summary
