"""AI Audit Package Builder — gathers all compliance data and generates a
comprehensive PDF with AI-written narrative, gap analysis, and recommendations."""
import json
import logging
import re
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

FRAMEWORK_LABELS = {
    "soc2":     "SOC 2 Type II",
    "iso27001": "ISO/IEC 27001",
    "hipaa":    "HIPAA",
    "gdpr":     "GDPR",
    "pci_dss":  "PCI DSS",
    "ccpa":     "CCPA",
    "nist_csf": "NIST CSF",
    "dpdp":     "DPDP Act 2023",
    "cert_in":  "CERT-In Directions 2022",
    "lpdp":     "Serbian LPDP 2018",
    "nis2":     "NIS2 Directive 2022",
    "iso42001": "ISO/IEC 42001:2023",
}

_INT_LABELS = {
    "aws": "AWS", "github": "GitHub", "slack": "Slack",
    "google_workspace": "Google Workspace", "okta": "Okta",
    "azure_ad": "Azure AD", "jira": "Jira", "gitlab": "GitLab",
    "gcp": "GCP", "linear": "Linear", "datadog": "Datadog",
    "pagerduty": "PagerDuty", "sentry": "Sentry", "teams": "Microsoft Teams",
    "stripe": "Stripe", "rippling": "Rippling", "bamboohr": "BambooHR",
    "notion": "Notion", "servicenow": "ServiceNow", "confluence": "Confluence",
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
    from models.score_snapshot import ScoreSnapshot
    from models.training import TrainingRecord
    from models.vendor import Vendor
    from services.compliance_service import get_compliance_score

    company = (
        await db.execute(select(Company).where(Company.id == company_id))
    ).scalar_one()

    score_data = await get_compliance_score(company_id, framework, db)

    now = datetime.now(timezone.utc)
    period_end = now
    period_start = now - timedelta(days=90)

    evidence_rows = list(
        (await db.execute(
            select(Evidence).where(Evidence.company_id == company_id)
        )).scalars().all()
    )

    by_control: dict[str, list] = {}
    _ev_stats: dict = {}
    _int_ev_count: dict[str, int] = {}
    _int_ev_types: dict[str, set] = {}

    for e in evidence_rows:
        by_control.setdefault(e.control, []).append({
            "integration": e.integration,
            "evidence_type": e.evidence_type,
            "source_id": e.source_id,
            "timestamp": e.timestamp.isoformat(),
            "data": e.data or {},
        })
        ctrl_stats = _ev_stats.setdefault(e.control, {})
        et_stats = ctrl_stats.setdefault(e.evidence_type, {
            "count": 0, "integrations": set(), "timestamps": [],
        })
        et_stats["count"] += 1
        et_stats["integrations"].add(e.integration)
        et_stats["timestamps"].append(e.timestamp.isoformat())
        _int_ev_count[e.integration] = _int_ev_count.get(e.integration, 0) + 1
        _int_ev_types.setdefault(e.integration, set()).add(e.evidence_type)

    evidence_stats: dict = {}
    for ctrl, by_type in _ev_stats.items():
        evidence_stats[ctrl] = {
            et: {
                "count": v["count"],
                "integrations": sorted(v["integrations"]),
                "freshest": max(v["timestamps"]),
            }
            for et, v in by_type.items()
        }

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

    score_history_rows = list(
        (await db.execute(
            select(ScoreSnapshot)
            .where(
                ScoreSnapshot.company_id == company_id,
                ScoreSnapshot.framework == framework,
                ScoreSnapshot.snapshot_at >= period_start,
            )
            .order_by(ScoreSnapshot.snapshot_at.asc())
        )).scalars().all()
    )
    # Deduplicate by date keeping the latest entry per day (rows are asc ordered)
    _seen_dates: dict[str, float] = {}
    for s in score_history_rows:
        _seen_dates[s.snapshot_at.strftime("%Y-%m-%d")] = s.overall_score
    score_history = [{"date": d, "score": sc} for d, sc in _seen_dates.items()]

    active_integration_types = {i.integration_type for i in integrations}
    connected_integrations_detail = sorted(
        [
            {
                "name": intg,
                "label": _INT_LABELS.get(intg, intg.replace("_", " ").title()),
                "evidence_count": _int_ev_count.get(intg, 0),
                "evidence_types": sorted(_int_ev_types.get(intg, set())),
            }
            for intg in active_integration_types
        ],
        key=lambda x: -x["evidence_count"],
    )

    return {
        "company_name": company.name,
        "framework": framework,
        "framework_label": FRAMEWORK_LABELS.get(framework, framework.upper()),
        "score_data": score_data,
        "total_evidence": len(evidence_rows),
        "controls_by_category": by_control,
        "evidence_stats": evidence_stats,
        "connected_integrations_detail": connected_integrations_detail,
        "score_history": score_history,
        "period_start": period_start.strftime("%B %d, %Y"),
        "period_end": period_end.strftime("%B %d, %Y"),
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


def _framework_specific_context(framework: str) -> str:
    """Return framework-specific regulatory context to inject into the AI prompt."""
    contexts = {
        "soc2": (
            "Framework Context: SOC 2 Type II evaluates Trust Services Criteria (TSC): "
            "Security, Availability, Processing Integrity, Confidentiality, and Privacy. "
            "The auditor opinion must address whether controls were suitably designed AND "
            "operating effectively over the audit period. Reference the AICPA TSC categories "
            "in your analysis. Management assertion must use formal SOC 2 language."
        ),
        "iso27001": (
            "Framework Context: ISO/IEC 27001:2022 requires demonstrating conformance to "
            "Annex A controls and the ISMS scope. Address clauses 4–10 (context, leadership, "
            "planning, support, operation, performance evaluation, improvement). Highlight "
            "risk treatment decisions and the Statement of Applicability (SoA). Use ISO audit "
            "language: 'conformance', 'nonconformity', 'corrective action'."
        ),
        "hipaa": (
            "Framework Context: HIPAA Security Rule (45 CFR Part 164) requires safeguarding "
            "ePHI through Administrative, Physical, and Technical Safeguards. Address the "
            "required vs. addressable implementation specifications. Reference the annual "
            "Security Risk Analysis requirement (§164.308(a)(1)). Use HIPAA terminology: "
            "'covered entity', 'business associate', 'ePHI', 'minimum necessary standard'."
        ),
        "gdpr": (
            "Framework Context: GDPR requires lawful basis for processing (Art. 6), data "
            "subject rights fulfillment, 72-hour breach notification to supervisory authority "
            "(Art. 33), and data protection by design and by default (Art. 25). Reference "
            "Article numbers in findings. Address controller vs. processor responsibilities "
            "and cross-border transfer mechanisms (SCCs, adequacy decisions)."
        ),
        "pci_dss": (
            "Framework Context: PCI DSS v4.0 has 12 requirements covering network security, "
            "cardholder data protection, vulnerability management, access control, monitoring, "
            "and information security policy. Address the Shared Responsibility Model for "
            "cloud environments. Reference SAQ type if applicable. Use PCI terminology: "
            "'cardholder data environment (CDE)', 'compensating controls', 'ROC'."
        ),
        "ccpa": (
            "Framework Context: CCPA/CPRA grants California consumers rights to know, delete, "
            "opt-out of sale/sharing, and non-discrimination. Businesses must respond to "
            "verifiable consumer requests within 45 days. Address the CPRA amendments: "
            "sensitive personal information, right to correct, and data minimization. "
            "Reference enforcement by the California Privacy Protection Agency (CPPA)."
        ),
        "nist_csf": (
            "Framework Context: NIST CSF 2.0 organizes controls across six Functions: "
            "Govern, Identify, Protect, Detect, Respond, Recover. Use maturity tiers "
            "(Partial/Risk Informed/Repeatable/Adaptive) to characterize each function. "
            "Reference applicable NIST SP 800-53 controls where relevant. Address the "
            "Cybersecurity Supply Chain Risk Management (C-SCRM) component."
        ),
        "dpdp": (
            "Framework Context: India's Digital Personal Data Protection Act 2023 designates "
            "Data Fiduciaries and Data Processors. Key obligations: lawful processing with "
            "consent or legitimate use, Data Principal rights (access, correction, erasure, "
            "grievance redressal), breach notification to DPBI (Data Protection Board of India), "
            "and Significant Data Fiduciary requirements. Reference the DPBI as the enforcement "
            "authority. Use DPDP terminology: 'Data Fiduciary', 'Data Principal', 'DPBI'."
        ),
        "cert_in": (
            "Framework Context: CERT-In Directions 2022 (MeitY) mandate 6-hour incident "
            "reporting to CERT-In for 20 specified incident categories. Requirements include: "
            "ICT infrastructure logging with 180-day retention in India, NTP synchronization "
            "to NIC/NPL/government time servers, virtual asset exchange KYC records for 5 years, "
            "and designated Point of Contact (PoC) registration with CERT-In. Assess compliance "
            "against the 6-hour SLA and reference CERT-In reference numbers where available."
        ),
        "lpdp": (
            "Framework Context: Serbian Law on Personal Data Protection (ZZPL/LPDP, Official "
            "Gazette 87/2018) is Serbia's GDPR-equivalent supervised by the Poverenik "
            "(Commissioner for Information of Public Importance). Key requirements: lawful "
            "processing basis (Art. 5-11), 30-day DSR response, 72-hour breach notification "
            "to Poverenik (Art. 53), DPO registration with Poverenik (Art. 57), ROPA maintenance "
            "(Art. 40), and cross-border transfer mechanisms (Art. 65-74). Reference Poverenik "
            "as the supervisory authority and use LPDP article numbers in findings."
        ),
        "nis2": (
            "Framework Context: NIS2 Directive (EU 2022/2555) applies to essential and important "
            "entities in 18 sectors. Art. 21 mandates 10 cybersecurity measures including risk "
            "management, incident handling, BCP/DR, supply chain security, MFA, and cryptography. "
            "Art. 23 requires 3-stage incident reporting: early warning within 24h, incident "
            "notification within 72h, and final report within 1 month — to national CSIRT or "
            "competent authority. Management bodies are personally liable (Art. 20). Address "
            "NIS2 proportionality between essential vs. important entity obligations."
        ),
        "iso42001": (
            "Framework Context: ISO/IEC 42001:2023 is the first international standard for AI "
            "Management Systems (AIMS), published December 2023. It applies to any organization "
            "that develops, provides, or uses AI-based products and services. The standard follows "
            "Annex SL (aligned with ISO 27001/9001) covering: AIMS scope and context (Cl. 4), "
            "AI policy and leadership (Cl. 5), AI risk assessment and objectives (Cl. 6), "
            "competence and awareness (Cl. 7), AI lifecycle operations including impact assessment "
            "(Cl. 8.3), data governance (Cl. 8.4), development/validation (Cl. 8.5), and human "
            "oversight (Cl. 8.6), plus performance evaluation and continual improvement (Cl. 9-10). "
            "Annex A provides 38 controls across 9 domains covering transparency (A.6.1), "
            "bias/fairness (A.6.2), privacy (A.8.2), AI incident management (A.9.1), and "
            "third-party AI supply chain (A.10.1). Use ISO audit language: 'conformance', "
            "'nonconformity', 'corrective action'. Address AI-specific risks: model bias, "
            "data poisoning, adversarial attacks, opaque decision-making, and regulatory "
            "alignment with the EU AI Act. Reference clause numbers in all findings."
        ),
    }
    return contexts.get(framework, f"Framework Context: {FRAMEWORK_LABELS.get(framework, framework.upper())} compliance assessment.")


async def _generate_ai_narrative(data: dict) -> dict:
    from core.config import settings

    score_data = data["score_data"]
    score = score_data["overall_score"]
    controls = score_data["controls"]
    num_controls = len(controls)
    passing_c = sum(1 for c in controls if c["status"] == "passing")
    failing_c = sum(1 for c in controls if c["status"] == "failing")
    warning_c = sum(1 for c in controls if c["status"] == "warning")
    no_ev_c   = num_controls - passing_c - failing_c - warning_c
    integrations_detail = data.get("connected_integrations_detail", [])
    int_names = ", ".join(i["label"] for i in integrations_detail) if integrations_detail else "no active integrations"
    failing_names = [c["name"] for c in controls if c["status"] == "failing"]
    warning_names = [c["name"] for c in controls if c["status"] == "warning"]
    no_ev_names   = [c["name"] for c in controls if c["status"] not in ("passing", "failing", "warning")]
    status_word = "satisfactory" if score >= 70 else ("developing" if score >= 40 else "early-stage")

    def _template_fallback() -> dict:
        p1 = (
            f"{data['company_name']} achieved an overall {data['framework_label']} compliance score of "
            f"{score}% during the assessment period {data.get('period_start', 'N/A')} through "
            f"{data.get('period_end', 'N/A')}, based on {data['total_evidence']} automated evidence "
            f"records collected across {num_controls} control domains. The overall posture reflects a "
            f"{status_word} compliance programme."
        )
        p2 = (
            f"Evidence was collected from {len(integrations_detail)} active integration(s): {int_names}. "
            f"Of the {num_controls} control domains evaluated, {passing_c} passed automated evidence testing"
            + (f", {warning_c} received exception-noted status" if warning_c else "")
            + (f", {failing_c} failed" if failing_c else "")
            + (f", and {no_ev_c} had insufficient evidence collected" if no_ev_c else "")
            + "."
        )
        gap_parts: list[str] = []
        if failing_names:
            gap_parts.append(f"The following control domains failed automated evidence testing: {', '.join(failing_names)}.")
        if warning_names:
            gap_parts.append(f"Exception-noted domains requiring remediation: {', '.join(warning_names)}.")
        if no_ev_names:
            gap_parts.append(
                f"The following domains had no automated evidence collected and require additional "
                f"integrations or manual attestations: {', '.join(no_ev_names)}."
            )
        p3 = " ".join(gap_parts) if gap_parts else "No material control failures were identified."
        p4 = (
            f"To improve the {data['framework_label']} compliance score, management should prioritise "
            f"connecting additional integrations to provide automated evidence for domains currently "
            f"lacking coverage, addressing all failing and exception-noted controls, and ensuring "
            f"continuous evidence collection throughout the next assessment period."
        )
        exec_summary = f"{p1}\n\n{p2}\n\n{p3}\n\n{p4}"

        if gap_parts:
            gp1 = (
                f"The primary compliance gaps identified during the assessment period relate to "
                + (f"insufficient automated evidence for {len(no_ev_names)} control domains " if no_ev_names else "")
                + (f"{'and ' if no_ev_names and (failing_names or warning_names) else ''}"
                   f"control failures in {', '.join(failing_names + warning_names)}"
                   if failing_names or warning_names else "")
                + ". Root causes include missing integrations and incomplete evidence collection pipelines."
            )
            gp2 = (
                "The absence of automated evidence across multiple control domains creates material "
                "compliance risk and would likely result in a qualified or adverse opinion in an "
                "external audit. Immediate action is required to connect the missing integrations "
                "and establish automated evidence collection."
            )
            gap_analysis = f"{gp1}\n\n{gp2}"
        else:
            gap_analysis = (
                f"Evidence collection is functioning across all {num_controls} control domains. "
                "The compliance programme appears to be operating effectively with no material gaps "
                "identified. Continue monitoring to maintain this posture."
            )

        recs: list[str] = []
        for c in sorted(controls, key=lambda x: x["score"]):
            if c["status"] != "passing" and c.get("missing_types") and len(recs) < 5:
                missing = ", ".join(c["missing_types"][:2])
                recs.append(f"Connect integrations to provide {missing} evidence for the {c['name']} control domain.")
        if len(recs) < 3:
            recs += [
                f"Review and adopt all required {data['framework_label']} compliance policies.",
                "Complete security awareness training for all staff.",
                "Conduct a comprehensive risk assessment and update the risk register.",
            ]
        recs = recs[:7]

        score_q = (
            "operating effectively" if score >= 70 else
            "partially operating with material gaps identified" if score >= 30 else
            "in early stages of implementation with significant gaps requiring remediation"
        )
        assertion = (
            f"{data['company_name']} management is responsible for establishing and maintaining "
            f"effective internal controls over {data['framework_label']} compliance. During the "
            f"assessment period {data.get('period_start', 'N/A')} through {data.get('period_end', 'N/A')}, "
            f"{data['total_evidence']} automated evidence records were collected via {int_names}. "
            f"The overall compliance score of {score}% reflects controls that are {score_q}. "
            + ("Management asserts that controls are suitably designed and operating effectively."
               if score >= 70 else
               "Management acknowledges the gaps identified in this report and commits to implementing "
               "remediation measures to achieve full compliance in the next assessment period.")
        )
        return {"executive_summary": exec_summary, "gap_analysis": gap_analysis,
                "recommendations": recs, "management_assertion": assertion}

    if not settings.anthropic_api_key:
        return _template_fallback()

    risks = data["risks"]
    training = data["training"]
    vendors = data["vendors"]
    pen_tests = data["pen_tests"]
    evidence_stats = data.get("evidence_stats", {})

    control_lines_parts = []
    for c in score_data["controls"]:
        ctrl_stats = evidence_stats.get(c["category"], {})
        et_summary = "; ".join(
            f"{et.replace('_', ' ')}: {v['count']} records via {', '.join(v['integrations'])}"
            for et, v in sorted(ctrl_stats.items())
        ) or "none"
        control_lines_parts.append(
            f"  - {c['name']}: {c['score']}% ({c['status']}) | "
            f"evidence: {et_summary} | "
            f"missing: {', '.join(c['missing_types']) or 'none'}"
        )
    control_lines = "\n".join(control_lines_parts)

    int_summary = "; ".join(
        f"{i['label']} ({i['evidence_count']} records, types: {', '.join(i['evidence_types'][:3])})"
        for i in integrations_detail
    ) or "none connected"

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

    failing_controls = [c["name"] for c in score_data["controls"] if c["status"] == "failing"]
    warning_controls = [c["name"] for c in score_data["controls"] if c["status"] == "warning"]

    framework_context = _framework_specific_context(data["framework"])

    prompt = f"""You are a senior compliance auditor writing a formal AI Audit Package for {data['company_name']}.

Assessment Period: {data.get('period_start', 'N/A')} through {data.get('period_end', 'N/A')}
Framework: {data['framework_label']}
Overall Compliance Score: {score_data['overall_score']}%
Total Evidence Records: {data['total_evidence']}
Active Integrations: {len(integrations_detail)}

{framework_context}

Connected Integrations ({len(integrations_detail)} total): {int_summary}

Control Assessment:
{control_lines}

Failing Controls: {', '.join(failing_controls) or 'none'}
Warning Controls: {', '.join(warning_controls) or 'none'}

Supporting Programs:
- Risk register: {risk_summary}
- Security training: {training_completion}
- Vendor management: {vendor_summary}
- Penetration testing: {pt_summary}
- Policies adopted: {len(data['policies'])}
- Manual controls tracked: {len(data['manual_controls'])}

Produce a formal audit package. Return valid JSON only with these exact keys:
{{
  "executive_summary": "4-paragraph executive summary for board presentation. P1: overall {data['framework_label']} compliance posture with specific score and evidence count. P2: strengths — name the specific integrations providing evidence and which control domains they support. P3: gaps — name the specific failing/warning controls and what evidence types are missing. P4: recommended path forward. Formal audit language. Separate paragraphs with \\n\\n.",
  "management_assertion": "1-paragraph formal management assertion. Start: '{data['company_name']} management is responsible for establishing and maintaining effective internal controls...' Include: what controls exist, which integrations provide automated evidence, the overall score, and the assessment period. End with management's assertion of operating effectiveness. Formal, signable tone. One paragraph only, no line breaks.",
  "gap_analysis": "2-3 paragraphs. P1: technical root cause of failing controls — name each and what evidence types are absent. P2: impact and risk from these gaps referencing the risk register data. P3 (if applicable): warning controls needing remediation. Name specific controls and evidence types. Separate with \\n\\n.",
  "recommendations": ["7 specific, actionable steps. Each: action verb + specific control/integration name from the data + max 35 words. Prioritize by severity."]
}}

Rules: Use ONLY names from the actual data. Use EXACTLY {len(integrations_detail)} integrations and {data['total_evidence']} evidence records — do not round or approximate these numbers. Do not invent tools, metrics, or dates. Write for an experienced auditor. Return only the JSON object with no other text."""

    from anthropic import AsyncAnthropic
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    try:
        message = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3500,
            messages=[{"role": "user", "content": prompt}],
        )
        content = message.content[0].text.strip()
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            fb = _template_fallback()
            return {
                "executive_summary": parsed.get("executive_summary", ""),
                "gap_analysis": parsed.get("gap_analysis", ""),
                "recommendations": parsed.get("recommendations", []),
                "management_assertion": parsed.get("management_assertion", fb["management_assertion"]),
            }
    except Exception:
        logger.exception("Claude narrative generation failed")

    return _template_fallback()


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
            "period_start": data["period_start"],
            "period_end": data["period_end"],
            "overall_score": data["score_data"]["overall_score"],
            "total_evidence": data["total_evidence"],
            "control_scores": data["score_data"]["controls"],
            "controls_by_category": data["controls_by_category"],
            "evidence_stats": data["evidence_stats"],
            "connected_integrations_detail": data["connected_integrations_detail"],
            "score_history": data["score_history"],
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
                    "content": (p.content or "").strip(),
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
            "access_reviews": list({
                (ar.title, ar.period): {
                    "title": ar.title,
                    "period": ar.period,
                    "status": ar.status,
                    "users_reviewed": ar.users_reviewed,
                    "access_changes": ar.access_changes,
                    "completed_at": ar.completed_at.strftime("%Y-%m-%d") if ar.completed_at else "In progress",
                }
                for ar in sorted(data["access_reviews"], key=lambda x: x.users_reviewed)
            }.values()),
            "integrations": data["integrations"],
            "ai_executive_summary": ai["executive_summary"],
            "ai_gap_analysis": ai["gap_analysis"],
            "ai_recommendations": ai["recommendations"],
            "ai_management_assertion": ai["management_assertion"],
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
