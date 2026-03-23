"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { api } from "@/lib/api";
import type { AuditEngagementView, ControlScore } from "@/lib/types";
import {
  Shield, CheckCircle2, XCircle, AlertTriangle, Clock,
  FileText, Lock, Calendar, Building2, Loader2, AlertCircle,
  ChevronDown, ChevronUp,
} from "lucide-react";

const FRAMEWORK_LABELS: Record<string, string> = {
  soc2: "SOC 2 Type II",
  iso27001: "ISO 27001:2022",
  hipaa: "HIPAA",
  gdpr: "GDPR",
  pci_dss: "PCI DSS",
  ccpa: "CCPA",
  nist_csf: "NIST CSF",
};

const STATUS_CONFIG = {
  passing: { icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-50", border: "border-emerald-200", label: "Passing" },
  warning: { icon: AlertTriangle, color: "text-amber-500", bg: "bg-amber-50", border: "border-amber-200", label: "Warning" },
  failing: { icon: XCircle, color: "text-red-500", bg: "bg-red-50", border: "border-red-200", label: "Failing" },
  no_evidence: { icon: Clock, color: "text-gray-400", bg: "bg-gray-50", border: "border-gray-200", label: "No evidence" },
  compliant: { icon: CheckCircle2, color: "text-emerald-500", bg: "bg-emerald-50", border: "border-emerald-200", label: "Compliant" },
  pending: { icon: Clock, color: "text-gray-400", bg: "bg-gray-50", border: "border-gray-200", label: "Pending" },
  not_applicable: { icon: Shield, color: "text-blue-400", bg: "bg-blue-50", border: "border-blue-200", label: "N/A" },
};

function ScoreRing({ score }: { score: number }) {
  const r = 40;
  const circ = 2 * Math.PI * r;
  const fill = (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 60 ? "#f59e0b" : "#ef4444";
  return (
    <svg width="100" height="100" viewBox="0 0 100 100" className="rotate-[-90deg]">
      <circle cx="50" cy="50" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10" />
      <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={`${fill} ${circ}`} strokeLinecap="round" />
    </svg>
  );
}

function ControlRow({ control }: { control: ControlScore }) {
  const [open, setOpen] = useState(false);
  const cfg = STATUS_CONFIG[control.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.no_evidence;
  const Icon = cfg.icon;
  return (
    <div className={`border rounded-xl overflow-hidden ${cfg.border}`}>
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50/50 transition-colors"
      >
        <Icon className={`w-4 h-4 shrink-0 ${cfg.color}`} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">{control.name}</p>
          <p className="text-xs text-gray-400 capitalize">{control.category?.replace(/_/g, " ")}</p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${cfg.bg} ${cfg.color}`}>{cfg.label}</span>
          <span className="text-xs text-gray-400">{control.evidence_count} records</span>
          {open ? <ChevronUp className="w-3.5 h-3.5 text-gray-400" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-400" />}
        </div>
      </button>
      {open && (
        <div className="border-t border-gray-100 px-4 py-3 bg-gray-50/30 space-y-1.5">
          {control.missing_types.length > 0 && (
            <p className="text-xs text-gray-500">Missing evidence: {control.missing_types.join(", ")}</p>
          )}
          {control.last_collected && (
            <p className="text-xs text-gray-400">
              Last collected: {new Date(control.last_collected).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function AuditViewPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<AuditEngagementView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    api.getAuditEngagementView(token)
      .then(setData)
      .catch((e) => setError(e.message ?? "Audit link not found or has expired"))
      .finally(() => setLoading(false));
  }, [token]);

  const fmtDate = (d: string) => new Date(d).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-brand-500" />
          <p className="text-sm text-gray-400">Loading audit view…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="bg-white rounded-2xl border border-red-100 p-8 max-w-md w-full text-center shadow-sm">
          <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-7 h-7 text-red-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Audit link unavailable</h2>
          <p className="text-sm text-gray-500 leading-relaxed">{error ?? "This link may have expired or been revoked."}</p>
          <p className="text-xs text-gray-400 mt-4">
            Contact <a href="mailto:support@tracelayer.it.com" className="text-brand-600 hover:underline">support@tracelayer.it.com</a> for help.
          </p>
        </div>
      </div>
    );
  }

  const frameworkLabel = FRAMEWORK_LABELS[data.framework] ?? data.framework.toUpperCase();
  const passing = data.controls.filter((c) => c.status === "passing").length;
  const failing = data.controls.filter((c) => c.status === "failing").length;
  const warning = data.controls.filter((c) => c.status === "warning").length;
  const noEvidence = data.controls.filter((c) => c.status === "no_evidence").length;
  const manualCompliant = data.manual_controls.filter((m) => m.status === "compliant").length;

  const sortedControls = [...data.controls].sort((a, b) => {
    const order: Record<string, number> = { failing: 0, warning: 1, no_evidence: 2, passing: 3 };
    return (order[a.status] ?? 4) - (order[b.status] ?? 4);
  });

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 px-4 sm:px-6 py-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between gap-4">
          <Link href="https://tracelayer.it.com" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-bold text-gray-900">TraceLayer</span>
          </Link>
          <div className="flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-gray-400" />
            <span className="text-xs text-gray-400 font-medium">Read-only audit access</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Engagement header */}
        <div className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-3">
                <span className="text-xs font-bold uppercase tracking-widest text-brand-600 bg-brand-50 px-2.5 py-1 rounded-full">
                  {frameworkLabel}
                </span>
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600">
                  Active engagement
                </span>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-1">{data.customer_name}</h1>
              <p className="text-sm text-gray-500 mb-4">
                {data.auditor_firm ? `${data.auditor_firm} — ` : ""}Audit access granted to {data.auditor_email}
              </p>
              <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-4 h-4 text-gray-400" />
                  <span>Observation period: <strong>{fmtDate(data.obs_start)} – {fmtDate(data.obs_end)}</strong></span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Building2 className="w-4 h-4 text-gray-400" />
                  <span>Access granted: {fmtDate(data.created_at)}</span>
                </div>
              </div>
            </div>
            <div className="relative shrink-0">
              <ScoreRing score={data.score} />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-black text-gray-900">{data.score}</span>
                <span className="text-[10px] text-gray-400 font-medium">/ 100</span>
              </div>
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Passing controls", value: passing, color: "text-emerald-600", bg: "bg-emerald-50" },
            { label: "Failing controls", value: failing, color: "text-red-600", bg: "bg-red-50" },
            { label: "Evidence records", value: data.evidence_count, color: "text-brand-600", bg: "bg-brand-50" },
            { label: "Manual controls", value: `${manualCompliant}/${data.manual_controls.length}`, color: "text-violet-600", bg: "bg-violet-50" },
          ].map(({ label, value, color, bg }) => (
            <div key={label} className="bg-white rounded-2xl border border-gray-100 p-4 shadow-sm">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className={`text-2xl font-black ${color}`}>{value}</p>
            </div>
          ))}
        </div>

        {/* Control breakdown bar */}
        {data.controls.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm">
            <p className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-3">Control breakdown</p>
            <div className="flex rounded-lg overflow-hidden h-3 mb-3">
              {passing > 0 && <div className="bg-emerald-400" style={{ width: `${(passing / data.controls.length) * 100}%` }} />}
              {warning > 0 && <div className="bg-amber-400" style={{ width: `${(warning / data.controls.length) * 100}%` }} />}
              {failing > 0 && <div className="bg-red-400" style={{ width: `${(failing / data.controls.length) * 100}%` }} />}
              {noEvidence > 0 && <div className="bg-gray-200" style={{ width: `${(noEvidence / data.controls.length) * 100}%` }} />}
            </div>
            <div className="flex flex-wrap gap-x-5 gap-y-1.5">
              {[
                { label: "Passing", count: passing, color: "bg-emerald-400" },
                { label: "Warning", count: warning, color: "bg-amber-400" },
                { label: "Failing", count: failing, color: "bg-red-400" },
                { label: "No evidence", count: noEvidence, color: "bg-gray-300" },
              ].map(({ label, count, color }) => (
                <div key={label} className="flex items-center gap-1.5 text-xs text-gray-500">
                  <div className={`w-2.5 h-2.5 rounded-sm ${color}`} />
                  {count} {label}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Automated controls */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Automated controls</h2>
              <p className="text-xs text-gray-400 mt-0.5">Collected continuously from connected integrations</p>
            </div>
            <div className="flex items-center gap-2">
              {failing + warning > 0 ? (
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-amber-50 text-amber-600">
                  {failing + warning} need attention
                </span>
              ) : (
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-600">All passing</span>
              )}
            </div>
          </div>
          <div className="p-4 space-y-2">
            {sortedControls.map((c) => (
              <ControlRow key={c.category} control={c} />
            ))}
            {sortedControls.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-6">No automated controls configured for this framework.</p>
            )}
          </div>
        </div>

        {/* Manual controls */}
        {data.manual_controls.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-900">Manual controls & documentation</h2>
              <p className="text-xs text-gray-400 mt-0.5">Policies, procedures, and human-managed controls</p>
            </div>
            <div className="divide-y divide-gray-50">
              {data.manual_controls.map((mc) => {
                const cfg = STATUS_CONFIG[mc.status as keyof typeof STATUS_CONFIG] ?? STATUS_CONFIG.pending;
                const Icon = cfg.icon;
                return (
                  <div key={mc.control_id} className="flex items-start gap-3 px-5 py-3.5">
                    <Icon className={`w-4 h-4 shrink-0 mt-0.5 ${cfg.color}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">{mc.name}</p>
                      <p className="text-xs text-gray-400 mt-0.5 leading-relaxed">{mc.description}</p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-0.5 rounded-full shrink-0 ${cfg.bg} ${cfg.color}`}>
                      {cfg.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="bg-white rounded-2xl border border-gray-100 p-5 shadow-sm flex flex-col sm:flex-row items-center gap-4">
          <FileText className="w-8 h-8 text-brand-400 shrink-0" />
          <div className="flex-1 text-center sm:text-left">
            <p className="text-sm font-semibold text-gray-900">Need the full audit package?</p>
            <p className="text-xs text-gray-400 mt-0.5">
              Ask {data.customer_name} to generate an AI Audit Package PDF from their TraceLayer dashboard — includes narrative, evidence index, and control status.
            </p>
          </div>
          <a
            href={`mailto:support@tracelayer.it.com`}
            className="shrink-0 text-xs font-semibold text-brand-600 hover:text-brand-700 border border-brand-200 hover:border-brand-300 px-4 py-2 rounded-xl transition-colors"
          >
            Contact support
          </a>
        </div>

        <p className="text-center text-xs text-gray-400 pb-4">
          Powered by{" "}
          <Link href="https://tracelayer.it.com" className="text-brand-500 hover:underline">TraceLayer</Link>
          {" "}· This view is read-only. Data is as of {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}.
        </p>
      </main>
    </div>
  );
}
