import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.plan_gate import require_growth
from models.evidence import Evidence
from models.integration import Integration
from models.manual_control import ManualControl
from models.user import User
from schemas.compliance import (
    ActionPlanResponse,
    AISummaryResponse,
    AssignManualControlRequest,
    ComplianceScoreResponse,
    EvidenceActivityPoint,
    ManualControlItem,
    RemediationResponse,
    ScoreHistoryPoint,
    SetDueDateRequest,
    UpdateManualControlRequest,
)
from services.ai_service import (
    chat_with_advisor,
    generate_action_plan,
    generate_compliance_summary,
    suggest_control_remediation,
)
from services.compliance_service import get_compliance_score, get_compliance_score_at, get_evidence_activity, get_score_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])

# ── Manual control definitions ───────────────────────────────────────────────

_MANUAL_CONTROLS: dict[str, list[dict]] = {
    "soc2": [
        {"control_id": "security_policy", "name": "Information Security Policy",
         "description": "Written security policy documented, approved by management, and reviewed in the last 12 months."},
        {"control_id": "incident_response", "name": "Incident Response Plan",
         "description": "Incident response plan documented, communicated to staff, and tested at least annually."},
        {"control_id": "security_training", "name": "Security Awareness Training",
         "description": "Annual security awareness training completed by all employees."},
        {"control_id": "vendor_risk", "name": "Vendor Risk Management",
         "description": "Third-party vendor risk assessments performed before onboarding and annually thereafter."},
        {"control_id": "background_checks", "name": "Background Checks",
         "description": "Background verification performed for all employees with access to production systems."},
        {"control_id": "bcp", "name": "Business Continuity Plan",
         "description": "Business continuity and disaster recovery plan documented and tested."},
    ],
    "iso27001": [
        {"control_id": "isms_policy", "name": "ISMS Policy",
         "description": "Information Security Management System policy documented and approved by top management."},
        {"control_id": "risk_assessment", "name": "Risk Assessment",
         "description": "Formal risk assessment completed covering all in-scope assets."},
        {"control_id": "statement_of_applicability", "name": "Statement of Applicability",
         "description": "Statement of Applicability (SoA) completed and signed off."},
        {"control_id": "management_review", "name": "Management Review",
         "description": "ISMS management review conducted at planned intervals (at least annually)."},
        {"control_id": "internal_audit", "name": "Internal Audit",
         "description": "Internal audit of the ISMS completed covering all controls."},
        {"control_id": "asset_inventory", "name": "Asset Inventory",
         "description": "Inventory of all information assets documented and maintained."},
    ],
    "hipaa": [
        {"control_id": "privacy_officer", "name": "Privacy Officer Designated",
         "description": "Privacy officer (and Security officer if separate) formally designated."},
        {"control_id": "hipaa_training", "name": "HIPAA Training",
         "description": "HIPAA privacy and security training completed by all workforce members who handle PHI."},
        {"control_id": "baa", "name": "Business Associate Agreements",
         "description": "Business Associate Agreements (BAAs) in place with all vendors who handle PHI."},
        {"control_id": "phi_inventory", "name": "PHI Inventory",
         "description": "Inventory of all PHI data flows and storage locations documented."},
        {"control_id": "breach_response", "name": "Breach Response Procedure",
         "description": "Breach notification procedure documented meeting HIPAA 60-day notification requirement."},
        {"control_id": "risk_analysis", "name": "Security Risk Analysis",
         "description": "Formal security risk analysis of PHI completed as required by the HIPAA Security Rule."},
    ],
    "gdpr": [
        {"control_id": "gdpr_ropa", "name": "Records of Processing Activities",
         "description": "Article 30 records of processing activities maintained and kept up to date."},
        {"control_id": "gdpr_privacy_notice", "name": "Privacy Notice",
         "description": "Transparent privacy notice published covering all data subjects and processing purposes."},
        {"control_id": "gdpr_dsr_procedure", "name": "Data Subject Rights Procedure",
         "description": "Documented procedure for handling DSRs (access, deletion, portability, objection) within 30 days."},
        {"control_id": "gdpr_dpo", "name": "DPO / Privacy Lead Designated",
         "description": "Data Protection Officer or privacy lead appointed where required; contact details published."},
        {"control_id": "gdpr_breach_notification", "name": "Breach Notification Procedure",
         "description": "72-hour breach notification procedure documented and tested."},
        {"control_id": "gdpr_dpia", "name": "Data Protection Impact Assessment",
         "description": "DPIA process defined and conducted for high-risk processing activities."},
        {"control_id": "gdpr_consent", "name": "Consent & Lawful Basis Management",
         "description": "Lawful basis identified for each processing activity; consent records maintained where applicable."},
        {"control_id": "gdpr_data_transfers", "name": "International Data Transfers",
         "description": "Appropriate safeguards (SCCs, adequacy decisions) in place for transfers outside the EEA."},
    ],
    "pci_dss": [
        {"control_id": "pci_network_security", "name": "Network Security Controls",
         "description": "Firewall and network security standards documented; CDE separated from untrusted networks."},
        {"control_id": "pci_cde_scope", "name": "Cardholder Data Environment Scoping",
         "description": "CDE scoped, documented, and reviewed annually; scope minimized through segmentation."},
        {"control_id": "pci_access_control", "name": "Access Control to Cardholder Data",
         "description": "Need-to-know access controls enforced; unique IDs assigned to all personnel with system access."},
        {"control_id": "pci_encryption", "name": "Encryption of Cardholder Data",
         "description": "Cardholder data encrypted in transit (TLS 1.2+) and at rest using strong cryptography."},
        {"control_id": "pci_vulnerability_mgmt", "name": "Vulnerability Management Program",
         "description": "Anti-malware deployed; systems patched promptly; annual penetration test and quarterly scans."},
        {"control_id": "pci_monitoring", "name": "Logging & Monitoring",
         "description": "Audit logs captured for all CDE access; logs reviewed daily; SIEM or equivalent in place."},
        {"control_id": "pci_incident_response", "name": "Incident Response Plan",
         "description": "PCI DSS incident response plan documented, tested annually, and communicated to staff."},
        {"control_id": "pci_third_party", "name": "Third-Party Service Provider Management",
         "description": "TPSP list maintained; compliance responsibility matrix documented; annual review conducted."},
    ],
    "ccpa": [
        {"control_id": "ccpa_privacy_policy", "name": "CCPA-Compliant Privacy Policy",
         "description": "Privacy policy includes CCPA disclosures: categories collected, purposes, and consumer rights."},
        {"control_id": "ccpa_opt_out", "name": "Opt-Out of Sale / Sharing",
         "description": '"Do Not Sell or Share My Personal Information" link implemented and requests honored within 15 days.'},
        {"control_id": "ccpa_data_inventory", "name": "Personal Information Inventory",
         "description": "Inventory of personal information collected, sources, purposes, and third parties documented."},
        {"control_id": "ccpa_dsr_procedure", "name": "Consumer Rights Procedure",
         "description": "Procedure for access, deletion, and correction requests; responded to within 45 days."},
        {"control_id": "ccpa_training", "name": "Employee CCPA Training",
         "description": "All personnel handling consumer personal information trained on CCPA rights and procedures."},
        {"control_id": "ccpa_service_providers", "name": "Service Provider Contracts",
         "description": "Contracts with all service providers include required CCPA data processing restrictions."},
    ],
    "nist_csf": [
        {"control_id": "nist_identify", "name": "Identify — Asset Management",
         "description": "Organizational assets (hardware, software, data) inventoried and risk-prioritized."},
        {"control_id": "nist_protect_access", "name": "Protect — Access Control",
         "description": "Identity management, authentication, and access control implemented across all systems."},
        {"control_id": "nist_protect_training", "name": "Protect — Awareness & Training",
         "description": "Cybersecurity awareness training conducted for all personnel."},
        {"control_id": "nist_detect", "name": "Detect — Anomalies & Events",
         "description": "Monitoring and detection processes in place to identify cybersecurity events."},
        {"control_id": "nist_respond", "name": "Respond — Response Planning",
         "description": "Incident response plan executed during or after a cybersecurity event."},
        {"control_id": "nist_recover", "name": "Recover — Recovery Planning",
         "description": "Recovery processes maintained to restore capabilities impaired by a cybersecurity incident."},
    ],
    "dpdp": [
        # ── Lawful Processing (Sec. 4–7) ──────────────────────────────────────
        {"control_id": "dpdp_notice", "name": "Privacy Notice to Data Principals",
         "description": "Notice provided to data principals before or at the time of collecting personal data, clearly stating: what data is collected, purpose of processing, how to exercise rights, and how to withdraw consent. Notice must be in plain language (Sec. 5)."},
        {"control_id": "dpdp_notice_language", "name": "Notice in Vernacular Languages",
         "description": "Privacy notice available in English and at least one of the 22 languages listed in the Eighth Schedule to the Constitution, as requested by the data principal (Sec. 5(3))."},
        {"control_id": "dpdp_consent_collection", "name": "Consent Collection Mechanism",
         "description": "Mechanism in place to obtain consent that is: free, specific, informed, unconditional, and unambiguous. Consent obtained through a clear affirmative action; no bundled or pre-ticked consents (Sec. 6(1))."},
        {"control_id": "dpdp_consent_withdrawal", "name": "Consent Withdrawal Mechanism",
         "description": "Mechanism for withdrawal of consent is as easy as the mechanism for giving consent. Withdrawal communicated to the data principal promptly. Processing ceases on withdrawal except where required by law (Sec. 6(4))."},
        {"control_id": "dpdp_consent_records", "name": "Consent Records Maintained",
         "description": "Records of all consents obtained, including: what was consented to, when, by whom, and through which channel. Records available for inspection and auditable (Sec. 6)."},
        {"control_id": "dpdp_lawful_basis", "name": "Lawful Basis Documented for All Processing",
         "description": "Every personal data processing activity has a documented lawful basis — consent (Sec. 6) or a specified legitimate use (Sec. 7). Processing register maps each activity to its lawful basis."},
        {"control_id": "dpdp_purpose_limitation", "name": "Purpose Limitation",
         "description": "Personal data collected for a specific, stated purpose and not processed for any other purpose without fresh notice and consent. Data minimisation practised — only data necessary for the stated purpose is collected (Sec. 8(1))."},
        # ── Data Fiduciary Obligations (Sec. 8, 8.3, 10) ─────────────────────
        {"control_id": "dpdp_security_safeguards", "name": "Reasonable Security Safeguards",
         "description": "Appropriate technical and organisational security safeguards implemented to prevent personal data breaches, proportionate to the volume and sensitivity of data processed. Safeguards documented and reviewed annually (Sec. 8)."},
        {"control_id": "dpdp_data_accuracy", "name": "Data Completeness and Accuracy",
         "description": "Personal data is maintained in a complete, accurate, and consistent state for the purpose for which it is processed. Processes in place to update or correct data when a data principal requests it (Sec. 8(4))."},
        {"control_id": "dpdp_retention", "name": "Data Retention and Erasure Policy",
         "description": "Defined retention periods for each category of personal data. Personal data erased when: (a) purpose for which it was collected is met, or (b) consent is withdrawn and no legal requirement to retain. Erasure process documented (Sec. 8.3)."},
        {"control_id": "dpdp_processor_contracts", "name": "Data Processor Agreements",
         "description": "Written agreements in place with all data processors (third parties processing data on behalf of the data fiduciary). Agreements specify: purpose, categories of data, security obligations, and sub-processing restrictions (Sec. 8(2))."},
        {"control_id": "dpdp_dpo", "name": "Data Protection Officer / Consent Manager",
         "description": "A Data Protection Officer (DPO) or equivalent contact designated for Significant Data Fiduciaries. For all data fiduciaries: a Consent Manager or named contact to receive and respond to data principal communications (Sec. 10(1)(a), Sec. 13)."},
        # ── Children's Data (Sec. 9) ─────────────────────────────────────────
        {"control_id": "dpdp_age_verification", "name": "Age Verification Before Processing Children's Data",
         "description": "Verifiable mechanism in place to determine if a user is a child (under 18) before processing their personal data. Parental or guardian consent obtained and verified before processing any child's data (Sec. 9(1))."},
        {"control_id": "dpdp_children_no_tracking", "name": "No Tracking or Targeting of Children",
         "description": "No behavioural monitoring, tracking, or targeted advertising directed at children. No processing of children's data in a manner that causes detrimental effect on their well-being (Sec. 9(3)). Technical controls documented."},
        # ── Data Principal Rights (Sec. 11–14, 17) ───────────────────────────
        {"control_id": "dpdp_right_to_access", "name": "Right to Access Information",
         "description": "Procedure enabling data principals to: (a) obtain a summary of personal data processed, (b) know the identities of data fiduciaries and processors with whom data has been shared, within prescribed timelines (Sec. 11)."},
        {"control_id": "dpdp_right_to_correction", "name": "Right to Correction and Erasure",
         "description": "Procedure enabling data principals to request: (a) correction of inaccurate or misleading personal data, (b) completion of incomplete data, (c) erasure of data no longer needed for the stated purpose. Requests processed within prescribed timelines (Sec. 12)."},
        {"control_id": "dpdp_grievance_officer", "name": "Grievance Officer and Response SLA",
         "description": "A Grievance Officer designated and their name + contact details published on the data fiduciary's website or app. Grievances acknowledged and resolved within prescribed timelines (Sec. 13). Escalation path to Data Protection Board documented."},
        {"control_id": "dpdp_nomination_rights", "name": "Nomination Rights Procedure",
         "description": "Procedure allowing data principals to nominate another individual to exercise their data principal rights in the event of the data principal's death or incapacity. Nomination records maintained (Sec. 14)."},
        # ── Breach Notification (Sec. 8.6) ────────────────────────────────────
        {"control_id": "dpdp_breach_detection", "name": "Personal Data Breach Detection",
         "description": "Technical and organisational capabilities in place to detect personal data breaches in a timely manner. Breach classification criteria documented: what constitutes a reportable breach under DPDP Act Sec. 8.6."},
        {"control_id": "dpdp_breach_dpbi_notification", "name": "DPBI Breach Notification Within 72 Hours",
         "description": "Documented and tested procedure to notify the Data Protection Board of India (DPBI) of a personal data breach in the prescribed form and within the prescribed time (72 hours of becoming aware). Affected data principals notified without undue delay (Sec. 8.6)."},
        # ── Cross-Border Transfers (Sec. 16) ─────────────────────────────────
        {"control_id": "dpdp_cross_border", "name": "Cross-Border Data Transfer Policy",
         "description": "Policy documenting all cross-border personal data transfers, the countries involved, and the legal basis for each transfer. Policy reviewed whenever the Central Government updates the list of restricted countries (Sec. 16)."},
        {"control_id": "dpdp_restricted_countries", "name": "Government-Restricted Country List Enforced",
         "description": "Technical controls in place to prevent transfer of personal data to countries notified by the Central Government as restricted for data transfers. Process to monitor and respond to updates to the restricted country list (Sec. 16)."},
    ],
    "cert_in": [
        {"control_id": "certin_incident_reporting", "name": "6-Hour Cyber Incident Reporting to CERT-In",
         "description": "Process documented and tested to report cyber incidents (data breaches, ransomware, DDoS, unauthorised access, etc.) to CERT-In within 6 hours of becoming aware (Dir. 1)."},
        {"control_id": "certin_point_of_contact", "name": "Designated Point of Contact with CERT-In",
         "description": "A named Point of Contact registered with CERT-In; contact details accurate and up to date; POC capable of receiving and responding to CERT-In advisories (Dir. 5)."},
        {"control_id": "certin_log_retention", "name": "180-Day ICT Log Retention",
         "description": "All ICT system logs (server, network, application, database, security device) retained for a rolling 180 days within Indian jurisdiction and available for submission to CERT-In on request (Dir. 3)."},
        {"control_id": "certin_ntp_sync", "name": "NTP Synchronisation to NIC / NPL",
         "description": "All ICT infrastructure clocks synchronised to NIC or NPL NTP servers (or servers traceable to them) to ensure consistent, accurate timestamps across all logs and systems (Dir. 2)."},
        {"control_id": "certin_incident_response", "name": "Cyber Incident Response Plan",
         "description": "Documented incident response plan covering detection, containment, eradication, recovery, and post-incident review. Plan tested and updated regularly (Dir. 6)."},
        {"control_id": "certin_vulnerability_mgmt", "name": "Vulnerability Assessment & Patch Management",
         "description": "Regular vulnerability assessments and penetration tests conducted. CERT-In advisories monitored; critical patches applied within timelines specified in advisories (Dir. 7)."},
        {"control_id": "certin_access_control", "name": "MFA and Privileged Access Management",
         "description": "Multi-factor authentication enforced for all administrative and privileged accounts. Access granted on least-privilege basis. Privileged sessions logged and monitored (Dir. 8)."},
        {"control_id": "certin_backups", "name": "Backup and Business Continuity",
         "description": "Critical data and systems backed up regularly; backups tested for restorability. Business continuity and disaster recovery plan documented and tested (Dir. 9)."},
        {"control_id": "certin_monitoring", "name": "Network Monitoring and Threat Detection",
         "description": "Network monitoring mechanisms deployed to detect anomalous activity and indicators of compromise. Security alerts reviewed and responded to promptly (Dir. 10)."},
        {"control_id": "certin_hardening", "name": "System Hardening and Secure Configuration",
         "description": "All ICT systems hardened against known attack vectors: default credentials changed, unused ports/services disabled, security configurations applied per best practices (Dir. 12)."},
    ],
}

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/score", response_model=ComplianceScoreResponse)
async def compliance_score(
    framework: str = Query("soc2", description="Compliance framework"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_compliance_score(current_user.company_id, framework, db)


@router.get("/score-history", response_model=list[ScoreHistoryPoint])
async def score_history(
    framework: str = Query("soc2"),
    days: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_score_history(current_user.company_id, framework, days, db)


@router.get("/time-machine")
async def time_machine_score(
    date: str = Query(..., description="ISO date YYYY-MM-DD — must be in the past"),
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the compliance score as it was on `date`.
    Uses evidence.created_at to reconstruct the historical state, so results
    are accurate as long as evidence records are never hard-deleted.
    """
    try:
        target = datetime.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)

    # End of the target day (23:59:59 UTC)
    as_of = target.replace(hour=23, minute=59, second=59, microsecond=0)

    if as_of >= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Date must be in the past.")

    historical = await get_compliance_score_at(current_user.company_id, framework, db, as_of)
    today_data = await get_compliance_score(current_user.company_id, framework, db)

    evidence_count = await db.scalar(
        select(func.count(Evidence.id)).where(
            Evidence.company_id == current_user.company_id,
            Evidence.created_at <= as_of,
        )
    ) or 0

    integration_count = await db.scalar(
        select(func.count(Integration.id)).where(
            Integration.company_id == current_user.company_id,
            Integration.created_at <= as_of,
        )
    ) or 0

    return {
        "as_of": date,
        "framework": framework,
        "historical": historical,
        "today_score": today_data["overall_score"],
        "delta": historical["overall_score"] - today_data["overall_score"],
        "evidence_count": evidence_count,
        "integration_count": integration_count,
    }


@router.get("/evidence-activity", response_model=list[EvidenceActivityPoint])
async def evidence_activity(
    days: int = Query(14, ge=7, le=30),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_evidence_activity(current_user.company_id, days, db)


@router.get("/manual-controls", response_model=list[ManualControlItem])
async def get_manual_controls(
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    definitions = _MANUAL_CONTROLS.get(framework, [])
    if not definitions:
        raise HTTPException(status_code=400, detail=f"Unknown framework: {framework}")

    # Load saved records for this company+framework
    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
        )
    )
    saved = {r.control_id: r for r in result.scalars().all()}

    # Load owner names in a single query
    owner_ids = {r.owner_user_id for r in saved.values() if r.owner_user_id}
    owners: dict = {}
    if owner_ids:
        owner_result = await db.execute(select(User).where(User.id.in_(owner_ids)))
        owners = {u.id: u for u in owner_result.scalars().all()}

    items = []
    for defn in definitions:
        cid = defn["control_id"]
        rec = saved.get(cid)
        owner = owners.get(rec.owner_user_id) if rec and rec.owner_user_id else None
        items.append(ManualControlItem(
            control_id=cid,
            name=defn["name"],
            description=defn["description"],
            status=rec.status if rec else "pending",
            notes=rec.notes if rec else None,
            updated_at=rec.updated_at.isoformat() if rec else None,
            owner_user_id=str(rec.owner_user_id) if rec and rec.owner_user_id else None,
            owner_name=(owner.full_name or owner.email) if owner else None,
            due_date=rec.due_date.isoformat() if rec and rec.due_date else None,
        ))
    return items


@router.put("/manual-controls/{control_id}", response_model=ManualControlItem)
async def update_manual_control(
    control_id: str,
    body: UpdateManualControlRequest,
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    definitions = _MANUAL_CONTROLS.get(framework, [])
    defn = next((d for d in definitions if d["control_id"] == control_id), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Control not found")

    valid_statuses = {"pending", "compliant", "not_applicable"}
    if body.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")

    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
            ManualControl.control_id == control_id,
        )
    )
    rec = result.scalar_one_or_none()

    if rec:
        rec.status = body.status
        rec.notes = body.notes
        rec.updated_by_id = current_user.id
    else:
        rec = ManualControl(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            framework=framework,
            control_id=control_id,
            status=body.status,
            notes=body.notes,
            updated_by_id=current_user.id,
        )
        db.add(rec)

    await db.commit()
    await db.refresh(rec)

    return ManualControlItem(
        control_id=control_id,
        name=defn["name"],
        description=defn["description"],
        status=rec.status,
        notes=rec.notes,
        updated_at=rec.updated_at.isoformat(),
        owner_user_id=str(rec.owner_user_id) if rec.owner_user_id else None,
        due_date=rec.due_date.isoformat() if rec.due_date else None,
    )


@router.patch("/manual-controls/{control_id}/assign", response_model=ManualControlItem)
async def assign_manual_control(
    control_id: str,
    body: AssignManualControlRequest,
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    definitions = _MANUAL_CONTROLS.get(framework, [])
    defn = next((d for d in definitions if d["control_id"] == control_id), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Control not found")

    # Validate owner belongs to same company
    owner = None
    owner_uid = None
    if body.owner_user_id:
        try:
            owner_uid = uuid.UUID(body.owner_user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid owner_user_id")
        owner_result = await db.execute(
            select(User).where(User.id == owner_uid, User.company_id == current_user.company_id)
        )
        owner = owner_result.scalar_one_or_none()
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found in your organisation")

    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
            ManualControl.control_id == control_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        rec = ManualControl(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            framework=framework,
            control_id=control_id,
            status="pending",
            updated_by_id=current_user.id,
        )
        db.add(rec)

    rec.owner_user_id = owner_uid
    await db.commit()
    await db.refresh(rec)

    return ManualControlItem(
        control_id=control_id,
        name=defn["name"],
        description=defn["description"],
        status=rec.status,
        notes=rec.notes,
        updated_at=rec.updated_at.isoformat(),
        owner_user_id=str(rec.owner_user_id) if rec.owner_user_id else None,
        owner_name=(owner.full_name or owner.email) if owner else None,
        due_date=rec.due_date.isoformat() if rec.due_date else None,
    )


@router.patch("/manual-controls/{control_id}/due-date", response_model=ManualControlItem)
async def set_control_due_date(
    control_id: str,
    body: SetDueDateRequest,
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set or clear the SLA due date for a manual control."""
    from datetime import date as date_type
    definitions = _MANUAL_CONTROLS.get(framework, [])
    defn = next((d for d in definitions if d["control_id"] == control_id), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Control not found")

    result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
            ManualControl.control_id == control_id,
        )
    )
    rec = result.scalar_one_or_none()
    if not rec:
        rec = ManualControl(
            id=uuid.uuid4(),
            company_id=current_user.company_id,
            framework=framework,
            control_id=control_id,
            status="pending",
            updated_by_id=current_user.id,
        )
        db.add(rec)

    if body.due_date:
        try:
            rec.due_date = date_type.fromisoformat(body.due_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="due_date must be YYYY-MM-DD")
    else:
        rec.due_date = None

    await db.commit()
    await db.refresh(rec)
    return ManualControlItem(
        control_id=control_id,
        name=defn["name"],
        description=defn["description"],
        status=rec.status,
        notes=rec.notes,
        updated_at=rec.updated_at.isoformat(),
        owner_user_id=str(rec.owner_user_id) if rec.owner_user_id else None,
        due_date=rec.due_date.isoformat() if rec.due_date else None,
    )


@router.post("/manual-controls/{control_id}/remediate", response_model=RemediationResponse)
async def remediate_control(
    control_id: str,
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-generated remediation steps for a pending/failing manual control."""
    definitions = _MANUAL_CONTROLS.get(framework, [])
    defn = next((d for d in definitions if d["control_id"] == control_id), None)
    if not defn:
        raise HTTPException(status_code=404, detail="Control not found")

    # Fetch connected integrations
    int_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    connected = [row[0] for row in int_result.all()]

    try:
        return await suggest_control_remediation(
            control_id=control_id,
            control_name=defn["name"],
            control_description=defn["description"],
            framework=framework,
            connected_integrations=connected,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/action-plan", response_model=ActionPlanResponse)
async def action_plan(
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """AI-generated prioritised action plan for the company's compliance posture."""
    try:
        return await generate_action_plan(current_user.company_id, framework, db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/readiness")
async def readiness(
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a readiness score (0-100) with estimated weeks to certification."""
    score_data = await get_compliance_score(current_user.company_id, framework, db)
    overall = score_data["overall_score"]

    # Manual controls completion rate
    definitions = _MANUAL_CONTROLS.get(framework, [])
    mc_result = await db.execute(
        select(ManualControl).where(
            ManualControl.company_id == current_user.company_id,
            ManualControl.framework == framework,
        )
    )
    saved = {r.control_id: r for r in mc_result.scalars().all()}
    compliant = sum(1 for d in definitions if saved.get(d["control_id"]) and saved[d["control_id"]].status == "compliant")
    mc_pct = int(compliant / len(definitions) * 100) if definitions else 0

    # Blended readiness: 70% automated controls, 30% manual controls
    readiness_score = int(overall * 0.70 + mc_pct * 0.30)

    # Estimate weeks at current pace (heuristic)
    if readiness_score >= 90:
        weeks_estimate = 0
        stage = "ready"
    elif readiness_score >= 75:
        weeks_estimate = 3
        stage = "final_push"
    elif readiness_score >= 55:
        weeks_estimate = 8
        stage = "in_progress"
    elif readiness_score >= 30:
        weeks_estimate = 16
        stage = "early"
    else:
        weeks_estimate = 24
        stage = "just_started"

    controls = score_data.get("controls", [])
    passing = sum(1 for c in controls if c["status"] == "passing")
    failing = sum(1 for c in controls if c["status"] == "failing")
    no_evidence = sum(1 for c in controls if c["status"] == "no_evidence")

    return {
        "framework": framework,
        "readiness_score": readiness_score,
        "automated_score": overall,
        "manual_score": mc_pct,
        "weeks_estimate": weeks_estimate,
        "stage": stage,
        "manual_total": len(definitions),
        "manual_compliant": compliant,
        "controls_passing": passing,
        "controls_failing": failing,
        "controls_no_evidence": no_evidence,
        "controls_total": len(controls),
    }


@router.get("/drift-events")
async def list_drift_events(
    limit: int = 50,
    framework: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return recent control drift events for the current company, newest first."""
    from models.control_drift_event import ControlDriftEvent
    from sqlalchemy import select

    q = (
        select(ControlDriftEvent)
        .where(ControlDriftEvent.company_id == current_user.company_id)
        .order_by(ControlDriftEvent.detected_at.desc())
        .limit(min(limit, 200))
    )
    if framework:
        q = q.where(ControlDriftEvent.framework == framework)

    result = await db.execute(q)
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "framework": e.framework,
            "control_category": e.control_category,
            "control_name": e.control_name,
            "previous_status": e.previous_status,
            "new_status": e.new_status,
            "is_regression": e.is_regression,
            "trigger_integration": e.trigger_integration,
            "detected_at": e.detected_at.isoformat(),
        }
        for e in events
    ]


@router.post("/ai-summary", response_model=AISummaryResponse)
async def ai_summary(
    framework: str = Query("soc2"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_growth),
):
    score_data = await get_compliance_score(current_user.company_id, framework, db)
    try:
        summary = await generate_compliance_summary(framework, score_data)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("AI summary generation failed for company=%s framework=%s", current_user.company_id, framework)
        raise HTTPException(status_code=503, detail="AI summary temporarily unavailable. Try again shortly.")

    return AISummaryResponse(
        summary=summary,
        framework=framework,
        overall_score=score_data["overall_score"],
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


# ── Advisor chat ──────────────────────────────────────────────────────────────

class AdvisorChatRequest(BaseModel):
    framework: str
    message: str
    history: list[dict] = []


class AdvisorChatResponse(BaseModel):
    reply: str


@router.post("/advisor/chat", response_model=AdvisorChatResponse)
async def advisor_chat(
    body: AdvisorChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_growth),
):
    score_data = await get_compliance_score(current_user.company_id, body.framework, db)
    integrations_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    connected_integrations = [row[0] for row in integrations_result.all()]
    try:
        reply = await chat_with_advisor(body.framework, score_data, body.message, body.history, connected_integrations)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Advisor chat failed for company=%s framework=%s", current_user.company_id, body.framework)
        raise HTTPException(status_code=503, detail="Advisor temporarily unavailable. Try again shortly.")
    return AdvisorChatResponse(reply=reply)
