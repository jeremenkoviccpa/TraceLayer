"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PenTest } from "@/lib/types";
import { ShieldAlert, Plus, Trash2, X, ChevronDown, ChevronUp, ExternalLink, Microscope } from "lucide-react";
import { DocumentUpload } from "@/components/document-upload";

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
  const [deletingId, setDeletingId] = useState<string | null>(null);

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
  const criticalFindings = tests.reduce((a, t) => a + t.critical_count, 0);
  const highFindings = tests.reduce((a, t) => a + t.high_count, 0);

  return (
    <div className="animate-fade-in overflow-x-hidden">

      {/* Dark hero card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6">
        {/* Row 1: icon + title + action */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center shrink-0">
              <ShieldAlert className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">Pen Test Tracker</h1>
              <p className="text-sm text-slate-400 mt-0.5">Track penetration test engagements and finding remediation.</p>
            </div>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors shrink-0"
          >
            <Plus className="w-4 h-4" /> Add pen test
          </button>
        </div>

        {/* Row 2: stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-3xl font-bold text-brand-400">{tests.length}</p>
            <p className="text-xs text-slate-400 mt-1">Tests tracked</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${criticalFindings > 0 ? "text-red-400" : "text-brand-400"}`}>{criticalFindings}</p>
            <p className="text-xs text-slate-400 mt-1">Critical findings</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${highFindings > 0 ? "text-orange-400" : "text-brand-400"}`}>{highFindings}</p>
            <p className="text-xs text-slate-400 mt-1">High findings</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-brand-400">{totalFindings}</p>
            <p className="text-xs text-slate-400 mt-1">Total findings</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : tests.length === 0 ? (
        <div className="space-y-4">
          <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-10 text-center">
            <ShieldAlert className="w-10 h-10 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-600 mb-1">No pen tests tracked yet</p>
            <p className="text-xs text-gray-400 mb-4">Log your penetration tests to demonstrate annual testing for SOC 2.</p>
            <button onClick={() => setShowModal(true)} className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-xl text-sm">
              <Plus className="w-4 h-4" /> Add first pen test
            </button>
          </div>
          {/* Partner CTA */}
          <div className="bg-orange-50 border border-orange-100 rounded-2xl p-5">
            <div className="flex items-center gap-2 mb-3">
              <Microscope className="w-4 h-4 text-orange-500" />
              <p className="text-sm font-semibold text-gray-900">Need a pen test? Use one of our vetted partners.</p>
            </div>
            <div className="grid sm:grid-cols-2 gap-2">
              {[
                { name: "Cobalt", note: "PtaaS — results in days", href: "https://cobalt.io" },
                { name: "NetSPI", note: "Enterprise-grade", href: "https://netspi.com" },
                { name: "Synack", note: "Crowdsourced red team", href: "https://synack.com" },
                { name: "Rapid7", note: "Full-service + vuln mgmt", href: "https://rapid7.com" },
              ].map(({ name, note, href }) => (
                <a key={name} href={href} target="_blank" rel="noopener noreferrer"
                  className="flex items-center justify-between bg-white border border-orange-100 rounded-xl px-3 py-2.5 hover:border-orange-200 transition-colors group"
                >
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{name}</p>
                    <p className="text-xs text-gray-400">{note}</p>
                  </div>
                  <ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-orange-400 transition-colors" />
                </a>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {tests.map((t) => (
            <div key={t.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-card">
              <div className="px-4 sm:px-5 py-3 sm:py-4 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
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
                <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap self-end sm:self-auto sm:shrink-0">
                  <button onClick={() => setEditing(t)} className="text-xs font-semibold text-gray-500 hover:text-gray-700 border border-gray-200 px-2.5 py-1 rounded-lg">Edit</button>
                  {deletingId === t.id ? (
                    <>
                      <button onClick={() => setDeletingId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">Cancel</button>
                      <button onClick={() => { handleDelete(t.id); setDeletingId(null); }} className="text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg">Delete</button>
                    </>
                  ) : (
                    <button onClick={() => setDeletingId(t.id)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 className="w-4 h-4" /></button>
                  )}
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
                  <DocumentUpload resourceType="pen_test" resourceId={t.id} />
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
