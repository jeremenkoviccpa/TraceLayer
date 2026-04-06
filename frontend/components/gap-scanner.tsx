"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, RotateCcw, Shield, CheckCircle2 } from "lucide-react";
import { ToolEmailGate } from "@/components/tool-email-gate";

// ── Control definitions ───────────────────────────────────────────────────────

type ControlDef = {
  id: string;
  category: string;
  name: string;
  question: string;
  risk: "critical" | "high" | "medium";
  audit_note: string;
};

const SOC2_CONTROLS: ControlDef[] = [
  {
    id: "mfa",
    category: "Access Control",
    name: "Multi-Factor Authentication",
    question: "MFA is enforced for all users and admin accounts across every critical system",
    risk: "critical",
    audit_note: "Auditors test this directly on day 1. Missing MFA on any admin account is an immediate, often fatal, audit finding.",
  },
  {
    id: "logging",
    category: "Monitoring",
    name: "Centralized Audit Logging",
    question: "All systems ship logs to a centralized, monitored, tamper-proof location",
    risk: "critical",
    audit_note: "No centralized logs = no evidence = no SOC 2. This directly fails CC7.1 and CC7.2.",
  },
  {
    id: "encryption",
    category: "Data Protection",
    name: "Encryption at Rest & In Transit",
    question: "Sensitive data is encrypted at rest (databases, storage) and in transit (TLS 1.2+)",
    risk: "critical",
    audit_note: "Auditors review every database and API surface. Unencrypted data is a critical finding against C1.",
  },
  {
    id: "access_reviews",
    category: "Access Control",
    name: "Quarterly Access Reviews",
    question: "User access is formally reviewed every quarter with dated, signed records",
    risk: "high",
    audit_note: "Doing reviews without records doesn't count. Auditors need dated, evidence-backed documentation.",
  },
  {
    id: "vuln_scanning",
    category: "Risk Management",
    name: "Vulnerability Scanning",
    question: "Automated vulnerability scans run on a schedule with tracked remediation",
    risk: "high",
    audit_note: "You need scan results AND evidence that critical findings were patched on time. 'We scan sometimes' fails.",
  },
  {
    id: "incident_response",
    category: "Operations",
    name: "Incident Response Plan",
    question: "A documented, versioned IR plan exists with evidence of a tabletop exercise",
    risk: "high",
    audit_note: "'We have a Notion doc' doesn't satisfy CC9. You need a versioned document with a dated exercise record.",
  },
  {
    id: "change_mgmt",
    category: "Change Management",
    name: "Code Review & Deployment Gates",
    question: "All code is peer-reviewed and production deployments require a formal approval",
    risk: "high",
    audit_note: "Auditors pull your git history. Any unreviewed commit to production is a direct CC8 failure.",
  },
  {
    id: "backup",
    category: "Availability",
    name: "Backup & Recovery Testing",
    question: "Backups run automatically, success is monitored, and recovery is tested annually",
    risk: "medium",
    audit_note: "You need backup success logs AND a documented recovery test result. 'We assume it works' fails.",
  },
  {
    id: "vendor_mgmt",
    category: "Vendor Risk",
    name: "Vendor Security Assessments",
    question: "Key vendors are assessed annually — SOC 2 reports collected, questionnaires reviewed",
    risk: "medium",
    audit_note: "SOC 2 CC9 requires documented vendor risk. Collect your critical vendors' SOC 2 reports each year.",
  },
  {
    id: "security_training",
    category: "Human Resources",
    name: "Annual Security Training",
    question: "Every team member completed documented security awareness training in the past 12 months",
    risk: "medium",
    audit_note: "Auditors ask for completion records with names and dates. 'We discussed it in a meeting' fails CC1.4.",
  },
];

const DPDP_CONTROLS: ControlDef[] = [
  {
    id: "consent_management",
    category: "Lawful Processing",
    name: "Consent Management",
    question: "Valid, specific, informed consent is obtained before processing personal data, with a clear withdrawal mechanism",
    risk: "critical",
    audit_note: "Section 6 of DPDP Act 2023 requires free, specific, informed, and unambiguous consent. Bundled or pre-ticked consent boxes are non-compliant and can attract a penalty of up to ₹250 crore.",
  },
  {
    id: "breach_notification_dpdp",
    category: "Breach Notification",
    name: "Personal Data Breach Notification",
    question: "A documented process exists to detect personal data breaches and notify the Data Protection Board and affected individuals within 72 hours",
    risk: "critical",
    audit_note: "Section 8(6) requires prompt notification to the Board AND data principals. Failure to notify is one of the most penalized obligations — up to ₹200 crore per breach notification failure.",
  },
  {
    id: "data_retention",
    category: "Data Fiduciary Obligations",
    name: "Data Retention & Erasure",
    question: "Personal data is deleted once the purpose of processing is fulfilled, with documented retention periods per data category",
    risk: "critical",
    audit_note: "Section 8(7) mandates erasure when purpose is complete. Retaining data indefinitely 'just in case' directly violates the storage limitation principle — regulators flag this immediately.",
  },
  {
    id: "data_principal_rights",
    category: "Data Principal Rights",
    name: "Data Principal Rights Mechanism",
    question: "Processes exist for data principals to access, correct, erase, and nominate for their personal data within statutory timelines",
    risk: "high",
    audit_note: "Sections 11–13 grant access, correction, erasure, and grievance rights. No working mechanism to honor these requests is a direct violation — grievance redressal must be provided within 48 hours.",
  },
  {
    id: "cross_border_transfers",
    category: "Cross-Border Transfers",
    name: "Cross-Border Transfer Controls",
    question: "Personal data is only transferred to countries on the Government's approved whitelist, with transfer controls documented",
    risk: "high",
    audit_note: "Section 16 restricts international transfers. Transferring personal data to blacklisted or unreviewed countries without government approval exposes you to penalties up to ₹250 crore.",
  },
  {
    id: "sdf_obligations",
    category: "Significant Data Fiduciary",
    name: "Significant Data Fiduciary (SDF) Obligations",
    question: "If classified as a Significant Data Fiduciary by the government, a Data Protection Officer is appointed and annual DPIA is conducted",
    risk: "high",
    audit_note: "SDFs face additional obligations under Section 10 — DPO appointment, annual DPIA, and algorithmic audits. Classification is based on data volume/sensitivity; failing to self-identify is a compounding risk.",
  },
  {
    id: "grievance_officer",
    category: "Data Fiduciary Obligations",
    name: "Grievance Officer & Privacy Notice",
    question: "A Grievance Officer is designated, contact details are published, and a privacy notice exists in all supported languages",
    risk: "medium",
    audit_note: "Section 8(1) requires a published Grievance Officer with a defined contact. Privacy notices must be available in all languages listed in the 8th Schedule if you serve those populations.",
  },
  {
    id: "children_data",
    category: "Special Categories",
    name: "Children's Data Controls",
    question: "Verifiable parental consent is obtained before processing personal data of children under 18, with no targeted advertising or behavioral monitoring",
    risk: "medium",
    audit_note: "Section 9 bans tracking, behavioral monitoring, or targeted advertising to minors. Processing children's data without verified parental consent triggers one of the highest penalty tiers — up to ₹200 crore.",
  },
];

const CERTIN_CONTROLS: ControlDef[] = [
  {
    id: "incident_reporting_6h",
    category: "Incident Reporting",
    name: "6-Hour Incident Reporting to CERT-In",
    question: "A documented process ensures all qualifying cybersecurity incidents are reported to CERT-In within 6 hours of detection",
    risk: "critical",
    audit_note: "Para 3(i) of CERT-In Directions 2022: reporting within 6 hours is mandatory — no exceptions. Failure to report is a criminal offense under section 70B(7) of IT Act. The list of 20 qualifying incident types must be known to all ops/security staff.",
  },
  {
    id: "log_retention_180",
    category: "Log Management",
    name: "180-Day Log Retention in India",
    question: "ICT system logs (network, application, security, DB) are retained for a rolling 180 days and stored in India-resident infrastructure",
    risk: "critical",
    audit_note: "Para 3(ii): logs must be preserved for 180 days within Indian jurisdiction. Cloud providers must be contractually bound to this. Non-compliant log storage (e.g., only in US-East) directly violates the Directions.",
  },
  {
    id: "ntp_sync",
    category: "IT Infrastructure",
    name: "NTP Clock Synchronization",
    question: "All ICT systems synchronize clocks with the NTP server of NIC, NPCI, or CERT-In (not public NTP pools)",
    risk: "critical",
    audit_note: "Para 3(iii): mandatory use of CERT-In/NIC/NPCI NTP servers. This seems minor but is directly auditable — logs from unsynchronized systems cannot be trusted as forensic evidence and CERT-In tests for this.",
  },
  {
    id: "poc_registration",
    category: "Identity Verification",
    name: "Designated POC Registered with CERT-In",
    question: "A designated Point of Contact for cyber incident reporting has been registered with CERT-In with current contact details",
    risk: "high",
    audit_note: "Para 4: you must designate and register a POC with CERT-In. An unregistered or outdated contact is an immediate compliance gap — CERT-In uses this contact to initiate incident response coordination.",
  },
  {
    id: "vasp_kyc",
    category: "Identity Verification",
    name: "Customer KYC & Transaction Records (VASP/Crypto)",
    question: "If operating as a Virtual Asset Service Provider, KYC records and all transaction histories are maintained for 5 years",
    risk: "high",
    audit_note: "Para 3(v): VASPs, crypto exchanges, and custodian wallets must maintain KYC and transaction records for 5 years. This applies to B2B SaaS handling crypto payments too — most teams miss this obligation.",
  },
  {
    id: "vulnerability_mgmt_certin",
    category: "Vulnerability Management",
    name: "Vulnerability Assessment & Patch Management",
    question: "Periodic vulnerability assessments and penetration tests are conducted with documented findings, remediation tracking, and timelines",
    risk: "high",
    audit_note: "CERT-In expects organizations to proactively identify and patch vulnerabilities — especially those listed in CERT-In advisories. No documented VA/PT schedule is a strong signal of poor security posture during audits.",
  },
  {
    id: "data_localization",
    category: "IT Infrastructure",
    name: "Data Localization for Regulated Entities",
    question: "If operating as a regulated entity (financial, telecom, government contractor), customer data is stored within India's borders",
    risk: "medium",
    audit_note: "Combined with RBI, SEBI, and TRAI requirements, CERT-In Directions strengthen data localization obligations for regulated sectors. Cloud configurations must explicitly route regulated data through India regions.",
  },
  {
    id: "incident_response_certin",
    category: "Incident Response",
    name: "Incident Response & Forensic Readiness",
    question: "An IR plan is in place, a forensic-capable CSIRT or retained vendor is designated, and runbooks exist for the 20 CERT-In reportable incident types",
    risk: "medium",
    audit_note: "CERT-In may request forensic logs and incident timelines during their inquiry. Without a retained CSIRT or documented IR capability, organizations often scramble to respond — delaying breach containment and compounding penalties.",
  },
];

const LPDP_CONTROLS: ControlDef[] = [
  {
    id: "lpdp_lawful_basis",
    category: "Lawful Processing",
    name: "Lawful Basis for Processing",
    question: "A documented lawful basis exists for every personal data processing activity (consent, contract, legal obligation, vital interests, public interest, or legitimate interests)",
    risk: "critical",
    audit_note: "Art. 5-11 LPDP. Poverenik audits frequently check that lawful basis is documented in ROPA. Processing without a legal ground is the most common LPDP violation.",
  },
  {
    id: "lpdp_dsr",
    category: "Data Subject Rights",
    name: "Data Subject Rights Procedures",
    question: "Written procedures exist for handling access, erasure, rectification, portability and objection requests, with a 30-day SLA tracked",
    risk: "critical",
    audit_note: "Art. 26-39 LPDP. The 30-day response deadline is strictly enforced. Failure to respond to a subject request is one of the top reasons Poverenik initiates an investigation.",
  },
  {
    id: "lpdp_ropa",
    category: "Controller Obligations",
    name: "Records of Processing Activities (ROPA)",
    question: "A ROPA is maintained listing all processing activities, purposes, legal bases, data categories, retention periods, and third-party processors",
    risk: "high",
    audit_note: "Art. 40-50 LPDP. ROPA is the first document requested by Poverenik during any audit. An absent or incomplete ROPA signals systemic non-compliance.",
  },
  {
    id: "lpdp_dpa_contracts",
    category: "Controller Obligations",
    name: "Data Processing Agreements with Processors",
    question: "Written data processing agreements (Art. 45 clauses) are signed with all third-party processors who handle personal data on your behalf",
    risk: "high",
    audit_note: "Art. 44-45 LPDP. Every cloud vendor, SaaS tool, or contractor who touches personal data needs a DPA. Missing DPAs are a straightforward violation with clear documentary evidence.",
  },
  {
    id: "lpdp_security",
    category: "Technical Security",
    name: "Technical and Organizational Security Measures",
    question: "Encryption at rest and in transit, access controls, audit logging, and vulnerability management are implemented and documented",
    risk: "high",
    audit_note: "Art. 49 LPDP. Security measures must be appropriate to the risk. Poverenik expects documented evidence: encryption configs, access control policies, and vulnerability scan results.",
  },
  {
    id: "lpdp_breach",
    category: "Breach Notification",
    name: "72-hour Breach Notification to Poverenik",
    question: "A breach response procedure exists and the team knows to notify the Poverenik (Commissioner) within 72 hours of becoming aware of a personal data breach",
    risk: "critical",
    audit_note: "Art. 53 LPDP. The 72-hour clock starts from when you 'become aware' — not when the breach occurred. High-risk breaches must also notify affected individuals. Missing notification is heavily fined.",
  },
  {
    id: "lpdp_dpo",
    category: "DPO",
    name: "Data Protection Officer Appointment",
    question: "If processing personal data at scale, a DPO is appointed, their contact details are published, and they are registered with the Poverenik",
    risk: "medium",
    audit_note: "Art. 57-61 LPDP. DPO registration with Poverenik is a public record. Mandatory for public bodies, large-scale systematic monitoring, and special category processing at scale.",
  },
  {
    id: "lpdp_transfers",
    category: "Cross-border Transfers",
    name: "Cross-border Data Transfer Safeguards",
    question: "Any transfer of personal data outside Serbia uses adequacy decisions, standard contractual clauses, or binding corporate rules as documented safeguards",
    risk: "medium",
    audit_note: "Art. 65-74 LPDP. Transfers to countries not on the Poverenik adequacy list require SCCs or BCRs. Cloud providers routing data through non-adequate countries are a common gap.",
  },
];

const NIS2_CONTROLS: ControlDef[] = [
  {
    id: "nis2_risk_policy",
    category: "Risk Management",
    name: "Risk Management Policy Approved by Management",
    question: "A formal cybersecurity risk management policy exists, is approved by the management body, and is reviewed at least annually",
    risk: "critical",
    audit_note: "Art. 20-21 NIS2. Management body accountability is a new NIS2 feature — individuals can be personally liable. Lack of management sign-off is a critical finding.",
  },
  {
    id: "nis2_incident_handling",
    category: "Incident Handling",
    name: "Incident Handling Procedures",
    question: "Documented incident response procedures covering detection, analysis, containment, eradication, and recovery are in place with defined on-call responsibilities",
    risk: "critical",
    audit_note: "Art. 21.2b NIS2. Competent authorities check that procedures exist and were actually followed during past incidents. Undocumented ad-hoc response is insufficient.",
  },
  {
    id: "nis2_incident_reporting",
    category: "Incident Reporting",
    name: "3-Stage Significant Incident Reporting to CSIRT",
    question: "The team knows the NIS2 3-stage reporting obligation: early warning within 24h, incident notification within 72h, and final report within 1 month, and incidents are tracked accordingly",
    risk: "critical",
    audit_note: "Art. 23 NIS2. Missing or late reports to national CSIRT carry heavy fines. The 24-hour early warning is the most commonly missed stage — it requires very fast triage.",
  },
  {
    id: "nis2_mfa_access",
    category: "Access Control",
    name: "Multi-Factor Authentication and Access Control",
    question: "MFA is enforced for all users, privileged access is managed separately, and access is reviewed regularly",
    risk: "critical",
    audit_note: "Art. 21.2i NIS2. MFA is explicitly mandated. Authorities test this directly. Privileged accounts without MFA are an automatic finding.",
  },
  {
    id: "nis2_network_security",
    category: "Network Security",
    name: "Vulnerability Management and Patch Programme",
    question: "A formal vulnerability management programme exists with defined SLAs for patching critical vulnerabilities, supported by regular scans",
    risk: "high",
    audit_note: "Art. 21.2e NIS2. Unpatched critical vulnerabilities are one of the leading causes of significant incidents. Authorities expect documented patch timelines and evidence.",
  },
  {
    id: "nis2_supply_chain",
    category: "Supply Chain Security",
    name: "Supplier and Third-party Security Assessments",
    question: "Direct suppliers and key service providers are assessed for cybersecurity risk, and security requirements are included in contracts",
    risk: "high",
    audit_note: "Art. 21.2d NIS2. Supply chain security is a new NIS2 emphasis. Authorities ask for vendor risk assessment records and evidence of security clauses in contracts.",
  },
  {
    id: "nis2_backup_bcp",
    category: "Business Continuity",
    name: "Backup, Disaster Recovery, and BCP Testing",
    question: "Backups are automated and tested, disaster recovery procedures exist with defined RTO/RPO, and the BCP has been tested in the past 12 months",
    risk: "high",
    audit_note: "Art. 21.2c NIS2. Untested BCPs are treated the same as no BCP by auditors. Backup restoration tests are specifically requested as evidence.",
  },
  {
    id: "nis2_logging",
    category: "Logging & Monitoring",
    name: "Security Event Monitoring and Audit Logging",
    question: "Security events are centrally logged with a minimum 12-month retention, alerts are configured for critical events, and logs are regularly reviewed",
    risk: "high",
    audit_note: "Art. 21.2e NIS2. Log retention and monitoring are the primary forensic tools after an incident. Missing logs make post-incident analysis impossible and indicate systemic gaps.",
  },
  {
    id: "nis2_training",
    category: "Cyber Hygiene",
    name: "Security Awareness Training Programme",
    question: "All staff complete annual security awareness training; management body members complete cybersecurity training as required by NIS2 Art. 20",
    risk: "medium",
    audit_note: "Art. 21.2g NIS2. NIS2 specifically requires management training — not just staff. Training completion records must show all employees and board members.",
  },
  {
    id: "nis2_encryption",
    category: "Cryptography",
    name: "Encryption and Cryptography Policy",
    question: "A cryptography policy exists covering encryption of data at rest and in transit, key management procedures, and certificate inventory",
    risk: "medium",
    audit_note: "Art. 21.2h NIS2. While not requiring specific algorithms, NIS2 expects a documented policy. Expired certificates and unencrypted sensitive data are common findings.",
  },
];

const ISO42001_CONTROLS: ControlDef[] = [
  {
    id: "iso42001_governance",
    category: "AI Governance",
    name: "AI Governance Policy and Leadership",
    question: "A formal AI policy has been approved by top management, with defined roles, responsibilities, and AI objectives communicated across the organization",
    risk: "critical",
    audit_note: "Cl.4-5 ISO 42001. The AI policy is the foundation of the AIMS. Without it, no other clause can be assessed. Auditors will ask for board sign-off and evidence of communication.",
  },
  {
    id: "iso42001_risk",
    category: "AI Risk Management",
    name: "AI Risk Assessment and Treatment Plan",
    question: "A systematic AI risk assessment has been conducted covering risks to individuals, groups, and society, with a documented risk treatment plan addressing each identified risk",
    risk: "critical",
    audit_note: "Cl.6.1 ISO 42001. This is the most-cited gap in first-time ISO 42001 assessments. Risk assessment must be AI-specific — generic IT risk assessments are insufficient.",
  },
  {
    id: "iso42001_impact",
    category: "AI Impact Assessment",
    name: "AI System Impact Assessment (AISIA)",
    question: "Before deploying any AI system, an AI system impact assessment has been performed covering intended use, foreseeable misuse, and impact on affected individuals",
    risk: "critical",
    audit_note: "Cl.8.3 ISO 42001. AISIAs must be documented for each AI system. Deploying AI without an AISIA is a major nonconformity. Evidence must include sign-offs and stakeholder consultation records.",
  },
  {
    id: "iso42001_data",
    category: "Data Governance",
    name: "Training Data Governance and Bias Controls",
    question: "Data quality, provenance, and representativeness are assessed for all AI training datasets; bias audits are performed and documented before and after model training",
    risk: "high",
    audit_note: "Cl.8.4 ISO 42001. Data governance is where AI failures originate. Auditors look for data lineage records, bias audit reports, and labelling guidelines. Lack of bias documentation is a common high finding.",
  },
  {
    id: "iso42001_development",
    category: "AI Development",
    name: "AI System Development, Testing, and Validation",
    question: "AI systems are developed and tested per documented procedures; validation reports, model cards, performance benchmarks, and security testing results exist before production release",
    risk: "high",
    audit_note: "Cl.8.5 ISO 42001. Model cards and validation reports are the primary artefacts. Security testing must include adversarial robustness and prompt injection testing for LLM-based systems.",
  },
  {
    id: "iso42001_oversight",
    category: "Human Oversight",
    name: "Human Oversight and Intervention Mechanisms",
    question: "Human oversight mechanisms are designed into AI systems; operators can intervene, override, or shut down AI systems; accountability for AI decisions is traceable to named individuals",
    risk: "critical",
    audit_note: "Cl.8.6 ISO 42001. Aligned with EU AI Act Art. 9. High-risk AI systems with no human override capability are a critical nonconformity. Accountability matrices must name individuals, not just teams.",
  },
  {
    id: "iso42001_monitoring",
    category: "AI Monitoring",
    name: "AI Performance Monitoring and Model Drift Detection",
    question: "Production AI systems are continuously monitored for performance degradation, model drift, and unexpected outputs; internal AIMS audits are conducted at planned intervals",
    risk: "high",
    audit_note: "Cl.9 ISO 42001. Model drift is the most common post-deployment issue. Monitoring dashboards must show metrics relevant to the AI use case (accuracy, fairness, confidence scores). Audit frequency must be defined.",
  },
  {
    id: "iso42001_transparency",
    category: "Transparency",
    name: "AI Transparency and Explainability",
    question: "Affected parties are informed when AI is used in decisions affecting them; AI-driven decisions can be meaningfully explained; model cards document system purpose, limitations, and performance",
    risk: "high",
    audit_note: "A.6.1 ISO 42001. Transparency requirements increase with AI risk level. For high-risk AI, SHAP/LIME analyses or equivalent explainability artefacts are expected. Undisclosed AI use in consumer decisions is a critical gap.",
  },
  {
    id: "iso42001_fairness",
    category: "Fairness",
    name: "Bias Detection and Fairness Monitoring",
    question: "Fairness metrics are defined for AI systems; bias detection runs continuously in production; bias remediation procedures exist and have been exercised",
    risk: "high",
    audit_note: "A.6.2 ISO 42001. Fairness metrics must be documented before deployment. Common finding: organizations perform one-time pre-deployment bias checks but have no ongoing monitoring. Demographic parity and equalized odds are standard metrics.",
  },
  {
    id: "iso42001_incidents",
    category: "AI Incident Management",
    name: "AI Incident Detection and Response",
    question: "AI-specific incidents (unexpected outputs, performance failures, safety events, misuse) are tracked in an incident log with documented post-incident analyses and model rollback capabilities",
    risk: "high",
    audit_note: "A.9.1 ISO 42001. AI incidents differ from IT incidents — auditors look for AI-specific categories (hallucinations, bias events, safety failures). Rollback/recall capability for model versions must be demonstrated.",
  },
  {
    id: "iso42001_supply_chain",
    category: "AI Supply Chain",
    name: "Third-Party AI Supplier Risk Management",
    question: "Third-party AI models, APIs, and datasets have been assessed for AI governance maturity; supplier contracts include transparency, auditability, and incident notification requirements",
    risk: "medium",
    audit_note: "A.10.1 ISO 42001. Most organizations rely on foundation models or AI APIs. Auditors expect due diligence records for OpenAI, Anthropic, Google, etc. Contracts must include AI-specific clauses — standard DPA/MSA terms are insufficient.",
  },
  {
    id: "iso42001_competence",
    category: "AI Competence",
    name: "AI Competence, Training, and Awareness",
    question: "Personnel developing or operating AI systems have demonstrated competence; an AI awareness programme has been delivered to all staff covering AI policy, risks, and their responsibilities",
    risk: "medium",
    audit_note: "Cl.7 ISO 42001. Competency must be evidenced — job descriptions, training records, certifications. Awareness training must cover AI-specific risks, not just general security awareness. Management must complete training on AI governance obligations.",
  },
];

const ISO27001_CONTROLS: ControlDef[] = [
  {
    id: "iso27001_access",
    category: "Access Control",
    name: "Access Control Policy and User Access Management",
    question: "A formal access control policy exists; user access is provisioned based on least privilege; privileged access rights are managed separately; access is reviewed at least annually",
    risk: "critical",
    audit_note: "A.5.15-18 ISO 27001:2022. Access reviews must produce dated records. Stale accounts (especially for departed employees) found during fieldwork are automatic findings. IAM audit logs must show every access change.",
  },
  {
    id: "iso27001_vuln",
    category: "Vulnerability Management",
    name: "Technical Vulnerability Management",
    question: "Vulnerability scans run on a defined schedule; findings are tracked to remediation with SLA timelines; patches are applied within defined windows",
    risk: "critical",
    audit_note: "A.8.8 ISO 27001:2022. Auditors pull scan results and compare open findings against your SLA. Critical vulnerabilities open beyond 30 days without a documented risk acceptance are major nonconformities.",
  },
  {
    id: "iso27001_logging",
    category: "Logging and Monitoring",
    name: "Event Logging and Security Monitoring",
    question: "Event logs capturing user activities, exceptions, and security events are generated, protected, and retained; anomalous behavior triggers alerts",
    risk: "critical",
    audit_note: "A.8.15-16 ISO 27001:2022. Log integrity is as important as log existence — logs must be tamper-evident. Missing logs for a specific period will immediately raise questions about incident concealment.",
  },
  {
    id: "iso27001_change",
    category: "Change Management",
    name: "Change Management and Secure SDLC",
    question: "All changes to production systems go through a formal approval process; code is peer-reviewed; security testing is performed before release",
    risk: "high",
    audit_note: "A.8.32-33 ISO 27001:2022. Auditors sample change records against git history. Any unreviewed direct commit to production is a finding. Emergency changes must have post-implementation review records.",
  },
  {
    id: "iso27001_endpoint",
    category: "Endpoint Security",
    name: "Endpoint Security and Malware Protection",
    question: "All corporate devices are enrolled in MDM; disk encryption, screen lock, and OS patching are enforced; EDR/anti-malware is deployed",
    risk: "high",
    audit_note: "A.8.1, A.8.7 ISO 27001:2022. MDM compliance reports are the primary evidence. Any unmanaged device with access to company systems is a finding. BYOD devices need compensating controls documented.",
  },
  {
    id: "iso27001_crypto",
    category: "Cryptography",
    name: "Cryptography and Key Management",
    question: "A cryptography policy governs encryption at rest and in transit; key management procedures cover generation, storage, rotation, and destruction; TLS certificates are inventoried",
    risk: "high",
    audit_note: "A.8.24 ISO 27001:2022. Expired certificates in production are embarrassingly common and easy for auditors to verify externally. Key rotation timelines must be documented and evidenced.",
  },
  {
    id: "iso27001_network",
    category: "Network Security",
    name: "Network Security and Segmentation",
    question: "Networks are segmented by sensitivity level; external network services have documented security requirements; firewall and WAF rules are reviewed periodically",
    risk: "high",
    audit_note: "A.8.20-22 ISO 27001:2022. Flat network architecture with no segmentation is a significant finding. Auditors look for network diagrams and evidence that production is isolated from development.",
  },
  {
    id: "iso27001_incident",
    category: "Incident Management",
    name: "Information Security Incident Management",
    question: "Incidents are classified, responded to per documented procedures, and followed by post-incident analysis; evidence is preserved per defined procedures",
    risk: "high",
    audit_note: "A.5.24-28 ISO 27001:2022. Post-incident reviews must result in documented lessons learned. Auditors check whether past incidents led to control improvements — no improvements signals a non-learning organization.",
  },
  {
    id: "iso27001_hr",
    category: "HR Security",
    name: "Human Resource Security Lifecycle",
    question: "Pre-employment screening is performed; all staff sign confidentiality agreements; security awareness training is completed annually; user access is revoked on termination same-day",
    risk: "medium",
    audit_note: "A.6.1-6.8 ISO 27001:2022. Termination access revocation timing is the most audited HR control — any account active more than 24h after departure is a finding. Training records must show completion dates and scope.",
  },
  {
    id: "iso27001_supplier",
    category: "Supplier Security",
    name: "Supplier and Cloud Service Security",
    question: "Security requirements are defined in agreements with all key suppliers; cloud service providers are assessed for security posture; supply chain risks are reviewed annually",
    risk: "medium",
    audit_note: "A.5.19-23 ISO 27001:2022. Missing security clauses in vendor contracts are common gaps. For cloud services, auditors want to see that you reviewed the provider's shared responsibility model and confirmed your responsibilities.",
  },
];

const HIPAA_CONTROLS: ControlDef[] = [
  {
    id: "hipaa_risk_analysis",
    category: "Security Management",
    name: "Risk Analysis and Risk Management",
    question: "A documented risk analysis has been completed assessing threats to ePHI confidentiality, integrity, and availability; a risk management plan with remediation priorities is maintained",
    risk: "critical",
    audit_note: "§164.308(a)(1) HIPAA. Risk analysis is the most-cited HIPAA violation in OCR enforcement actions. It must be comprehensive (all systems handling ePHI), current (updated after significant changes), and documented in writing.",
  },
  {
    id: "hipaa_access_control",
    category: "Access Control",
    name: "Unique User Identification and Access Management",
    question: "Every user has a unique identifier; access to ePHI is limited to minimum necessary; access provisioning and de-provisioning is documented; emergency access procedures exist",
    risk: "critical",
    audit_note: "§164.312(a) HIPAA. Shared accounts are a direct violation — each user must be individually identifiable in audit logs. OCR specifically requests audit logs showing who accessed what ePHI and when during investigations.",
  },
  {
    id: "hipaa_audit_controls",
    category: "Audit Controls",
    name: "Audit Controls and Activity Review",
    question: "Activity logs for all systems containing ePHI are generated and retained; logs are regularly reviewed for unauthorized access; audit trail integrity is protected",
    risk: "critical",
    audit_note: "§164.312(b) HIPAA. Audit logs are OCR's primary forensic tool. Missing logs for ePHI systems is a critical finding in every investigation. Retention must be at least 6 years per the documentation requirement.",
  },
  {
    id: "hipaa_breach_notification",
    category: "Breach Notification",
    name: "Breach Notification Procedures",
    question: "A documented breach response procedure exists; the 4-factor risk assessment is performed for every potential breach; affected individuals are notified within 60 days; HHS is notified of breaches affecting 500+ individuals within 60 days",
    risk: "critical",
    audit_note: "HIPAA Breach Notification Rule. Late notification is heavily penalized. The 60-day clock starts from discovery, not occurrence. Breaches affecting 500+ individuals in a state require media notification — a commonly missed obligation.",
  },
  {
    id: "hipaa_transmission",
    category: "Transmission Security",
    name: "Transmission Security and Encryption",
    question: "ePHI transmitted over open networks is encrypted (TLS 1.2+); encryption status of data at rest in ePHI systems is documented and justified",
    risk: "high",
    audit_note: "§164.312(e) HIPAA. While encryption is 'addressable', failing to encrypt and not documenting an equivalent alternative measure is indefensible. OCR treats unencrypted ePHI on lost/stolen devices as automatic breaches.",
  },
  {
    id: "hipaa_workforce",
    category: "Workforce Security",
    name: "Workforce Screening, Training, and Sanctions",
    question: "Workforce members receive HIPAA training at hire and annually; a sanction policy for violations exists and has been applied; background checks are conducted for roles with ePHI access",
    risk: "high",
    audit_note: "§164.308(a)(3),(5) HIPAA. OCR requests training completion logs covering all workforce members. 'We trained everyone verbally' fails — you need dated records with each individual's name and topics covered.",
  },
  {
    id: "hipaa_contingency",
    category: "Contingency Plan",
    name: "Contingency Plan, Backup, and Disaster Recovery",
    question: "A contingency plan covers data backup, disaster recovery, and emergency mode operations; backups of ePHI are tested regularly; RTO and RPO are defined and documented",
    risk: "high",
    audit_note: "§164.308(a)(7) HIPAA. Backup plans without test records are treated as non-existent. OCR wants to see that you can actually restore ePHI — untested backups fail during real incidents and audits alike.",
  },
  {
    id: "hipaa_business_associates",
    category: "Business Associate Agreements",
    name: "Business Associate Agreements (BAAs)",
    question: "BAAs are signed with all vendors, contractors, and service providers who create, receive, maintain, or transmit ePHI on your behalf; BAAs are current and contain required provisions",
    risk: "critical",
    audit_note: "§164.308(b) HIPAA. Missing BAAs are among the top OCR enforcement findings. Every cloud provider storing ePHI (AWS, Google Cloud, Microsoft) must have a signed BAA in place before you store a single record.",
  },
];

const GDPR_CONTROLS: ControlDef[] = [
  {
    id: "gdpr_lawful_basis",
    category: "Lawful Basis",
    name: "Lawful Basis and Consent Management",
    question: "A documented lawful basis exists for every processing activity; consent (where used) is freely given, specific, and withdrawable; processing purposes are clearly defined and not exceeded",
    risk: "critical",
    audit_note: "Art. 6-9 GDPR. DPAs audit ROPA entries against actual processing. Purpose creep — using data collected for one reason for another — is a frequent violation. Consent mechanisms must be granular, not bundled.",
  },
  {
    id: "gdpr_dsr",
    category: "Data Subject Rights",
    name: "Data Subject Rights Procedures",
    question: "Documented processes exist for access, rectification, erasure, portability, and objection requests with a 30-day SLA; a response mechanism is publicly communicated",
    risk: "critical",
    audit_note: "Art. 15-22 GDPR. DPAs track complaint response times. Failing to respond to a subject access request within 30 days is an automatic violation. 'We don't have a process' is not an acceptable answer to an erasure request.",
  },
  {
    id: "gdpr_ropa",
    category: "Records of Processing",
    name: "Records of Processing Activities (ROPA)",
    question: "A ROPA is maintained for all processing activities, documenting purpose, legal basis, data categories, recipients, retention periods, and security measures",
    risk: "high",
    audit_note: "Art. 30 GDPR. ROPA is the first document any DPA requests during an investigation. An absent or outdated ROPA signals systemic non-compliance and typically triggers a broader audit.",
  },
  {
    id: "gdpr_breach",
    category: "Breach Notification",
    name: "72-Hour Breach Notification to Supervisory Authority",
    question: "A breach response procedure exists; the team knows the 72-hour reporting obligation to the supervisory authority; high-risk breaches are also communicated to affected individuals",
    risk: "critical",
    audit_note: "Art. 33-34 GDPR. The 72-hour clock starts from awareness — not occurrence. Late notifications attract fines up to €10M / 2% of global turnover. Individual notification for high-risk breaches is separately required and commonly missed.",
  },
  {
    id: "gdpr_security",
    category: "Security of Processing",
    name: "Technical and Organizational Security Measures",
    question: "Appropriate security measures are implemented including pseudonymisation, encryption, access controls, and tested incident response; security is reviewed regularly",
    risk: "high",
    audit_note: "Art. 32 GDPR. DPAs require evidence that security measures are proportionate to the risk. Encryption at rest and in transit is now expected as a baseline. 'Appropriate' is risk-based — document your reasoning.",
  },
  {
    id: "gdpr_dpia",
    category: "Data Protection Impact",
    name: "Data Protection Impact Assessments (DPIAs)",
    question: "DPIAs are completed for all high-risk processing (profiling, systematic monitoring, large-scale special category data); DPIAs are reviewed when processing changes significantly",
    risk: "high",
    audit_note: "Art. 35-36 GDPR. DPIAs are mandatory for 9 listed high-risk processing types. DPAs check whether DPIAs were completed before high-risk processing began — post-hoc DPIAs are non-compliant.",
  },
  {
    id: "gdpr_processor_agreements",
    category: "Processor Agreements",
    name: "Data Processing Agreements with All Processors",
    question: "Written DPAs containing all Art. 28 mandatory clauses are signed with every processor (cloud providers, SaaS tools, contractors) before they process any personal data",
    risk: "high",
    audit_note: "Art. 28 GDPR. DPAs must include all 8 mandatory clauses — generic terms of service do not qualify. Sub-processor approval provisions are frequently missing. Processors using unauthorized sub-processors put you in violation.",
  },
  {
    id: "gdpr_transfers",
    category: "Cross-border Transfers",
    name: "International Data Transfer Safeguards",
    question: "Transfers of personal data outside the EEA rely on adequacy decisions, SCCs, BCRs, or derogations; a transfer impact assessment (TIA) is conducted for high-risk transfers",
    risk: "high",
    audit_note: "Art. 44-49 GDPR. Post-Schrems II, US-based transfers require a TIA demonstrating SCCs provide 'essentially equivalent' protection. Cloud routing data through US regions without SCCs is a systematic violation.",
  },
];

const PCI_DSS_CONTROLS: ControlDef[] = [
  {
    id: "pci_network",
    category: "Network Security",
    name: "Network Security Controls and Segmentation",
    question: "The cardholder data environment (CDE) is isolated from other networks via firewalls; network segmentation is tested annually; security groups/NSGs are reviewed quarterly",
    risk: "critical",
    audit_note: "Req. 1-2 PCI DSS v4.0. Network segmentation is the most impactful control — without it, your entire infrastructure is in scope. QSAs test segmentation effectiveness. A flat network makes passing PCI DSS essentially impossible.",
  },
  {
    id: "pci_encryption_transit",
    category: "Encryption in Transit",
    name: "Strong Cryptography for Transmitted Cardholder Data",
    question: "All cardholder data transmitted over public networks uses strong cryptography (TLS 1.2+); PANs are never sent in clear text; SSL/early TLS is completely eliminated",
    risk: "critical",
    audit_note: "Req. 4 PCI DSS v4.0. TLS 1.0 and 1.1 are explicitly prohibited. QSAs use protocol scanners to find weak cipher suites. Any cleartext PAN transmission is an immediate critical finding.",
  },
  {
    id: "pci_access_control",
    category: "Access Control",
    name: "Least Privilege Access Control and Unique IDs",
    question: "Access to cardholder data and CDE systems is restricted to minimum necessary; every user has a unique ID; access is reviewed every 6 months for CDE systems",
    risk: "critical",
    audit_note: "Req. 7-8 PCI DSS v4.0. Generic or shared accounts in the CDE are immediate findings. QSAs pull user lists and verify each account has a documented business need. Semi-annual access reviews must produce dated records.",
  },
  {
    id: "pci_mfa",
    category: "MFA and Authentication",
    name: "Multi-Factor Authentication for CDE Access",
    question: "MFA is enforced for all access to the CDE, including all administrative access and remote access to the CDE",
    risk: "critical",
    audit_note: "Req. 8.4-8.5 PCI DSS v4.0. MFA for CDE is now mandatory for all personnel — not just remote access. QSAs test this on day 1. Single-factor access to production systems handling PANs is an immediate Level 1 finding.",
  },
  {
    id: "pci_vuln_mgmt",
    category: "Vulnerability Management",
    name: "Vulnerability Scanning and Penetration Testing",
    question: "Internal and external vulnerability scans run quarterly (external by ASV); penetration testing covers both network and application layers annually; all high-severity vulnerabilities are remediated within defined timelines",
    risk: "high",
    audit_note: "Req. 6, 11.3 PCI DSS v4.0. External scans must be performed by an ASV (Approved Scanning Vendor). Pen tests must explicitly test segmentation controls. QSAs request scan reports for the past 12 months — gaps in scan frequency are findings.",
  },
  {
    id: "pci_logging",
    category: "Logging and Monitoring",
    name: "Audit Logging and Log Monitoring",
    question: "All access to CDE systems and cardholder data is logged; logs are retained for at least 12 months (3 months immediately available); logs are reviewed daily for anomalies",
    risk: "high",
    audit_note: "Req. 10 PCI DSS v4.0. Daily log review is explicitly required — 'we review logs when something happens' fails. Automated alerting can satisfy this, but QSAs want to see alert configurations and evidence of follow-up on alerts.",
  },
  {
    id: "pci_data_storage",
    category: "Data Protection",
    name: "Cardholder Data Storage and Tokenization",
    question: "PANs are never stored post-authorization unless absolutely necessary; stored PANs are masked (first 6 / last 4 digits maximum visible); tokenization or encryption is used for any stored PANs",
    risk: "critical",
    audit_note: "Req. 3 PCI DSS v4.0. Discovering an unprotected PAN anywhere — in logs, backups, spreadsheets, test environments — is an immediate critical finding. A data discovery scan of your entire environment is essential before any QSA assessment.",
  },
  {
    id: "pci_secure_config",
    category: "Secure Configuration",
    name: "Secure System and Software Configuration",
    question: "Hardening standards exist for all CDE system types; default credentials are changed before deployment; all unnecessary services, ports, and protocols are disabled",
    risk: "high",
    audit_note: "Req. 2 PCI DSS v4.0. QSAs run configuration scans on CDE systems. Default passwords are the most embarrassing — and still common — finding. System components must have a documented hardening baseline against CIS Benchmarks or equivalent.",
  },
];

const NIST_CSF_CONTROLS: ControlDef[] = [
  {
    id: "nist_govern",
    category: "Govern",
    name: "Cybersecurity Strategy and Governance",
    question: "A cybersecurity strategy is approved by leadership; roles and responsibilities are formally defined; cybersecurity is integrated into risk management decisions across the organization",
    risk: "high",
    audit_note: "GV Function NIST CSF 2.0. Govern is new in v2.0 and sits above everything else. Without leadership-endorsed strategy, all other controls lack authority. Assessors look for a cybersecurity charter or policy with executive sign-off.",
  },
  {
    id: "nist_asset_inventory",
    category: "Identify",
    name: "Asset Inventory and Risk Assessment",
    question: "An inventory of hardware, software, data, and services exists; a cybersecurity risk assessment is conducted at least annually; supply chain risks are identified and managed",
    risk: "high",
    audit_note: "ID Function NIST CSF 2.0. You can't protect what you don't know you have. Asset inventories are consistently the most incomplete control area in assessments. Cloud asset discovery tools (AWS Config, Wiz) are expected evidence.",
  },
  {
    id: "nist_identity_protect",
    category: "Protect",
    name: "Identity Management, Access Control, and Data Security",
    question: "Identity and access management enforces least privilege and MFA; data is classified and protected proportionally; awareness training is conducted annually for all staff",
    risk: "critical",
    audit_note: "PR Function NIST CSF 2.0. The Protect function covers the broadest control surface. MFA gaps are the most cited finding. Assessors check training records, IAM policies, and data encryption configurations together.",
  },
  {
    id: "nist_monitoring",
    category: "Detect",
    name: "Continuous Monitoring and Anomaly Detection",
    question: "Continuous monitoring of network and system activity is in place; anomalies and potential cybersecurity events are detected promptly; monitoring processes are tested",
    risk: "high",
    audit_note: "DE Function NIST CSF 2.0. 'Continuous' means automated, not periodic manual review. SIEM or cloud-native logging with alerting is expected. Detection capability is tested by assessors — can you detect a simulated attack?",
  },
  {
    id: "nist_incident_response",
    category: "Respond",
    name: "Incident Response Planning and Execution",
    question: "An incident response plan is documented, tested annually via tabletop or simulation, and covers roles, escalation paths, external notification obligations, and lessons learned",
    risk: "high",
    audit_note: "RS Function NIST CSF 2.0. The most common gap: IRP exists but has never been tested. Assessors ask for the last tabletop exercise date and attendees. An untested IRP provides false assurance.",
  },
  {
    id: "nist_recover",
    category: "Recover",
    name: "Recovery Planning and Backup Testing",
    question: "Recovery plans exist with defined RTO and RPO; backups run automatically for all critical systems; recovery is tested at least annually; lessons from incidents drive plan improvements",
    risk: "high",
    audit_note: "RC Function NIST CSF 2.0. Recovery is the most neglected CSF function. Assessors want to see actual restore test results — 'we have backups' without test evidence fails. RTO/RPO targets must be documented and achievable.",
  },
];

const CCPA_CONTROLS: ControlDef[] = [
  {
    id: "ccpa_privacy_notice",
    category: "Privacy Notice",
    name: "Privacy Notice at Collection",
    question: "A privacy notice is provided at or before the point of collection, listing categories of PI collected, purposes, and whether PI is sold or shared; the notice is easy to understand and accessible",
    risk: "critical",
    audit_note: "§1798.100(b) CCPA/CPRA. The notice must be visible and available at the point of collection — not buried in Terms of Service. California AG enforcement specifically targets vague, incomplete, or inaccessible notices.",
  },
  {
    id: "ccpa_consumer_rights",
    category: "Consumer Rights",
    name: "Consumer Rights Request Procedures (Know, Delete, Correct)",
    question: "A documented process handles consumer requests to know, delete, and correct personal information within 45 days; at least 2 submission methods are available (toll-free number + web form or email)",
    risk: "critical",
    audit_note: "§1798.100-105 CCPA/CPRA. The 45-day response clock has a 45-day extension (with notice) — 90 days total maximum. AG enforcement targets businesses that ignore requests or charge fees for exercising rights.",
  },
  {
    id: "ccpa_opt_out",
    category: "Opt-out Mechanisms",
    name: "Do Not Sell or Share My Personal Information",
    question: "If PI is sold or shared for cross-context behavioral advertising, a 'Do Not Sell or Share My Personal Information' link is prominently displayed; opt-out requests are honored within 15 business days",
    risk: "critical",
    audit_note: "§1798.120 CCPA/CPRA. CPRA expanded 'sale' to include 'sharing' for targeted advertising — many companies that don't 'sell' data are still covered via ad tech partnerships. The opt-out link must be visible on the homepage.",
  },
  {
    id: "ccpa_data_inventory",
    category: "Data Inventory",
    name: "Personal Information Data Inventory and Mapping",
    question: "A PI inventory documents all categories of personal information collected, the business purposes, sources, and parties with whom it is shared; the inventory is updated when data practices change",
    risk: "high",
    audit_note: "§1798.140 CCPA/CPRA. A data inventory is the foundation for both the privacy notice and responding to consumer requests. Without it, you cannot accurately describe your data practices or fulfill deletion requests across all systems.",
  },
  {
    id: "ccpa_service_providers",
    category: "Service Provider Contracts",
    name: "Service Provider and Contractor Contracts",
    question: "Written contracts with service providers and contractors contain CCPA-required clauses prohibiting PI use beyond the contracted services and requiring the same protections",
    risk: "high",
    audit_note: "§1798.140 CCPA/CPRA. Generic vendor contracts without CCPA-specific clauses make the vendor a 'third party' — meaning sharing with them constitutes a 'sale' of PI. Every cloud provider, analytics vendor, and contractor needs updated contracts.",
  },
  {
    id: "ccpa_sensitive_pi",
    category: "Sensitive Personal Information",
    name: "Sensitive Personal Information Use Limitation",
    question: "If sensitive PI is processed (SSNs, financial data, geolocation, health, biometrics, etc.), its use is limited to permitted purposes; a 'Limit the Use of My Sensitive PI' link is provided if used beyond permitted purposes",
    risk: "high",
    audit_note: "§1798.121 CPRA (effective 2023). Sensitive PI has heightened protections. Many companies inadvertently collect precise geolocation through mobile apps. Any use of sensitive PI for targeted advertising without a limit link is a direct violation.",
  },
];

type Status = "yes" | "partial" | "no";
type Answers = Record<string, Status>;
type Framework = "soc2" | "iso27001" | "hipaa" | "gdpr" | "pci_dss" | "ccpa" | "nist_csf" | "dpdp" | "cert_in" | "lpdp" | "nis2" | "iso42001";

const FRAMEWORK_OPTIONS: { id: Framework; label: string; flag: string; controls: ControlDef[]; desc: string }[] = [
  { id: "soc2",      label: "SOC 2",        flag: "🇺🇸", controls: SOC2_CONTROLS,       desc: "10 controls — Type I & II trust criteria" },
  { id: "iso27001",  label: "ISO 27001",    flag: "🌍", controls: ISO27001_CONTROLS,    desc: "10 controls — information security management" },
  { id: "hipaa",     label: "HIPAA",        flag: "🇺🇸", controls: HIPAA_CONTROLS,      desc: "8 controls — US health data safeguards" },
  { id: "gdpr",      label: "GDPR",         flag: "🇪🇺", controls: GDPR_CONTROLS,       desc: "8 controls — EU data protection regulation" },
  { id: "pci_dss",   label: "PCI DSS",      flag: "💳", controls: PCI_DSS_CONTROLS,     desc: "8 controls — payment card security" },
  { id: "ccpa",      label: "CCPA / CPRA",  flag: "🌴", controls: CCPA_CONTROLS,        desc: "6 controls — California privacy law" },
  { id: "nist_csf",  label: "NIST CSF",     flag: "🇺🇸", controls: NIST_CSF_CONTROLS,   desc: "6 controls — NIST Cybersecurity Framework 2.0" },
  { id: "dpdp",      label: "DPDP Act",     flag: "🇮🇳", controls: DPDP_CONTROLS,       desc: "8 controls — India personal data law" },
  { id: "cert_in",   label: "CERT-In",      flag: "🇮🇳", controls: CERTIN_CONTROLS,     desc: "8 controls — India cyber security directions" },
  { id: "lpdp",      label: "Serbian LPDP", flag: "🇷🇸", controls: LPDP_CONTROLS,       desc: "8 controls — Serbia personal data law" },
  { id: "nis2",      label: "NIS2",         flag: "🇪🇺", controls: NIS2_CONTROLS,       desc: "10 controls — EU cybersecurity directive" },
  { id: "iso42001",  label: "ISO 42001",    flag: "🤖", controls: ISO42001_CONTROLS,    desc: "12 controls — AI management system" },
];

// ── Scoring ───────────────────────────────────────────────────────────────────

function computeResult(answers: Answers, controls: ControlDef[]) {
  let points = 0;
  let maxPoints = 0;
  const criticalGaps: ControlDef[] = [];
  const highGaps: ControlDef[] = [];
  const partialControls: ControlDef[] = [];

  for (const ctrl of controls) {
    const weight = ctrl.risk === "critical" ? 3 : ctrl.risk === "high" ? 2 : 1;
    maxPoints += weight;
    const ans = answers[ctrl.id];
    if (ans === "yes") {
      points += weight;
    } else if (ans === "partial") {
      points += weight * 0.4;
      partialControls.push(ctrl);
    } else {
      if (ctrl.risk === "critical") criticalGaps.push(ctrl);
      else highGaps.push(ctrl);
    }
  }

  const score = Math.round((points / maxPoints) * 100);
  let riskLevel: "critical" | "high" | "medium" | "good";
  let riskLabel: string;
  let headline: string;

  if (score < 35) {
    riskLevel = "critical"; riskLabel = "Critical Risk";
    headline = "You have critical gaps to fix";
  } else if (score < 60) {
    riskLevel = "high"; riskLabel = "High Risk";
    headline = "Significant gaps that auditors will find";
  } else if (score < 80) {
    riskLevel = "medium"; riskLabel = "Moderate Risk";
    headline = "Solid foundation — a few gaps to close";
  } else {
    riskLevel = "good"; riskLabel = "Good Posture";
    headline = "Strong compliance posture";
  }

  return { score, riskLevel, riskLabel, headline, criticalGaps, highGaps, partialControls };
}

// ── Gauge ─────────────────────────────────────────────────────────────────────

function GaugeRing({ score, riskLevel }: { score: number; riskLevel: string }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color =
    riskLevel === "critical" ? "#dc2626" :
    riskLevel === "high"     ? "#ea580c" :
    riskLevel === "medium"   ? "#d97706" : "#10b981";

  return (
    <div className="relative w-32 h-32 shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle cx="60" cy="60" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10" />
        <circle
          cx="60" cy="60" r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.4s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black" style={{ color }}>{score}%</span>
        <span className="text-[10px] text-gray-400 font-semibold uppercase tracking-wide text-center">compliant</span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function GapScanner() {
  const [started, setStarted] = useState(false);
  const [framework, setFramework] = useState<Framework>("soc2");
  const [answers, setAnswers] = useState<Answers>({});
  const [done, setDone] = useState(false);
  const [emailCaptured, setEmailCaptured] = useState(false);

  const fwDef = FRAMEWORK_OPTIONS.find((f) => f.id === framework)!;
  const CONTROLS = fwDef.controls;

  const answered = Object.keys(answers).length;
  const allAnswered = answered === CONTROLS.length;
  const result = done ? computeResult(answers, CONTROLS) : null;

  const setAnswer = (id: string, status: Status) =>
    setAnswers((a) => ({ ...a, [id]: status }));

  const reset = () => { setStarted(false); setAnswers({}); setDone(false); setEmailCaptured(false); };

  const RISK_CONFIG = {
    critical: { label: "Critical", bg: "bg-red-100", text: "text-red-700" },
    high:     { label: "High",     bg: "bg-orange-100", text: "text-orange-700" },
    medium:   { label: "Medium",   bg: "bg-yellow-100", text: "text-yellow-700" },
  };

  // ── Intro ──
  if (!started) {
    return (
      <div className="max-w-lg mx-auto text-center">
        <div className="w-16 h-16 bg-teal-50 border border-teal-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
          <Shield className="w-8 h-8 text-teal-600" />
        </div>
        <h3 className="text-2xl font-extrabold text-gray-900 mb-3">Compliance Gap Scanner</h3>
        <p className="text-gray-500 text-sm mb-6 leading-relaxed max-w-sm mx-auto">
          Assess the critical controls for your target framework in 2 minutes. See which gaps would fail your audit — and exactly what the regulator will say about each one.
        </p>

        {/* Framework selector */}
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Choose your framework</p>
        <div className="grid grid-cols-3 gap-2 mb-7">
          {FRAMEWORK_OPTIONS.map((fw) => (
            <button
              key={fw.id}
              onClick={() => setFramework(fw.id)}
              className={`flex flex-col items-center gap-1.5 px-3 py-3 rounded-xl border-2 text-sm font-semibold transition-all ${
                framework === fw.id
                  ? "border-teal-600 bg-teal-50 text-teal-700"
                  : "border-gray-200 text-gray-600 hover:border-teal-200 hover:bg-gray-50"
              }`}
            >
              <span className="text-xl">{fw.flag}</span>
              <span className="font-bold text-sm">{fw.label}</span>
              <span className="text-[10px] text-gray-400 leading-tight">{fw.desc}</span>
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-3 justify-center mb-7 text-xs">
          {[
            `${CONTROLS.length} controls assessed`,
            "No signup needed",
            "Real regulatory criteria",
          ].map((t) => (
            <div key={t} className="flex items-center gap-1.5 text-gray-500">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" /> {t}
            </div>
          ))}
        </div>
        <button
          onClick={() => setStarted(true)}
          className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-sm"
        >
          Scan my {fwDef.label} compliance <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    );
  }

  // ── Email gate ──
  if (done && result && !emailCaptured) {
    const riskColors: Record<string, string> = {
      critical: "text-red-600",
      high: "text-orange-600",
      medium: "text-yellow-600",
      good: "text-emerald-600",
    };
    const totalGaps = result.criticalGaps.length + result.highGaps.length;
    return (
      <ToolEmailGate
        toolName={`${framework}-gap-scanner`}
        headline={result.headline}
        subline={
          totalGaps > 0
            ? `${result.criticalGaps.length} critical gap${result.criticalGaps.length !== 1 ? "s" : ""} · ${result.highGaps.length} high-risk control${result.highGaps.length !== 1 ? "s" : ""} identified`
            : "Your controls are in good shape — full details below"
        }
        teasers={[
          {
            label: "readiness score",
            value: `${result.score}%`,
            valueColor: riskColors[result.riskLevel],
          },
          {
            label: "risk level",
            value: result.riskLabel,
            valueColor: riskColors[result.riskLevel],
          },
        ]}
        onUnlocked={() => setEmailCaptured(true)}
      />
    );
  }

  // ── Results ──
  if (done && result) {
    const totalGaps = result.criticalGaps.length + result.highGaps.length;
    const riskColors = {
      critical: "text-red-600",
      high:     "text-orange-600",
      medium:   "text-yellow-600",
      good:     "text-emerald-600",
    };

    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-lg p-6 md:p-8">
          {/* Score header */}
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 mb-6 pb-6 border-b border-gray-100">
            <GaugeRing score={result.score} riskLevel={result.riskLevel} />
            <div className="text-center sm:text-left">
              <p className={`text-xs font-bold uppercase tracking-widest mb-1 ${riskColors[result.riskLevel]}`}>
                {result.riskLabel}
              </p>
              <h3 className="text-xl font-extrabold text-gray-900 mb-2">{result.headline}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">
                {result.criticalGaps.length > 0 &&
                  `${result.criticalGaps.length} critical gap${result.criticalGaps.length > 1 ? "s" : ""} — immediate audit failures. `}
                {result.highGaps.length > 0 &&
                  `${result.highGaps.length} high-risk control${result.highGaps.length > 1 ? "s" : ""} auditors will probe. `}
                {result.partialControls.length > 0 &&
                  `${result.partialControls.length} partial control${result.partialControls.length > 1 ? "s" : ""} needing documentation. `}
                {totalGaps === 0 && result.partialControls.length === 0 &&
                  "Great shape. TraceLayer can automate the evidence collection to prove it continuously."}
              </p>
            </div>
          </div>

          {/* Control grid */}
          <div className="mb-6">
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-3">Control status overview — {fwDef.label}</p>
            <div className="flex flex-wrap gap-2">
              {CONTROLS.map((ctrl) => {
                const ans = answers[ctrl.id];
                return (
                  <div key={ctrl.id} title={ctrl.name} className="flex flex-col items-center gap-1">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-[10px] font-bold ${
                      ans === "yes" ? "bg-emerald-500" :
                      ans === "partial" ? "bg-yellow-400" : "bg-red-500"
                    }`}>
                      {ans === "yes" ? "✓" : ans === "partial" ? "~" : "✕"}
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex items-center gap-4 mt-2 text-[10px] text-gray-400">
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-500" /> In place</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400" /> Partial</span>
              <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500" /> Missing</span>
            </div>
          </div>

          {/* Critical gaps */}
          {result.criticalGaps.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-bold text-red-600 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                Critical gaps — immediate audit failures
              </p>
              <div className="space-y-2.5">
                {result.criticalGaps.map((ctrl) => (
                  <div key={ctrl.id} className="bg-red-50 border border-red-100 rounded-xl p-4">
                    <p className="font-semibold text-gray-900 text-sm mb-1">{ctrl.name}</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{ctrl.audit_note}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* High-risk gaps */}
          {result.highGaps.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-bold text-orange-600 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                High-risk gaps — auditors will probe these
              </p>
              <div className="space-y-2.5">
                {result.highGaps.map((ctrl) => (
                  <div key={ctrl.id} className="bg-orange-50 border border-orange-100 rounded-xl p-4">
                    <p className="font-semibold text-gray-900 text-sm mb-1">{ctrl.name}</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{ctrl.audit_note}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Partial controls */}
          {result.partialControls.length > 0 && (
            <div className="mb-5">
              <p className="text-[10px] font-bold text-yellow-600 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-yellow-500" />
                Partial — needs documentation to count
              </p>
              <div className="space-y-2">
                {result.partialControls.map((ctrl) => (
                  <div key={ctrl.id} className="bg-yellow-50 border border-yellow-100 rounded-xl px-4 py-3">
                    <p className="font-semibold text-gray-900 text-sm mb-0.5">{ctrl.name}</p>
                    <p className="text-xs text-gray-500 leading-relaxed">{ctrl.audit_note}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3 pt-5 border-t border-gray-100">
            <Link
              href="/register"
              className="flex-1 flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
            >
              Fix these {fwDef.label} gaps with TraceLayer <ArrowRight className="w-4 h-4" />
            </Link>
            <button
              onClick={reset}
              className="flex items-center justify-center gap-2 text-gray-500 hover:text-gray-700 text-sm font-medium px-4 py-3 rounded-xl border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" /> Rescan
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Checklist ──
  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress */}
      <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
        <span>{answered} of {CONTROLS.length} controls assessed</span>
        <span>{allAnswered ? "Ready — generate your report" : `${CONTROLS.length - answered} remaining`}</span>
      </div>
      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-6">
        <div
          className="h-full bg-teal-500 rounded-full transition-all duration-300"
          style={{ width: `${(answered / CONTROLS.length) * 100}%` }}
        />
      </div>

      <div className="space-y-3 mb-6">
        {CONTROLS.map((ctrl) => {
          const ans = answers[ctrl.id];
          const rCfg = RISK_CONFIG[ctrl.risk];
          return (
            <div
              key={ctrl.id}
              className={`bg-white border rounded-xl p-4 transition-all ${
                ans ? "border-gray-200 shadow-sm" : "border-gray-100"
              }`}
            >
              <div className="flex flex-wrap items-center gap-2 mb-2.5">
                <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${rCfg.bg} ${rCfg.text}`}>
                  {rCfg.label}
                </span>
                <span className="text-[10px] text-gray-400 font-medium">{ctrl.category}</span>
                <span className="text-[10px] text-gray-700 font-semibold">· {ctrl.name}</span>
              </div>
              <p className="text-sm text-gray-700 mb-3 leading-relaxed">{ctrl.question}</p>
              <div className="flex gap-2">
                {(
                  [
                    { v: "yes",     label: "In place",    active: "bg-emerald-600 text-white border-emerald-600" },
                    { v: "partial", label: "Partial",      active: "bg-yellow-500 text-white border-yellow-500" },
                    { v: "no",      label: "Not started", active: "bg-red-500 text-white border-red-500" },
                  ] as const
                ).map(({ v, label, active }) => (
                  <button
                    key={v}
                    onClick={() => setAnswer(ctrl.id, v)}
                    className={`flex-1 py-2 text-xs font-semibold rounded-lg border-2 transition-all ${
                      ans === v
                        ? active
                        : "border-gray-200 text-gray-500 hover:border-gray-300 hover:bg-gray-50"
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <button
        onClick={() => setDone(true)}
        disabled={!allAnswered}
        className="w-full flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-30 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-colors text-sm"
      >
        Generate my gap report <ArrowRight className="w-4 h-4" />
      </button>
    </div>
  );
}
