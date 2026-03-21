"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { TrainingRecord } from "@/lib/types";
import { GraduationCap, Plus, CheckCircle2, Clock, AlertTriangle, Trash2, X, RefreshCw, Sparkles } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  completed: "bg-emerald-50 text-emerald-700",
  pending: "bg-amber-50 text-amber-700",
  overdue: "bg-red-50 text-red-600",
};

const STATUS_ICONS: Record<string, React.ElementType> = {
  completed: CheckCircle2,
  pending: Clock,
  overdue: AlertTriangle,
};

const TRAINING_TITLES = [
  "Security Awareness Training",
  "HIPAA Privacy & Security Training",
  "Phishing Simulation",
  "Password & Access Control Training",
  "Data Handling & Classification",
  "Incident Response Awareness",
  "SOC 2 Controls Overview",
  "Code of Conduct & Acceptable Use",
];

function Modal({ onClose, onSave }: { onClose: () => void; onSave: (data: Partial<TrainingRecord>) => Promise<void> }) {
  const [form, setForm] = useState({
    assignee_email: "",
    assignee_name: "",
    title: TRAINING_TITLES[0],
    due_date: "",
    annual: false,
    notes: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.assignee_email || !form.title) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        assignee_name: form.assignee_name || null,
        due_date: form.due_date || null,
        notes: form.notes || null,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">Assign Training</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Training title</label>
            <select
              value={form.title}
              onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            >
              {TRAINING_TITLES.map((t) => <option key={t}>{t}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Assignee email *</label>
              <input
                type="email"
                value={form.assignee_email}
                onChange={(e) => setForm((p) => ({ ...p, assignee_email: e.target.value }))}
                placeholder="alice@acme.com"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name (optional)</label>
              <input
                value={form.assignee_name}
                onChange={(e) => setForm((p) => ({ ...p, assignee_name: e.target.value }))}
                placeholder="Alice Smith"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
              />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Due date</label>
            <input
              type="date"
              value={form.due_date}
              onChange={(e) => setForm((p) => ({ ...p, due_date: e.target.value }))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
              rows={2}
              placeholder="Any instructions or context…"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
            />
          </div>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.annual}
              onChange={(e) => setForm((p) => ({ ...p, annual: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Annual renewal required</span>
          </label>
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-xl">Cancel</button>
          <button
            onClick={handleSubmit}
            disabled={saving || !form.assignee_email}
            className="px-4 py-2 text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-40"
          >
            {saving ? "Saving…" : "Assign"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TrainingPage() {
  const [records, setRecords] = useState<TrainingRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [detectMsg, setDetectMsg] = useState<string | null>(null);

  const load = () => api.getTraining().then(setRecords).catch(() => {}).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const handleCreate = async (data: Partial<TrainingRecord>) => {
    const rec = await api.createTraining(data);
    setRecords((prev) => [rec, ...prev]);
  };

  const markComplete = async (id: string) => {
    const updated = await api.updateTraining(id, {
      completed_at: new Date().toISOString(),
      status: "completed",
    });
    setRecords((prev) => prev.map((r) => r.id === id ? updated : r));
  };

  const handleDelete = async (id: string) => {
    await api.deleteTraining(id);
    setRecords((prev) => prev.filter((r) => r.id !== id));
  };

  const handleDetect = async () => {
    setDetecting(true);
    setDetectMsg(null);
    try {
      const result = await api.runTrainingDetection();
      const fresh = await api.getTraining();
      setRecords(fresh);
      setDetectMsg(result.created > 0 ? `${result.created} training assignment${result.created > 1 ? "s" : ""} created` : "All team members have training");
    } catch {
      setDetectMsg("Detection failed");
    } finally {
      setDetecting(false);
      setTimeout(() => setDetectMsg(null), 4000);
    }
  };

  const completed = records.filter((r) => r.status === "completed").length;
  const overdue = records.filter((r) => r.status === "overdue").length;
  const pending = records.filter((r) => r.status === "pending").length;
  const pct = records.length > 0 ? Math.round(completed / records.length * 100) : 0;

  return (
    <div className="animate-fade-in overflow-x-hidden">

      {/* Dark hero card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6">
        {/* Row 1: icon + title + action */}
        <div className="flex items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 rounded-xl bg-brand-500/20 flex items-center justify-center shrink-0">
              <GraduationCap className="w-5 h-5 text-brand-400" />
            </div>
            <div className="min-w-0">
              <h1 className="text-base sm:text-lg font-bold text-white leading-tight truncate">Training Tracker</h1>
              <p className="text-xs sm:text-sm text-slate-400 mt-0.5 hidden sm:block">Track security awareness training for SOC 2 CC1.4 compliance.</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            {detectMsg && <span className="text-xs text-slate-300 hidden sm:inline">{detectMsg}</span>}
            <button
              onClick={handleDetect}
              disabled={detecting}
              className="flex items-center gap-1.5 bg-white/10 border border-white/20 hover:bg-white/20 text-white font-semibold px-3 py-2 rounded-xl text-xs transition-colors disabled:opacity-50"
            >
              {detecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">Auto-detect</span>
            </button>
            <button
              onClick={() => setShowModal(true)}
              className="flex items-center gap-1.5 bg-brand-600 hover:bg-brand-500 text-white font-semibold px-3 py-2 rounded-xl text-xs transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Assign training</span>
              <span className="sm:hidden">Assign</span>
            </button>
          </div>
        </div>

        {/* Row 2: stats grid */}
        <div className="grid grid-cols-4 gap-2 sm:gap-4">
          <div>
            <p className={`text-2xl sm:text-3xl font-bold ${pct >= 80 ? "text-brand-400" : pct >= 50 ? "text-amber-400" : "text-red-400"}`}>{pct}%</p>
            <p className="text-xs text-slate-400 mt-1">Completion</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-brand-400">{completed}</p>
            <p className="text-xs text-slate-400 mt-1">Done</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-brand-400">{pending}</p>
            <p className="text-xs text-slate-400 mt-1">Pending</p>
          </div>
          <div>
            <p className={`text-2xl sm:text-3xl font-bold ${overdue > 0 ? "text-red-400" : "text-brand-400"}`}>{overdue}</p>
            <p className="text-xs text-slate-400 mt-1">Overdue</p>
          </div>
        </div>
      </div>

      {/* Progress bar */}
      {records.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-4 mb-6">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-2">
            <span>Overall completion</span>
            <span className="font-semibold">{completed}/{records.length} employees trained</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-700 ${pct >= 80 ? "bg-brand-500" : pct >= 50 ? "bg-amber-400" : "bg-red-400"}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : records.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <GraduationCap className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-600 mb-1">No training records yet</p>
          <p className="text-xs text-gray-400 mb-4 max-w-xs mx-auto">
            SOC 2 CC1.4 requires annual security awareness training for all employees. Auditors will ask to see records. Assign training to each team member and mark it complete when done.
          </p>
          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-xl text-sm"
          >
            <Plus className="w-4 h-4" /> Assign first training
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[420px]">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">Assignee</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide hidden sm:table-cell">Training</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide hidden md:table-cell">Due date</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">Status</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {records.map((r) => {
                  const StatusIcon = STATUS_ICONS[r.status] ?? Clock;
                  return (
                    <tr key={r.id} className="hover:bg-gray-50/50">
                      <td className="px-5 py-3.5">
                        <p className="font-medium text-gray-900">{r.assignee_name || r.assignee_email}</p>
                        {r.assignee_name && <p className="text-xs text-gray-400">{r.assignee_email}</p>}
                        <p className="text-xs text-gray-500 sm:hidden mt-0.5 truncate max-w-[160px]">{r.title}</p>
                      </td>
                      <td className="px-5 py-3.5 hidden sm:table-cell">
                        <div className="flex items-center gap-2">
                          <span className="text-gray-700">{r.title}</span>
                          {r.annual && <span title="Annual renewal"><RefreshCw className="w-3 h-3 text-gray-400" /></span>}
                          {r.auto_detected && (
                            <span className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-600 border border-violet-100">
                              <Sparkles className="h-2.5 w-2.5" />Auto
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-gray-500 hidden md:table-cell">
                        {r.due_date ? new Date(r.due_date).toLocaleDateString() : "—"}
                      </td>
                      <td className="px-5 py-3.5">
                        <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[r.status]}`}>
                          <StatusIcon className="w-3 h-3" />
                          {r.status.charAt(0).toUpperCase() + r.status.slice(1)}
                        </span>
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2 justify-end">
                          {r.status !== "completed" && (
                            <button
                              onClick={() => markComplete(r.id)}
                              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 border border-emerald-200 hover:border-emerald-300 px-2.5 py-1 rounded-lg transition-colors whitespace-nowrap"
                            >
                              Mark complete
                            </button>
                          )}
                          {deletingId === r.id ? (
                            <>
                              <button onClick={() => setDeletingId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">Cancel</button>
                              <button onClick={() => { handleDelete(r.id); setDeletingId(null); }} className="text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg">Delete</button>
                            </>
                          ) : (
                            <button
                              onClick={() => setDeletingId(r.id)}
                              className="text-gray-300 hover:text-red-400 transition-colors p-1"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && <Modal onClose={() => setShowModal(false)} onSave={handleCreate} />}
    </div>
  );
}
