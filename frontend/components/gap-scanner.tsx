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

type Status = "yes" | "partial" | "no";
type Answers = Record<string, Status>;
type Framework = "soc2" | "dpdp" | "cert_in" | "lpdp" | "nis2";

const FRAMEWORK_OPTIONS: { id: Framework; label: string; flag: string; controls: ControlDef[]; desc: string }[] = [
  { id: "soc2",     label: "SOC 2",        flag: "🇺🇸", controls: SOC2_CONTROLS,    desc: "10 critical controls — Type I & II" },
  { id: "dpdp",     label: "DPDP Act",     flag: "🇮🇳", controls: DPDP_CONTROLS,    desc: "8 controls — India personal data law" },
  { id: "cert_in",  label: "CERT-In",      flag: "🇮🇳", controls: CERTIN_CONTROLS,  desc: "8 controls — India cyber security directions" },
  { id: "lpdp",     label: "Serbian LPDP", flag: "🇷🇸", controls: LPDP_CONTROLS,    desc: "8 controls — Serbia personal data law" },
  { id: "nis2",     label: "NIS2",         flag: "🇪🇺", controls: NIS2_CONTROLS,    desc: "10 controls — EU cybersecurity directive" },
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
