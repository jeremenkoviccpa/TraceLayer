"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, RotateCcw, Shield, CheckCircle2 } from "lucide-react";

// ── Control definitions ───────────────────────────────────────────────────────

const CONTROLS = [
  {
    id: "mfa",
    category: "Access Control",
    name: "Multi-Factor Authentication",
    question: "MFA is enforced for all users and admin accounts across every critical system",
    risk: "critical" as const,
    audit_note: "Auditors test this directly on day 1. Missing MFA on any admin account is an immediate, often fatal, audit finding.",
  },
  {
    id: "logging",
    category: "Monitoring",
    name: "Centralized Audit Logging",
    question: "All systems ship logs to a centralized, monitored, tamper-proof location",
    risk: "critical" as const,
    audit_note: "No centralized logs = no evidence = no SOC 2. This directly fails CC7.1 and CC7.2.",
  },
  {
    id: "encryption",
    category: "Data Protection",
    name: "Encryption at Rest & In Transit",
    question: "Sensitive data is encrypted at rest (databases, storage) and in transit (TLS 1.2+)",
    risk: "critical" as const,
    audit_note: "Auditors review every database and API surface. Unencrypted data is a critical finding against C1.",
  },
  {
    id: "access_reviews",
    category: "Access Control",
    name: "Quarterly Access Reviews",
    question: "User access is formally reviewed every quarter with dated, signed records",
    risk: "high" as const,
    audit_note: "Doing reviews without records doesn't count. Auditors need dated, evidence-backed documentation.",
  },
  {
    id: "vuln_scanning",
    category: "Risk Management",
    name: "Vulnerability Scanning",
    question: "Automated vulnerability scans run on a schedule with tracked remediation",
    risk: "high" as const,
    audit_note: "You need scan results AND evidence that critical findings were patched on time. 'We scan sometimes' fails.",
  },
  {
    id: "incident_response",
    category: "Operations",
    name: "Incident Response Plan",
    question: "A documented, versioned IR plan exists with evidence of a tabletop exercise",
    risk: "high" as const,
    audit_note: "'We have a Notion doc' doesn't satisfy CC9. You need a versioned document with a dated exercise record.",
  },
  {
    id: "change_mgmt",
    category: "Change Management",
    name: "Code Review & Deployment Gates",
    question: "All code is peer-reviewed and production deployments require a formal approval",
    risk: "high" as const,
    audit_note: "Auditors pull your git history. Any unreviewed commit to production is a direct CC8 failure.",
  },
  {
    id: "backup",
    category: "Availability",
    name: "Backup & Recovery Testing",
    question: "Backups run automatically, success is monitored, and recovery is tested annually",
    risk: "medium" as const,
    audit_note: "You need backup success logs AND a documented recovery test result. 'We assume it works' fails.",
  },
  {
    id: "vendor_mgmt",
    category: "Vendor Risk",
    name: "Vendor Security Assessments",
    question: "Key vendors are assessed annually — SOC 2 reports collected, questionnaires reviewed",
    risk: "medium" as const,
    audit_note: "SOC 2 CC9 requires documented vendor risk. Collect your critical vendors' SOC 2 reports each year.",
  },
  {
    id: "security_training",
    category: "Human Resources",
    name: "Annual Security Training",
    question: "Every team member completed documented security awareness training in the past 12 months",
    risk: "medium" as const,
    audit_note: "Auditors ask for completion records with names and dates. 'We discussed it in a meeting' fails CC1.4.",
  },
];

type Status = "yes" | "partial" | "no";
type Answers = Record<string, Status>;

// ── Scoring ───────────────────────────────────────────────────────────────────

function computeResult(answers: Answers) {
  let points = 0;
  let maxPoints = 0;
  const criticalGaps: typeof CONTROLS = [];
  const highGaps: typeof CONTROLS = [];
  const partialControls: typeof CONTROLS = [];

  for (const ctrl of CONTROLS) {
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
    headline = "Your audit would fail today";
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
  const [answers, setAnswers] = useState<Answers>({});
  const [done, setDone] = useState(false);

  const answered = Object.keys(answers).length;
  const allAnswered = answered === CONTROLS.length;
  const result = done ? computeResult(answers) : null;

  const setAnswer = (id: string, status: Status) =>
    setAnswers((a) => ({ ...a, [id]: status }));

  const reset = () => { setStarted(false); setAnswers({}); setDone(false); };

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
        <h3 className="text-2xl font-extrabold text-gray-900 mb-3">SOC 2 Gap Scanner</h3>
        <p className="text-gray-500 text-sm mb-6 leading-relaxed max-w-sm mx-auto">
          Assess 10 critical SOC 2 controls in 2 minutes. See which gaps would fail your audit — and exactly what your auditor will say about each one.
        </p>
        <div className="flex flex-wrap gap-3 justify-center mb-7 text-xs">
          {[
            "10 SOC 2 controls",
            "No signup needed",
            "Real audit criteria",
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
          Scan my compliance <ArrowRight className="w-4 h-4" />
        </button>
      </div>
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
            <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-widest mb-3">Control status overview</p>
            <div className="grid grid-cols-10 gap-2">
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
              Fix these gaps with TraceLayer <ArrowRight className="w-4 h-4" />
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
