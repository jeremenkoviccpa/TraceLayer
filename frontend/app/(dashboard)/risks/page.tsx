"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Member, Risk } from "@/lib/types";
import { AlertTriangle, Plus, Trash2, X, ChevronDown, ChevronUp, Sparkles, RefreshCw } from "lucide-react";
import { DocumentUpload } from "@/components/document-upload";

const CATEGORIES = ["Access Control", "Data Protection", "Availability", "Change Management", "Logging & Monitoring", "Incident Response", "Vendor Management", "Physical Security", "General"];
const STATUSES: Risk["status"][] = ["open", "mitigated", "accepted"];

function riskLevel(l: number, i: number): Risk["risk_level"] {
  const score = l * i;
  if (score >= 16) return "critical";
  if (score >= 9)  return "high";
  if (score >= 4)  return "medium";
  return "low";
}

const LEVEL_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
};

const LEVEL_BAR: Record<string, string> = {
  critical: "bg-red-500",
  high:     "bg-orange-500",
  medium:   "bg-amber-400",
  low:      "bg-emerald-500",
};

const STATUS_STYLES: Record<string, string> = {
  open:      "bg-red-50 text-red-600",
  mitigated: "bg-emerald-50 text-emerald-700",
  accepted:  "bg-gray-100 text-gray-500",
};

function RatingButton({ value, selected, onClick }: { value: number; selected: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${
        selected
          ? "bg-brand-600 text-white shadow-sm"
          : "bg-gray-100 text-gray-500 hover:bg-gray-200"
      }`}
    >
      {value}
    </button>
  );
}

const EMPTY: Partial<Risk> = {
  title: "",
  description: "",
  category: "General",
  likelihood: 3,
  impact: 3,
  status: "open",
  notes: "",
  owner_user_id: null,
};

export default function RisksPage() {
  const [risks, setRisks]         = useState<Risk[]>([]);
  const [members, setMembers]     = useState<Member[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Risk | null>(null);
  const [form, setForm]           = useState<Partial<Risk>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [sortCol, setSortCol]     = useState<"risk_level" | "status" | "category">("risk_level");
  const [sortAsc, setSortAsc]     = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [detectMsg, setDetectMsg] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getRisks(), api.getMembers()])
      .then(([r, m]) => { setRisks(r); setMembers(m); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (r: Risk) => { setEditing(r); setForm({ ...r }); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateRisk(editing.id, form);
        setRisks((prev) => prev.map((r) => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createRisk(form);
        setRisks((prev) => [created, ...prev]);
      }
      closeModal();
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    await api.deleteRisk(id).catch(() => {});
    setRisks((prev) => prev.filter((r) => r.id !== id));
  };

  const handleDetect = async () => {
    setDetecting(true);
    setDetectMsg(null);
    try {
      const result = await api.runRiskDetection();
      const fresh = await api.getRisks();
      setRisks(fresh);
      setDetectMsg(result.created > 0 ? `${result.created} new risk${result.created > 1 ? "s" : ""} detected` : "No new risks found");
    } catch {
      setDetectMsg("Detection failed");
    } finally {
      setDetecting(false);
      setTimeout(() => setDetectMsg(null), 4000);
    }
  };

  const toggleSort = (col: typeof sortCol) => {
    if (sortCol === col) setSortAsc((v) => !v);
    else { setSortCol(col); setSortAsc(true); }
  };

  const LEVEL_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };
  const sorted = [...risks].sort((a, b) => {
    let cmp = 0;
    if (sortCol === "risk_level") cmp = LEVEL_ORDER[a.risk_level] - LEVEL_ORDER[b.risk_level];
    else if (sortCol === "status") cmp = a.status.localeCompare(b.status);
    else cmp = a.category.localeCompare(b.category);
    return sortAsc ? cmp : -cmp;
  });

  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  risks.forEach((r) => { counts[r.risk_level]++; });
  const openCount      = risks.filter((r) => r.status === "open").length;
  const mitigatedCount = risks.filter((r) => r.status === "mitigated").length;

  const SortIcon = ({ col }: { col: typeof sortCol }) =>
    sortCol === col
      ? (sortAsc
          ? <ChevronUp className="w-3 h-3 inline ml-1" />
          : <ChevronDown className="w-3 h-3 inline ml-1" />)
      : null;

  return (
    <div className="animate-fade-in space-y-6 overflow-x-hidden">

      {/* ── Dark hero card ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        {/* subtle grid texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />

        <div className="relative flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          {/* Left: icon + copy + stats */}
          <div className="flex-1 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/20 ring-1 ring-brand-500/30">
                <AlertTriangle className="h-5 w-5 text-brand-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white leading-tight">Risk Register</h1>
                <p className="text-sm text-slate-400">Identify and manage your compliance risks.</p>
              </div>
            </div>

            {/* Stats row */}
            <div className="grid grid-cols-2 sm:flex sm:flex-wrap gap-3 sm:gap-4">
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Critical</span>
                <span className="text-2xl font-black text-red-400">{counts.critical}</span>
              </div>
              <div className="hidden sm:block w-px self-stretch bg-slate-700/60" />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">High</span>
                <span className="text-2xl font-black text-orange-400">{counts.high}</span>
              </div>
              <div className="hidden sm:block w-px self-stretch bg-slate-700/60" />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Open risks</span>
                <span className="text-2xl font-black text-amber-400">{openCount}</span>
              </div>
              <div className="hidden sm:block w-px self-stretch bg-slate-700/60" />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Mitigated</span>
                <span className="text-2xl font-black text-emerald-400">{mitigatedCount}</span>
              </div>
            </div>
          </div>

          {/* Right: action buttons */}
          <div className="flex shrink-0 items-start gap-2">
            {detectMsg && (
              <span className="self-center text-xs font-medium text-slate-300">{detectMsg}</span>
            )}
            <button
              onClick={handleDetect}
              disabled={detecting}
              className="flex items-center gap-2 rounded-xl bg-white/10 border border-white/20 px-4 py-2.5 text-sm font-semibold text-white transition-all hover:bg-white/20 active:scale-95 disabled:opacity-50"
            >
              {detecting ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="h-4 w-4" />
              )}
              Auto-detect
            </button>
            <button
              onClick={openCreate}
              className="flex items-center gap-2 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-brand-600/25 transition-all hover:bg-brand-500 hover:shadow-brand-500/30 active:scale-95"
            >
              <Plus className="h-4 w-4" />
              Add risk
            </button>
          </div>
        </div>
      </div>

      {/* ── Table / empty / loading ── */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
        </div>
      ) : sorted.length === 0 ? (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-gray-100 bg-white py-20 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50">
            <AlertTriangle className="h-7 w-7 text-brand-500" />
          </div>
          <p className="text-sm font-semibold text-gray-700">No risks recorded yet</p>
          <p className="mt-1 text-xs text-gray-400 max-w-xs">
            A risk register is required by SOC 2 (CC3) and ISO 27001. Log anything that could threaten your data security, availability, or compliance — we also auto-detect gaps like missing pen tests and stale vendor reviews.
          </p>
          <button
            onClick={openCreate}
            className="mt-5 flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-all hover:bg-brand-500 active:scale-95"
          >
            <Plus className="h-4 w-4" /> Add risk
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-card">
          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[640px]">
            <thead className="border-b border-gray-100 bg-gray-50/80">
              <tr>
                <th className="py-3 pl-5 pr-4 text-left text-xs font-semibold text-gray-500">Risk</th>
                <th
                  className="hidden cursor-pointer px-4 py-3 text-left text-xs font-semibold text-gray-500 transition-colors hover:text-gray-800 sm:table-cell"
                  onClick={() => toggleSort("category")}
                >
                  Category <SortIcon col="category" />
                </th>
                <th
                  className="cursor-pointer px-4 py-3 text-left text-xs font-semibold text-gray-500 transition-colors hover:text-gray-800"
                  onClick={() => toggleSort("risk_level")}
                >
                  Level <SortIcon col="risk_level" />
                </th>
                <th
                  className="hidden cursor-pointer px-4 py-3 text-left text-xs font-semibold text-gray-500 transition-colors hover:text-gray-800 md:table-cell"
                  onClick={() => toggleSort("status")}
                >
                  Status <SortIcon col="status" />
                </th>
                <th className="hidden px-4 py-3 text-left text-xs font-semibold text-gray-500 lg:table-cell">Owner</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sorted.map((r) => (
                <tr
                  key={r.id}
                  className="group cursor-pointer transition-colors hover:bg-gray-50/60"
                  onClick={() => openEdit(r)}
                >
                  {/* Colored level bar + title */}
                  <td className="py-3.5 pl-0 pr-4">
                    <div className="flex items-stretch gap-3">
                      <div className={`w-1 shrink-0 self-stretch rounded-r-full ${LEVEL_BAR[r.risk_level]}`} />
                      <div className="min-w-0 pl-1">
                        <div className="flex items-center gap-2">
                          <p className="font-medium leading-snug text-gray-800">{r.title}</p>
                          {r.auto_detected && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-600 border border-violet-100">
                              <Sparkles className="h-2.5 w-2.5" />
                              Auto
                            </span>
                          )}
                        </div>
                        {r.description && (
                          <p className="mt-0.5 line-clamp-1 text-xs text-gray-400">{r.description}</p>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="hidden px-4 py-3.5 sm:table-cell">
                    <span className="text-xs text-gray-500">{r.category}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${LEVEL_STYLES[r.risk_level]}`}
                    >
                      {r.risk_level}
                    </span>
                  </td>
                  <td className="hidden px-4 py-3.5 md:table-cell">
                    <span
                      className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold capitalize ${STATUS_STYLES[r.status]}`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="hidden px-4 py-3.5 lg:table-cell">
                    <span className="text-xs text-gray-400">{r.owner_name ?? "Unassigned"}</span>
                  </td>
                  <td
                    className="px-4 py-3.5 text-right"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {deletingId === r.id ? (
                      <div className="flex items-center gap-1 justify-end">
                        <button onClick={() => setDeletingId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">Cancel</button>
                        <button onClick={() => { handleDelete(r.id); setDeletingId(null); }} className="text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg">Delete</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeletingId(r.id)}
                        className="rounded-lg p-1.5 text-gray-300 transition-colors hover:bg-red-50 hover:text-red-500"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {/* ── Modal ── */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-lg overflow-hidden rounded-2xl bg-white shadow-2xl">

            {/* Modal header */}
            <div className="flex items-center justify-between border-b border-gray-100 px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-50">
                  <AlertTriangle className="h-4 w-4 text-brand-500" />
                </div>
                <h2 className="font-bold text-gray-900">{editing ? "Edit risk" : "Add risk"}</h2>
              </div>
              <button
                onClick={closeModal}
                className="rounded-lg p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Modal body */}
            <div className="max-h-[calc(90vh-8rem)] overflow-y-auto px-4 sm:px-6 py-4 sm:py-5 space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-600">Title *</label>
                <input
                  type="text"
                  value={form.title ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
                  placeholder="e.g. Shared admin credentials in AWS"
                />
              </div>

              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-600">Description</label>
                <textarea
                  value={form.description ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-gray-600">Category</label>
                  <select
                    value={form.category ?? "General"}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-gray-600">Status</label>
                  <select
                    value={form.status ?? "open"}
                    onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Risk["status"] }))}
                    className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    {STATUSES.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="mb-2 block text-xs font-medium text-gray-600">Likelihood (1–5)</label>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <RatingButton
                        key={v}
                        value={v}
                        selected={form.likelihood === v}
                        onClick={() => setForm((f) => ({ ...f, likelihood: v }))}
                      />
                    ))}
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-xs font-medium text-gray-600">Impact (1–5)</label>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <RatingButton
                        key={v}
                        value={v}
                        selected={form.impact === v}
                        onClick={() => setForm((f) => ({ ...f, impact: v }))}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {form.likelihood && form.impact && (
                <div className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-2.5">
                  <span className="text-xs text-gray-500">Risk level:</span>
                  <span
                    className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${LEVEL_STYLES[riskLevel(form.likelihood, form.impact)]}`}
                  >
                    {riskLevel(form.likelihood, form.impact)}
                  </span>
                  <span className="ml-1 text-xs text-gray-400">
                    ({form.likelihood} × {form.impact} = {form.likelihood * form.impact})
                  </span>
                </div>
              )}

              {members.length > 0 && (
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-gray-600">Owner</label>
                  <select
                    value={form.owner_user_id ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, owner_user_id: e.target.value || null }))}
                    className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => <option key={m.id} value={m.id}>{m.email}</option>)}
                  </select>
                </div>
              )}

              <div>
                <label className="mb-1.5 block text-xs font-medium text-gray-600">Notes / Mitigation plan</label>
                <textarea
                  value={form.notes ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={2}
                  className="w-full resize-none rounded-xl border border-gray-200 px-3 py-2.5 text-sm transition-shadow focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  placeholder="Describe the mitigation plan or acceptance rationale…"
                />
              </div>
              {editing && (
                <DocumentUpload resourceType="risk" resourceId={editing.id} />
              )}
            </div>

            {/* Modal footer */}
            <div className="flex justify-end gap-2 border-t border-gray-100 px-6 py-4">
              <button
                onClick={closeModal}
                className="rounded-xl border border-gray-200 px-4 py-2 text-sm text-gray-500 transition-colors hover:bg-gray-50 hover:text-gray-700"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.title}
                className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm shadow-brand-600/20 transition-all hover:bg-brand-500 disabled:opacity-40"
              >
                {saving ? "Saving…" : editing ? "Save changes" : "Add risk"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
