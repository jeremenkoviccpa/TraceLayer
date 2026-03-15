"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PenTest } from "@/lib/types";
import { ShieldAlert, Plus, Trash2, X, ChevronDown, ChevronUp, AlertTriangle } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-emerald-50 text-emerald-700",
  remediated: "bg-teal-50 text-teal-700",
};

const STATUS_LABELS: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
  completed: "Completed",
  remediated: "Remediated",
};

const STATUSES = ["scheduled", "in_progress", "completed", "remediated"];

function Modal({
  onClose,
  onSave,
  initial,
}: {
  onClose: () => void;
  onSave: (data: Partial<PenTest>) => Promise<void>;
  initial?: PenTest;
}) {
  const [form, setForm] = useState({
    vendor_name: initial?.vendor_name ?? "",
    status: initial?.status ?? "scheduled",
    scope: initial?.scope ?? "",
    conducted_at: initial?.conducted_at ? initial.conducted_at.slice(0, 10) : "",
    next_scheduled_at: initial?.next_scheduled_at ? initial.next_scheduled_at.slice(0, 10) : "",
    critical_count: initial?.critical_count ?? 0,
    high_count: initial?.high_count ?? 0,
    medium_count: initial?.medium_count ?? 0,
    low_count: initial?.low_count ?? 0,
    summary: initial?.summary ?? "",
    remediation_notes: initial?.remediation_notes ?? "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.vendor_name) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        scope: form.scope || null,
        conducted_at: form.conducted_at || null,
        next_scheduled_at: form.next_scheduled_at || null,
        summary: form.summary || null,
        remediation_notes: form.remediation_notes || null,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <h2 className="font-bold text-gray-900">{initial ? "Edit Pen Test" : "Add Pen Test"}</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Vendor / firm name *</label>
              <input
                value={form.vendor_name}
                onChange={(e) => setForm((p) => ({ ...p, vendor_name: e.target.value }))}
                placeholder="e.g. Cobalt.io"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((p) => ({ ...p, status: e.target.value as PenTest["status"] }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {STATUSES.map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Conducted date</label>
              <input type="date" value={form.conducted_at} onChange={(e) => setForm((p) => ({ ...p, conducted_at: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Next scheduled</label>
              <input type="date" value={form.next_scheduled_at} onChange={(e) => setForm((p) => ({ ...p, next_scheduled_at: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Scope</label>
            <textarea value={form.scope} onChange={(e) => setForm((p) => ({ ...p, scope: e.target.value }))} rows={2} placeholder="e.g. External network, web application, API endpoints…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">Findings by severity</label>
            <div className="grid grid-cols-4 gap-2">
              {(["critical", "high", "medium", "low"] as const).map((sev) => (
                <div key={sev}>
                  <label className="block text-[10px] font-semibold uppercase text-gray-400 mb-1">{sev}</label>
                  <input
                    type="number"
                    min={0}
                    value={form[`${sev}_count` as keyof typeof form] as number}
                    onChange={(e) => setForm((p) => ({ ...p, [`${sev}_count`]: parseInt(e.target.value) || 0 }))}
                    className="w-full border border-gray-200 rounded-xl px-2 py-1.5 text-sm text-center focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  />
                </div>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Executive summary</label>
            <textarea value={form.summary} onChange={(e) => setForm((p) => ({ ...p, summary: e.target.value }))} rows={3} placeholder="High-level findings summary…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Remediation notes</label>
            <textarea value={form.remediation_notes} onChange={(e) => setForm((p) => ({ ...p, remediation_notes: e.target.value }))} rows={2} placeholder="Steps taken to remediate findings…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-xl">Cancel</button>
          <button onClick={handleSubmit} disabled={saving || !form.vendor_name} className="px-4 py-2 text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-40">
            {saving ? "Saving…" : initial ? "Update" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function PenTestsPage() {
  const [tests, setTests] = useState<PenTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<PenTest | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    api.getPenTests().then(setTests).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (data: Partial<PenTest>) => {
    const pt = await api.createPenTest(data);
    setTests((prev) => [pt, ...prev]);
  };

  const handleUpdate = async (data: Partial<PenTest>) => {
    if (!editing) return;
    const pt = await api.updatePenTest(editing.id, data);
    setTests((prev) => prev.map((t) => t.id === editing.id ? pt : t));
    setEditing(null);
  };

  const handleDelete = async (id: string) => {
    await api.deletePenTest(id);
    setTests((prev) => prev.filter((t) => t.id !== id));
  };

  const totalFindings = tests.reduce((acc, t) => acc + t.critical_count + t.high_count + t.medium_count + t.low_count, 0);

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pen Test Tracker</h1>
          <p className="text-sm text-gray-500 mt-0.5">Track penetration test engagements and finding remediation.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-semibold px-4 py-2 rounded-xl text-sm"
        >
          <Plus className="w-4 h-4" /> Add pen test
        </button>
      </div>

      {tests.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Tests tracked", value: tests.length, color: "text-gray-900" },
            { label: "Critical findings", value: tests.reduce((a, t) => a + t.critical_count, 0), color: "text-red-600" },
            { label: "High findings", value: tests.reduce((a, t) => a + t.high_count, 0), color: "text-orange-600" },
            { label: "Total findings", value: totalFindings, color: "text-gray-700" },
          ].map(({ label, value, color }) => (
            <div key={label} className="bg-white rounded-2xl border border-gray-100 shadow-card p-4">
              <p className="text-xs text-gray-400 mb-1">{label}</p>
              <p className={`text-2xl font-bold ${color}`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : tests.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <ShieldAlert className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-600 mb-1">No pen tests tracked yet</p>
          <p className="text-xs text-gray-400 mb-4">Log your penetration tests to demonstrate annual testing for SOC 2.</p>
          <button onClick={() => setShowModal(true)} className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-xl text-sm">
            <Plus className="w-4 h-4" /> Add first pen test
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {tests.map((t) => (
            <div key={t.id} className="bg-white rounded-2xl border border-gray-100 shadow-card overflow-hidden">
              <div className="px-5 py-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="font-semibold text-gray-900">{t.vendor_name}</span>
                    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[t.status]}`}>
                      {STATUS_LABELS[t.status]}
                    </span>
                    {t.conducted_at && (
                      <span className="text-xs text-gray-400">Conducted {new Date(t.conducted_at).toLocaleDateString()}</span>
                    )}
                  </div>
                  {/* Finding badges */}
                  <div className="flex items-center gap-2 mt-2">
                    {t.critical_count > 0 && <span className="text-[10px] font-bold bg-red-50 text-red-700 px-2 py-0.5 rounded-full">C: {t.critical_count}</span>}
                    {t.high_count > 0 && <span className="text-[10px] font-bold bg-orange-50 text-orange-700 px-2 py-0.5 rounded-full">H: {t.high_count}</span>}
                    {t.medium_count > 0 && <span className="text-[10px] font-bold bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full">M: {t.medium_count}</span>}
                    {t.low_count > 0 && <span className="text-[10px] font-bold bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">L: {t.low_count}</span>}
                    {t.critical_count === 0 && t.high_count === 0 && t.medium_count === 0 && t.low_count === 0 && (
                      <span className="text-[10px] text-gray-400">No findings logged</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => setEditing(t)} className="text-xs font-semibold text-gray-500 hover:text-gray-700 border border-gray-200 px-2.5 py-1 rounded-lg">Edit</button>
                  <button onClick={() => handleDelete(t.id)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 className="w-4 h-4" /></button>
                  <button onClick={() => setExpanded(expanded === t.id ? null : t.id)} className="text-gray-400 hover:text-gray-600 p-1">
                    {expanded === t.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {expanded === t.id && (
                <div className="border-t border-gray-100 px-5 py-4 bg-gray-50/50 space-y-3">
                  {t.scope && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Scope</p><p className="text-sm text-gray-700">{t.scope}</p></div>}
                  {t.summary && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Summary</p><p className="text-sm text-gray-700">{t.summary}</p></div>}
                  {t.remediation_notes && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Remediation</p><p className="text-sm text-gray-700">{t.remediation_notes}</p></div>}
                  {t.next_scheduled_at && <p className="text-xs text-gray-400">Next test scheduled: {new Date(t.next_scheduled_at).toLocaleDateString()}</p>}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {showModal && <Modal onClose={() => setShowModal(false)} onSave={handleCreate} />}
      {editing && <Modal onClose={() => setEditing(null)} onSave={handleUpdate} initial={editing} />}
    </div>
  );
}
