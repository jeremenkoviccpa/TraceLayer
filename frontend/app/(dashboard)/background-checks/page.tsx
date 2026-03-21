"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { BackgroundCheck } from "@/lib/types";
import { UserCheck, Plus, Trash2, X, Sparkles, RefreshCw } from "lucide-react";

const CHECK_TYPES = ["standard", "enhanced", "international"] as const;
const STATUSES    = ["pending", "in_progress", "completed", "failed", "expired"] as const;

const STATUS_STYLES: Record<string, string> = {
  pending:     "bg-gray-100 text-gray-500",
  in_progress: "bg-amber-50 text-amber-700",
  completed:   "bg-emerald-50 text-emerald-700",
  failed:      "bg-red-50 text-red-600",
  expired:     "bg-red-100 text-red-700",
};

const EMPTY: Partial<BackgroundCheck> = {
  employee_name: "", employee_email: "", check_type: "standard", status: "pending", vendor: "", notes: "",
};

export default function BackgroundChecksPage() {
  const [checks, setChecks]       = useState<BackgroundCheck[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<BackgroundCheck | null>(null);
  const [form, setForm]           = useState<Partial<BackgroundCheck>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectMsg, setDetectMsg] = useState<string | null>(null);

  useEffect(() => {
    api.getBackgroundChecks().then(setChecks).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (c: BackgroundCheck) => { setEditing(c); setForm(c); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateBackgroundCheck(editing.id, form);
        setChecks(prev => prev.map(c => c.id === updated.id ? updated : c));
      } else {
        const created = await api.createBackgroundCheck(form);
        setChecks(prev => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this background check record?")) return;
    await api.deleteBackgroundCheck(id);
    setChecks(prev => prev.filter(c => c.id !== id));
  };

  const handleDetect = async () => {
    setDetecting(true);
    setDetectMsg(null);
    try {
      const result = await api.runBackgroundCheckDetection();
      const fresh = await api.getBackgroundChecks();
      setChecks(fresh);
      setDetectMsg(result.created > 0 ? `${result.created} member${result.created > 1 ? "s" : ""} flagged` : "All members have records");
    } catch {
      setDetectMsg("Detection failed");
    } finally {
      setDetecting(false);
      setTimeout(() => setDetectMsg(null), 4000);
    }
  };

  const isExpired = (c: BackgroundCheck) => c.valid_until && new Date(c.valid_until) < new Date() && c.status === "completed";
  const pending = checks.filter(c => c.status === "pending" || c.status === "in_progress");
  const done    = checks.filter(c => c.status === "completed" || c.status === "failed" || c.status === "expired");

  const stats = {
    total: checks.length,
    completed: checks.filter(c => c.status === "completed").length,
    pending: checks.filter(c => c.status === "pending" || c.status === "in_progress").length,
    expired: checks.filter(c => c.status === "expired" || isExpired(c)).length,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <UserCheck className="w-5 h-5 text-brand-600 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Background Checks</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Track employee background check status and expiry</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {detectMsg && <span className="text-xs text-gray-500 hidden sm:inline">{detectMsg}</span>}
          <button
            onClick={handleDetect}
            disabled={detecting}
            className="btn-secondary gap-1.5 disabled:opacity-50 !px-3 !py-2 text-xs"
          >
            {detecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Auto-detect</span>
          </button>
          <button onClick={openCreate} className="btn-primary gap-1.5 !px-3 !py-2 text-xs">
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Add Check</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Total", value: stats.total, color: "text-gray-900" },
          { label: "Completed", value: stats.completed, color: "text-emerald-600" },
          { label: "Pending", value: stats.pending, color: "text-amber-600" },
          { label: "Expired", value: stats.expired, color: "text-red-600" },
        ].map(s => (
          <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-4">
            <p className="text-xs text-gray-400 font-medium mb-1">{s.label}</p>
            <p className={`text-2xl font-bold ${s.value > 0 ? s.color : "text-gray-300"}`}>{s.value}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : checks.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <UserCheck className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No background checks recorded</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> Add Check</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Employee</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:table-cell">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">Valid until</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {checks.map(check => (
                <tr key={check.id} className="hover:bg-gray-50/50 transition-colors">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-gray-900">{check.employee_name}</p>
                      {check.auto_detected && (
                        <span className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-600 border border-violet-100">
                          <Sparkles className="h-2.5 w-2.5" />Auto
                        </span>
                      )}
                    </div>
                    {check.employee_email && <p className="text-xs text-gray-400">{check.employee_email}</p>}
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <span className="text-xs capitalize text-gray-600">{check.check_type}</span>
                    {check.vendor && <span className="text-xs text-gray-400 ml-1">via {check.vendor}</span>}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[isExpired(check) ? "expired" : check.status]}`}>
                      {isExpired(check) ? "expired" : check.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    {check.valid_until ? (
                      <span className={`text-xs font-medium ${isExpired(check) ? "text-red-600" : "text-gray-600"}`}>
                        {new Date(check.valid_until).toLocaleDateString()}
                      </span>
                    ) : <span className="text-xs text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center gap-1 justify-end">
                      <button onClick={() => openEdit(check)} className="text-xs text-gray-500 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-100">Edit</button>
                      <button onClick={() => handleDelete(check.id)} className="text-xs text-red-400 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
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
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Background Check" : "Add Background Check"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Employee name *</label>
                  <input className="input" value={form.employee_name ?? ""} onChange={e => setForm(p => ({ ...p, employee_name: e.target.value }))} required />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input type="email" className="input" value={form.employee_email ?? ""} onChange={e => setForm(p => ({ ...p, employee_email: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Check type</label>
                  <select className="input" value={form.check_type ?? "standard"} onChange={e => setForm(p => ({ ...p, check_type: e.target.value as BackgroundCheck["check_type"] }))}>
                    {CHECK_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                  <select className="input" value={form.status ?? "pending"} onChange={e => setForm(p => ({ ...p, status: e.target.value as BackgroundCheck["status"] }))}>
                    {STATUSES.map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Vendor / Provider</label>
                <input className="input" value={form.vendor ?? ""} onChange={e => setForm(p => ({ ...p, vendor: e.target.value }))} placeholder="e.g. Sterling, Checkr" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Initiated</label>
                  <input type="date" className="input" value={form.initiated_at ? form.initiated_at.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, initiated_at: e.target.value || null }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Completed</label>
                  <input type="date" className="input" value={form.completed_at ? form.completed_at.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, completed_at: e.target.value || null }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Valid until</label>
                <input type="date" className="input" value={form.valid_until ? form.valid_until.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, valid_until: e.target.value || null }))} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                <textarea className="input min-h-[60px]" value={form.notes ?? ""} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Add check"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
