"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Building2, Plus, Trash2, X, Check, Edit2, Globe, CheckCircle2, Circle } from "lucide-react";
import { toast } from "@/lib/toast";

const DATA_CATEGORIES = [
  "personal_identifiers", "contact_data", "financial_data", "health_data",
  "usage_data", "device_data", "location_data", "behavioral_data",
  "credentials", "communications", "employee_data", "biometric_data",
];
const LEGAL_BASES = ["consent", "contract", "legal_obligation", "vital_interests", "public_task", "legitimate_interests"];
const TRANSFER_MECHANISMS = ["adequacy_decision", "standard_contractual_clauses", "binding_corporate_rules", "derogation", "not_applicable"];

const fmt = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());

function DpaStatus({ signed }: { signed: boolean }) {
  return signed
    ? <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700"><Check className="w-2.5 h-2.5" /> DPA signed</span>
    : <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-amber-50 text-amber-700"><Circle className="w-2.5 h-2.5" /> DPA pending</span>;
}

function SubprocessorModal({
  initial,
  onClose,
  onSave,
}: {
  initial?: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? "",
    country: initial?.country ?? "",
    purpose: initial?.purpose ?? "",
    data_categories: (initial?.data_categories ?? []) as string[],
    legal_basis: initial?.legal_basis ?? "contract",
    transfer_mechanism: initial?.transfer_mechanism ?? "not_applicable",
    dpa_signed: initial?.dpa_signed ?? false,
    website: initial?.website ?? "",
    contact_email: initial?.contact_email ?? "",
  });
  const [saving, setSaving] = useState(false);

  const toggleCategory = (cat: string) => {
    setForm(f => ({
      ...f,
      data_categories: f.data_categories.includes(cat)
        ? f.data_categories.filter(c => c !== cat)
        : [...f.data_categories, cat],
    }));
  };

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        country: form.country || null,
        purpose: form.purpose || null,
        website: form.website || null,
        contact_email: form.contact_email || null,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 my-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">{initial ? "Edit" : "Add"} Subprocessor</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-gray-600 mb-1">Name *</label>
            <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30" placeholder="e.g. Amazon Web Services" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Country</label>
            <input value={form.country} onChange={e => setForm(f => ({ ...f, country: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30" placeholder="United States" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Website</label>
            <input value={form.website} onChange={e => setForm(f => ({ ...f, website: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30" placeholder="https://aws.amazon.com" />
          </div>
          <div className="col-span-2">
            <label className="block text-xs font-semibold text-gray-600 mb-1">Processing purpose</label>
            <textarea value={form.purpose} onChange={e => setForm(f => ({ ...f, purpose: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 resize-none" placeholder="Cloud infrastructure hosting, storage, and compute" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Legal basis</label>
            <select value={form.legal_basis} onChange={e => setForm(f => ({ ...f, legal_basis: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30">
              {LEGAL_BASES.map(b => <option key={b} value={b}>{fmt(b)}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Transfer mechanism</label>
            <select value={form.transfer_mechanism} onChange={e => setForm(f => ({ ...f, transfer_mechanism: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30">
              {TRANSFER_MECHANISMS.map(m => <option key={m} value={m}>{fmt(m)}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-600 mb-2">Data categories processed</label>
          <div className="flex flex-wrap gap-1.5">
            {DATA_CATEGORIES.map(cat => (
              <button
                key={cat}
                onClick={() => toggleCategory(cat)}
                className={`text-[11px] font-medium px-2 py-1 rounded-lg border transition-all ${
                  form.data_categories.includes(cat)
                    ? "bg-teal-500 text-white border-teal-500"
                    : "bg-white text-gray-500 border-gray-200 hover:border-teal-300"
                }`}
              >
                {fmt(cat)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setForm(f => ({ ...f, dpa_signed: !f.dpa_signed }))}
            className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-medium transition-all ${
              form.dpa_signed ? "bg-emerald-50 border-emerald-200 text-emerald-700" : "bg-white border-gray-200 text-gray-600 hover:border-emerald-200"
            }`}
          >
            {form.dpa_signed ? <CheckCircle2 className="w-4 h-4" /> : <Circle className="w-4 h-4" />}
            DPA signed
          </button>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving || !form.name} className="flex-1 bg-teal-600 text-white rounded-xl py-2 text-sm font-semibold hover:bg-teal-700 disabled:opacity-50">
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SubprocessorsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [editing, setEditing] = useState<any | null>(null);

  useEffect(() => {
    api.getSubprocessors().then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const dpaSigned = items.filter(i => i.dpa_signed).length;

  const handleCreate = async (data: any) => {
    const created = await api.createSubprocessor(data);
    setItems(prev => [...prev, created]);
  };

  const handleUpdate = async (data: any) => {
    const updated = await api.updateSubprocessor(editing.id, data);
    setItems(prev => prev.map(i => i.id === updated.id ? updated : i));
    setEditing(null);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteSubprocessor(id);
      setItems(prev => prev.filter(i => i.id !== id));
    } catch { }
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/20 ring-1 ring-violet-500/30">
              <Building2 className="h-5 w-5 text-violet-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Subprocessors</h1>
              <p className="text-sm text-slate-400">GDPR Art. 28 — third parties who process personal data on your behalf.</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-violet-400">{items.length}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Total</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{dpaSigned}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">DPA signed</span>
            </div>
            {items.length - dpaSigned > 0 && (
              <>
                <div className="w-px h-8 bg-slate-700" />
                <div className="flex flex-col items-center">
                  <span className="text-2xl font-black text-amber-400">{items.length - dpaSigned}</span>
                  <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">DPA pending</span>
                </div>
              </>
            )}
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 bg-violet-500 hover:bg-violet-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" /> Add
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-2xl border border-dashed border-gray-200 bg-white text-center">
          <Building2 className="w-8 h-8 text-gray-200" />
          <p className="text-sm font-medium text-gray-500">No subprocessors added yet</p>
          <p className="text-xs text-gray-400">Add third-party vendors who process personal data on your behalf.</p>
          <button onClick={() => setShowAdd(true)} className="text-xs font-semibold text-violet-600 hover:text-violet-700">+ Add first subprocessor</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Subprocessor</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden sm:table-cell">Country</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden md:table-cell">Transfer</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">DPA</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {items.map(item => (
                <tr key={item.id} className="border-b border-gray-50 hover:bg-gray-50/40 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-semibold text-gray-900">{item.name}</div>
                    {item.purpose && <div className="text-xs text-gray-400 mt-0.5 line-clamp-1">{item.purpose}</div>}
                    {item.data_categories?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {(item.data_categories as string[]).slice(0, 3).map(cat => (
                          <span key={cat} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded-md">{fmt(cat)}</span>
                        ))}
                        {item.data_categories.length > 3 && <span className="text-[10px] text-gray-400">+{item.data_categories.length - 3}</span>}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">
                    <div className="flex items-center gap-1">
                      <Globe className="w-3 h-3 text-gray-300" />
                      {item.country || <span className="text-gray-300">—</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell">
                    {item.transfer_mechanism && item.transfer_mechanism !== "not_applicable"
                      ? <span className="text-[11px] font-medium text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded-md">{fmt(item.transfer_mechanism)}</span>
                      : <span className="text-gray-300">N/A</span>
                    }
                  </td>
                  <td className="px-4 py-3"><DpaStatus signed={item.dpa_signed} /></td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <button onClick={() => setEditing(item)} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600"><Edit2 className="w-3.5 h-3.5" /></button>
                      <button onClick={() => handleDelete(item.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showAdd && <SubprocessorModal onClose={() => setShowAdd(false)} onSave={handleCreate} />}
      {editing && <SubprocessorModal initial={editing} onClose={() => setEditing(null)} onSave={handleUpdate} />}
    </div>
  );
}
