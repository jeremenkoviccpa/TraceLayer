"use client";

import { Fragment, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Vendor } from "@/lib/types";
import { Building2, Plus, Trash2, X, CheckCircle2, Circle, ExternalLink, ChevronDown, ChevronUp } from "lucide-react";
import { DocumentUpload } from "@/components/document-upload";
import { toast } from "@/lib/toast";

const RISK_STYLES: Record<string, string> = {
  low: "bg-emerald-50 text-emerald-700",
  medium: "bg-amber-50 text-amber-700",
  high: "bg-orange-50 text-orange-700",
  critical: "bg-red-50 text-red-600",
};

const CATEGORIES = ["cloud", "payment", "identity", "security", "communication", "hr", "legal", "other"];
const RISK_LEVELS = ["low", "medium", "high", "critical"];

function Modal({
  onClose,
  onSave,
  initial,
}: {
  onClose: () => void;
  onSave: (data: Partial<Vendor>) => Promise<void>;
  initial?: Vendor;
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? "",
    category: initial?.category ?? "cloud",
    risk_level: initial?.risk_level ?? "medium",
    website: initial?.website ?? "",
    contact_email: initial?.contact_email ?? "",
    soc2_certified: initial?.soc2_certified ?? false,
    iso27001_certified: initial?.iso27001_certified ?? false,
    hipaa_certified: initial?.hipaa_certified ?? false,
    review_date: initial?.review_date ? initial.review_date.slice(0, 10) : "",
    notes: initial?.notes ?? "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.name) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        website: form.website || null,
        contact_email: form.contact_email || null,
        review_date: form.review_date || null,
        notes: form.notes || null,
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
          <h2 className="font-bold text-gray-900">{initial ? "Edit Vendor" : "Add Vendor"}</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Vendor name *</label>
            <input value={form.name} onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))} placeholder="e.g. AWS, Stripe, Okta" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
              <select value={form.category} onChange={(e) => setForm((p) => ({ ...p, category: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
                {CATEGORIES.map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Risk level</label>
              <select value={form.risk_level} onChange={(e) => setForm((p) => ({ ...p, risk_level: e.target.value as Vendor["risk_level"] }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
                {RISK_LEVELS.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Website</label>
              <input value={form.website} onChange={(e) => setForm((p) => ({ ...p, website: e.target.value }))} placeholder="https://aws.amazon.com" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Contact email</label>
              <input value={form.contact_email} onChange={(e) => setForm((p) => ({ ...p, contact_email: e.target.value }))} placeholder="security@vendor.com" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Last review date</label>
            <input type="date" value={form.review_date} onChange={(e) => setForm((p) => ({ ...p, review_date: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">Certifications</label>
            <div className="flex flex-col gap-2">
              {([["soc2_certified", "SOC 2 Type II"], ["iso27001_certified", "ISO 27001"], ["hipaa_certified", "HIPAA"]] as const).map(([key, label]) => (
                <label key={key} className="flex items-center gap-2 cursor-pointer">
                  <input type="checkbox" checked={form[key]} onChange={(e) => setForm((p) => ({ ...p, [key]: e.target.checked }))} className="rounded" />
                  <span className="text-sm text-gray-700">{label} certified</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} rows={2} placeholder="Risk assessment notes, mitigation controls…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-xl">Cancel</button>
          <button onClick={handleSubmit} disabled={saving || !form.name} className="px-4 py-2 text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white rounded-xl disabled:opacity-40">
            {saving ? "Saving…" : initial ? "Update" : "Add vendor"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function VendorsPage() {
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Vendor | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    api.getVendors().then(setVendors).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (data: Partial<Vendor>) => {
    try {
      const v = await api.createVendor(data);
      setVendors((prev) => [...prev, v].sort((a, b) => a.name.localeCompare(b.name)));
      toast("Vendor added");
    } catch { toast("Failed to add vendor", "error"); throw new Error("failed"); }
  };

  const handleUpdate = async (data: Partial<Vendor>) => {
    if (!editing) return;
    try {
      const v = await api.updateVendor(editing.id, data);
      setVendors((prev) => prev.map((x) => x.id === editing.id ? v : x));
      setEditing(null);
      toast("Vendor updated");
    } catch { toast("Failed to update vendor", "error"); throw new Error("failed"); }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteVendor(id);
      setVendors((prev) => prev.filter((v) => v.id !== id));
      toast("Vendor deleted");
    } catch { toast("Failed to delete vendor", "error"); }
  };

  const highRisk = vendors.filter((v) => v.risk_level === "high" || v.risk_level === "critical").length;
  const certified = vendors.filter((v) => v.soc2_certified || v.iso27001_certified).length;
  const needsReview = vendors.filter((v) => !v.review_date).length;

  return (
    <div className="animate-fade-in overflow-x-hidden">

      {/* Dark hero card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6">
        {/* Row 1: icon + title + action */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center shrink-0">
              <Building2 className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">Vendor Due Diligence</h1>
              <p className="text-sm text-slate-400 mt-0.5">Track third-party vendors, their certifications, and risk levels.</p>
            </div>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-brand-600 hover:bg-brand-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors shrink-0"
          >
            <Plus className="w-4 h-4" /> Add vendor
          </button>
        </div>

        {/* Row 2: stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4">
          <div>
            <p className="text-3xl font-bold text-brand-400">{vendors.length}</p>
            <p className="text-xs text-slate-400 mt-1">Total vendors</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${highRisk > 0 ? "text-red-400" : "text-brand-400"}`}>{highRisk}</p>
            <p className="text-xs text-slate-400 mt-1">High / critical risk</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-brand-400">{certified}</p>
            <p className="text-xs text-slate-400 mt-1">Certified</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${needsReview > 0 ? "text-orange-400" : "text-brand-400"}`}>{needsReview}</p>
            <p className="text-xs text-slate-400 mt-1">Needs review</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : vendors.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <Building2 className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-600 mb-1">No vendors tracked yet</p>
          <p className="text-xs text-gray-400 mb-4 max-w-xs mx-auto">
            SOC 2 CC9.2 requires vendor risk management. Add the tools and services you rely on (AWS, Stripe, Salesforce…) and track whether each is SOC 2 or ISO 27001 certified. Enterprise buyers ask about this.
          </p>
          <button onClick={() => setShowModal(true)} className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold px-4 py-2 rounded-xl text-sm">
            <Plus className="w-4 h-4" /> Add first vendor
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[420px]">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">Vendor</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide hidden sm:table-cell">Category</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide">Risk</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide hidden md:table-cell">Certifications</th>
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wide hidden lg:table-cell">Last review</th>
                  <th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {vendors.map((v) => (
                  <Fragment key={v.id}>
                    <tr className="hover:bg-gray-50/50">
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-gray-900">{v.name}</span>
                          {v.website && (
                            <a href={v.website} target="_blank" rel="noopener noreferrer" className="text-gray-300 hover:text-brand-500">
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                        {v.contact_email && <p className="text-xs text-gray-400 hidden sm:block">{v.contact_email}</p>}
                        <p className="text-xs text-gray-400 sm:hidden mt-0.5 capitalize">{v.category} · {v.review_date ? new Date(v.review_date).toLocaleDateString() : <span className="text-amber-500">Not reviewed</span>}</p>
                      </td>
                      <td className="px-5 py-3.5 text-gray-500 capitalize hidden sm:table-cell">{v.category}</td>
                      <td className="px-5 py-3.5">
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full capitalize ${RISK_STYLES[v.risk_level]}`}>
                          {v.risk_level}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 hidden md:table-cell">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {v.soc2_certified
                            ? <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded"><CheckCircle2 className="w-2.5 h-2.5" />SOC 2</span>
                            : <span className="flex items-center gap-1 text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded"><Circle className="w-2.5 h-2.5" />SOC 2</span>}
                          {v.iso27001_certified
                            ? <span className="flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded"><CheckCircle2 className="w-2.5 h-2.5" />ISO</span>
                            : <span className="flex items-center gap-1 text-[10px] text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded"><Circle className="w-2.5 h-2.5" />ISO</span>}
                        </div>
                      </td>
                      <td className="px-5 py-3.5 text-gray-500 text-xs hidden lg:table-cell">
                        {v.review_date ? new Date(v.review_date).toLocaleDateString() : <span className="text-amber-500 font-medium">Not reviewed</span>}
                      </td>
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2 justify-end">
                          <button onClick={() => setEditing(v)} className="text-xs font-semibold text-gray-500 hover:text-gray-700 border border-gray-200 px-2.5 py-1 rounded-lg">Edit</button>
                          {deletingId === v.id ? (
                            <>
                              <button onClick={() => setDeletingId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">Cancel</button>
                              <button onClick={() => { handleDelete(v.id); setDeletingId(null); }} className="text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg">Delete</button>
                            </>
                          ) : (
                            <button onClick={() => setDeletingId(v.id)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 className="w-4 h-4" /></button>
                          )}
                          <button onClick={() => setExpanded(expanded === v.id ? null : v.id)} className="text-gray-400 hover:text-gray-600 p-1">
                            {expanded === v.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>
                      </td>
                    </tr>
                    {expanded === v.id && (
                      <tr>
                        <td colSpan={6} className="px-5 pb-4 bg-gray-50/50">
                          {v.notes && (
                            <p className="text-xs text-gray-500 pt-3 pb-1">{v.notes}</p>
                          )}
                          <DocumentUpload resourceType="vendor" resourceId={v.id} />
                        </td>
                      </tr>
                    )}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {showModal && <Modal onClose={() => setShowModal(false)} onSave={handleCreate} />}
      {editing && <Modal onClose={() => setEditing(null)} onSave={handleUpdate} initial={editing} />}
    </div>
  );
}
