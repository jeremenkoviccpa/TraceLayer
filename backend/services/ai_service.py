import json
import logging
import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

logger = logging.getLogger(__name__)

FRAMEWORK_LABELS = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}


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
    from models.company import Company
    from models.integration import Integration
    from models.manual_control import ManualControl
    from models.pen_test import PenTest
    from models.policy import Policy
    from models.risk import Risk
    from models.training import TrainingRecord

    company = (await db.execute(select(Company).where(Company.id == company_id))).scalar_one_or_none()
    company_name = company.name if company else "Our Company"

    integrations = (await db.execute(
        select(Integration).where(Integration.company_id == company_id, Integration.status == "active")
    )).scalars().all()

    policies = (await db.execute(
        select(Policy).where(Policy.company_id == company_id, Policy.content != "")
    )).scalars().all()

    manual_controls = (await db.execute(
        select(ManualControl).where(ManualControl.company_id == company_id)
    )).scalars().all()

    pen_test = (await db.execute(
        select(PenTest).where(PenTest.company_id == company_id)
        .order_by(PenTest.conducted_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    training = (await db.execute(
        select(TrainingRecord).where(TrainingRecord.company_id == company_id)
    )).scalars().all()

    risks = (await db.execute(
        select(Risk).where(Risk.company_id == company_id)
    )).scalars().all()

    access_review = (await db.execute(
        select(AccessReview).where(AccessReview.company_id == company_id)
        .order_by(AccessReview.completed_at.desc())
        .limit(1)
    )).scalar_one_or_none()

    return {
        "company_name": company_name,
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
        },
        "risks": {
            "total": len(risks),
            "critical": sum(1 for r in risks if r.risk_level == "critical"),
            "high": sum(1 for r in risks if r.risk_level == "high"),
            "open": sum(1 for r in risks if r.status == "open"),
            "mitigated": sum(1 for r in risks if r.status == "mitigated"),
        },
        "access_review": access_review,
    }


def _build_autofill_prompt(ctx: dict, questions: list[str]) -> str:
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
    else:
        pt_str = "No penetration test on record"

    tr = ctx["training"]
    if tr["total"] > 0:
        rate = round(tr["completed"] / tr["total"] * 100)
        tr_str = f"{tr['total']} records — {tr['completed']} completed ({rate}%), {tr['overdue']} overdue"
    else:
        tr_str = "No training records"

    rs = ctx["risks"]
    rs_str = (
        f"{rs['total']} identified — {rs['critical']} critical, {rs['high']} high; "
        f"{rs['open']} open, {rs['mitigated']} mitigated"
    ) if rs["total"] > 0 else "No risks recorded"

    ar = ctx["access_review"]
    ar_str = (
        f"Most recent: '{ar.title}', period {ar.period}, status: {ar.status}, "
        f"{ar.users_reviewed} users reviewed, {ar.access_changes} access changes"
    ) if ar else "No access reviews on record"

    numbered_qs = "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))

    return f"""You are a compliance expert helping {company_name} fill out a security questionnaire.

Use ONLY the factual information provided. Do not invent specific dates, tool names, or numbers not present in the context. If specific data is unavailable, write a professional answer describing what is in place and note details can be confirmed during due diligence.

COMPANY CONTEXT:
- Company: {company_name}
- Active security integrations: {integrations_str}
- Adopted policies: {policies_str}
- Compliance controls: {mc_str}
- Penetration testing: {pt_str}
- Security training: {tr_str}
- Risk register: {rs_str}
- Access reviews: {ar_str}

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
- Do not fabricate specific tool names, vendors, or dates not in the context"""


async def autofill_questionnaire(
    company_id: uuid.UUID,
    questions: list[str],
    db: AsyncSession,
) -> list[dict]:
    if not settings.groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured on this server.")

    try:
        from groq import AsyncGroq
    except ImportError as exc:
        raise RuntimeError("groq package not installed — add it to requirements.txt") from exc

    ctx = await _gather_company_context(company_id, db)
    prompt = _build_autofill_prompt(ctx, questions)

    client = AsyncGroq(api_key=settings.groq_api_key)
    completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=4000,
    )

    content = completion.choices[0].message.content.strip()

    # Extract JSON array from response (model may wrap it in markdown)
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        raise ValueError("AI response did not contain a valid JSON array")

    raw = json.loads(match.group(0))

    # Normalise to list[{question, answer}] aligned by index
    answer_map = {item["index"]: item["answer"] for item in raw if "index" in item and "answer" in item}
    return [
        {"question": q, "answer": answer_map.get(i + 1, "")}
        for i, q in enumerate(questions)
    ]
