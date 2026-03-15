"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ComplianceScore, ManualControl, Member } from "@/lib/types";
import { getRemediationForMissingType, getRemediationForCategory } from "@/lib/remediation";
import {
  ShieldCheck,
  CheckCircle2,
  MinusCircle,
  Circle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  RefreshCw,
  Copy,
  Check,
  AlertCircle,
  Wrench,
  User as UserIcon,
} from "lucide-react";

const FRAMEWORKS = [
  { value: "soc2",     label: "SOC 2",     description: "Trust Service Criteria"        },
  { value: "iso27001", label: "ISO 27001", description: "Information Security Mgmt"     },
  { value: "hipaa",    label: "HIPAA",     description: "Health Data Privacy"            },
  { value: "gdpr",     label: "GDPR",      description: "EU Data Protection"             },
  { value: "pci_dss",  label: "PCI DSS",   description: "Payment Card Security"          },
  { value: "ccpa",     label: "CCPA",      description: "California Privacy"             },
  { value: "nist_csf", label: "NIST CSF",  description: "Cybersecurity Framework"        },
];

type Status = "pending" | "compliant" | "not_applicable";
const STATUS_CYCLE: Status[] = ["pending", "compliant", "not_applicable"];

function StatusIcon({ status }: { status: Status }) {
  if (status === "compliant")
    return <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />;
  if (status === "not_applicable")
    return <MinusCircle className="w-5 h-5 text-gray-300 shrink-0" />;
  return <Circle className="w-5 h-5 text-gray-300 shrink-0" />;
}

function statusLabel(status: Status) {
  if (status === "compliant")      return "Compliant";
  if (status === "not_applicable") return "N/A";
  return "Pending";
}

function AutoBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    passing:     "bg-emerald-50 text-emerald-700",
    warning:     "bg-amber-50   text-amber-700",
    failing:     "bg-red-50     text-red-600",
    no_evidence: "bg-gray-100   text-gray-500",
  };
  const labels: Record<string, string> = {
    passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
  };
  return (
    <span className={`inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${styles[status] ?? "bg-gray-100 text-gray-500"}`}>
      {labels[status] ?? status}
    </span>
  );
}

function scoreColor(score: number) {
  if (score >= 80) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-500";
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-400";
  return "bg-red-400";
}

// ── Evidence dot chips ─────────────────────────────────────────────────────────
function EvidenceDots({
  covered,
  missing,
}: {
  covered: string[];
  missing: string[];
}) {
  if (covered.length === 0 && missing.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2.5">
      {covered.map((t) => (
        <span
          key={`c-${t}`}
          className="inline-flex items-center gap-1 bg-emerald-50 border border-emerald-100 text-emerald-700 text-[11px] font-medium px-2 py-0.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
          {t}
        </span>
      ))}
      {missing.map((t) => (
        <span
          key={`m-${t}`}
          className="inline-flex items-center gap-1 bg-red-50 border border-red-100 text-red-600 text-[11px] font-medium px-2 py-0.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
          {t}
        </span>
      ))}
    </div>
  );
}

// ── Remediation panel ─────────────────────────────────────────────────────────
function RemediationPanel({ missingTypes, category }: { missingTypes: string[]; category: string }) {
  const [open, setOpen] = useState(false);

  const guides = missingTypes
    .map((t) => getRemediationForMissingType(t))
    .filter(Boolean);
  const fallback = guides.length === 0 ? getRemediationForCategory(category) : null;
  const allGuides = guides.length > 0 ? guides : fallback ? [fallback] : [];

  if (allGuides.length === 0) return null;

  return (
    <div className="mt-2.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-600 hover:text-amber-700 transition-colors"
      >
        <Wrench className="w-3 h-3" />
        {open ? "Hide fix guide" : "How to fix this"}
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>
      {open && (
        <div className="mt-2 space-y-3">
          {allGuides.map((guide, i) => guide && (
            <div key={i} className="bg-amber-50 border border-amber-100 rounded-xl p-3.5">
              <div className="flex items-center gap-1.5 mb-2">
                <span className={`text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full ${
                  guide.urgency === "critical" ? "bg-red-100 text-red-700" :
                  guide.urgency === "high"     ? "bg-orange-100 text-orange-700" :
                  "bg-yellow-100 text-yellow-700"
                }`}>{guide.urgency}</span>
                <span className="text-xs font-semibold text-gray-700">{guide.title}</span>
              </div>
              <ol className="space-y-1.5">
                {guide.steps.map((step, j) => (
                  <li key={j} className="flex items-start gap-2 text-xs text-gray-600">
                    <span className="w-4 h-4 rounded-full bg-amber-200 text-amber-800 flex items-center justify-center text-[9px] font-bold shrink-0 mt-0.5">{j + 1}</span>
                    {step}
                  </li>
                ))}
              </ol>
              {guide.hint && (
                <p className="text-[10px] text-gray-400 mt-2 italic">{guide.hint}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Manual control row ────────────────────────────────────────────────────────
function ManualControlRow({
  control,
  framework,
  members,
  onUpdate,
}: {
  control: ManualControl;
  framework: string;
  members: Member[];
  onUpdate: (updated: ManualControl) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState(control.notes ?? "");
  const [saving, setSaving] = useState(false);
  const [assigning, setAssigning] = useState(false);

  const cycleStatus = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const idx  = STATUS_CYCLE.indexOf(control.status as Status);
    const next = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length];
    setSaving(true);
    try {
      const updated = await api.updateManualControl(control.control_id, framework, next, notes || null);
      onUpdate(updated);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const saveNotes = async () => {
    setSaving(true);
    try {
      const updated = await api.updateManualControl(control.control_id, framework, control.status, notes || null);
      onUpdate(updated);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const handleAssign = async (ownerUserId: string | null) => {
    setAssigning(true);
    try {
      const updated = await api.assignManualControl(control.control_id, framework, ownerUserId);
      onUpdate(updated);
    } catch { /* ignore */ } finally { setAssigning(false); }
  };

  const statusColors: Record<Status, string> = {
    compliant:       "text-emerald-600",
    not_applicable:  "text-gray-400",
    pending:         "text-amber-600",
  };

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
      <div
        className="flex items-center gap-3 p-4 cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <button
          onClick={cycleStatus}
          disabled={saving}
          className="shrink-0 disabled:opacity-40 hover:scale-110 transition-transform"
          title="Click to cycle status"
        >
          <StatusIcon status={control.status as Status} />
        </button>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-800 leading-snug">{control.name}</p>
          <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{control.description}</p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className={`text-xs font-semibold hidden sm:block ${statusColors[control.status as Status]}`}>
            {statusLabel(control.status as Status)}
          </span>
          {expanded
            ? <ChevronUp className="w-4 h-4 text-gray-300" />
            : <ChevronDown className="w-4 h-4 text-gray-300" />
          }
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3 bg-gray-50/50">
          <p className="text-xs text-gray-500 mb-3 leading-relaxed">{control.description}</p>

          {/* Status pills */}
          <div className="flex gap-2 mb-3">
            {STATUS_CYCLE.map((s) => (
              <button
                key={s}
                onClick={async () => {
                  if (s === control.status) return;
                  setSaving(true);
                  try {
                    const updated = await api.updateManualControl(control.control_id, framework, s, notes || null);
                    onUpdate(updated);
                  } catch { /* ignore */ } finally { setSaving(false); }
                }}
                disabled={saving}
                className={`text-xs px-2.5 py-1 rounded-lg font-medium border transition-all ${
                  control.status === s
                    ? s === "compliant"    ? "bg-emerald-50 border-emerald-200 text-emerald-700"
                    : s === "not_applicable" ? "bg-gray-100 border-gray-200 text-gray-500"
                    : "bg-amber-50 border-amber-200 text-amber-700"
                    : "bg-white border-gray-200 text-gray-400 hover:border-gray-300 hover:text-gray-600"
                }`}
              >
                {statusLabel(s)}
              </button>
            ))}
          </div>

          {/* Owner assignment */}
          {members.length > 0 && (
            <div className="mb-3">
              <label className="block text-xs font-medium text-gray-500 mb-1.5 flex items-center gap-1">
                <UserIcon className="w-3 h-3" /> Owner
              </label>
              <select
                value={control.owner_user_id ?? ""}
                onChange={(e) => handleAssign(e.target.value || null)}
                disabled={assigning}
                className="w-full text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500/25 focus:border-brand-400 bg-white text-gray-700 transition-all disabled:opacity-50"
              >
                <option value="">Unassigned</option>
                {members.map((m) => (
                  <option key={m.id} value={m.id}>{m.email}</option>
                ))}
              </select>
              {control.owner_name && (
                <p className="text-[10px] text-gray-400 mt-1">Currently: {control.owner_name}</p>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes, evidence links, or context…"
              rows={2}
              className="flex-1 text-xs border border-gray-200 rounded-xl px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500/25 focus:border-brand-400 resize-none bg-white transition-all"
            />
            <button
              onClick={saveNotes}
              disabled={saving}
              className="self-end px-3 py-2 text-xs font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-40 transition-colors"
            >
              {saving ? "…" : "Save"}
            </button>
          </div>
          {control.updated_at && (
            <p className="text-xs text-gray-400 mt-2">
              Updated {new Date(control.updated_at).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ── AI Advisor ────────────────────────────────────────────────────────────────
function AIAdvisor({
  framework,
  onGenerate,
  loading,
  summary,
  generatedAt,
  error,
}: {
  framework: string;
  onGenerate: () => void;
  loading: boolean;
  summary: string | null;
  generatedAt: string | null;
  error: string | null;
}) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!summary) return;
    navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden shadow-card-md">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 px-4 sm:px-5 py-3.5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/15 flex items-center justify-center shrink-0">
          <Sparkles className="w-4 h-4 text-violet-300" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-none">AI Compliance Advisor</p>
          <div className="flex items-center gap-1.5 mt-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
            <span className="text-xs text-slate-400">Llama 3.3 · Groq</span>
          </div>
        </div>
        {summary && !loading && (
          <button
            onClick={onGenerate}
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white bg-white/10 hover:bg-white/20 px-2.5 py-1.5 rounded-lg border border-white/10 transition-all shrink-0"
          >
            <RefreshCw className="w-3 h-3" />
            <span className="hidden sm:block">Regenerate</span>
          </button>
        )}
      </div>

      {/* Body */}
      <div className="bg-white px-4 sm:px-5 py-5">

        {/* Empty state */}
        {!summary && !loading && !error && (
          <div className="flex flex-col items-center text-center py-6 gap-4">
            <div className="relative">
              <div className="w-14 h-14 rounded-2xl bg-slate-900 flex items-center justify-center shadow-lg">
                <Sparkles className="w-6 h-6 text-violet-300" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 rounded-full border-2 border-white flex items-center justify-center">
                <span className="text-white text-[9px] font-black">AI</span>
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900 mb-1">Get your compliance briefing</p>
              <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
                Analyzes your live {framework.toUpperCase()} evidence and surfaces the single most impactful action to improve your score.
              </p>
            </div>
            <button
              onClick={onGenerate}
              className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-violet-300" />
              Generate insight
            </button>
          </div>
        )}

        {/* Loading — typing indicator */}
        {loading && (
          <div className="py-2">
            <div className="flex items-start gap-3">
              <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center shrink-0 mt-0.5">
                <Sparkles className="w-3.5 h-3.5 text-violet-300" />
              </div>
              <div className="flex-1">
                <div className="inline-flex items-center gap-1 bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3 mb-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
                </div>
                <div className="space-y-2 max-w-md">
                  <div className="h-2.5 bg-slate-100 rounded-full animate-pulse w-full" />
                  <div className="h-2.5 bg-slate-100 rounded-full animate-pulse w-[88%]" />
                  <div className="h-2.5 bg-slate-100 rounded-full animate-pulse w-[72%]" />
                </div>
                <p className="text-xs text-gray-400 mt-2">Analyzing your compliance posture…</p>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="flex items-start gap-3 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-red-700">Couldn&apos;t generate summary</p>
              <p className="text-xs text-red-400 mt-0.5 break-words">{error}</p>
            </div>
            <button
              onClick={onGenerate}
              className="text-xs font-semibold text-red-600 hover:text-red-700 shrink-0 underline underline-offset-2"
            >
              Retry
            </button>
          </div>
        )}

        {/* Result — chat bubble style */}
        {summary && !loading && (
          <div className="flex items-start gap-3">
            <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3.5 mb-2">
                <p className="text-sm text-gray-800 leading-relaxed whitespace-pre-line">{summary}</p>
              </div>
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <span className="text-xs text-gray-400">
                  {generatedAt
                    ? `Generated at ${new Date(generatedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
                    : ""}
                </span>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-700 transition-colors"
                >
                  {copied
                    ? <><Check className="w-3.5 h-3.5 text-emerald-500" /><span className="text-emerald-600">Copied</span></>
                    : <><Copy className="w-3.5 h-3.5" />Copy</>
                  }
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CompliancePage() {
  const [framework, setFramework] = useState("soc2");
  const [score, setScore]         = useState<ComplianceScore | null>(null);
  const [manualControls, setManualControls] = useState<ManualControl[]>([]);
  const [members, setMembers]     = useState<Member[]>([]);
  const [loading, setLoading]     = useState(true);

  const [aiSummary, setAiSummary]         = useState<string | null>(null);
  const [aiLoading, setAiLoading]         = useState(false);
  const [aiError, setAiError]             = useState<string | null>(null);
  const [aiGeneratedAt, setAiGeneratedAt] = useState<string | null>(null);

  const load = async (fw: string) => {
    setLoading(true);
    setAiSummary(null);
    setAiError(null);
    setAiGeneratedAt(null);
    try {
      const [s, m] = await Promise.all([api.getComplianceScore(fw), api.getManualControls(fw)]);
      setScore(s);
      setManualControls(m);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => { load(framework); }, [framework]); // eslint-disable-line
  useEffect(() => { api.getMembers().then(setMembers).catch(() => {}); }, []);

  const generateSummary = async () => {
    setAiLoading(true);
    setAiError(null);
    try {
      const result = await api.getAISummary(framework);
      setAiSummary(result.summary);
      setAiGeneratedAt(result.generated_at);
    } catch (e: unknown) {
      setAiError(e instanceof Error ? e.message : "Failed to generate summary");
    } finally {
      setAiLoading(false);
    }
  };

  const handleUpdate = (updated: ManualControl) =>
    setManualControls((prev) => prev.map((c) => (c.control_id === updated.control_id ? { ...c, ...updated } : c)));

  const manualCompliant = manualControls.filter((c) => c.status === "compliant").length;
  const manualTotal     = manualControls.filter((c) => c.status !== "not_applicable").length;

  return (
    <div className="animate-fade-in">
      {/* Page header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>

        {/* Framework pill selector */}
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {FRAMEWORKS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFramework(f.value)}
              className={`shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all duration-150 ${
                framework === f.value
                  ? "bg-brand-600 text-white shadow-sm shadow-brand-600/25"
                  : "bg-white border border-gray-200 text-gray-500 hover:border-brand-300 hover:text-brand-600"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="space-y-6">
          <div className="h-36 bg-gray-100 rounded-2xl animate-pulse" />
          <div className="space-y-2">
            {[0,1,2,3,4,5].map((i) => <div key={i} className="h-16 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
          <div className="space-y-2">
            {[0,1,2,3].map((i) => <div key={i} className="h-14 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        </div>
      ) : (
        <div className="space-y-6">

          {/* AI Advisor */}
          <AIAdvisor
            framework={framework}
            onGenerate={generateSummary}
            loading={aiLoading}
            summary={aiSummary}
            generatedAt={aiGeneratedAt}
            error={aiError}
          />

          {/* Automated controls */}
          <section>
            <div className="flex items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-brand-500 shrink-0" />
                <h2 className="font-semibold text-gray-800 text-sm">Automated controls</h2>
              </div>
              {score && (
                <span className={`text-xl font-bold shrink-0 ${scoreColor(score.overall_score)}`}>
                  {score.overall_score}%
                </span>
              )}
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-card divide-y divide-gray-50 overflow-hidden">
              {score?.controls.map((c) => (
                <div key={c.category} className="px-4 sm:px-5 py-4">
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <span className="text-sm font-semibold text-gray-800 leading-snug">{c.name}</span>
                      <AutoBadge status={c.status} />
                    </div>
                    <span className={`text-sm font-bold shrink-0 ${scoreColor(c.score)}`}>{c.score}%</span>
                  </div>

                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mb-2">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${scoreBarColor(c.score)}`}
                      style={{ width: `${c.score}%` }}
                    />
                  </div>

                  <EvidenceDots covered={c.covered_types} missing={c.missing_types} />
                  {(c.status === "failing" || c.status === "warning" || c.status === "no_evidence") && (
                    <RemediationPanel missingTypes={c.missing_types} category={c.category} />
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Manual controls */}
          <section>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <CheckCircle2 className="w-4 h-4 text-brand-500 shrink-0" />
              <h2 className="font-semibold text-gray-800 text-sm">Manual controls</h2>
              <span className="text-xs text-gray-400">
                {manualCompliant}/{manualTotal} complete
              </span>
              <div className="ml-auto h-1.5 w-28 bg-gray-100 rounded-full overflow-hidden shrink-0">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                  style={{ width: `${manualTotal > 0 ? (manualCompliant / manualTotal) * 100 : 0}%` }}
                />
              </div>
            </div>
            <p className="text-xs text-gray-400 mb-4">
              Tap the circle to cycle status. Expand a row to set status explicitly or add notes.
            </p>
            <div className="space-y-2">
              {manualControls.map((c) => (
                <ManualControlRow
                  key={c.control_id}
                  control={c}
                  framework={framework}
                  members={members}
                  onUpdate={handleUpdate}
                />
              ))}
            </div>
          </section>

        </div>
      )}
    </div>
  );
}
