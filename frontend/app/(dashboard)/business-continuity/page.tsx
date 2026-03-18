"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { BcpRecord } from "@/lib/types";
import { RefreshCw, Plus, Trash2, X, Clock } from "lucide-react";

const TYPES   = ["bcp", "drp", "both"] as const;
const STATUSES = ["not_tested", "scheduled", "tested", "passed", "failed"] as const;

const STATUS_STYLES: Record<string, string> = {
  not_tested: "bg-gray-100 text-gray-500",
  scheduled:  "bg-blue-50 text-blue-600",
  tested:     "bg-amber-50 text-amber-700",
  passed:     "bg-emerald-50 text-emerald-700",
  failed:     "bg-red-50 text-red-600",
};

const TYPE_LABELS: Record<string, string> = { bcp: "BCP", drp: "DRP", both: "BCP + DRP" };

const EMPTY: Partial<BcpRecord> = {
  title: "", record_type: "both", status: "not_tested", scope: "", notes: "",
};

function fmtMinutes(m: number | null | undefined): string {
  if (!m) return "—";
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem ? `${h}h ${rem}m` : `${h}h`;
}

export default function BusinessContinuityPage() {
  const [records, setRecords]     = useState<BcpRecord[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<BcpRecord | null>(null);
  const [form, setForm]           = useState<Partial<BcpRecord>>(EMPTY);
  const [saving, setSaving]       = useState(false);

  useEffect(() => {
    api.getBcpRecords().then(setRecords).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (r: BcpRecord) => { setEditing(r); setForm(r); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateBcpRecord(editing.id, form);
        setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createBcpRecord(form);
        setRecords(prev => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this record?")) return;
    await api.deleteBcpRecord(id);
    setRecords(prev => prev.filter(r => r.id !== id));
  };

  const isDue = (r: BcpRecord) => r.next_test_due && new Date(r.next_test_due) < new Date();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <RefreshCw className="w-6 h-6 text-brand-600" /> Business Continuity
          </h1>
          <p className="text-sm text-gray-500 mt-1">Track BCP/DRP plans, tests, and recovery objectives</p>
        </div>
        <button onClick={openCreate} className="btn-primary gap-2">
          <Plus className="w-4 h-4" /> Add Record
        </button>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {STATUSES.map(s => {
          const count = records.filter(r => r.status === s).length;
          return (
            <div key={s} className="bg-white rounded-xl border border-gray-100 p-4">
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[s]}`}>{s.replace("_", " ")}</span>
              <p className={`text-2xl font-bold mt-2 ${count > 0 ? "text-gray-900" : "text-gray-300"}`}>{count}</p>
            </div>
          );
        })}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : records.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <RefreshCw className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No BCP/DRP records</p>
          <p className="text-sm text-gray-400 mt-1">Document your business continuity and disaster recovery plans</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> Add Record</button>
        </div>
      ) : (
        <div className="space-y-3">
          {records.map(record => (
            <div key={record.id} className="bg-white rounded-xl border border-gray-100 p-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="inline-flex px-2 py-0.5 rounded-md text-xs font-bold bg-brand-50 text-brand-700">{TYPE_LABELS[record.record_type]}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[record.status]}`}>{record.status.replace("_", " ")}</span>
                    {isDue(record) && <span className="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700">⚠️ Test overdue</span>}
                  </div>
                  <p className="font-semibold text-gray-900">{record.title}</p>
                  {record.scope && <p className="text-sm text-gray-500 mt-1">{record.scope}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button onClick={() => openEdit(record)} className="btn-secondary text-xs py-1.5 px-3">Edit</button>
                  <button onClick={() => handleDelete(record.id)} className="text-red-400 hover:text-red-600 p-1.5 rounded hover:bg-red-50"><Trash2 className="w-4 h-4" /></button>
                </div>
              </div>
              <div className="flex items-center gap-6 mt-3 pt-3 border-t border-gray-50 flex-wrap">
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <Clock className="w-3.5 h-3.5 text-gray-400" />
                  <span>RTO: <strong className="text-gray-700">{fmtMinutes(record.rto_minutes)}</strong></span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-500">
                  <Clock className="w-3.5 h-3.5 text-gray-400" />
                  <span>RPO: <strong className="text-gray-700">{fmtMinutes(record.rpo_minutes)}</strong></span>
                </div>
                {record.last_tested_at && (
                  <div className="text-xs text-gray-500">Last tested: <strong className="text-gray-700">{new Date(record.last_tested_at).toLocaleDateString()}</strong></div>
                )}
                {record.next_test_due && (
                  <div className={`text-xs font-medium ${isDue(record) ? "text-red-600" : "text-gray-500"}`}>
                    Next test: <strong>{new Date(record.next_test_due).toLocaleDateString()}</strong>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit BCP/DRP Record" : "Add BCP/DRP Record"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
                <input className="input" value={form.title ?? ""} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required placeholder="e.g. Production Database Recovery Plan" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                  <select className="input" value={form.record_type ?? "both"} onChange={e => setForm(p => ({ ...p, record_type: e.target.value as BcpRecord["record_type"] }))}>
                    {TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t]}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                  <select className="input" value={form.status ?? "not_tested"} onChange={e => setForm(p => ({ ...p, status: e.target.value as BcpRecord["status"] }))}>
                    {STATUSES.map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">RTO (minutes)</label>
                  <input type="number" className="input" value={form.rto_minutes ?? ""} onChange={e => setForm(p => ({ ...p, rto_minutes: e.target.value ? Number(e.target.value) : null }))} placeholder="e.g. 240" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">RPO (minutes)</label>
                  <input type="number" className="input" value={form.rpo_minutes ?? ""} onChange={e => setForm(p => ({ ...p, rpo_minutes: e.target.value ? Number(e.target.value) : null }))} placeholder="e.g. 60" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Last tested</label>
                  <input type="date" className="input" value={form.last_tested_at ? form.last_tested_at.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, last_tested_at: e.target.value || null }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Next test due</label>
                  <input type="date" className="input" value={form.next_test_due ? form.next_test_due.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, next_test_due: e.target.value || null }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Scope</label>
                <textarea className="input min-h-[60px]" value={form.scope ?? ""} onChange={e => setForm(p => ({ ...p, scope: e.target.value }))} placeholder="What systems and processes does this cover?" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Test results / Notes</label>
                <textarea className="input min-h-[70px]" value={form.notes ?? ""} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Add record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
