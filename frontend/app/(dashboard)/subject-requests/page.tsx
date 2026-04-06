"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import type { SubjectRequest } from "@/lib/types";
import {
  UserSearch,
  Plus,
  Trash2,
  X,
  AlertTriangle,
  Clock,
  CheckCircle2,
  ChevronDown,
  Timer,
  Calendar,
} from "lucide-react";

// ─── Constants ───────────────────────────────────────────────────────────────

const STATUSES = ["pending", "in_progress", "completed", "refused", "extended"] as const;
const REQUEST_TYPES = ["access", "deletion", "rectification", "portability", "objection", "restriction", "nomination", "grievance"] as const;
const REGULATIONS = ["gdpr", "ccpa", "dpdp", "lpdp", "other"] as const;

const SLA_DAYS: Record<string, number> = {
  gdpr: 30,
  ccpa: 45,
  dpdp: 30,
  lpdp: 30,
  other: 30,
};

// DPDP-specific request types (Sec. 11-14)
const DPDP_TYPE_LABELS: Record<string, string> = {
  access:        "Access (Sec. 11)",
  deletion:      "Erasure (Sec. 12)",
  rectification: "Correction (Sec. 12)",
  nomination:    "Nomination (Sec. 14)",
  grievance:     "Grievance (Sec. 13)",
};

// LPDP-specific request types (Art. 26-39)
const LPDP_TYPE_LABELS: Record<string, string> = {
  access:        "Access (Art. 26)",
  deletion:      "Erasure (Art. 30)",
  rectification: "Rectification (Art. 29)",
  portability:   "Portability (Art. 36)",
  objection:     "Objection (Art. 37)",
  restriction:   "Restriction (Art. 31)",
};

// ─── Style maps ──────────────────────────────────────────────────────────────

const TYPE_STYLES: Record<string, string> = {
  access:        "bg-blue-100 text-blue-700",
  deletion:      "bg-red-100 text-red-700",
  rectification: "bg-amber-100 text-amber-700",
  portability:   "bg-blue-50 text-blue-600",
  objection:     "bg-gray-100 text-gray-600",
  restriction:   "bg-gray-100 text-gray-600",
  nomination:    "bg-violet-100 text-violet-700",
  grievance:     "bg-orange-100 text-orange-700",
};

const STATUS_STYLES: Record<string, string> = {
  pending:     "bg-gray-100 text-gray-500",
  in_progress: "bg-amber-100 text-amber-700",
  completed:   "bg-emerald-100 text-emerald-700",
  refused:     "bg-red-100 text-red-700",
  extended:    "bg-blue-100 text-blue-700",
};

const REG_STYLES: Record<string, string> = {
  gdpr:  "bg-purple-100 text-purple-700",
  ccpa:  "bg-blue-100 text-blue-700",
  dpdp:  "bg-orange-100 text-orange-700",
  lpdp:  "bg-blue-100 text-blue-700",
  other: "bg-gray-100 text-gray-500",
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

const EMPTY: Partial<SubjectRequest> = {
  requester_name: "",
  requester_email: "",
  request_type: "access",
  received_at: new Date().toISOString(),
  regulation: "gdpr",
  status: "pending",
};

function fmt(dt?: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString();
}

function getDueDate(req: SubjectRequest): Date {
  if (req.due_at) return new Date(req.due_at);
  const d = new Date(req.received_at);
  d.setDate(d.getDate() + (SLA_DAYS[req.regulation] ?? 30));
  return d;
}

function getDaysRemaining(req: SubjectRequest): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const due = getDueDate(req);
  due.setHours(0, 0, 0, 0);
  return Math.round((due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
}

function getDaysElapsed(req: SubjectRequest): number {
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  const received = new Date(req.received_at);
  received.setHours(0, 0, 0, 0);
  return Math.round((now.getTime() - received.getTime()) / (1000 * 60 * 60 * 24));
}

function isActive(req: SubjectRequest): boolean {
  return req.status !== "completed" && req.status !== "refused";
}

function isOverdue(req: SubjectRequest): boolean {
  if (!isActive(req)) return false;
  return getDaysRemaining(req) < 0;
}

function getStripeColor(req: SubjectRequest): string {
  if (!isActive(req)) return "bg-gray-300";
  const days = getDaysRemaining(req);
  if (days < 0) return "bg-red-500";
  if (days <= 7) return "bg-amber-400";
  return "bg-emerald-500";
}

function getBarColor(req: SubjectRequest): string {
  if (!isActive(req)) return "bg-gray-300";
  const days = getDaysRemaining(req);
  const slaDays = SLA_DAYS[req.regulation] ?? 30;
  const elapsed = getDaysElapsed(req);
  const pct = (elapsed / slaDays) * 100;
  if (days < 0) return "bg-red-500";
  if (pct > 80) return "bg-amber-400";
  return "bg-emerald-500";
}

function getBarWidth(req: SubjectRequest): string {
  const slaDays = SLA_DAYS[req.regulation] ?? 30;
  const elapsed = getDaysElapsed(req);
  const pct = Math.min((elapsed / slaDays) * 100, 100);
  return `${pct}%`;
}

function nextStatus(current: string): string {
  const idx = STATUSES.indexOf(current as typeof STATUSES[number]);
  if (idx === -1) return "pending";
  return STATUSES[(idx + 1) % STATUSES.length];
}

// ─── Status dropdown component ────────────────────────────────────────────────

function StatusDropdown({
  req,
  onStatusChange,
}: {
  req: SubjectRequest;
  onStatusChange: (id: string, status: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [open]);

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-opacity hover:opacity-80 ${STATUS_STYLES[req.status] ?? "bg-gray-100 text-gray-500"}`}
      >
        {req.status.replace("_", " ")}
        <ChevronDown className="w-3 h-3" />
      </button>
      {open && (
        <div className="absolute z-20 top-full mt-1 left-0 bg-white border border-gray-100 rounded-xl shadow-lg py-1 min-w-[140px]">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => {
                onStatusChange(req.id, s);
                setOpen(false);
              }}
              className={`w-full text-left px-3 py-1.5 text-xs hover:bg-gray-50 transition-colors ${req.status === s ? "font-semibold" : ""}`}
            >
              <span className={`inline-flex px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[s] ?? "bg-gray-100 text-gray-500"}`}>
                {s.replace("_", " ")}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function SubjectRequestsPage() {
  const [requests, setRequests]   = useState<SubjectRequest[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<SubjectRequest | null>(null);
  const [form, setForm]           = useState<Partial<SubjectRequest>>(EMPTY);
  const [saving, setSaving]       = useState(false);

  useEffect(() => {
    api.getSubjectRequests().then(setRequests).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (r: SubjectRequest) => { setEditing(r); setForm(r); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateSubjectRequest(editing.id, form);
        setRequests((prev) => prev.map((r) => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createSubjectRequest(form);
        setRequests((prev) => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this request?")) return;
    await api.deleteSubjectRequest(id);
    setRequests((prev) => prev.filter((r) => r.id !== id));
  };

  const handleQuickStatus = async (id: string, newStatus: string) => {
    const updated = await api.updateSubjectRequest(id, { status: newStatus });
    setRequests((prev) => prev.map((r) => r.id === updated.id ? updated : r));
  };

  const sf = (key: keyof SubjectRequest) => ({
    value: (form[key] as string) ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  // ─── Stats ──────────────────────────────────────────────────────────────────
  const totalCount     = requests.length;
  const pendingCount   = requests.filter((r) => r.status === "pending" || r.status === "in_progress").length;
  const overdueCount   = requests.filter(isOverdue).length;
  const completedCount = requests.filter((r) => r.status === "completed").length;
  const activeCount    = requests.filter(isActive).length;
  const slaHealth      = activeCount === 0
    ? 100
    : Math.round(((activeCount - overdueCount) / activeCount) * 100);
  const slaHealthColor = slaHealth >= 90
    ? "text-emerald-600"
    : slaHealth >= 70
    ? "text-amber-600"
    : "text-red-600";

  // ─── Loading ─────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <UserSearch className="w-5 h-5 text-brand-600 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">
              Subject Access Requests
            </h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">
              GDPR Art. 15–22 · CCPA consumer rights
            </p>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 bg-brand-600 text-white text-xs font-semibold px-3 py-2 rounded-xl hover:bg-brand-700 transition-colors shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Request</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>

      {/* Overdue alert banner */}
      {overdueCount > 0 && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <p className="text-sm text-amber-800">
            <span className="font-semibold">{overdueCount} request{overdueCount !== 1 ? "s" : ""} past their response deadline.</span>
            {" "}GDPR/DPDP/LPDP: 30-day response deadline. CCPA: 45 days.
          </p>
        </div>
      )}

      {/* Stats row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{totalCount}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Total</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{pendingCount}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Active</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-red-600">{overdueCount}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Overdue</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className={`text-xl sm:text-2xl font-bold ${slaHealthColor}`}>{slaHealth}%</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">SLA Health</p>
        </div>
      </div>

      {/* Cards / Empty state */}
      {requests.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20 px-6">
          <UserSearch className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm font-medium text-gray-700 mb-1">No subject requests yet</p>
          <p className="text-xs text-gray-400 max-w-sm mx-auto mb-5">
            Under GDPR Art. 15–22 you must respond to access, deletion, rectification and portability
            requests within 30 days.
          </p>
          <button
            onClick={openCreate}
            className="text-sm font-semibold text-brand-600 hover:text-brand-700 transition-colors"
          >
            Log first request →
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {requests.map((r) => {
            const overdueMark   = isOverdue(r);
            const active        = isActive(r);
            const daysRemaining = getDaysRemaining(r);
            const slaDays       = SLA_DAYS[r.regulation] ?? 30;
            const stripeColor   = getStripeColor(r);
            const barColor      = getBarColor(r);
            const barWidth      = getBarWidth(r);
            const dueDate       = getDueDate(r);

            return (
              <div
                key={r.id}
                className="bg-white rounded-2xl border border-gray-100 overflow-hidden flex shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Left color stripe */}
                <div className={`w-1 shrink-0 ${stripeColor}`} />

                {/* Card body */}
                <div className="flex-1 p-4 min-w-0 space-y-3">

                  {/* Top row: name + actions */}
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="font-semibold text-gray-900 truncate leading-tight">{r.requester_name}</p>
                      {r.requester_email && (
                        <p className="text-xs text-gray-400 truncate">{r.requester_email}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={() => openEdit(r)}
                        className="text-xs text-brand-600 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(r.id)}
                        className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Badges row */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${TYPE_STYLES[r.request_type] ?? "bg-gray-100 text-gray-500"}`}
                    >
                      {r.regulation === "dpdp" && DPDP_TYPE_LABELS[r.request_type]
                        ? DPDP_TYPE_LABELS[r.request_type]
                        : r.request_type}
                    </span>
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium uppercase ${REG_STYLES[r.regulation] ?? "bg-gray-100 text-gray-500"}`}
                    >
                      {r.regulation === "dpdp" ? "DPDP Act" : r.regulation}
                    </span>
                    <StatusDropdown req={r} onStatusChange={handleQuickStatus} />
                  </div>

                  {/* SLA progress bar */}
                  {active && (
                    <div>
                      <div className="w-full h-1.5 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${barColor}`}
                          style={{ width: barWidth }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Days remaining + dates */}
                  <div className="flex items-end justify-between gap-2">
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {fmt(r.received_at)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Timer className="w-3 h-3" />
                        {fmt(dueDate.toISOString())}
                        {!r.due_at && <span className="text-[10px] text-gray-300">(calc.)</span>}
                      </span>
                    </div>

                    {active && (
                      <div className="shrink-0">
                        {overdueMark ? (
                          <span className="inline-flex items-center gap-1 bg-red-50 text-red-600 text-xs font-bold px-2 py-1 rounded-xl">
                            <Clock className="w-3 h-3" />
                            {Math.abs(daysRemaining)}d overdue
                          </span>
                        ) : daysRemaining <= 7 ? (
                          <span className="inline-flex items-center gap-1 bg-amber-50 text-amber-700 text-xs font-bold px-2 py-1 rounded-xl">
                            <Clock className="w-3 h-3" />
                            {daysRemaining}d left
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 text-xs font-bold px-2 py-1 rounded-xl">
                            <CheckCircle2 className="w-3 h-3" />
                            {daysRemaining}d left
                          </span>
                        )}
                      </div>
                    )}

                    {!active && (
                      <span className="inline-flex items-center gap-1 bg-gray-50 text-gray-400 text-xs font-medium px-2 py-1 rounded-xl">
                        <CheckCircle2 className="w-3 h-3" />
                        {r.status.replace("_", " ")}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">
                {editing ? "Edit Subject Request" : "New Subject Request"}
              </h2>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <form onSubmit={handleSave} className="p-6 space-y-4">

              {/* SLA note */}
              <p className="text-xs text-amber-600 bg-amber-50 p-3 rounded-xl">
                Response deadline: {SLA_DAYS[form.regulation] ?? 30} days (auto-calculated from received date).
              </p>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Requester Name *</label>
                  <input
                    {...sf("requester_name")}
                    required
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Requester Email</label>
                  <input
                    {...sf("requester_email")}
                    type="email"
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Request Type *</label>
                  <select
                    {...sf("request_type")}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <optgroup label="Universal">
                      {(["access", "deletion", "rectification", "portability", "objection", "restriction"] as const).map((t) => (
                        <option key={t} value={t} className="capitalize">{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                      ))}
                    </optgroup>
                    <optgroup label="DPDP Act (India)">
                      {(["nomination", "grievance"] as const).map((t) => (
                        <option key={t} value={t}>{DPDP_TYPE_LABELS[t] ?? t}</option>
                      ))}
                    </optgroup>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Regulation</label>
                  <select
                    {...sf("regulation")}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {REGULATIONS.map((reg) => (
                      <option key={reg} value={reg}>{reg === "dpdp" ? "DPDP Act (India)" : reg.toUpperCase()}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Received At *</label>
                  <input
                    type="date"
                    value={form.received_at ? new Date(form.received_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        received_at: e.target.value ? new Date(e.target.value).toISOString() : "",
                      }))
                    }
                    required
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Due Date (override)</label>
                  <input
                    type="date"
                    value={form.due_at ? new Date(form.due_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        due_at: e.target.value ? new Date(e.target.value).toISOString() : null,
                      }))
                    }
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Status</label>
                  <select
                    {...sf("status")}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>{s.replace("_", " ")}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Completed At</label>
                  <input
                    type="date"
                    value={form.completed_at ? new Date(form.completed_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) =>
                      setForm((f) => ({
                        ...f,
                        completed_at: e.target.value ? new Date(e.target.value).toISOString() : null,
                      }))
                    }
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Response Notes</label>
                  <textarea
                    {...sf("response_notes")}
                    rows={3}
                    className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-60 transition-colors"
                >
                  {saving ? "Saving…" : editing ? "Save Changes" : "Create Request"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
