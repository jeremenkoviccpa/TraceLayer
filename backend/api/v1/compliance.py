import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from core.plan_gate import require_growth
from models.control_exclusion import ControlExclusion
from models.evidence import Evidence
from models.integration import Integration
from models.manual_control import ManualControl
from models.risk_exception import RiskException
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
        # ── Incident Reporting (Dir.1, 5) ─────────────────────────────────────
        {"control_id": "certin_incident_reporting", "name": "6-Hour Cyber Incident Reporting to CERT-In",
         "description": "Documented and tested process to report cyber incidents to CERT-In within 6 hours of becoming aware. Reportable incidents include: data breaches, ransomware, DDoS, unauthorised access, identity theft, phishing, malicious code attacks, and compromise of critical systems (Dir. 1)."},
        {"control_id": "certin_incident_report_format", "name": "Incident Reports in Prescribed CERT-In Format",
         "description": "All incident reports to CERT-In submitted using the prescribed format containing: nature of incident, affected systems, IPs involved, date/time of detection, impact assessment, and steps taken. Report template maintained and available to the incident response team (Dir. 1)."},
        {"control_id": "certin_point_of_contact", "name": "Designated Point of Contact with CERT-In",
         "description": "A named Point of Contact (PoC) registered with CERT-In with accurate name, designation, email, and phone number. PoC details updated with CERT-In whenever they change. PoC capable of receiving CERT-In advisories and coordinating incident reports 24×7 (Dir. 5)."},
        # ── IT Infrastructure & NTP (Dir.2, 12) ──────────────────────────────
        {"control_id": "certin_ntp_sync", "name": "NTP Synchronisation to NIC / NPL",
         "description": "All ICT infrastructure clocks (servers, network devices, applications, security tools) synchronised to NIC or NPL NTP servers, or to servers traceable to NIC/NPL. NTP configuration documented and verified. Consistent timestamps across all logs and systems (Dir. 2)."},
        {"control_id": "certin_hardening", "name": "System Hardening and Secure Configuration",
         "description": "All ICT systems, network devices, servers, and applications hardened before deployment: default credentials changed, unnecessary accounts disabled, unused ports/services/protocols turned off, and security configurations applied per CIS or equivalent baseline (Dir. 12)."},
        {"control_id": "certin_config_audit", "name": "Annual Security Configuration Review",
         "description": "Annual review of security configurations across all ICT systems against hardening baselines. Findings tracked to remediation. Review covers: OS hardening, network device configs, cloud security group rules, database configurations, and application server settings (Dir. 12)."},
        # ── Log Management (Dir.3) ────────────────────────────────────────────
        {"control_id": "certin_log_retention", "name": "180-Day ICT Log Retention",
         "description": "All ICT system logs retained for a rolling 180-day period: server logs, network logs, application logs, database logs, and security device logs. Logs available for immediate submission to CERT-In on request. Log sources enumerated and coverage gaps tracked (Dir. 3)."},
        {"control_id": "certin_log_jurisdiction", "name": "Logs Stored Within Indian Jurisdiction",
         "description": "All ICT logs mandatorily stored within India's geographical boundaries. Cross-border log replication or offshoring documented and restricted. Cloud storage regions confirmed as Indian data centres. Compliance with this requirement evidenced by storage configuration records (Dir. 3)."},
        # ── KYC for Service Providers (Dir.4) ────────────────────────────────
        {"control_id": "certin_kyc_subscribers", "name": "KYC of Subscribers and Customers",
         "description": "For data centres, VPS providers, cloud service providers, and VPN service providers: register and maintain accurate customer information including validated names, addresses, contact numbers, email IDs, IP addresses allotted and used, registration/expiration dates, and purpose of service (Dir. 4)."},
        {"control_id": "certin_kyc_retention", "name": "5-Year Customer Data Retention",
         "description": "Customer KYC data maintained for a minimum of 5 years or such longer duration as mandated by applicable law. Data available for disclosure to CERT-In or law enforcement on request. Retention schedule documented and enforced (Dir. 4)."},
        # ── Incident Response (Dir.6) ─────────────────────────────────────────
        {"control_id": "certin_incident_response", "name": "Cyber Incident Response Plan",
         "description": "Documented cyber incident response plan covering: detection, triage, containment, eradication, recovery, and post-incident review. Roles and responsibilities defined. Plan reviewed and updated at least annually and after any major incident. Tabletop exercises conducted regularly (Dir. 6)."},
        {"control_id": "certin_post_incident_review", "name": "Post-Incident Review and Lessons Learned",
         "description": "Post-incident review conducted after every significant cyber incident. Review documents: root cause, timeline, containment actions, recovery steps, and lessons learned. Findings used to update the incident response plan, hardening baselines, and monitoring rules (Dir. 6)."},
        # ── Vulnerability Management (Dir.7) ─────────────────────────────────
        {"control_id": "certin_vulnerability_mgmt", "name": "Vulnerability Assessments and Penetration Testing",
         "description": "Regular vulnerability assessments (at minimum annually and after significant infrastructure changes) and penetration tests conducted on all internet-facing and internal systems. Critical findings remediated within 30 days; high within 90 days. VA/PT reports retained (Dir. 7)."},
        {"control_id": "certin_advisory_response", "name": "CERT-In Advisory Monitoring and Response",
         "description": "Process in place to receive, review, and act on CERT-In security advisories and alerts. Critical patches and mitigations applied within the timelines specified in the advisory. Advisory response log maintained showing: advisory reference, date received, action taken, and closure date (Dir. 7)."},
        # ── Access Control (Dir.8) ────────────────────────────────────────────
        {"control_id": "certin_access_control", "name": "MFA on All Administrative and Privileged Accounts",
         "description": "Multi-factor authentication enforced for all administrative, privileged, and remote access accounts without exception. MFA bypass procedures documented and subject to approval. Access provisioned on least-privilege and need-to-know basis. Periodic access reviews conducted (Dir. 8)."},
        {"control_id": "certin_privileged_logging", "name": "Privileged Session Logging and Monitoring",
         "description": "All privileged and administrative sessions logged with full activity capture (commands executed, files accessed, configuration changes). Logs tamper-proof and reviewed regularly. Alerts configured for suspicious privileged activity. Session recording retained for at least 180 days (Dir. 8)."},
        # ── Resilience (Dir.9) ────────────────────────────────────────────────
        {"control_id": "certin_backups", "name": "Regular Backups of Critical Data and Systems",
         "description": "All critical data and systems backed up on a regular schedule (daily for critical systems, weekly for others). Backups encrypted and stored separately from production systems. Backup schedule documented with coverage list and retention periods (Dir. 9)."},
        {"control_id": "certin_backup_testing", "name": "Backup Restoration Testing and BCP/DR",
         "description": "Backup restoration tested at minimum quarterly for critical systems to confirm recoverability. Business continuity and disaster recovery (BCP/DR) plan documented with RTO and RPO targets. DR plan tested annually with results and gaps recorded (Dir. 9)."},
        # ── Monitoring (Dir.10) ───────────────────────────────────────────────
        {"control_id": "certin_monitoring", "name": "Network and System Monitoring for Threat Detection",
         "description": "Continuous monitoring deployed across all network segments and critical systems: SIEM or equivalent aggregating logs, anomaly detection rules configured, alerts triaged by a responsible team. Indicators of Compromise (IoCs) from CERT-In threat feeds integrated into detection rules (Dir. 10)."},
        # ── Endpoint Security (Dir.11) ────────────────────────────────────────
        {"control_id": "certin_endpoint_security", "name": "Endpoint Protection on All Devices",
         "description": "Up-to-date endpoint detection and response (EDR) or antivirus software deployed on all workstations, servers, and mobile devices accessing organisational systems. Signatures and agents updated automatically. Devices with outdated protection quarantined until remediated (Dir. 11)."},
        {"control_id": "certin_device_management", "name": "Unauthorised Device Prevention and Encryption",
         "description": "Unauthorised devices blocked from connecting to organisational networks (NAC or equivalent). All endpoints storing sensitive or organisational data encrypted with full-disk encryption. Mobile device management (MDM) policy enforced. BYOD devices scoped and controlled (Dir. 11)."},
    ],
    # ── Serbian LPDP (Zakon o zaštiti podataka o ličnosti, Official Gazette 87/2018) ──
    "lpdp": [
        # Art. 5-11: Lawful Processing
        {"control_id": "lpdp_lawful_basis", "name": "Lawful Basis Documented for All Processing Activities",
         "description": "A documented lawful basis (consent, contract, legal obligation, vital interests, public interest, or legitimate interests) exists for every personal data processing activity and is recorded in the ROPA. Lawful basis reviewed when processing purposes change (Art. 5-11 LPDP)."},
        {"control_id": "lpdp_consent_mechanism", "name": "Consent Collection and Withdrawal Mechanism",
         "description": "Where consent is the lawful basis: consent obtained in a freely given, specific, informed, and unambiguous manner. Consent records maintained. Withdrawal mechanism as easy as giving consent. Consent renewed when processing purposes change (Art. 15-16 LPDP)."},
        {"control_id": "lpdp_privacy_notice", "name": "Privacy Notice Provided at Collection",
         "description": "Clear and plain-language privacy notice provided to data subjects at or before collection of their personal data. Notice contains: identity of controller, processing purposes, lawful basis, recipients, retention periods, data subject rights, and right to lodge complaint with Poverenik (Art. 23-25 LPDP)."},
        # Art. 26-39: Data Subject Rights
        {"control_id": "lpdp_dsr_procedure", "name": "Data Subject Rights Request Procedure",
         "description": "Written procedure exists for handling requests to access, rectify, erase, restrict processing, and port personal data. Requests responded to within 30 days (extendable to 90 days for complex cases with notification). Request log maintained with dates and outcomes (Art. 26-39 LPDP)."},
        {"control_id": "lpdp_right_to_erasure", "name": "Right to Erasure (Right to be Forgotten)",
         "description": "Process in place to erase personal data on request where: the data is no longer needed, consent is withdrawn, or the processing is unlawful. Erasure propagated to processors and notified to third parties where feasible. Erasure exceptions documented (Art. 30 LPDP)."},
        {"control_id": "lpdp_right_to_object", "name": "Right to Object and Restrict Processing",
         "description": "Process to honour objections to processing based on legitimate interests and direct marketing. Processing restricted upon request while objection is considered. Right to object communicated clearly in privacy notice (Art. 37-39 LPDP)."},
        # Art. 40-50: Controller Obligations
        {"control_id": "lpdp_ropa", "name": "Records of Processing Activities (ROPA) Maintained",
         "description": "ROPA maintained listing all processing activities with: controller details, processing purposes, lawful basis, data categories, recipients, cross-border transfer details, retention schedules, and security measures. ROPA available to Poverenik on request. Reviewed and updated at least annually (Art. 40-42 LPDP)."},
        {"control_id": "lpdp_dpa_contracts", "name": "Data Processing Agreements with All Processors",
         "description": "Written data processing agreement (DPA) containing all required Art. 45 LPDP clauses signed with every processor before processing begins. DPA covers: processing scope, instructions, confidentiality, security, sub-processor management, audit rights, and post-contract data deletion. Processor list maintained (Art. 44-45 LPDP)."},
        {"control_id": "lpdp_privacy_by_design", "name": "Data Protection by Design and by Default",
         "description": "Data protection principles embedded into processing systems from design phase. Default settings collect minimum necessary personal data. Privacy impact considered for all new or changed processing activities. Data minimisation, pseudonymisation, and storage limitation implemented by default (Art. 43 LPDP)."},
        # Art. 54-56: DPIA
        {"control_id": "lpdp_dpia", "name": "Data Protection Impact Assessment (DPIA)",
         "description": "DPIA conducted before commencing high-risk processing: systematic profiling, large-scale processing of special categories, or large-scale systematic monitoring of public areas. Poverenik consulted before processing if residual risk remains high. DPIA documents maintained (Art. 54-56 LPDP)."},
        # Art. 49: Security Measures
        {"control_id": "lpdp_security_measures", "name": "Technical and Organisational Security Measures",
         "description": "Appropriate technical and organisational security measures implemented considering state of the art, cost, and risk: pseudonymisation, encryption, ongoing confidentiality/integrity/availability/resilience of systems, ability to restore data after incident, regular security testing. Measures documented (Art. 49 LPDP)."},
        # Art. 53: Breach Notification
        {"control_id": "lpdp_breach_detection", "name": "Personal Data Breach Detection Capability",
         "description": "Technical controls in place to detect personal data breaches including: SIEM monitoring, DLP alerts, anomaly detection, and endpoint threat detection. Breach detection process documented with escalation path to the person responsible for notifying Poverenik (Art. 53 LPDP)."},
        {"control_id": "lpdp_breach_poverenik", "name": "72-Hour Breach Notification to Poverenik",
         "description": "Process in place to notify the Poverenik (Commissioner for Information of Public Importance and Personal Data Protection) within 72 hours of becoming aware of a personal data breach that is likely to result in risk to individuals. Notification contains: nature of breach, categories and approximate number of individuals affected, and measures taken. Breach register maintained (Art. 53 LPDP)."},
        {"control_id": "lpdp_breach_individual", "name": "High-Risk Breach Notification to Individuals",
         "description": "Process to notify affected individuals without undue delay when a breach is likely to result in high risk to their rights and freedoms. Communication in clear and plain language. Exceptions documented (law enforcement exemption, technical measures rendering data unintelligible, disproportionate effort). Poverenik consulted when individual notification is deferred (Art. 53 LPDP)."},
        # Art. 57-61: DPO
        {"control_id": "lpdp_dpo", "name": "Data Protection Officer Appointed and Registered",
         "description": "DPO appointed where mandatory (public authorities, large-scale systematic monitoring, large-scale special category processing). DPO contact details published and communicated to data subjects. DPO registered with Poverenik. DPO provided with resources and access to data. DPO not given other tasks causing conflict of interest (Art. 57-61 LPDP)."},
        # Art. 65-74: Cross-border Transfers
        {"control_id": "lpdp_transfer_safeguards", "name": "Cross-Border Data Transfer Safeguards",
         "description": "Personal data transferred outside Serbia only to countries/organisations with adequate protection (Poverenik adequacy list), or using appropriate safeguards: standard contractual clauses, binding corporate rules, or approved codes of conduct. Transfer impact assessment conducted for high-risk transfers. Data flow inventory documents all cross-border transfers (Art. 65-74 LPDP)."},
    ],
    # ── NIS2 Directive (EU 2022/2555) ────────────────────────────────────────────
    "nis2": [
        # Art. 20-21: Management Accountability and Risk Management
        {"control_id": "nis2_management_accountability", "name": "Management Body Cybersecurity Accountability",
         "description": "Management body has approved the organisation's cybersecurity risk management approach. Members of the management body have completed cybersecurity training. Management body can be held personally liable for NIS2 non-compliance. Accountability documented and evidenced (Art. 20 NIS2)."},
        {"control_id": "nis2_risk_policy", "name": "Cybersecurity Risk Management Policy",
         "description": "Formal cybersecurity risk management policy adopted and approved by the management body. Policy covers: risk analysis methodology, risk treatment options, acceptable risk levels, and review cycle. Policy reviewed at least annually and after significant incidents (Art. 21.2a NIS2)."},
        {"control_id": "nis2_risk_assessment", "name": "Regular Cybersecurity Risk Assessment",
         "description": "Systematic risk assessments conducted at least annually and after significant changes. Assessment covers: asset inventory, threat identification, vulnerability identification, risk scoring, and risk treatment decisions. Risk register maintained and reviewed by management (Art. 21.2a NIS2)."},
        # Art. 21.2b: Incident Handling
        {"control_id": "nis2_incident_procedures", "name": "Incident Handling Procedures",
         "description": "Documented incident handling procedures covering: detection and classification, initial triage, analysis, containment, eradication, recovery, and post-incident review. On-call escalation procedures defined. Procedures tested at least annually via tabletop exercise. Roles and responsibilities assigned (Art. 21.2b NIS2)."},
        # Art. 23: Incident Reporting
        {"control_id": "nis2_incident_reporting_procedure", "name": "Significant Incident 3-Stage Reporting Procedure",
         "description": "Documented procedure for 3-stage NIS2 significant incident reporting: (1) early warning to national CSIRT/authority within 24 hours — nature, initial scope; (2) incident notification within 72 hours — update, initial assessment, indicators of compromise; (3) final report within 1 month — full incident description, severity, impact, root cause, measures taken. CSIRT reference numbers tracked (Art. 23 NIS2)."},
        {"control_id": "nis2_significant_incident_criteria", "name": "Significant Incident Classification Criteria",
         "description": "Criteria defined for classifying incidents as 'significant' requiring NIS2 reporting: incidents causing severe operational disruption, financial loss, or affecting other organisations. Classification criteria documented and communicated to all incident response staff. Competent authority guidance on national threshold criteria reviewed (Art. 23 NIS2)."},
        # Art. 21.2c: Business Continuity
        {"control_id": "nis2_bcp", "name": "Business Continuity Plan with RTO and RPO",
         "description": "Business continuity plan covering: backup management, disaster recovery procedures, crisis management, and defined RTO and RPO for critical systems and services. BCP tested at least annually. Test results documented with gaps identified and remediated (Art. 21.2c NIS2)."},
        {"control_id": "nis2_backup_testing", "name": "Backup Management and Restoration Testing",
         "description": "Automated backups of all critical systems and data. Backups encrypted and stored separately from production. Restoration tested at minimum quarterly for critical systems. Backup coverage documented. Retention periods aligned with RPO requirements (Art. 21.2c NIS2)."},
        # Art. 21.2d: Supply Chain Security
        {"control_id": "nis2_supplier_assessment", "name": "Supplier and Service Provider Security Assessments",
         "description": "Security assessments conducted for all direct suppliers and key service providers that could affect the security of network and information systems. Assessment covers: security policies, incident response capability, data protection, and access controls. Assessments documented and repeated at least every 2 years (Art. 21.2d NIS2)."},
        {"control_id": "nis2_supplier_contracts", "name": "Security Requirements in Supplier Contracts",
         "description": "Supplier and service provider contracts include specific security requirements: security standards compliance, right to audit, incident notification obligations, data protection, access control requirements, and security contact. Contract clauses reviewed against NIS2 supply chain risk guidance (Art. 21.2d NIS2)."},
        # Art. 21.2e: Network and System Security
        {"control_id": "nis2_vulnerability_management", "name": "Vulnerability Management Programme",
         "description": "Formal vulnerability management programme: asset inventory, regular vulnerability scanning, severity-based remediation SLAs (critical: 7 days, high: 30 days), patch management process, and tracking to closure. Vulnerability disclosure policy published. ENISA vulnerability database monitored (Art. 21.2e NIS2)."},
        {"control_id": "nis2_network_security", "name": "Network and Information System Security Controls",
         "description": "Network security controls implemented: network segmentation, firewall rules, intrusion detection/prevention, web application firewall, zero-trust architecture (where applicable). Security configurations documented and reviewed. Production environments isolated from development (Art. 21.2e NIS2)."},
        # Art. 21.2g: Cyber Hygiene
        {"control_id": "nis2_staff_training", "name": "Cybersecurity Awareness Training for All Staff",
         "description": "Annual cybersecurity awareness training programme covering: phishing recognition, password hygiene, incident reporting, social engineering, and remote working security. Management body members complete cybersecurity training meeting Art. 20 NIS2 requirements. Training completion records maintained (Art. 21.2g NIS2)."},
        # Art. 21.2h: Cryptography
        {"control_id": "nis2_cryptography_policy", "name": "Cryptography and Encryption Policy",
         "description": "Documented cryptography policy covering: approved encryption algorithms, key management lifecycle (generation, distribution, storage, rotation, revocation, destruction), certificate management, and use of encryption for data at rest and in transit. Policy reviewed annually and when cryptographic standards change (Art. 21.2h NIS2)."},
        # Art. 21.2i: Access Control and MFA
        {"control_id": "nis2_access_control", "name": "Access Control and Least Privilege",
         "description": "Formal access control policy enforcing least privilege. Access provisioned based on documented business need, revoked promptly on role change or departure. Privileged access managed separately with additional controls. Access reviews conducted at minimum every 6 months (Art. 21.2i NIS2)."},
        {"control_id": "nis2_mfa", "name": "Multi-Factor Authentication Enforced",
         "description": "MFA enforced for all user accounts accessing network and information systems, without exception. Privileged accounts subject to phishing-resistant MFA (e.g., FIDO2/hardware keys). MFA bypass procedures require documented approval. MFA coverage audited quarterly (Art. 21.2i NIS2)."},
    ],
    # ── ISO/IEC 42001:2023 (AI Management System) ─────────────────────────────
    "iso42001": [
        # Cl. 4-5: Context and Leadership
        {"control_id": "iso42001_ai_policy", "name": "AI Policy Approved by Top Management",
         "description": "A formal AI policy has been approved by top management, is appropriate to the organisation's AI activities, includes commitments to responsible AI and continual improvement, and is communicated throughout the organisation and to relevant interested parties. Policy reviewed at least annually (Cl. 5.2 ISO 42001)."},
        {"control_id": "iso42001_ai_roles", "name": "AI Management Roles and Responsibilities Defined",
         "description": "Roles, responsibilities, and authorities for AI management assigned and documented: AI system owner, AI risk officer, data governance lead, and human oversight coordinator. Accountability matrix maps each AI system to responsible individuals. Reporting lines to management body defined (Cl. 5.3 ISO 42001)."},
        {"control_id": "iso42001_interested_parties", "name": "Interested Parties and AI Context Analysis",
         "description": "Internal and external interested parties relevant to the AIMS identified. Their requirements and expectations documented. External context (regulatory, societal, ethical standards) and internal context (organisational capabilities, culture, existing management systems) assessed and used to define AIMS scope (Cl. 4.2 ISO 42001)."},
        # Cl. 6.1: AI Risk Assessment
        {"control_id": "iso42001_ai_risk_assessment", "name": "AI Risk Assessment Methodology and Process",
         "description": "Documented AI risk assessment process covering: identification of risks to individuals, groups, and society; risk evaluation criteria; likelihood and impact scoring; risk owners. Risk assessment conducted before deploying AI systems and when systems change significantly. Risk assessment results documented (Cl. 6.1 ISO 42001)."},
        {"control_id": "iso42001_ai_risk_treatment", "name": "AI Risk Treatment Plan",
         "description": "Risk treatment plan developed for all identified AI risks above acceptance threshold. Treatment options selected (mitigate, transfer, accept, avoid). Residual risk assessed. Treatment actions assigned to owners with due dates. Progress tracked. Management approval obtained for accepted residual risks (Cl. 6.1 ISO 42001)."},
        # Cl. 7: Support
        {"control_id": "iso42001_ai_competence", "name": "AI Competence and Training Programme",
         "description": "Competence requirements defined for personnel developing, deploying, and operating AI systems. Competence gaps assessed and addressed through training or hiring. AI awareness programme delivered to all staff. Management body members trained on AI governance obligations. Training records maintained (Cl. 7.2-7.3 ISO 42001)."},
        # Cl. 8.3: AI Impact Assessment
        {"control_id": "iso42001_aisia", "name": "AI System Impact Assessment Before Deployment",
         "description": "AI System Impact Assessment (AISIA) completed for every AI system before deployment. Assessment covers: intended use, reasonably foreseeable misuse, potential impacts on individuals/groups/society, vulnerable populations, and safeguards. Stakeholder consultation documented. AISIA signed off by accountable owner. Reassessed when system changes (Cl. 8.3 ISO 42001)."},
        # Cl. 8.4: Data Governance
        {"control_id": "iso42001_data_governance", "name": "AI Training Data Governance",
         "description": "Data governance controls applied to all AI training, validation, and test datasets: data quality assessment, provenance documentation, representativeness evaluation, bias testing, and retention policy. Data lineage tracked from source to model. Documentation maintained for each dataset used in each model version (Cl. 8.4 ISO 42001)."},
        {"control_id": "iso42001_bias_audit", "name": "Bias Detection and Fairness Evaluation",
         "description": "Bias detection conducted on training data and model outputs before deployment. Fairness metrics defined for each AI system (demographic parity, equalized odds, or appropriate alternatives). Bias audits repeated at defined intervals in production. Bias remediation procedures documented and tested (Cl. 8.4, A.6.2 ISO 42001)."},
        # Cl. 8.5: AI Development
        {"control_id": "iso42001_development_procedures", "name": "AI Development and Testing Procedures",
         "description": "Documented procedures govern AI system development: requirements specification, data selection, model architecture selection, training, testing, validation, and acceptance criteria. Security testing covers adversarial robustness and prompt injection (for LLM systems). Model cards produced for each deployed system (Cl. 8.5 ISO 42001)."},
        # Cl. 8.6: Human Oversight
        {"control_id": "iso42001_human_oversight", "name": "Human Oversight Mechanisms",
         "description": "Human oversight mechanisms designed into AI systems: ability to monitor AI decisions, intervene in automated processes, override AI outputs, and shut down AI systems. Accountability matrices name individuals responsible for each AI decision domain. High-risk AI decisions require human review before action (Cl. 8.6 ISO 42001)."},
        {"control_id": "iso42001_rollback", "name": "AI System Version Control and Rollback Capability",
         "description": "All AI model versions tracked in a model registry with deployment history. Rollback to a previous stable version achievable within a defined timeframe. Rollback procedures documented and tested. Rollback triggered by: performance degradation, safety incidents, regulatory direction, or fairness failures (Cl. 8.5, A.9.1 ISO 42001)."},
        # Cl. 9: Performance Evaluation
        {"control_id": "iso42001_monitoring", "name": "AI System Performance and Drift Monitoring",
         "description": "Production AI systems monitored continuously for: performance metrics (accuracy, precision, recall), model drift, distribution shift, anomalous outputs, and safety events. Alerting configured for threshold breaches. Monitoring dashboards reviewed at defined intervals. Monitoring results documented (Cl. 9.1 ISO 42001)."},
        {"control_id": "iso42001_internal_audit", "name": "AIMS Internal Audit Programme",
         "description": "Internal audit programme defined and executed at planned intervals to verify AIMS conformance. Audit scope covers all AI systems, processes, and controls. Findings documented with nonconformity classifications. Corrective actions tracked to closure. Audit results reported to management body (Cl. 9.2 ISO 42001)."},
        # A.6.1: Transparency
        {"control_id": "iso42001_transparency", "name": "AI Transparency and Explainability",
         "description": "Affected individuals informed when AI is used in decisions that affect them significantly. AI-generated decisions can be explained in meaningful terms. Model cards document: system purpose, training data summary, performance metrics, limitations, and intended use cases. Explainability approach proportionate to risk of the AI system (A.6.1 ISO 42001)."},
        # A.9.1: AI Incident Management
        {"control_id": "iso42001_ai_incidents", "name": "AI Incident Detection and Response",
         "description": "AI-specific incident categories defined: unexpected outputs, performance failures, safety events, fairness failures, and misuse. AI incidents logged in a dedicated register. Post-incident analysis identifies root cause and remediation. Serious incidents escalated to management body. Lessons learned used to update risk assessments and controls (A.9.1 ISO 42001)."},
        # A.10.1: Supply Chain
        {"control_id": "iso42001_ai_supply_chain", "name": "Third-Party AI Supplier Risk Management",
         "description": "Due diligence conducted on all third-party AI models, APIs, and datasets before use: transparency on training data, safety testing results, usage policies, and incident notification capabilities. Supplier contracts include AI-specific clauses: auditability, usage restrictions, bias disclosure, and breach notification. Annual review of AI supplier risk posture (A.10.1 ISO 42001)."},
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


# ── Risk Exceptions ───────────────────────────────────────────────────────────

class RiskExceptionCreate(BaseModel):
    framework: str
    control_category: str
    control_name: str
    justification: str
    owner_name: Optional[str] = None
    owner_email: Optional[str] = None
    expires_at: Optional[datetime] = None


@router.get("/exceptions")
async def list_exceptions(
    framework: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(RiskException).where(RiskException.company_id == current_user.company_id)
    if framework:
        q = q.where(RiskException.framework == framework)
    result = await db.execute(q.order_by(RiskException.created_at.desc()))
    now = datetime.now(timezone.utc)
    items = []
    for e in result.scalars().all():
        is_expired = e.expires_at and e.expires_at < now
        items.append({
            "id": str(e.id),
            "framework": e.framework,
            "control_category": e.control_category,
            "control_name": e.control_name,
            "justification": e.justification,
            "owner_name": e.owner_name,
            "owner_email": e.owner_email,
            "expires_at": e.expires_at,
            "status": "expired" if is_expired else e.status,
            "created_at": e.created_at,
        })
    return items


@router.post("/exceptions", status_code=201)
async def create_exception(
    body: RiskExceptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    exc = RiskException(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        framework=body.framework,
        control_category=body.control_category,
        control_name=body.control_name,
        justification=body.justification,
        owner_name=body.owner_name,
        owner_email=body.owner_email,
        expires_at=body.expires_at,
        status="active",
        created_by_id=current_user.id,
        created_at=now,
    )
    db.add(exc)
    await db.commit()
    await db.refresh(exc)
    from services.audit_service import log_action
    await log_action(db, current_user.company_id, "compliance.exception_created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="risk_exception", resource_id=str(exc.id),
                     metadata={"framework": body.framework, "control": body.control_name})
    return {"id": str(exc.id), "status": "active"}


@router.delete("/exceptions/{exc_id}", status_code=204)
async def delete_exception(
    exc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exc = (await db.execute(
        select(RiskException).where(
            RiskException.id == exc_id,
            RiskException.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")
    await db.delete(exc)
    await db.commit()


# ── Control Exclusions ────────────────────────────────────────────────────────

class ControlExclusionCreate(BaseModel):
    framework: str
    control_category: str
    control_name: str
    justification: str
    exclusion_type: str = "not_applicable"  # not_applicable | out_of_scope


@router.get("/exclusions")
async def list_exclusions(
    framework: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(ControlExclusion).where(ControlExclusion.company_id == current_user.company_id)
    if framework:
        q = q.where(ControlExclusion.framework == framework)
    result = await db.execute(q.order_by(ControlExclusion.created_at.desc()))
    return [
        {
            "id": str(e.id),
            "framework": e.framework,
            "control_category": e.control_category,
            "control_name": e.control_name,
            "justification": e.justification,
            "exclusion_type": e.exclusion_type,
            "created_at": e.created_at,
        }
        for e in result.scalars().all()
    ]


@router.post("/exclusions", status_code=201)
async def create_exclusion(
    body: ControlExclusionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    existing = (await db.execute(
        select(ControlExclusion).where(
            ControlExclusion.company_id == current_user.company_id,
            ControlExclusion.framework == body.framework,
            ControlExclusion.control_category == body.control_category,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="An exclusion already exists for this control.")

    now = datetime.now(timezone.utc)
    excl = ControlExclusion(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        framework=body.framework,
        control_category=body.control_category,
        control_name=body.control_name,
        justification=body.justification,
        exclusion_type=body.exclusion_type,
        created_by_id=current_user.id,
        created_at=now,
    )
    db.add(excl)
    await db.commit()
    await db.refresh(excl)
    from services.audit_service import log_action
    await log_action(db, current_user.company_id, "compliance.exclusion_created",
                     user_id=current_user.id, user_email=current_user.email,
                     resource_type="control_exclusion", resource_id=str(excl.id),
                     metadata={"framework": body.framework, "control": body.control_name, "type": body.exclusion_type})
    return {"id": str(excl.id)}


@router.delete("/exclusions/{excl_id}", status_code=204)
async def delete_exclusion(
    excl_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    excl = (await db.execute(
        select(ControlExclusion).where(
            ControlExclusion.id == excl_id,
            ControlExclusion.company_id == current_user.company_id,
        )
    )).scalar_one_or_none()
    if not excl:
        raise HTTPException(status_code=404, detail="Exclusion not found")
    await db.delete(excl)
    await db.commit()
