"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DataBreach } from "@/lib/types";
import {
  ShieldX, Plus, Trash2, X, ChevronDown, ChevronUp, Bell,
  AlertOctagon, Timer, CheckCircle2, Circle, ChevronRight, Clock,
} from "lucide-react";

/* ─── Style maps ─────────────────────────────────────────────────────────── */

const SEV_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
};

const SEV_STRIPE: Record<string, string> = {
  critical: "bg-red-500",
  high:     "bg-orange-500",
  medium:   "bg-amber-400",
  low:      "bg-emerald-500",
};

const STATUS_STYLES: Record<string, string> = {
  investigating: "bg-amber-100 text-amber-700",
  contained:     "bg-blue-100 text-blue-700",
  resolved:      "bg-emerald-100 text-emerald-700",
  closed:        "bg-gray-100 text-gray-500",
};

const BREACH_TYPE_STYLES: Record<string, string> = {
  confidentiality: "bg-red-50 text-red-600",
  integrity:       "bg-orange-50 text-orange-600",
  availability:    "bg-blue-50 text-blue-600",
};

/* ─── Empty form state ───────────────────────────────────────────────────── */

const EMPTY: Partial<DataBreach> = {
  title: "", breach_type: "confidentiality", severity: "medium", status: "investigating",
  notification_required: false, description: "", affected_systems: "",
  root_cause: "", remediation: "", reporter_name: "",
};

/* ─── Helpers ────────────────────────────────────────────────────────────── */

function fmt(dt?: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString();
}

function hoursElapsed(discoveredAt: string): number {
  return Math.floor((Date.now() - new Date(discoveredAt).getTime()) / 3600000);
}

function gdprCountdownColor(hours: number): { badge: string; bar: string } {
  if (hours > 72) return { badge: "bg-red-100 text-red-700", bar: "bg-red-500" };
  if (hours > 48) return { badge: "bg-amber-100 text-amber-700", bar: "bg-amber-400" };
  return { badge: "bg-emerald-100 text-emerald-700", bar: "bg-emerald-500" };
}

/* ─── Sub-components ─────────────────────────────────────────────────────── */

function TimelineDot({ done, label }: { done: boolean; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1">
      {done
        ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
        : <Circle className="w-3.5 h-3.5 text-gray-300 shrink-0" />}
      <span className={`text-[9px] leading-tight text-center ${done ? "text-emerald-600 font-medium" : "text-gray-400"}`}>{label}</span>
    </div>
  );
}

function TimelineRow({ b }: { b: DataBreach }) {
  const steps = [
    { done: !!b.occurred_at,           label: "Occurred" },
    { done: !!b.discovered_at,         label: "Discovered" },
    { done: !!b.dpa_notified_at,       label: "DPA Notified" },
    { done: !!b.individuals_notified_at, label: "Individuals" },
    { done: b.status === "resolved" || b.status === "closed", label: "Resolved" },
  ];

  return (
    <div className="flex items-start gap-1 mt-3">
      {steps.map((s, i) => (
        <div key={i} className="flex items-center gap-1 flex-1 min-w-0">
          <TimelineDot done={s.done} label={s.label} />
          {i < steps.length - 1 && (
            <ChevronRight className="w-3 h-3 text-gray-200 shrink-0 mb-3" />
          )}
        </div>
      ))}
    </div>
  );
}

/* ─── Page ───────────────────────────────────────────────────────────────── */

export default function DataBreachesPage() {
  const [breaches, setBreaches]     = useState<DataBreach[]>([]);
  const [loading, setLoading]       = useState(true);
  const [showModal, setShowModal]   = useState(false);
  const [editing, setEditing]       = useState<DataBreach | null>(null);
  const [form, setForm]             = useState<Partial<DataBreach>>(EMPTY);
  const [saving, setSaving]         = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    api.getDataBreaches().then(setBreaches).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (b: DataBreach) => { setEditing(b); setForm(b); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateDataBreach(editing.id, form);
        setBreaches((prev) => prev.map((b) => b.id === updated.id ? updated : b));
      } else {
        const created = await api.createDataBreach(form);
        setBreaches((prev) => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this breach record?")) return;
    await api.deleteDataBreach(id);
    setBreaches((prev) => prev.filter((b) => b.id !== id));
  };

  const handleQuickStatus = async (id: string, status: string) => {
    const updated = await api.updateDataBreach(id, { status });
    setBreaches((prev) => prev.map((b) => b.id === updated.id ? updated : b));
  };

  const sf = (key: keyof DataBreach) => ({
    value: (form[key] as string) ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  /* ─ Derived stats ─ */
  const activeBreaches   = breaches.filter((b) => b.status === "investigating" || b.status === "contained");
  const resolved         = breaches.filter((b) => b.status === "resolved" || b.status === "closed").length;
  const overdueBreaches  = breaches.filter((b) =>
    b.notification_required &&
    !b.dpa_notified_at &&
    b.discovered_at &&
    hoursElapsed(b.discovered_at) > 72
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-5">

      {/* ── Alert Banner ── */}
      {overdueBreaches.length > 0 && (
        <div className="flex items-center gap-3 bg-red-600 text-white text-sm font-medium px-4 py-3 rounded-2xl shadow-sm">
          <AlertOctagon className="w-4 h-4 shrink-0" />
          <span>
            ⚠ {overdueBreaches.length} breach{overdueBreaches.length > 1 ? "es" : ""} past GDPR 72-hour DPA notification deadline
          </span>
        </div>
      )}

      {/* ── Header ── */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <ShieldX className="w-5 h-5 text-red-500 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Data Breach Register</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">GDPR Art. 33–34 · HIPAA breach tracking</p>
          </div>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-1.5 bg-brand-600 text-white text-xs font-semibold px-3 py-2 rounded-xl hover:bg-brand-700 transition-colors shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Log Breach</span>
          <span className="sm:hidden">Log</span>
        </button>
      </div>

      {/* ── Stats Row ── */}
      <div className="grid grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{breaches.length}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Total</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{activeBreaches.length}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Active</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-red-600">{overdueBreaches.length}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1 leading-tight">Notif. Overdue</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-emerald-600">{resolved}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Resolved</p>
        </div>
      </div>

      {/* ── Cards ── */}
      {breaches.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20 px-6">
          <ShieldX className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm font-medium text-gray-500 mb-1">No breaches recorded</p>
          <p className="text-xs text-gray-400 max-w-sm mx-auto mb-5">
            Under GDPR Art. 33 you must notify your DPA within 72 hours of discovering a personal data breach.
          </p>
          <button
            onClick={openCreate}
            className="text-sm font-semibold text-brand-600 hover:text-brand-700"
          >
            Log first breach →
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {breaches.map((b) => {
            const needsCountdown =
              b.notification_required && b.discovered_at && !b.dpa_notified_at;
            const hours = needsCountdown ? hoursElapsed(b.discovered_at!) : 0;
            const colors = needsCountdown ? gdprCountdownColor(hours) : null;
            const barPct = needsCountdown ? Math.min((hours / 72) * 100, 100) : 0;
            const isExpanded = expandedId === b.id;

            return (
              <div key={b.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                {/* Colored severity stripe + main content */}
                <div className="flex">
                  {/* Left stripe */}
                  <div className={`w-1 shrink-0 ${SEV_STRIPE[b.severity] ?? "bg-gray-300"}`} />

                  <div className="flex-1 min-w-0">
                    {/* Card header row */}
                    <div className="px-4 pt-4 pb-3 flex items-start gap-3">
                      <div className="flex-1 min-w-0">
                        {/* Title + badges */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-gray-900 text-sm">{b.title}</h3>
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${SEV_STYLES[b.severity] ?? "bg-gray-100 text-gray-500"}`}>
                            {b.severity}
                          </span>
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[b.status] ?? "bg-gray-100 text-gray-500"}`}>
                            {b.status}
                          </span>
                          <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${BREACH_TYPE_STYLES[b.breach_type] ?? "bg-gray-100 text-gray-500"}`}>
                            {b.breach_type}
                          </span>
                          {b.affected_records != null && (
                            <span className="inline-flex items-center gap-1 text-xs font-semibold text-gray-600 bg-gray-50 px-2 py-0.5 rounded-full border border-gray-100">
                              {b.affected_records.toLocaleString()} records
                            </span>
                          )}
                        </div>

                        {/* 72h countdown badge */}
                        {needsCountdown && colors && (
                          <div className="mt-2 flex items-center gap-2">
                            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${colors.badge}`}>
                              <Timer className="w-3 h-3" />
                              {hours}h / 72h elapsed
                              {hours > 72 && " — OVERDUE"}
                            </span>
                          </div>
                        )}

                        {/* 72h progress bar */}
                        {needsCountdown && colors && (
                          <div className="mt-2 w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all ${colors.bar}`}
                              style={{ width: `${barPct}%` }}
                            />
                          </div>
                        )}

                        {/* Timeline */}
                        <TimelineRow b={b} />

                        {/* Quick status buttons */}
                        <div className="flex items-center gap-2 mt-3 flex-wrap">
                          {b.status === "investigating" && (
                            <button
                              onClick={() => handleQuickStatus(b.id, "contained")}
                              className="inline-flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              Mark Contained
                            </button>
                          )}
                          {(b.status === "investigating" || b.status === "contained") && (
                            <button
                              onClick={() => handleQuickStatus(b.id, "resolved")}
                              className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 hover:bg-emerald-100 px-2.5 py-1 rounded-lg transition-colors"
                            >
                              <CheckCircle2 className="w-3 h-3" />
                              Mark Resolved
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Action buttons */}
                      <div className="flex items-center gap-1 shrink-0 mt-0.5">
                        <button
                          onClick={() => openEdit(b)}
                          className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDelete(b.id)}
                          className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setExpandedId(isExpanded ? null : b.id)}
                          className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"
                        >
                          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>

                    {/* Expanded section */}
                    {isExpanded && (
                      <div className="px-4 pb-4 pt-0 border-t border-gray-50 space-y-3 mt-1">
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3">
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5 flex items-center gap-1">
                              <Clock className="w-2.5 h-2.5" /> Occurred
                            </p>
                            <p className="text-xs text-gray-700">{fmt(b.occurred_at)}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5 flex items-center gap-1">
                              <Clock className="w-2.5 h-2.5" /> Discovered
                            </p>
                            <p className="text-xs text-gray-700">{fmt(b.discovered_at)}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5 flex items-center gap-1">
                              <Bell className="w-2.5 h-2.5" /> DPA Notified
                            </p>
                            <p className="text-xs text-gray-700">{fmt(b.dpa_notified_at)}</p>
                          </div>
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5 flex items-center gap-1">
                              <Bell className="w-2.5 h-2.5" /> Individuals
                            </p>
                            <p className="text-xs text-gray-700">{fmt(b.individuals_notified_at)}</p>
                          </div>
                        </div>

                        {b.affected_systems && (
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5">Affected Systems</p>
                            <p className="text-xs text-gray-700">{b.affected_systems}</p>
                          </div>
                        )}

                        {b.description && (
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5">Description</p>
                            <p className="text-xs text-gray-700 whitespace-pre-wrap">{b.description}</p>
                          </div>
                        )}

                        {b.root_cause && (
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5">Root Cause</p>
                            <p className="text-xs text-gray-700 whitespace-pre-wrap">{b.root_cause}</p>
                          </div>
                        )}

                        {b.remediation && (
                          <div>
                            <p className="text-[10px] text-gray-400 mb-0.5">Remediation</p>
                            <p className="text-xs text-gray-700 whitespace-pre-wrap">{b.remediation}</p>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div className="flex items-center gap-2">
                <ShieldX className="w-4 h-4 text-red-500" />
                <h2 className="font-semibold text-gray-900">{editing ? "Edit Breach" : "Log Data Breach"}</h2>
              </div>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="p-6 space-y-6">

              {/* Section: Reporter Info */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Reporter Info</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 sm:col-span-1">
                    <label className="text-xs font-medium text-gray-500 block mb-1">Reporter Name</label>
                    <input
                      {...sf("reporter_name")}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                      placeholder="Full name"
                    />
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-100" />

              {/* Section: Incident Details */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Incident Details</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-gray-500 block mb-1">Title *</label>
                    <input
                      {...sf("title")}
                      required
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                      placeholder="Brief description of the breach"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Breach Type</label>
                    <select {...sf("breach_type")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                      <option value="confidentiality">Confidentiality</option>
                      <option value="integrity">Integrity</option>
                      <option value="availability">Availability</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Severity</label>
                    <select {...sf("severity")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Status</label>
                    <select {...sf("status")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                      <option value="investigating">Investigating</option>
                      <option value="contained">Contained</option>
                      <option value="resolved">Resolved</option>
                      <option value="closed">Closed</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Affected Records</label>
                    <input
                      type="number"
                      value={form.affected_records ?? ""}
                      onChange={(e) => setForm((f) => ({ ...f, affected_records: e.target.value ? Number(e.target.value) : null }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                      placeholder="0"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Occurred At</label>
                    <input
                      type="datetime-local"
                      value={form.occurred_at ? new Date(form.occurred_at).toISOString().slice(0, 16) : ""}
                      onChange={(e) => setForm((f) => ({ ...f, occurred_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Discovered At</label>
                    <input
                      type="datetime-local"
                      value={form.discovered_at ? new Date(form.discovered_at).toISOString().slice(0, 16) : ""}
                      onChange={(e) => setForm((f) => ({ ...f, discovered_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-gray-500 block mb-1">Affected Systems</label>
                    <input
                      {...sf("affected_systems")}
                      className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                      placeholder="e.g. User database, Payment service"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="text-xs font-medium text-gray-500 block mb-1">Description</label>
                    <textarea {...sf("description")} rows={3} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Root Cause</label>
                    <textarea {...sf("root_cause")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-500 block mb-1">Remediation</label>
                    <textarea {...sf("remediation")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-100" />

              {/* Section: Notifications */}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Notifications</p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2 flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="notif"
                      checked={!!form.notification_required}
                      onChange={(e) => setForm((f) => ({ ...f, notification_required: e.target.checked }))}
                      className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    />
                    <label htmlFor="notif" className="text-sm text-gray-700">
                      Notification required (DPA / individuals)
                    </label>
                  </div>
                  {form.notification_required && (
                    <>
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1">DPA Notified At</label>
                        <input
                          type="datetime-local"
                          value={form.dpa_notified_at ? new Date(form.dpa_notified_at).toISOString().slice(0, 16) : ""}
                          onChange={(e) => setForm((f) => ({ ...f, dpa_notified_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-500 block mb-1">Individuals Notified At</label>
                        <input
                          type="datetime-local"
                          value={form.individuals_notified_at ? new Date(form.individuals_notified_at).toISOString().slice(0, 16) : ""}
                          onChange={(e) => setForm((f) => ({ ...f, individuals_notified_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex justify-end gap-2 pt-2 border-t border-gray-100">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-60 transition-colors">
                  {saving ? "Saving…" : editing ? "Save Changes" : "Log Breach"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
