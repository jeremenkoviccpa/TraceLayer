"""AI Audit Package Builder — gathers all compliance data and generates a
comprehensive PDF with AI-written narrative, gap analysis, and recommendations."""
import json
import logging
import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

FRAMEWORK_LABELS = {
    "soc2": "SOC 2 Type II",
    "iso27001": "ISO/IEC 27001",
    "hipaa": "HIPAA",
    "gdpr": "GDPR",
    "pci_dss": "PCI DSS",
    "ccpa": "CCPA",
    "nist_csf": "NIST CSF",
}

_INT_LABELS = {
    "aws": "AWS", "github": "GitHub", "slack": "Slack",
    "google_workspace": "Google Workspace", "okta": "Okta",
    "azure_ad": "Azure AD", "jira": "Jira", "gitlab": "GitLab",
    "gcp": "GCP", "linear": "Linear", "datadog": "Datadog",
    "pagerduty": "PagerDuty", "sentry": "Sentry", "teams": "Microsoft Teams",
    "stripe": "Stripe", "rippling": "Rippling", "bamboohr": "BambooHR",
    "notion": "Notion",
}


def _risk_level(likelihood: int, impact: int) -> str:
    score = likelihood * impact
    if score >= 15:
        return "critical"
    if score >= 10:
        return "high"
    if score >= 5:
        return "medium"
    return "low"


async def _gather_all_data(
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
) -> dict:
    from sqlalchemy import select
    from models.access_review import AccessReview
    from models.company import Company
    from models.evidence import Evidence
    from models.integration import Integration
    from models.manual_control import ManualControl
    from models.pen_test import PenTest
    from models.policy import Policy
    from models.risk import Risk
    from models.training import TrainingRecord
    from models.vendor import Vendor
    from services.compliance_service import get_compliance_score

    company = (
        await db.execute(select(Company).where(Company.id == company_id))
    ).scalar_one()

    score_data = await get_compliance_score(company_id, framework, db)

    evidence_rows = list(
        (await db.execute(
            select(Evidence).where(Evidence.company_id == company_id)
        )).scalars().all()
    )
    by_control: dict[str, list] = {}
    for e in evidence_rows:
        by_control.setdefault(e.control, []).append({
            "integration": e.integration,
            "evidence_type": e.evidence_type,
            "source_id": e.source_id,
            "timestamp": e.timestamp.isoformat(),
        })

    manual_controls = list(
        (await db.execute(
            select(ManualControl).where(ManualControl.company_id == company_id)
        )).scalars().all()
    )

    policies = list(
        (await db.execute(
            select(Policy).where(Policy.company_id == company_id)
        )).scalars().all()
    )

    pen_tests = list(
        (await db.execute(
            select(PenTest)
            .where(PenTest.company_id == company_id)
            .order_by(PenTest.conducted_at.desc())
        )).scalars().all()
    )

    training = list(
        (await db.execute(
            select(TrainingRecord).where(TrainingRecord.company_id == company_id)
        )).scalars().all()
    )

    risks = list(
        (await db.execute(
            select(Risk)
            .where(Risk.company_id == company_id)
            .order_by(Risk.likelihood.desc(), Risk.impact.desc())
        )).scalars().all()
    )

    vendors = list(
        (await db.execute(
            select(Vendor)
            .where(Vendor.company_id == company_id)
            .order_by(Vendor.risk_level.desc())
        )).scalars().all()
    )

    access_reviews = list(
        (await db.execute(
            select(AccessReview)
            .where(AccessReview.company_id == company_id)
            .order_by(AccessReview.completed_at.desc())
        )).scalars().all()
    )

    integrations = list(
        (await db.execute(
            select(Integration).where(
                Integration.company_id == company_id,
                Integration.status == "active",
            )
        )).scalars().all()
    )

    return {
        "company_name": company.name,
        "framework": framework,
        "framework_label": FRAMEWORK_LABELS.get(framework, framework.upper()),
        "score_data": score_data,
        "total_evidence": len(evidence_rows),
        "controls_by_category": by_control,
        "manual_controls": manual_controls,
        "policies": policies,
        "pen_tests": pen_tests,
        "training": training,
        "risks": risks,
        "vendors": vendors,
        "access_reviews": access_reviews,
        "integrations": [
            _INT_LABELS.get(i.integration_type, i.integration_type)
            for i in integrations
        ],
    }


async def _generate_ai_narrative(data: dict) -> dict:
    fallback = {
        "executive_summary": (
            f"{data['company_name']} is pursuing {data['framework_label']} compliance. "
            "Configure GROQ_API_KEY to enable AI-generated narrative."
        ),
        "gap_analysis": "",
        "recommendations": [],
    }

    from core.config import settings
    if not settings.groq_api_key:
        return fallback

    try:
        from groq import AsyncGroq
    except ImportError:
        return fallback

    score_data = data["score_data"]
    risks = data["risks"]
    training = data["training"]
    vendors = data["vendors"]
    pen_tests = data["pen_tests"]

    control_lines = "\n".join(
        f"  - {c['name']}: {c['score']}% ({c['status']}) | "
        f"evidence: {c['evidence_count']} | "
        f"missing: {', '.join(c['missing_types']) or 'none'}"
        for c in score_data["controls"]
    )

    risk_summary = (
        f"{len(risks)} risks — "
        f"{sum(1 for r in risks if _risk_level(r.likelihood, r.impact) == 'critical')} critical, "
        f"{sum(1 for r in risks if _risk_level(r.likelihood, r.impact) == 'high')} high, "
        f"{sum(1 for r in risks if r.status == 'open')} open"
    ) if risks else "No risks logged"

    training_completion = (
        f"{round(sum(1 for t in training if t.status == 'completed') / len(training) * 100)}% completion "
        f"({sum(1 for t in training if t.status == 'overdue')} overdue of {len(training)} total)"
        if training else "No training records"
    )

    vendor_summary = (
        f"{len(vendors)} vendors — "
        f"{sum(1 for v in vendors if v.risk_level in ('critical', 'high'))} rated high/critical risk"
    ) if vendors else "No vendors tracked"

    pt_summary = (
        f"Most recent: {pen_tests[0].vendor_name} — "
        f"{pen_tests[0].critical_count}C / {pen_tests[0].high_count}H findings, "
        f"status: {pen_tests[0].status}"
        if pen_tests else "No penetration tests on record"
    )

    prompt = f"""You are a senior compliance advisor writing a formal AI Audit Package for {data['company_name']}.

Framework: {data['framework_label']}
Overall Compliance Score: {score_data['overall_score']}%

Control Status:
{control_lines}

Supporting Programs:
- Risk register: {risk_summary}
- Security training: {training_completion}
- Vendor management: {vendor_summary}
- Penetration testing: {pt_summary}
- Policies adopted: {len(data['policies'])}
- Manual controls tracked: {len(data['manual_controls'])}
- Active integrations: {len(data['integrations'])}

Produce a formal audit package narrative. Return valid JSON only with these exact keys:
{{
  "executive_summary": "3-4 paragraph executive summary suitable for a board presentation. Paragraph 1: overall compliance posture for {data['framework_label']}. Paragraph 2: strengths — what evidence collection and controls are working well. Paragraph 3: key gaps and risk exposure. Paragraph 4: path forward. Use formal, precise language. Separate paragraphs with \\n\\n.",
  "gap_analysis": "2-3 paragraph technical gap analysis. Name specific control names and evidence types that are missing or insufficient. Address highest-priority gaps first. Separate paragraphs with \\n\\n.",
  "recommendations": ["5 specific, actionable remediation steps. Each must start with a strong action verb. Reference specific control names or evidence types from the data. Max 30 words each."]
}}

Rules: Use actual control names and numbers from the data. Do not fabricate tool names or dates. Write for an experienced auditor. Return only the JSON object with no other text."""

    client = AsyncGroq(api_key=settings.groq_api_key)
    try:
        completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1800,
        )
        content = completion.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            return {
                "executive_summary": parsed.get("executive_summary", ""),
                "gap_analysis": parsed.get("gap_analysis", ""),
                "recommendations": parsed.get("recommendations", []),
            }
    except Exception:
        logger.exception("Groq narrative generation failed")

    return fallback


async def generate_audit_package(
    report_id: uuid.UUID,
    company_id: uuid.UUID,
    framework: str,
    db: AsyncSession,
) -> None:
    """Generate the AI audit package PDF, upload to storage, and mark the report complete."""
    from sqlalchemy import select
    from core.config import settings
    from models.report import Report
    from reports.audit_package_generator import render_audit_package_pdf
    from services.storage_service import upload_bytes

    report = (
        await db.execute(
            select(Report).where(Report.id == report_id, Report.company_id == company_id)
        )
    ).scalar_one_or_none()

    if not report:
        raise ValueError("Report not found")

    try:
        data = await _gather_all_data(company_id, framework, db)
        ai = await _generate_ai_narrative(data)
        now = datetime.now(timezone.utc)

        context = {
            "report_id": str(report_id),
            "company_name": data["company_name"],
            "framework": framework,
            "framework_label": data["framework_label"],
            "generated_at": now.strftime("%B %d, %Y"),
            "generated_at_full": now.strftime("%Y-%m-%d %H:%M UTC"),
            "overall_score": data["score_data"]["overall_score"],
            "total_evidence": data["total_evidence"],
            "control_scores": data["score_data"]["controls"],
            "controls_by_category": data["controls_by_category"],
            "manual_controls": [
                {
                    "control_id": m.control_id,
                    "framework": m.framework,
                    "status": m.status,
                    "notes": m.notes or "",
                    "updated_at": m.updated_at.strftime("%Y-%m-%d") if m.updated_at else "",
                }
                for m in data["manual_controls"]
            ],
            "policies": [
                {
                    "name": p.slug.replace("_", " ").replace("-", " ").title(),
                    "slug": p.slug,
                    "has_content": bool(p.content and p.content.strip()),
                    "updated_at": p.updated_at.strftime("%Y-%m-%d") if p.updated_at else "",
                }
                for p in data["policies"]
            ],
            "pen_tests": [
                {
                    "vendor_name": pt.vendor_name,
                    "status": pt.status,
                    "conducted_at": pt.conducted_at.strftime("%Y-%m-%d") if pt.conducted_at else "N/A",
                    "critical_count": pt.critical_count,
                    "high_count": pt.high_count,
                    "medium_count": pt.medium_count,
                    "low_count": pt.low_count,
                    "summary": pt.summary or "",
                }
                for pt in data["pen_tests"]
            ],
            "training": [
                {
                    "title": t.title,
                    "assignee_email": t.assignee_email,
                    "status": t.status,
                    "due_date": t.due_date.strftime("%Y-%m-%d") if t.due_date else "",
                    "completed_at": t.completed_at.strftime("%Y-%m-%d") if t.completed_at else "",
                }
                for t in data["training"]
            ],
            "risks": [
                {
                    "title": r.title,
                    "category": r.category,
                    "likelihood": r.likelihood,
                    "impact": r.impact,
                    "risk_level": _risk_level(r.likelihood, r.impact),
                    "status": r.status,
                }
                for r in data["risks"]
            ],
            "vendors": [
                {
                    "name": v.name,
                    "category": v.category,
                    "risk_level": v.risk_level,
                    "soc2_certified": v.soc2_certified,
                    "iso27001_certified": v.iso27001_certified,
                    "hipaa_certified": v.hipaa_certified,
                    "review_date": v.review_date.strftime("%Y-%m-%d") if v.review_date else "Not reviewed",
                }
                for v in data["vendors"]
            ],
            "access_reviews": [
                {
                    "title": ar.title,
                    "period": ar.period,
                    "status": ar.status,
                    "users_reviewed": ar.users_reviewed,
                    "access_changes": ar.access_changes,
                    "completed_at": ar.completed_at.strftime("%Y-%m-%d") if ar.completed_at else "In progress",
                }
                for ar in data["access_reviews"]
            ],
            "integrations": data["integrations"],
            "ai_executive_summary": ai["executive_summary"],
            "ai_gap_analysis": ai["gap_analysis"],
            "ai_recommendations": ai["recommendations"],
        }

        pdf_bytes = render_audit_package_pdf(context)
        bucket = settings.storage_bucket or "reports"
        path = f"audit-packages/{company_id}/{report_id}.pdf"
        upload_bytes(bucket, path, pdf_bytes, "application/pdf")

        report.status = "complete"
        report.generated_at = now
        report.file_url = f"/v1/reports/{report_id}/download?format=pdf"
        report.storage_bucket = bucket
        report.storage_path = path
        report.file_name = f"{framework}_audit_package.pdf"
        report.mime_type = "application/pdf"
        report.file_size = len(pdf_bytes)
        await db.commit()

    except Exception:
        logger.exception("Audit package generation failed: report_id=%s", report_id)
        report.status = "error"
        await db.commit()
        raise
