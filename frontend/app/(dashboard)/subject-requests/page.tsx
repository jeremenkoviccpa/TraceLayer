"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SubjectRequest } from "@/lib/types";
import { UserSearch, Plus, Trash2, X } from "lucide-react";

const TYPE_STYLES: Record<string, string> = {
  access:        "bg-blue-100 text-blue-700",
  deletion:      "bg-red-100 text-red-700",
  rectification: "bg-amber-100 text-amber-700",
  portability:   "bg-blue-50 text-blue-600",
  objection:     "bg-gray-100 text-gray-600",
  restriction:   "bg-gray-100 text-gray-600",
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
  other: "bg-gray-100 text-gray-500",
};

const REQUEST_TYPES = ["access", "deletion", "rectification", "portability", "objection", "restriction"] as const;
const REGULATIONS   = ["gdpr", "ccpa", "other"] as const;
const STATUSES      = ["pending", "in_progress", "completed", "refused", "extended"] as const;

const EMPTY: Partial<SubjectRequest> = {
  requester_name: "", requester_email: "", request_type: "access",
  received_at: new Date().toISOString(), regulation: "gdpr", status: "pending",
};

function fmt(dt?: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString();
}

function sla30(req: SubjectRequest): string {
  if (req.due_at) return fmt(req.due_at);
  const d = new Date(req.received_at);
  d.setDate(d.getDate() + 30);
  return d.toLocaleDateString() + " (calc.)";
}

function isOverdue(req: SubjectRequest): boolean {
  if (req.status === "completed" || req.status === "refused") return false;
  const due = req.due_at ? new Date(req.due_at) : (() => { const d = new Date(req.received_at); d.setDate(d.getDate() + 30); return d; })();
  return due < new Date();
}

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
    e.preventDefault(); setSaving(true);
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

  const sf = (key: keyof SubjectRequest) => ({
    value: (form[key] as string) ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

  const pending  = requests.filter((r) => r.status === "pending" || r.status === "in_progress").length;
  const overdue  = requests.filter(isOverdue).length;
  const completed = requests.filter((r) => r.status === "completed").length;

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
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Subject Access Requests</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">GDPR Art. 15-22 · CCPA consumer rights</p>
          </div>
        </div>
        <button onClick={openCreate} className="flex items-center gap-1.5 bg-brand-600 text-white text-xs font-semibold px-3 py-2 rounded-xl hover:bg-brand-700 transition-colors shrink-0">
          <Plus className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">New Request</span>
          <span className="sm:hidden">New</span>
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-2 sm:gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{requests.length}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Total</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-amber-600">{pending}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Pending</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-red-600">{overdue}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Overdue</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4 text-center">
          <p className="text-xl sm:text-2xl font-bold text-emerald-600">{completed}</p>
          <p className="text-[10px] sm:text-xs text-gray-500 mt-1">Done</p>
        </div>
      </div>

      {/* Table */}
      {requests.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20">
          <UserSearch className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm text-gray-400">No subject requests yet.</p>
          <button onClick={openCreate} className="mt-4 text-sm font-semibold text-brand-600 hover:text-brand-700">Log first request →</button>
        </div>
      ) : (
        <>
          {/* Mobile cards */}
          <div className="sm:hidden space-y-2">
            {requests.map((r) => {
              const overdueMark = isOverdue(r);
              return (
                <div key={r.id} className="bg-white rounded-2xl border border-gray-100 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-gray-900 truncate">{r.requester_name}</p>
                      {r.requester_email && <p className="text-xs text-gray-400 truncate">{r.requester_email}</p>}
                      <div className="flex items-center gap-1.5 flex-wrap mt-2">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${TYPE_STYLES[r.request_type] ?? "bg-gray-100 text-gray-500"}`}>{r.request_type}</span>
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium uppercase ${REG_STYLES[r.regulation] ?? "bg-gray-100 text-gray-500"}`}>{r.regulation}</span>
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[r.status] ?? "bg-gray-100 text-gray-500"}`}>{r.status.replace("_", " ")}</span>
                      </div>
                      <p className={`text-xs mt-1.5 ${overdueMark ? "text-red-600 font-semibold" : "text-gray-400"}`}>
                        Due: {sla30(r)}
                      </p>
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      <button onClick={() => openEdit(r)} className="text-xs text-brand-600 font-medium px-2 py-1 rounded-lg hover:bg-brand-50">Edit</button>
                      <button onClick={() => handleDelete(r.id)} className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Desktop table */}
          <div className="hidden sm:block bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wider">
                  <th className="px-4 py-3 text-left">Requester</th>
                  <th className="px-4 py-3 text-left w-32">Type</th>
                  <th className="px-4 py-3 text-left w-24">Regulation</th>
                  <th className="px-4 py-3 text-left w-28">Received</th>
                  <th className="px-4 py-3 text-left w-36">Due Date</th>
                  <th className="px-4 py-3 text-left w-28">Status</th>
                  <th className="px-4 py-3 text-right w-24">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {requests.map((r) => {
                  const overdueMark = isOverdue(r);
                  return (
                    <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-900">{r.requester_name}</p>
                        {r.requester_email && <p className="text-xs text-gray-400">{r.requester_email}</p>}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium capitalize ${TYPE_STYLES[r.request_type] ?? "bg-gray-100 text-gray-500"}`}>{r.request_type}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium uppercase ${REG_STYLES[r.regulation] ?? "bg-gray-100 text-gray-500"}`}>{r.regulation}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-500 text-xs">{fmt(r.received_at)}</td>
                      <td className="px-4 py-3 text-xs">
                        <span className={overdueMark ? "text-red-600 font-semibold" : "text-gray-500"}>{sla30(r)}</span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[r.status] ?? "bg-gray-100 text-gray-500"}`}>{r.status.replace("_", " ")}</span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button onClick={() => openEdit(r)} className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors">Edit</button>
                          <button onClick={() => handleDelete(r.id)} className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Request" : "New Subject Request"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSave} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Requester Name *</label>
                  <input {...sf("requester_name")} required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Requester Email</label>
                  <input {...sf("requester_email")} type="email" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Request Type *</label>
                  <select {...sf("request_type")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    {REQUEST_TYPES.map((t) => <option key={t} value={t} className="capitalize">{t}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Regulation</label>
                  <select {...sf("regulation")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    {REGULATIONS.map((r) => <option key={r} value={r} className="uppercase">{r.toUpperCase()}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Received At *</label>
                  <input
                    type="date"
                    value={form.received_at ? new Date(form.received_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) => setForm((f) => ({ ...f, received_at: e.target.value ? new Date(e.target.value).toISOString() : "" }))}
                    required
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Due Date</label>
                  <input
                    type="date"
                    value={form.due_at ? new Date(form.due_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) => setForm((f) => ({ ...f, due_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Status</label>
                  <select {...sf("status")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    {STATUSES.map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Completed At</label>
                  <input
                    type="date"
                    value={form.completed_at ? new Date(form.completed_at).toISOString().slice(0, 10) : ""}
                    onChange={(e) => setForm((f) => ({ ...f, completed_at: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Response Notes</label>
                  <textarea {...sf("response_notes")} rows={3} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-60 transition-colors">
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
