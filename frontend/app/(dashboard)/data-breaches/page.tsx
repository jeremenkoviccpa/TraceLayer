"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DataBreach } from "@/lib/types";
import { ShieldX, Plus, Trash2, X, ChevronDown, ChevronUp, Bell } from "lucide-react";

const SEV_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
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

const EMPTY: Partial<DataBreach> = {
  title: "", breach_type: "confidentiality", severity: "medium", status: "investigating",
  notification_required: false, description: "", affected_systems: "",
  root_cause: "", remediation: "", reporter_name: "",
};

function fmt(dt?: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString();
}

export default function DataBreachesPage() {
  const [breaches, setBreaches]   = useState<DataBreach[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<DataBreach | null>(null);
  const [form, setForm]           = useState<Partial<DataBreach>>(EMPTY);
  const [saving, setSaving]       = useState(false);
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

  const sf = (key: keyof DataBreach) => ({
    value: (form[key] as string) ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  const investigating  = breaches.filter((b) => b.status === "investigating").length;
  const notifRequired  = breaches.filter((b) => b.notification_required).length;
  const resolved       = breaches.filter((b) => b.status === "resolved" || b.status === "closed").length;

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
          <ShieldX className="w-5 h-5 text-red-500 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Data Breach Register</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">GDPR Art. 33-34 · HIPAA breach tracking</p>
          </div>
        </div>
        <button onClick={openCreate} className="flex items-center gap-1.5 bg-brand-600 text-white text-xs font-semibold px-3 py-2 rounded-xl hover:bg-brand-700 transition-colors shrink-0">
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Log Breach</span>
          <span className="sm:hidden">Log</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{breaches.length}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Total</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{investigating}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Active</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-red-600">{notifRequired}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Notify</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-emerald-600">{resolved}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Resolved</p>
        </div>
      </div>

      {/* Cards */}
      {breaches.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20">
          <ShieldX className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm text-gray-400">No breach incidents recorded.</p>
          <button onClick={openCreate} className="mt-4 text-sm font-semibold text-brand-600 hover:text-brand-700">Log first breach →</button>
        </div>
      ) : (
        <div className="space-y-3">
          {breaches.map((b) => (
            <div key={b.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
              <div className="px-5 py-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-semibold text-gray-900 text-sm truncate">{b.title}</h3>
                    {b.notification_required && (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-red-50 text-red-600 text-xs font-medium">
                        <Bell className="w-2.5 h-2.5" /> Notify Required
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${SEV_STYLES[b.severity] ?? "bg-gray-100 text-gray-500"}`}>{b.severity}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[b.status] ?? "bg-gray-100 text-gray-500"}`}>{b.status}</span>
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${BREACH_TYPE_STYLES[b.breach_type] ?? "bg-gray-100 text-gray-500"}`}>{b.breach_type}</span>
                    {b.affected_records != null && (
                      <span className="text-xs text-gray-400">{b.affected_records.toLocaleString()} records affected</span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <button onClick={() => openEdit(b)} className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors">Edit</button>
                  <button onClick={() => handleDelete(b.id)} className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                  <button onClick={() => setExpandedId(expandedId === b.id ? null : b.id)} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors">
                    {expandedId === b.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>
              {expandedId === b.id && (
                <div className="px-5 pb-4 pt-0 border-t border-gray-50 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-gray-400 mb-0.5">Occurred</p>
                    <p className="text-gray-700">{fmt(b.occurred_at)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-0.5">Discovered</p>
                    <p className="text-gray-700">{fmt(b.discovered_at)}</p>
                  </div>
                  {b.dpa_notified_at && (
                    <div>
                      <p className="text-xs text-gray-400 mb-0.5">DPA Notified</p>
                      <p className="text-gray-700">{fmt(b.dpa_notified_at)}</p>
                    </div>
                  )}
                  {b.individuals_notified_at && (
                    <div>
                      <p className="text-xs text-gray-400 mb-0.5">Individuals Notified</p>
                      <p className="text-gray-700">{fmt(b.individuals_notified_at)}</p>
                    </div>
                  )}
                  {b.description && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-400 mb-0.5">Description</p>
                      <p className="text-gray-700 whitespace-pre-wrap">{b.description}</p>
                    </div>
                  )}
                  {b.root_cause && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-400 mb-0.5">Root Cause</p>
                      <p className="text-gray-700 whitespace-pre-wrap">{b.root_cause}</p>
                    </div>
                  )}
                  {b.remediation && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-400 mb-0.5">Remediation</p>
                      <p className="text-gray-700 whitespace-pre-wrap">{b.remediation}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Breach" : "Log Data Breach"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSave} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Title *</label>
                  <input {...sf("title")} required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="Brief description of the breach" />
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
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Reporter Name</label>
                  <input {...sf("reporter_name")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div className="col-span-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="notif"
                    checked={!!form.notification_required}
                    onChange={(e) => setForm((f) => ({ ...f, notification_required: e.target.checked }))}
                    className="w-4 h-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                  />
                  <label htmlFor="notif" className="text-sm text-gray-700">Notification required (DPA / individuals)</label>
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
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Affected Systems</label>
                  <input {...sf("affected_systems")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
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
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">Cancel</button>
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
