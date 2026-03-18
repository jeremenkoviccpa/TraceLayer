"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RopaRecord } from "@/lib/types";
import { Database, Plus, Trash2, X } from "lucide-react";

const ROLES = ["controller", "processor", "joint_controller"] as const;
const ROLE_STYLES: Record<string, string> = {
  controller:       "bg-blue-100 text-blue-700",
  processor:        "bg-amber-100 text-amber-700",
  joint_controller: "bg-purple-100 text-purple-700",
};
const ROLE_LABELS: Record<string, string> = {
  controller:       "Controller",
  processor:        "Processor",
  joint_controller: "Joint Controller",
};

const LEGAL_BASES = [
  { value: "consent",              label: "Consent" },
  { value: "contract",             label: "Contract" },
  { value: "legal_obligation",     label: "Legal Obligation" },
  { value: "vital_interests",      label: "Vital Interests" },
  { value: "public_task",          label: "Public Task" },
  { value: "legitimate_interests", label: "Legitimate Interests" },
];

const EMPTY: Partial<RopaRecord> = {
  name: "", role: "controller", purpose: "", legal_basis: "",
  data_categories: "", data_subjects: "", recipients: "",
  third_country_transfers: "", retention_period: "", security_measures: "",
  dpa_url: "", notes: "",
};

export default function RopaPage() {
  const [records, setRecords]     = useState<RopaRecord[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<RopaRecord | null>(null);
  const [form, setForm]           = useState<Partial<RopaRecord>>(EMPTY);
  const [saving, setSaving]       = useState(false);

  useEffect(() => {
    api.getRopaRecords().then(setRecords).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (r: RopaRecord) => { setEditing(r); setForm(r); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateRopaRecord(editing.id, form);
        setRecords((prev) => prev.map((r) => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createRopaRecord(form);
        setRecords((prev) => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this RoPA record?")) return;
    await api.deleteRopaRecord(id);
    setRecords((prev) => prev.filter((r) => r.id !== id));
  };

  const field = (key: keyof RopaRecord) => ({
    value: (form[key] as string) ?? "",
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [key]: e.target.value })),
  });

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <Database className="w-6 h-6 text-brand-600" />
            Records of Processing Activities
          </h1>
          <p className="text-sm text-gray-500 mt-1">GDPR Art. 30 · Data processing register</p>
        </div>
        <button
          onClick={openCreate}
          className="flex items-center gap-2 bg-brand-600 text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-brand-700 transition-colors"
        >
          <Plus className="w-4 h-4" /> Add Record
        </button>
      </div>

      {/* Table */}
      {records.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20">
          <Database className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm text-gray-400">No processing activities yet.</p>
          <button onClick={openCreate} className="mt-4 text-sm font-semibold text-brand-600 hover:text-brand-700">
            Add your first record →
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wider">
                <th className="px-4 py-3 text-left">Name</th>
                <th className="px-4 py-3 text-left w-36">Role</th>
                <th className="px-4 py-3 text-left w-48">Legal Basis</th>
                <th className="px-4 py-3 text-left w-40">Retention</th>
                <th className="px-4 py-3 text-right w-24">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {records.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-900">{r.name}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_STYLES[r.role] ?? "bg-gray-100 text-gray-500"}`}>
                      {ROLE_LABELS[r.role] ?? r.role}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{r.legal_basis || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{r.retention_period || "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1">
                      <button onClick={() => openEdit(r)} className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors">Edit</button>
                      <button onClick={() => handleDelete(r.id)} className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Record" : "New Processing Activity"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSave} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Activity Name *</label>
                  <input {...field("name")} required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. Customer account management" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Role</label>
                  <select {...field("role")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    {ROLES.map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Legal Basis</label>
                  <select {...field("legal_basis")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    <option value="">— Select —</option>
                    {LEGAL_BASES.map((b) => <option key={b.value} value={b.value}>{b.label}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Purpose</label>
                  <textarea {...field("purpose")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Why is this data being processed?" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Data Categories</label>
                  <textarea {...field("data_categories")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="e.g. Name, email, IP address" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Data Subjects</label>
                  <textarea {...field("data_subjects")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="e.g. Customers, employees" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Recipients</label>
                  <textarea {...field("recipients")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Who receives this data?" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Third Country Transfers</label>
                  <textarea {...field("third_country_transfers")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Any transfers outside the EEA?" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Retention Period</label>
                  <input {...field("retention_period")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="e.g. 2 years after contract end" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">DPA / Agreement URL</label>
                  <input {...field("dpa_url")} type="url" className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" placeholder="https://..." />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Security Measures</label>
                  <textarea {...field("security_measures")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Notes</label>
                  <textarea {...field("notes")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-60 transition-colors">
                  {saving ? "Saving…" : editing ? "Save Changes" : "Create Record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
