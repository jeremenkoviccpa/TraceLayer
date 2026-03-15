"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Member, Risk } from "@/lib/types";
import { AlertTriangle, Plus, Trash2, X, ChevronDown, ChevronUp } from "lucide-react";

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
      className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${selected ? "bg-brand-600 text-white shadow-sm" : "bg-gray-100 text-gray-500 hover:bg-gray-200"}`}
    >
      {value}
    </button>
  );
}

const EMPTY: Partial<Risk> = { title: "", description: "", category: "General", likelihood: 3, impact: 3, status: "open", notes: "", owner_user_id: null };

export default function RisksPage() {
  const [risks, setRisks]     = useState<Risk[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]    = useState<Risk | null>(null);
  const [form, setForm]          = useState<Partial<Risk>>(EMPTY);
  const [saving, setSaving]      = useState(false);
  const [sortCol, setSortCol]    = useState<"risk_level" | "status" | "category">("risk_level");
  const [sortAsc, setSortAsc]    = useState(false);

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

  const SortIcon = ({ col }: { col: typeof sortCol }) =>
    sortCol === col
      ? (sortAsc ? <ChevronUp className="w-3 h-3 inline ml-1" /> : <ChevronDown className="w-3 h-3 inline ml-1" />)
      : null;

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Risk Register</h1>
          <p className="text-sm text-gray-500 mt-0.5">Track, assess, and manage your compliance risks.</p>
        </div>
        <button onClick={openCreate} className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors">
          <Plus className="w-4 h-4" /> Add risk
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {(["critical", "high", "medium", "low"] as const).map((level) => (
          <div key={level} className="bg-white rounded-2xl border border-gray-100 shadow-card p-4">
            <p className="text-xs text-gray-400 capitalize mb-1">{level}</p>
            <p className={`text-2xl font-black ${level === "critical" ? "text-red-600" : level === "high" ? "text-orange-600" : level === "medium" ? "text-amber-600" : "text-emerald-600"}`}>
              {counts[level]}
            </p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : sorted.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-12 text-center">
          <AlertTriangle className="w-8 h-8 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-500">No risks recorded yet.</p>
          <p className="text-xs text-gray-400 mt-1">Add your first risk to start tracking your compliance posture.</p>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500">Risk</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 cursor-pointer hover:text-gray-800 hidden sm:table-cell" onClick={() => toggleSort("category")}>
                  Category <SortIcon col="category" />
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 cursor-pointer hover:text-gray-800" onClick={() => toggleSort("risk_level")}>
                  Level <SortIcon col="risk_level" />
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 cursor-pointer hover:text-gray-800 hidden md:table-cell" onClick={() => toggleSort("status")}>
                  Status <SortIcon col="status" />
                </th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 hidden lg:table-cell">Owner</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {sorted.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50/50 cursor-pointer" onClick={() => openEdit(r)}>
                  <td className="px-5 py-3.5">
                    <p className="font-medium text-gray-800 leading-snug">{r.title}</p>
                    {r.description && <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{r.description}</p>}
                  </td>
                  <td className="px-4 py-3.5 hidden sm:table-cell">
                    <span className="text-xs text-gray-500">{r.category}</span>
                  </td>
                  <td className="px-4 py-3.5">
                    <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${LEVEL_STYLES[r.risk_level]}`}>
                      {r.risk_level}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 hidden md:table-cell">
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize ${STATUS_STYLES[r.status]}`}>
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3.5 hidden lg:table-cell">
                    <span className="text-xs text-gray-400">{r.owner_name ?? "Unassigned"}</span>
                  </td>
                  <td className="px-4 py-3.5 text-right" onClick={(e) => e.stopPropagation()}>
                    <button onClick={() => handleDelete(r.id)} className="text-gray-300 hover:text-red-500 transition-colors p-1">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-bold text-gray-900">{editing ? "Edit risk" : "Add risk"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Title *</label>
                <input
                  type="text"
                  value={form.title ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
                  placeholder="e.g. Shared admin credentials in AWS"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Description</label>
                <textarea
                  value={form.description ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">Category</label>
                  <select
                    value={form.category ?? "General"}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">Status</label>
                  <select
                    value={form.status ?? "open"}
                    onChange={(e) => setForm((f) => ({ ...f, status: e.target.value as Risk["status"] }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    {STATUSES.map((s) => <option key={s} value={s} className="capitalize">{s}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">Likelihood (1–5)</label>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <RatingButton key={v} value={v} selected={form.likelihood === v} onClick={() => setForm((f) => ({ ...f, likelihood: v }))} />
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-2">Impact (1–5)</label>
                  <div className="flex gap-1.5">
                    {[1, 2, 3, 4, 5].map((v) => (
                      <RatingButton key={v} value={v} selected={form.impact === v} onClick={() => setForm((f) => ({ ...f, impact: v }))} />
                    ))}
                  </div>
                </div>
              </div>
              {form.likelihood && form.impact && (
                <div className="flex items-center gap-2 bg-gray-50 rounded-xl px-3 py-2">
                  <span className="text-xs text-gray-500">Risk level:</span>
                  <span className={`text-[10px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${LEVEL_STYLES[riskLevel(form.likelihood, form.impact)]}`}>
                    {riskLevel(form.likelihood, form.impact)}
                  </span>
                  <span className="text-xs text-gray-400 ml-1">({form.likelihood} × {form.impact} = {form.likelihood * form.impact})</span>
                </div>
              )}
              {members.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1.5">Owner</label>
                  <select
                    value={form.owner_user_id ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, owner_user_id: e.target.value || null }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  >
                    <option value="">Unassigned</option>
                    {members.map((m) => <option key={m.id} value={m.id}>{m.email}</option>)}
                  </select>
                </div>
              )}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Notes / Mitigation plan</label>
                <textarea
                  value={form.notes ?? ""}
                  onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
                  rows={2}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none"
                  placeholder="Describe the mitigation plan or acceptance rationale…"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-gray-100 flex justify-end gap-2">
              <button onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !form.title}
                className="px-4 py-2 text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-40 transition-colors"
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
