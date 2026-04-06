"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ActionPlan, AuditComment, AuditEngagement, ComplianceScore, ControlScore, ManualControl, Member, Document, RemediationSuggestion } from "@/lib/types";
import { useRef } from "react";
import { PlanGate, useUpgrade } from "@/components/plan-gate";
import { usePlan } from "@/hooks/usePlan";
import { getRemediationForMissingType, getRemediationForCategory } from "@/lib/remediation";
import {
  ShieldCheck,
  CheckCircle2,
  MinusCircle,
  Circle,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  AlertCircle,
  Wrench,
  User as UserIcon,
  Lock,
  Paperclip,
  Upload,
  Trash2,
  FileText,
  X,
  FileSearch,
  Send,
  Link as LinkIcon,
  Loader2,
  MessageCircle,
  CalendarDays,
  Sparkles,
  Zap,
  ArrowRight,
  RefreshCw,
  ShieldOff,
  ShieldAlert,
  Ban,
} from "lucide-react";

const FRAMEWORKS = [
  { value: "soc2",     label: "SOC 2",     description: "Trust Service Criteria"        },
  { value: "iso27001", label: "ISO 27001", description: "Information Security Mgmt"     },
  { value: "hipaa",    label: "HIPAA",     description: "Health Data Privacy"            },
  { value: "gdpr",     label: "GDPR",      description: "EU Data Protection"             },
  { value: "pci_dss",  label: "PCI DSS",   description: "Payment Card Security"          },
  { value: "ccpa",     label: "CCPA",      description: "California Privacy"             },
  { value: "nist_csf", label: "NIST CSF",  description: "Cybersecurity Framework"        },
  { value: "dpdp",     label: "DPDP Act",  description: "India Data Protection 2023"     },
  { value: "cert_in",  label: "CERT-In",   description: "India Cybersecurity Directions" },
  { value: "lpdp",     label: "Serbian LPDP", description: "Serbian Law on Personal Data Protection" },
  { value: "nis2",     label: "NIS2 Directive", description: "EU Network and Information Security" },
  { value: "iso42001", label: "ISO 42001",    description: "AI Management System Standard" },
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
    exception:   "bg-amber-50   text-amber-700 border border-amber-200",
    excluded:    "bg-gray-100   text-gray-400",
  };
  const labels: Record<string, string> = {
    passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
    exception: "Risk accepted", excluded: "N/A",
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

// ── Control documents ─────────────────────────────────────────────────────────
function ControlDocuments({ controlId, framework }: { controlId: string; framework: string }) {
  const resourceId = `${framework}_${controlId}`;
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (open) {
      api.getDocuments("control", resourceId).then(setDocs).catch(() => {});
    }
  }, [open, resourceId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";
    setUploading(true);
    try {
      const doc = await api.uploadDocument(file, "control", resourceId);
      setDocs((prev) => [doc, ...prev]);
    } catch { /* ignore */ } finally { setUploading(false); }
  };

  const handleDelete = async (id: string) => {
    setDeleting(id);
    try {
      await api.deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch { /* ignore */ } finally { setDeleting(null); }
  };

  const handleDownload = async (doc: Document) => {
    try {
      const { url } = await api.getDocumentUrl(doc.id);
      window.open(url, "_blank");
    } catch { /* ignore */ }
  };

  const formatBytes = (b: number) =>
    b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(0)} KB` : `${(b / (1024 * 1024)).toFixed(1)} MB`;

  return (
    <div className="mt-2.5">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 hover:text-slate-700 transition-colors"
      >
        <Paperclip className="w-3 h-3" />
        {open ? "Hide attachments" : `Attachments${docs.length > 0 && !open ? ` (${docs.length})` : ""}`}
        {open ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
      </button>

      {open && (
        <div className="mt-2 bg-slate-50 border border-slate-100 rounded-xl p-3">
          {/* Upload */}
          <label className={`flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg border border-dashed cursor-pointer transition-colors mb-2 ${
            uploading ? "opacity-50 cursor-not-allowed border-slate-200 text-slate-400" : "border-teal-200 text-teal-600 hover:bg-teal-50"
          }`}>
            {uploading ? <Upload className="w-3.5 h-3.5 animate-pulse" /> : <Upload className="w-3.5 h-3.5" />}
            {uploading ? "Uploading…" : "Attach file"}
            <input type="file" className="hidden" disabled={uploading} onChange={handleUpload} />
          </label>

          {/* List */}
          {docs.length === 0 ? (
            <p className="text-[11px] text-slate-400 text-center py-1">No files attached yet.</p>
          ) : (
            <div className="space-y-1.5">
              {docs.map((doc) => (
                <div key={doc.id} className="flex items-center gap-2 bg-white rounded-lg border border-slate-100 px-2.5 py-1.5">
                  <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  <button
                    onClick={() => handleDownload(doc)}
                    className="flex-1 min-w-0 text-left text-[11px] text-slate-600 hover:text-teal-600 font-medium truncate transition-colors"
                  >
                    {doc.filename}
                  </button>
                  <span className="text-[10px] text-slate-400 shrink-0">{formatBytes(doc.file_size)}</span>
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deleting === doc.id}
                    className="shrink-0 text-slate-300 hover:text-red-400 transition-colors disabled:opacity-40"
                  >
                    {deleting === doc.id ? <X className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Manual control row ────────────────────────────────────────────────────────
// ── SLA helpers ───────────────────────────────────────────────────────────────
function slaDaysRemaining(due_date: string | null): number | null {
  if (!due_date) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  return Math.ceil((new Date(due_date).getTime() - today.getTime()) / 86_400_000);
}

function SlaBadge({ due_date }: { due_date: string | null }) {
  const days = slaDaysRemaining(due_date);
  if (days === null) return null;
  if (days < 0)  return <span className="text-[10px] font-bold bg-red-100 text-red-700 px-1.5 py-0.5 rounded-md">Overdue {Math.abs(days)}d</span>;
  if (days <= 3) return <span className="text-[10px] font-bold bg-orange-100 text-orange-700 px-1.5 py-0.5 rounded-md">Due in {days}d</span>;
  if (days <= 7) return <span className="text-[10px] font-semibold bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-md">Due in {days}d</span>;
  return <span className="text-[10px] text-gray-400 px-1.5 py-0.5 rounded-md bg-gray-100">{new Date(due_date!).toLocaleDateString("en-US", { month: "short", day: "numeric" })}</span>;
}

// ── AI Remediation panel ──────────────────────────────────────────────────────
function AiRemediationPanel({ suggestion, onClose }: { suggestion: RemediationSuggestion; onClose: () => void }) {
  const priorityColors = {
    critical: "bg-red-100 text-red-700",
    high:     "bg-orange-100 text-orange-700",
    medium:   "bg-amber-100 text-amber-700",
    low:      "bg-gray-100 text-gray-600",
  };
  return (
    <div className="mt-3 rounded-xl border border-brand-100 bg-brand-50/40 p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-3.5 h-3.5 text-brand-600 shrink-0" />
          <span className="text-xs font-semibold text-brand-700">AI Remediation Plan</span>
          <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${priorityColors[suggestion.priority]}`}>
            {suggestion.priority}
          </span>
          <span className="text-[10px] text-gray-500">· suggested SLA: {suggestion.suggested_sla_days}d</span>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-0.5"><X className="w-3.5 h-3.5"/></button>
      </div>

      <ol className="space-y-2.5 mb-3">
        {suggestion.steps.map((s) => (
          <li key={s.step} className="flex gap-2.5">
            <span className="w-5 h-5 rounded-full bg-brand-600 text-white text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">{s.step}</span>
            <div>
              <p className="text-xs font-semibold text-gray-800">{s.action}</p>
              <p className="text-[11px] text-gray-500 leading-relaxed">{s.detail}</p>
            </div>
          </li>
        ))}
      </ol>

      {suggestion.missing_integrations.length > 0 && (
        <div className="flex items-start gap-2 bg-white rounded-lg border border-amber-200 px-3 py-2">
          <Zap className="w-3 h-3 text-amber-500 shrink-0 mt-0.5"/>
          <p className="text-[11px] text-amber-700">
            <strong>Connect to automate:</strong> {suggestion.missing_integrations.join(", ")}
          </p>
        </div>
      )}
    </div>
  );
}

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
  const [editingDue, setEditingDue] = useState(false);
  const [dueValue, setDueValue] = useState(control.due_date ?? "");
  const [savingDue, setSavingDue] = useState(false);
  const [remediation, setRemediation] = useState<RemediationSuggestion | null>(null);
  const [loadingRemediation, setLoadingRemediation] = useState(false);

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

  const saveDueDate = async () => {
    setSavingDue(true);
    try {
      const updated = await api.setControlDueDate(control.control_id, framework, dueValue || null);
      onUpdate(updated);
      setEditingDue(false);
    } catch { /* ignore */ } finally { setSavingDue(false); }
  };

  const handleGetRemediation = async () => {
    if (remediation) { setRemediation(null); return; }
    setLoadingRemediation(true);
    try {
      const result = await api.getControlRemediation(control.control_id, framework);
      setRemediation(result);
    } catch { /* ignore */ } finally { setLoadingRemediation(false); }
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
          <SlaBadge due_date={control.due_date} />
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

          {/* Due date / SLA */}
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            <CalendarDays className="w-3.5 h-3.5 text-gray-400 shrink-0" />
            <span className="text-xs text-gray-500 font-medium">SLA due date:</span>
            {!editingDue ? (
              <>
                {control.due_date
                  ? <span className="text-xs text-gray-700">{new Date(control.due_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}</span>
                  : <span className="text-xs text-gray-400 italic">Not set</span>
                }
                <SlaBadge due_date={control.due_date} />
                <button onClick={() => setEditingDue(true)} className="text-xs text-brand-600 hover:text-brand-700 font-semibold">
                  {control.due_date ? "Change" : "Set"}
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <input
                  type="date"
                  value={dueValue}
                  onChange={(e) => setDueValue(e.target.value)}
                  min={new Date().toISOString().slice(0, 10)}
                  className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-500/25"
                />
                <button onClick={saveDueDate} disabled={savingDue}
                  className="text-xs font-semibold text-white bg-brand-600 hover:bg-brand-700 px-2.5 py-1 rounded-lg disabled:opacity-50">
                  {savingDue ? "…" : "Save"}
                </button>
                {control.due_date && (
                  <button onClick={async () => { setDueValue(""); setSavingDue(true); try { const u = await api.setControlDueDate(control.control_id, framework, null); onUpdate(u); setEditingDue(false); } finally { setSavingDue(false); } }}
                    className="text-xs text-red-500 hover:text-red-700">Clear</button>
                )}
                <button onClick={() => { setEditingDue(false); setDueValue(control.due_date ?? ""); }} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
              </div>
            )}
          </div>

          {/* AI Fix */}
          {control.status !== "compliant" && (
            <div className="mt-3">
              <button
                onClick={handleGetRemediation}
                disabled={loadingRemediation}
                className="flex items-center gap-1.5 text-xs font-semibold text-brand-600 bg-brand-50 hover:bg-brand-100 border border-brand-100 px-3 py-1.5 rounded-xl transition-colors disabled:opacity-50"
              >
                {loadingRemediation
                  ? <><Loader2 className="w-3.5 h-3.5 animate-spin"/> Analysing…</>
                  : remediation
                  ? <><X className="w-3.5 h-3.5"/> Hide AI plan</>
                  : <><Sparkles className="w-3.5 h-3.5"/> AI Fix</>
                }
              </button>
              {remediation && <AiRemediationPanel suggestion={remediation} onClose={() => setRemediation(null)} />}
            </div>
          )}

          <ControlDocuments controlId={control.control_id} framework={framework} />
        </div>
      )}
    </div>
  );
}

// ── Exception / Exclusion modals ─────────────────────────────────────────────
function RiskExceptionModal({ control, framework, onClose, onSaved }: {
  control: ControlScore; framework: string; onClose: () => void; onSaved: () => void;
}) {
  const [form, setForm] = useState({ justification: "", owner_name: "", owner_email: "", expires_at: "" });
  const [saving, setSaving] = useState(false);
  const handleSave = async () => {
    if (!form.justification) return;
    setSaving(true);
    try {
      await api.createException({
        framework,
        control_category: control.category,
        control_name: control.name,
        justification: form.justification,
        owner_name: form.owner_name || undefined,
        owner_email: form.owner_email || undefined,
        expires_at: form.expires_at ? new Date(form.expires_at).toISOString() : undefined,
      });
      onSaved();
      onClose();
    } catch { } finally { setSaving(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Accept Risk</h3>
            <p className="text-xs text-gray-400 mt-0.5">{control.name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Justification *</label>
          <textarea value={form.justification} onChange={e => setForm(f => ({ ...f, justification: e.target.value }))} rows={3} placeholder="Explain why this risk is being accepted and what compensating controls exist…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30 resize-none" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Owner name</label>
            <input value={form.owner_name} onChange={e => setForm(f => ({ ...f, owner_name: e.target.value }))} placeholder="Jane Smith" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Owner email</label>
            <input value={form.owner_email} onChange={e => setForm(f => ({ ...f, owner_email: e.target.value }))} placeholder="jane@company.com" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30" />
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Exception expiry</label>
          <input type="date" value={form.expires_at} onChange={e => setForm(f => ({ ...f, expires_at: e.target.value }))} min={new Date().toISOString().slice(0, 10)} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/30" />
        </div>
        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving || !form.justification} className="flex-1 bg-amber-500 text-white rounded-xl py-2 text-sm font-semibold hover:bg-amber-600 disabled:opacity-50">{saving ? "Saving…" : "Accept risk"}</button>
        </div>
      </div>
    </div>
  );
}

function ControlExclusionModal({ control, framework, onClose, onSaved }: {
  control: ControlScore; framework: string; onClose: () => void; onSaved: () => void;
}) {
  const [justification, setJustification] = useState("");
  const [exclusionType, setExclusionType] = useState("not_applicable");
  const [saving, setSaving] = useState(false);
  const handleSave = async () => {
    if (!justification) return;
    setSaving(true);
    try {
      await api.createExclusion({ framework, control_category: control.category, control_name: control.name, justification, exclusion_type: exclusionType });
      onSaved();
      onClose();
    } catch { } finally { setSaving(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="font-bold text-gray-900">Mark as Not Applicable</h3>
            <p className="text-xs text-gray-400 mt-0.5">{control.name}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1.5">Exclusion type</label>
          <div className="flex gap-2">
            {[["not_applicable", "Not applicable"], ["out_of_scope", "Out of scope"]].map(([val, label]) => (
              <button key={val} onClick={() => setExclusionType(val)} className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${exclusionType === val ? "bg-gray-800 text-white border-gray-800" : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"}`}>{label}</button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-1">Justification *</label>
          <textarea value={justification} onChange={e => setJustification(e.target.value)} rows={3} placeholder="Explain why this control does not apply to your environment…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-500/30 resize-none" />
        </div>
        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving || !justification} className="flex-1 bg-gray-700 text-white rounded-xl py-2 text-sm font-semibold hover:bg-gray-800 disabled:opacity-50">{saving ? "Saving…" : "Mark N/A"}</button>
        </div>
      </div>
    </div>
  );
}

// ── Automated control row ─────────────────────────────────────────────────────
function AutoControlRow({ control, framework, onRefresh }: { control: ControlScore; framework: string; onRefresh: () => void }) {
  const isGood     = control.status === "passing";
  const isWarn     = control.status === "warning";
  const isBad      = control.status === "failing";
  const noData     = control.status === "no_evidence";
  const isExcept   = (control as any).status === "exception";
  const isExcluded = (control as any).status === "excluded";

  // Failing + warning start expanded so users immediately see what needs fixing
  const [expanded, setExpanded] = useState(isBad || isWarn);
  const [showException, setShowException]   = useState(false);
  const [showExclusion, setShowExclusion]   = useState(false);
  const [removingException, setRemovingException] = useState(false);
  const [removingExclusion, setRemovingExclusion] = useState(false);

  const handleRemoveException = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const exc = (control as any).exception;
    if (!exc?.id) return;
    setRemovingException(true);
    try { await api.deleteException(exc.id); onRefresh(); } catch { } finally { setRemovingException(false); }
  };

  const handleRemoveExclusion = async (e: React.MouseEvent) => {
    e.stopPropagation();
    const excl = (control as any).exclusion;
    if (!excl?.id) return;
    setRemovingExclusion(true);
    try { await api.deleteExclusion(excl.id); onRefresh(); } catch { } finally { setRemovingExclusion(false); }
  };

  const borderColor = isGood ? "border-l-emerald-300" : isWarn ? "border-l-amber-400" : isBad ? "border-l-red-400" : isExcept ? "border-l-amber-300" : isExcluded ? "border-l-gray-200" : "border-l-gray-200";
  const bgColor     = isGood ? "" : isWarn ? "bg-amber-50/40" : isBad ? "bg-red-50/20" : isExcept ? "bg-amber-50/20" : isExcluded ? "bg-gray-50/40" : "";
  const iconBg      = isGood ? "bg-emerald-50" : isWarn ? "bg-amber-50" : isBad ? "bg-red-50" : isExcept ? "bg-amber-50" : "bg-gray-50";
  const dotColor    = isGood ? "bg-emerald-400" : isWarn ? "bg-amber-400" : isBad ? "bg-red-400" : isExcept ? "bg-amber-300" : "bg-gray-200";

  return (
    <div className={`bg-white rounded-2xl border border-gray-100 border-l-4 ${borderColor} shadow-sm overflow-hidden ${bgColor}`}>
      <div
        className="flex items-center gap-3 px-4 sm:px-5 py-3 cursor-pointer select-none"
        onClick={() => setExpanded((v) => !v)}
      >
        <div className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 ${iconBg}`}>
          <div className={`w-2 h-2 rounded-full ${dotColor}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-sm font-semibold leading-snug ${isGood || isExcluded ? "text-gray-500" : "text-gray-900"}`}>
              {control.name}
            </span>
            <AutoBadge status={control.status} />
          </div>
          {!isGood && !isExcluded && (
            <div className="mt-1.5 h-1 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${scoreBarColor(control.score)}`}
                style={{ width: `${control.score}%` }}
              />
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {control.last_collected && (() => {
            const daysOld = Math.floor((Date.now() - new Date(control.last_collected).getTime()) / 86_400_000);
            if (daysOld > 30) return (
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-600 border border-amber-200">
                Stale {daysOld}d
              </span>
            );
            return null;
          })()}
          {!isExcluded && (
            <span className={`font-bold ${isGood ? "text-xs text-emerald-600" : "text-sm " + scoreColor(control.score)}`}>
              {control.score}%
            </span>
          )}
          {expanded
            ? <ChevronUp className="w-4 h-4 text-gray-300" />
            : <ChevronDown className="w-4 h-4 text-gray-300" />}
        </div>
      </div>

      {expanded && (
        <div className={`border-t px-4 sm:px-5 pb-4 pt-3 ${
          isWarn ? "border-amber-100/60 bg-amber-50/30" :
          isBad  ? "border-red-100/60 bg-red-50/20" :
          isExcept ? "border-amber-100/60 bg-amber-50/20" :
          "border-gray-50 bg-gray-50/30"
        }`}>
          {isExcluded ? (
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-0.5">Exclusion reason</p>
                <p className="text-xs text-gray-400">{(control as any).exclusion?.justification || "No justification provided"}</p>
                <p className="text-xs text-gray-300 mt-1 capitalize">{(control as any).exclusion?.exclusion_type?.replace(/_/g, " ")}</p>
              </div>
              <button
                onClick={handleRemoveExclusion}
                disabled={removingExclusion}
                className="shrink-0 text-xs text-red-400 hover:text-red-600 font-medium disabled:opacity-50"
              >
                {removingExclusion ? "Removing…" : "Remove exclusion"}
              </button>
            </div>
          ) : isExcept ? (
            <>
              <div className="flex items-start justify-between gap-3 mb-3">
                <div>
                  <p className="text-xs font-semibold text-amber-700 mb-0.5">Risk accepted</p>
                  <p className="text-xs text-gray-500">{(control as any).exception?.justification || "No justification provided"}</p>
                  {(control as any).exception?.owner_name && (
                    <p className="text-xs text-gray-400 mt-0.5">Owner: {(control as any).exception.owner_name}</p>
                  )}
                  {(control as any).exception?.expires_at && (
                    <p className="text-xs text-gray-400">Expires: {new Date((control as any).exception.expires_at).toLocaleDateString()}</p>
                  )}
                </div>
                <button
                  onClick={handleRemoveException}
                  disabled={removingException}
                  className="shrink-0 text-xs text-red-400 hover:text-red-600 font-medium disabled:opacity-50"
                >
                  {removingException ? "Removing…" : "Remove exception"}
                </button>
              </div>
              <EvidenceDots covered={control.covered_types} missing={control.missing_types} />
            </>
          ) : (
            <>
              <EvidenceDots covered={control.covered_types} missing={control.missing_types} />
              {!isGood && (
                <RemediationPanel missingTypes={control.missing_types} category={control.category} />
              )}
              <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-100/80">
                {isBad && (
                  <button
                    onClick={(e) => { e.stopPropagation(); setShowException(true); }}
                    className="flex items-center gap-1.5 text-xs font-medium text-amber-700 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2.5 py-1.5 rounded-lg transition-colors"
                  >
                    <ShieldAlert className="w-3 h-3" /> Accept risk
                  </button>
                )}
                <button
                  onClick={(e) => { e.stopPropagation(); setShowExclusion(true); }}
                  className="flex items-center gap-1.5 text-xs font-medium text-gray-500 bg-gray-50 hover:bg-gray-100 border border-gray-200 px-2.5 py-1.5 rounded-lg transition-colors"
                >
                  <Ban className="w-3 h-3" /> Mark N/A
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {showException && (
        <RiskExceptionModal
          control={control}
          framework={framework}
          onClose={() => setShowException(false)}
          onSaved={() => { setShowException(false); onRefresh(); }}
        />
      )}
      {showExclusion && (
        <ControlExclusionModal
          control={control}
          framework={framework}
          onClose={() => setShowExclusion(false)}
          onSaved={() => { setShowExclusion(false); onRefresh(); }}
        />
      )}
    </div>
  );
}

// ── AI Advisor Chat ────────────────────────────────────────────────────────────

// ── Invite Auditor Modal ──────────────────────────────────────────────────────
function InviteAuditorModal({
  framework,
  onClose,
  onCreated,
}: {
  framework: string;
  onClose: () => void;
  onCreated: (e: AuditEngagement) => void;
}) {
  const today = new Date().toISOString().slice(0, 10);
  const ninetyDaysAgo = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
  const [form, setForm] = useState({
    auditor_email: "",
    auditor_name: "",
    auditor_firm: "",
    obs_start: ninetyDaysAgo,
    obs_end: today,
    send_email: true,
  });
  const [saving, setSaving] = useState(false);
  const [err, setErr] = useState("");
  const [auditorFirms, setAuditorFirms] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    api.getPartnerDirectory("auditor").then((firms) => setAuditorFirms(firms.map((f) => ({ id: f.id, name: f.name })))).catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.auditor_email) return;
    setSaving(true);
    setErr("");
    try {
      const result = await api.createAuditEngagement({
        auditor_email: form.auditor_email,
        auditor_name: form.auditor_name || undefined,
        auditor_firm: form.auditor_firm || undefined,
        framework,
        obs_start: form.obs_start,
        obs_end: form.obs_end,
        send_email: form.send_email,
      });
      onCreated(result);
    } catch (ex: unknown) {
      setErr(ex instanceof Error ? ex.message : "Failed to create audit link");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-fade-in">
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Invite auditor</h2>
            <p className="text-sm text-gray-400 mt-0.5">Generate a read-only compliance link for your auditor</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {err && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {err}
            </div>
          )}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Auditor email <span className="text-red-400">*</span></label>
            <input type="email" required value={form.auditor_email}
              onChange={(e) => setForm((f) => ({ ...f, auditor_email: e.target.value }))}
              className="input" placeholder="auditor@firm.com" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Auditor name</label>
              <input type="text" value={form.auditor_name}
                onChange={(e) => setForm((f) => ({ ...f, auditor_name: e.target.value }))}
                className="input" placeholder="Jane Smith" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Firm</label>
              {auditorFirms.length > 0 ? (
                <select
                  value={form.auditor_firm}
                  onChange={(e) => setForm((f) => ({ ...f, auditor_firm: e.target.value }))}
                  className="input"
                >
                  <option value="">Select a firm…</option>
                  {auditorFirms.map((f) => (
                    <option key={f.id} value={f.name}>{f.name}</option>
                  ))}
                  <option value="__other__">Other (type manually)</option>
                </select>
              ) : (
                <input type="text" value={form.auditor_firm}
                  onChange={(e) => setForm((f) => ({ ...f, auditor_firm: e.target.value }))}
                  className="input" placeholder="Prescient Assurance" />
              )}
              {form.auditor_firm === "__other__" && (
                <input type="text" className="input mt-2" placeholder="Firm name"
                  onChange={(e) => setForm((f) => ({ ...f, auditor_firm: e.target.value }))} />
              )}
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Obs. period start</label>
              <input type="date" value={form.obs_start}
                onChange={(e) => setForm((f) => ({ ...f, obs_start: e.target.value }))}
                className="input" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Obs. period end</label>
              <input type="date" value={form.obs_end}
                onChange={(e) => setForm((f) => ({ ...f, obs_end: e.target.value }))}
                className="input" />
            </div>
          </div>
          <label className="flex items-center gap-2.5 cursor-pointer">
            <input type="checkbox" checked={form.send_email}
              onChange={(e) => setForm((f) => ({ ...f, send_email: e.target.checked }))}
              className="rounded border-gray-300 text-brand-500 focus:ring-brand-500" />
            <span className="text-sm text-gray-600">Send invitation email to auditor</span>
          </label>
          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="flex-1 btn-secondary justify-center py-2.5">Cancel</button>
            <button type="submit" disabled={saving || !form.auditor_email} className="flex-1 btn-primary justify-center py-2.5">
              {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating…</> : <><Send className="w-4 h-4" /> Create link</>}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function CompliancePage() {
  const { isPro } = usePlan();
  const { trigger: triggerUpgrade } = useUpgrade();
  const [framework, setFramework] = useState("soc2");
  const [score, setScore]         = useState<ComplianceScore | null>(null);
  const [manualControls, setManualControls] = useState<ManualControl[]>([]);
  const [members, setMembers]     = useState<Member[]>([]);
  const [loading, setLoading]     = useState(true);

  const [engagements, setEngagements]     = useState<AuditEngagement[]>([]);
  const [showInvite, setShowInvite]       = useState(false);
  const [copiedId, setCopiedId]           = useState<string | null>(null);
  const [chatEngagement, setChatEngagement] = useState<AuditEngagement | null>(null);
  const [comments, setComments]           = useState<AuditComment[]>([]);
  const [commentText, setCommentText]     = useState("");
  const [commentSending, setCommentSending] = useState(false);
  const commentScrollRef                  = useRef<HTMLDivElement>(null);

  const load = async (fw: string) => {
    setLoading(true);
    try {
      const [s, m] = await Promise.all([api.getComplianceScore(fw), api.getManualControls(fw)]);
      setScore(s);
      setManualControls(m);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => { load(framework); }, [framework]); // eslint-disable-line
  useEffect(() => { api.getMembers().then(setMembers).catch(() => {}); }, []);
  useEffect(() => { api.getAuditEngagements().then(setEngagements).catch(() => {}); }, []);

  const handleCopyLink = async (link: string, id: string) => {
    await navigator.clipboard.writeText(link);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleRevokeEngagement = async (id: string) => {
    await api.revokeAuditEngagement(id);
    setEngagements((prev) => prev.map((e) => e.id === id ? { ...e, status: "revoked" } : e));
  };

  const openChat = async (e: AuditEngagement) => {
    setChatEngagement(e);
    setComments([]);
    setCommentText("");
    try {
      const c = await api.getEngagementComments(e.id);
      setComments(c);
    } catch { /* ignore */ }
  };

  const sendComment = async () => {
    if (!chatEngagement || !commentText.trim()) return;
    setCommentSending(true);
    try {
      await api.addEngagementComment(chatEngagement.id, commentText.trim());
      setCommentText("");
      const c = await api.getEngagementComments(chatEngagement.id);
      setComments(c);
    } catch { /* ignore */ } finally { setCommentSending(false); }
  };

  // Auto-scroll comments to bottom
  useEffect(() => {
    if (commentScrollRef.current) {
      commentScrollRef.current.scrollTop = commentScrollRef.current.scrollHeight;
    }
  }, [comments]);

  const handleUpdate = (updated: ManualControl) =>
    setManualControls((prev) => prev.map((c) => (c.control_id === updated.control_id ? { ...c, ...updated } : c)));

  const manualCompliant = manualControls.filter((c) => c.status === "compliant").length;
  const manualTotal     = manualControls.filter((c) => c.status !== "not_applicable").length;

  // ── Action Plan state ──────────────────────────────────────────────────────
  const [actionPlan, setActionPlan] = useState<ActionPlan | null>(null);
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [planOpen, setPlanOpen] = useState(false);

  const handleGetActionPlan = async () => {
    if (actionPlan) { setPlanOpen((o) => !o); return; }
    setLoadingPlan(true);
    setPlanOpen(true);
    try {
      const plan = await api.getActionPlan(framework);
      setActionPlan(plan);
    } catch { /* ignore */ } finally { setLoadingPlan(false); }
  };

  // Reset plan when framework changes
  useEffect(() => { setActionPlan(null); setPlanOpen(false); }, [framework]);

  return (
    <div className="animate-fade-in">
      {/* Page header */}
      <div className="mb-5">
        <div className="flex items-center justify-between gap-4 mb-3">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 leading-none">Compliance</h1>
            <p className="text-xs text-gray-400 mt-1">
              {FRAMEWORKS.find((f) => f.value === framework)?.description ?? "Select a framework"}
            </p>
          </div>
        </div>

        {/* Framework tab strip */}
        <div className="flex gap-0 bg-gray-100 rounded-xl p-1 overflow-x-auto no-scrollbar">
          {FRAMEWORKS.map((f) => {
            const locked = !isPro && f.value !== "soc2";
            const active = framework === f.value;
            return (
              <button
                key={f.value}
                onClick={() => locked ? triggerUpgrade() : setFramework(f.value)}
                className={`shrink-0 flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-150 whitespace-nowrap ${
                  active
                    ? "bg-white text-gray-900 shadow-sm"
                    : locked
                    ? "text-amber-500 hover:text-amber-600"
                    : "text-gray-500 hover:text-gray-700"
                }`}
              >
                {locked && <Lock className="w-2.5 h-2.5 shrink-0" />}
                {f.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── AI Action Plan ── */}
      {!loading && (
        <div className="mb-5 bg-white border border-gray-100 shadow-card rounded-2xl overflow-hidden">
          <button
            onClick={handleGetActionPlan}
            className="w-full flex items-center justify-between px-5 py-3.5 hover:bg-gray-50/60 transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <Sparkles className="w-4 h-4 text-brand-600 shrink-0" />
              <span className="text-sm font-semibold text-gray-800">AI Action Plan</span>
              <span className="text-xs text-gray-400">— top gaps and exactly what to do</span>
            </div>
            <div className="flex items-center gap-2">
              {actionPlan && <span className="text-xs text-gray-400">{actionPlan.items.length} actions</span>}
              {loadingPlan
                ? <Loader2 className="w-4 h-4 text-brand-500 animate-spin" />
                : planOpen
                ? <ChevronUp className="w-4 h-4 text-gray-400" />
                : <ChevronDown className="w-4 h-4 text-gray-400" />
              }
            </div>
          </button>

          {planOpen && (
            <div className="border-t border-gray-50 px-5 pb-5">
              {loadingPlan && !actionPlan && (
                <div className="flex items-center gap-3 py-6 justify-center text-gray-400">
                  <Loader2 className="w-5 h-5 animate-spin text-brand-500" />
                  <span className="text-sm">Analysing your compliance posture…</span>
                </div>
              )}
              {actionPlan && (
                <div className="mt-4 space-y-3">
                  {actionPlan.items.map((item) => {
                    const effortColor = item.effort === "quick" ? "bg-emerald-100 text-emerald-700" : item.effort === "medium" ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700";
                    const impactColor = item.impact === "high" ? "text-brand-600 font-bold" : item.impact === "medium" ? "text-amber-600" : "text-gray-400";
                    return (
                      <div key={item.rank} className="flex gap-3 bg-gray-50/60 border border-gray-100 rounded-xl p-3.5">
                        <span className="w-6 h-6 rounded-full bg-brand-600 text-white text-[11px] font-black flex items-center justify-center shrink-0 mt-0.5">{item.rank}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap mb-1">
                            <span className="text-sm font-semibold text-gray-800">{item.title}</span>
                            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${effortColor}`}>{item.effort}</span>
                            <span className={`text-[10px] font-semibold ${impactColor}`}>{item.impact} impact</span>
                          </div>
                          <p className="text-xs text-gray-500 mb-2">{item.description}</p>
                          <div className="flex items-start gap-1.5">
                            <ArrowRight className="w-3 h-3 text-brand-500 shrink-0 mt-0.5" />
                            <p className="text-xs font-medium text-brand-700">{item.suggested_action}</p>
                          </div>
                          {item.control_refs.length > 0 && (
                            <div className="flex gap-1 mt-2 flex-wrap">
                              {item.control_refs.map((ref) => (
                                <span key={ref} className="text-[10px] font-mono bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{ref}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                  <button
                    onClick={() => { setActionPlan(null); setLoadingPlan(true); setPlanOpen(true); api.getActionPlan(framework).then(setActionPlan).catch(() => {}).finally(() => setLoadingPlan(false)); }}
                    className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
                  >
                    <RefreshCw className="w-3 h-3" /> Regenerate
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {loading ? (
        <div className="space-y-4">
          <div className="h-28 bg-gray-100 rounded-2xl animate-pulse" />
          <div className="h-24 bg-gray-100 rounded-2xl animate-pulse" />
          <div className="space-y-2">
            {[0,1,2,3,4,5].map((i) => <div key={i} className="h-14 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
          <div className="space-y-2">
            {[0,1,2,3].map((i) => <div key={i} className="h-14 bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        </div>
      ) : (
        <div className="space-y-5">

          {/* Score overview */}
          {score && (() => {
            const fw = FRAMEWORKS.find((f) => f.value === framework);
            const cats = [
              { label: "Passing", status: "passing",     color: "text-emerald-400", bar: "bg-emerald-400", count: score.controls.filter((c) => c.status === "passing").length },
              { label: "Warning", status: "warning",     color: "text-amber-400",   bar: "bg-amber-400",   count: score.controls.filter((c) => c.status === "warning").length },
              { label: "Failing", status: "failing",     color: "text-red-400",     bar: "bg-red-400",     count: score.controls.filter((c) => c.status === "failing").length },
              { label: "No data", status: "no_evidence", color: "text-slate-500",   bar: "bg-slate-600",   count: score.controls.filter((c) => c.status === "no_evidence").length },
            ];
            const total = score.controls.length || 1;
            const scoreColor = score.overall_score >= 80 ? "text-emerald-400" : score.overall_score >= 50 ? "text-amber-400" : "text-red-400";
            const strokeColor = score.overall_score >= 80 ? "#10b981" : score.overall_score >= 50 ? "#f59e0b" : "#ef4444";
            return (
              <div className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-5 sm:p-6 overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(20,184,166,0.1),_transparent_55%)] pointer-events-none" />
                <div className="relative">
                  <div className="flex items-center gap-5 sm:gap-6">
                    {/* Score ring */}
                    <div className="relative shrink-0">
                      <svg viewBox="0 0 80 80" className="w-20 h-20">
                        <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="8" />
                        <circle cx="40" cy="40" r="34" fill="none" stroke={strokeColor} strokeWidth="8"
                          strokeDasharray={`${(2 * Math.PI * 34).toFixed(2)}`}
                          strokeDashoffset={`${(2 * Math.PI * 34 * (1 - score.overall_score / 100)).toFixed(2)}`}
                          strokeLinecap="round" transform="rotate(-90 40 40)"
                        />
                      </svg>
                      <div className="absolute inset-0 flex flex-col items-center justify-center">
                        <span className={`text-xl font-black leading-none ${scoreColor}`}>{score.overall_score}</span>
                        <span className="text-[10px] text-white/30 font-semibold">/ 100</span>
                      </div>
                    </div>

                    {/* Details */}
                    <div className="flex-1 min-w-0">
                      <p className="text-white font-bold text-base leading-none mb-0.5">{fw?.label} Compliance</p>
                      <p className="text-slate-400 text-xs mb-3">{fw?.description}</p>
                      <div className="flex gap-3 sm:gap-5 flex-wrap">
                        {cats.filter((c) => c.count > 0).map(({ label, count, color }) => (
                          <div key={label} className="flex items-center gap-1.5">
                            <span className={`text-sm font-bold ${color}`}>{count}</span>
                            <span className="text-slate-500 text-xs">{label}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Category breakdown bar */}
                  <div className="mt-4 pt-4 border-t border-white/8">
                    <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
                      {cats.filter((c) => c.count > 0).map(({ status, bar, count }) => (
                        <div key={status} className={`h-full ${bar} first:rounded-l-full last:rounded-r-full`} style={{ flex: count / total }} />
                      ))}
                    </div>
                    <div className="flex gap-3 sm:gap-4 mt-2 flex-wrap">
                      {cats.filter((c) => c.count > 0).map(({ label, bar, count }) => (
                        <div key={label} className="flex items-center gap-1">
                          <div className={`w-1.5 h-1.5 rounded-full ${bar}`} />
                          <span className="text-[10px] text-slate-500">{count} {label}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            );
          })()}

          {/* Audit-ready CTA — shown when score >= 75 */}
          {score && score.overall_score >= 75 && (
            <div className="flex items-center gap-4 bg-violet-50 border border-violet-200 rounded-2xl px-5 py-4">
              <div className="w-9 h-9 bg-violet-100 rounded-xl flex items-center justify-center shrink-0">
                <FileSearch className="w-4.5 h-4.5 text-violet-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900">You're audit-ready</p>
                <p className="text-xs text-gray-500 mt-0.5">Your score is {score.overall_score}/100. Invite your auditor to access your evidence — no account needed on their end.</p>
              </div>
              <button
                onClick={() => setShowInvite(true)}
                className="shrink-0 btn-primary text-xs py-1.5 px-3"
              >
                Invite auditor
              </button>
            </div>
          )}

          {/* Automated controls */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-brand-500 shrink-0" />
              <h2 className="font-semibold text-gray-800 text-sm">Automated controls</h2>
              {score && (() => {
                const needsAttention = score.controls.filter((c) => c.status !== "passing").length;
                return needsAttention > 0
                  ? <span className="ml-auto text-xs font-semibold text-amber-600 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">{needsAttention} need attention</span>
                  : <span className="ml-auto text-xs font-semibold text-emerald-600 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">All passing</span>;
              })()}
            </div>
            <div className="space-y-2">
              {score?.controls.map((c) => (
                <AutoControlRow key={c.category} control={c} framework={framework} onRefresh={() => load(framework)} />
              ))}
            </div>
          </section>

          {/* Manual controls */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-4 h-4 text-brand-500 shrink-0" />
              <h2 className="font-semibold text-gray-800 text-sm">Manual controls</h2>
              <div className="ml-auto flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-500 font-medium">{manualCompliant} / {manualTotal} compliant</span>
                <div className="h-1.5 w-24 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${manualTotal > 0 ? (manualCompliant / manualTotal) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
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

          {/* Audit access links */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <LinkIcon className="w-4 h-4 text-brand-500 shrink-0" />
              <h2 className="font-semibold text-gray-800 text-sm">Audit access links</h2>
              <button
                onClick={() => setShowInvite(true)}
                className="ml-auto btn-secondary text-xs py-1 px-3"
              >
                + Invite auditor
              </button>
            </div>
            {engagements.filter((e) => e.status === "active").length === 0 ? (
              <div className="bg-gray-50 border border-gray-100 rounded-2xl px-5 py-4 flex items-center gap-3">
                <FileSearch className="w-4 h-4 text-gray-300 shrink-0" />
                <p className="text-sm text-gray-400">No active audit access links. Invite an auditor to give them a read-only view of your compliance evidence.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {engagements.filter((e) => e.status === "active").map((e) => (
                  <div key={e.id} className={`bg-white border rounded-2xl px-4 py-3 flex items-center gap-3 transition-colors ${chatEngagement?.id === e.id ? "border-brand-300 shadow-sm shadow-brand-100" : "border-gray-100"}`}>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {e.auditor_firm ? `${e.auditor_firm} — ` : ""}{e.auditor_email}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {e.obs_start} → {e.obs_end} · {e.framework.toUpperCase().replace("SOC2","SOC 2")}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => chatEngagement?.id === e.id ? setChatEngagement(null) : openChat(e)}
                        className={`inline-flex items-center gap-1.5 text-xs py-1 px-2.5 rounded-lg font-medium transition-colors ${chatEngagement?.id === e.id ? "bg-brand-600 text-white" : "btn-secondary"}`}
                        title="Auditor comments"
                      >
                        <MessageCircle className="w-3.5 h-3.5" />
                        Chat
                      </button>
                      <button
                        onClick={() => handleCopyLink(e.access_link, e.id)}
                        className="btn-secondary text-xs py-1 px-2.5"
                        title="Copy link"
                      >
                        {copiedId === e.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                      <button
                        onClick={() => handleRevokeEngagement(e.id)}
                        className="text-gray-400 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 transition-colors"
                        title="Revoke access"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Auditor comments panel */}
          {chatEngagement && (
            <section className="bg-white border border-gray-100 rounded-2xl overflow-hidden shadow-sm">
              <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
                <div>
                  <p className="text-sm font-semibold text-gray-900">
                    {chatEngagement.auditor_firm
                      ? `${chatEngagement.auditor_firm} — ${chatEngagement.auditor_email}`
                      : chatEngagement.auditor_email}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">External-facing conversation · visible to the auditor</p>
                </div>
                <button
                  onClick={() => setChatEngagement(null)}
                  className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div
                ref={commentScrollRef}
                className="h-72 overflow-y-auto px-5 py-4 space-y-4 bg-gray-50"
              >
                {comments.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center gap-2">
                    <MessageCircle className="w-8 h-8 text-gray-200" />
                    <p className="text-sm text-gray-400">No messages yet. Start the conversation with your auditor.</p>
                  </div>
                )}
                {comments.map((c) => (
                  <div key={c.id} className={`flex gap-3 ${c.author_role === "team" ? "flex-row-reverse" : ""}`}>
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${c.author_role === "auditor" ? "bg-amber-100 text-amber-700" : "bg-brand-100 text-brand-700"}`}>
                      {c.author_name.charAt(0).toUpperCase()}
                    </div>
                    <div className={`max-w-[75%] ${c.author_role === "team" ? "items-end" : "items-start"} flex flex-col gap-0.5`}>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-semibold text-gray-700">{c.author_name}</span>
                        {c.author_role === "auditor" && (
                          <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-100 text-amber-700">Auditor</span>
                        )}
                        <span className="text-[10px] text-gray-400">
                          {new Date(c.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                        </span>
                      </div>
                      <div className={`text-sm px-3 py-2 rounded-xl leading-relaxed ${c.author_role === "auditor" ? "bg-white border border-gray-100 text-gray-800" : "bg-brand-600 text-white"}`}>
                        {c.body}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex items-center gap-3 px-5 py-3 border-t border-gray-100 bg-white">
                <input
                  type="text"
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendComment(); } }}
                  placeholder="Reply to auditor…"
                  className="flex-1 text-sm bg-gray-50 border border-gray-200 rounded-xl px-3 py-2 outline-none focus:ring-2 focus:ring-brand-400/30 focus:border-brand-400 transition-colors"
                />
                <button
                  onClick={sendComment}
                  disabled={!commentText.trim() || commentSending}
                  className="w-9 h-9 rounded-xl bg-brand-600 hover:bg-brand-700 text-white flex items-center justify-center transition-colors disabled:opacity-40"
                >
                  {commentSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                </button>
              </div>
            </section>
          )}

        </div>
      )}

      {showInvite && (
        <InviteAuditorModal
          framework={framework}
          onClose={() => setShowInvite(false)}
          onCreated={(e) => {
            setEngagements((prev) => [e, ...prev]);
            setShowInvite(false);
          }}
        />
      )}
    </div>
  );
}
