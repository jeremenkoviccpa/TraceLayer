"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Vulnerability } from "@/lib/types";
import { Bug, Plus, Trash2, X, Sparkles, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";

const SEVERITIES = ["critical", "high", "medium", "low", "info"] as const;
const STATUSES = ["open", "in_remediation", "resolved", "accepted_risk"] as const;

const SEV_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
  info:     "bg-blue-50 text-blue-600",
};

const STATUS_STYLES: Record<string, string> = {
  open:           "bg-red-50 text-red-600",
  in_remediation: "bg-amber-50 text-amber-700",
  resolved:       "bg-emerald-50 text-emerald-700",
  accepted_risk:  "bg-gray-100 text-gray-500",
};

const EMPTY: Partial<Vulnerability> = {
  title: "", severity: "medium", status: "open", cve_id: "", affected_system: "", description: "", remediation_notes: "",
};

export default function VulnerabilitiesPage() {
  const [vulns, setVulns]         = useState<Vulnerability[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Vulnerability | null>(null);
  const [form, setForm]           = useState<Partial<Vulnerability>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [detecting, setDetecting] = useState(false);

  useEffect(() => {
    api.getVulnerabilities().then(setVulns).finally(() => setLoading(false));
  }, []);

  const handleAutoDetect = async () => {
    setDetecting(true);
    try {
      const result = await api.autoDetectVulnerabilities();
      if (result.created > 0) {
        const fresh = await api.getVulnerabilities();
        setVulns(fresh);
        toast(`Auto-detected ${result.created} vulnerability${result.created !== 1 ? "s" : ""}`);
      } else {
        toast("No new vulnerabilities found in integration data");
      }
    } catch { toast("Auto-detect failed", "error"); } finally { setDetecting(false); }
  };

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (v: Vulnerability) => { setEditing(v); setForm(v); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateVulnerability(editing.id, form);
        setVulns(prev => prev.map(v => v.id === updated.id ? updated : v));
        toast("Vulnerability updated");
      } else {
        const created = await api.createVulnerability(form);
        setVulns(prev => [created, ...prev]);
        toast("Vulnerability logged");
      }
      closeModal();
    } catch { toast("Failed to save", "error"); } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this vulnerability?")) return;
    try {
      await api.deleteVulnerability(id);
      setVulns(prev => prev.filter(v => v.id !== id));
      toast("Vulnerability deleted");
    } catch { toast("Failed to delete", "error"); }
  };

  const isOverdue = (v: Vulnerability) => v.due_date && new Date(v.due_date) < new Date() && v.status !== "resolved" && v.status !== "accepted_risk";
  const openVulns = vulns.filter(v => v.status === "open" || v.status === "in_remediation");
  const closedVulns = vulns.filter(v => v.status === "resolved" || v.status === "accepted_risk");

  const counts = SEVERITIES.reduce((acc, s) => ({ ...acc, [s]: openVulns.filter(v => v.severity === s).length }), {} as Record<string, number>);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <Bug className="w-5 h-5 text-orange-500 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Vulnerability Management</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Track CVEs, patch status, and remediation</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button onClick={handleAutoDetect} disabled={detecting} className="btn-secondary gap-1.5 !px-3 !py-2 text-xs">
            {detecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Auto-detect</span>
          </button>
          <button onClick={openCreate} className="btn-primary gap-1.5 !px-3 !py-2 text-xs">
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Add Vulnerability</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </div>

      {/* Severity stats */}
      <div className="grid grid-cols-5 gap-3">
        {SEVERITIES.map(sev => (
          <div key={sev} className="bg-white rounded-xl border border-gray-100 p-3 text-center">
            <p className={`text-xl font-bold ${counts[sev] > 0 ? SEV_STYLES[sev].split(" ")[1] : "text-gray-300"}`}>{counts[sev]}</p>
            <p className="text-xs text-gray-400 capitalize mt-0.5">{sev}</p>
          </div>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : vulns.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <Bug className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No vulnerabilities tracked</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> Add Vulnerability</button>
        </div>
      ) : (
        <div className="space-y-6">
          {openVulns.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Open ({openVulns.length})</h2>
              <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-100">
                    <tr>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Vulnerability</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Severity</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:table-cell">Status</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">Due</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {openVulns.map(v => (
                      <tr key={v.id} className="hover:bg-gray-50/50 transition-colors">
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-900">{v.title}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            {v.cve_id && <span className="text-xs font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">{v.cve_id}</span>}
                            {v.affected_system && <span className="text-xs text-gray-400">{v.affected_system}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${SEV_STYLES[v.severity]}`}>{v.severity}</span>
                        </td>
                        <td className="px-4 py-3 hidden sm:table-cell">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[v.status]}`}>{v.status.replace("_", " ")}</span>
                        </td>
                        <td className="px-4 py-3 hidden md:table-cell">
                          {v.due_date ? (
                            <span className={`text-xs font-medium ${isOverdue(v) ? "text-red-600" : "text-gray-600"}`}>
                              {isOverdue(v) ? "⚠️ " : ""}{new Date(v.due_date).toLocaleDateString()}
                            </span>
                          ) : <span className="text-xs text-gray-300">—</span>}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center gap-1 justify-end">
                            <button onClick={() => openEdit(v)} className="text-xs text-gray-500 hover:text-gray-900 px-2 py-1 rounded hover:bg-gray-100">Edit</button>
                            <button onClick={() => handleDelete(v.id)} className="text-xs text-red-400 hover:text-red-600 px-2 py-1 rounded hover:bg-red-50"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
          {closedVulns.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Closed ({closedVulns.length})</h2>
              <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <table className="w-full text-sm">
                  <tbody className="divide-y divide-gray-50">
                    {closedVulns.map(v => (
                      <tr key={v.id} className="hover:bg-gray-50/50">
                        <td className="px-4 py-3">
                          <p className="font-medium text-gray-500">{v.title}</p>
                          {v.cve_id && <span className="text-xs font-mono bg-gray-50 text-gray-400 px-1.5 py-0.5 rounded">{v.cve_id}</span>}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[v.status]}`}>{v.status.replace("_", " ")}</span>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center gap-1 justify-end">
                            <button onClick={() => openEdit(v)} className="text-xs text-gray-400 hover:text-gray-700 px-2 py-1 rounded hover:bg-gray-100">Edit</button>
                            <button onClick={() => handleDelete(v.id)} className="text-xs text-red-300 hover:text-red-500 px-2 py-1 rounded hover:bg-red-50"><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Vulnerability" : "Add Vulnerability"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
                <input className="input" value={form.title ?? ""} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required placeholder="e.g. OpenSSL buffer overflow" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
                  <select className="input" value={form.severity ?? "medium"} onChange={e => setForm(p => ({ ...p, severity: e.target.value as Vulnerability["severity"] }))}>
                    {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                  <select className="input" value={form.status ?? "open"} onChange={e => setForm(p => ({ ...p, status: e.target.value as Vulnerability["status"] }))}>
                    {STATUSES.map(s => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">CVE ID</label>
                  <input className="input font-mono" value={form.cve_id ?? ""} onChange={e => setForm(p => ({ ...p, cve_id: e.target.value }))} placeholder="CVE-2024-XXXX" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Affected system</label>
                  <input className="input" value={form.affected_system ?? ""} onChange={e => setForm(p => ({ ...p, affected_system: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Discovered at</label>
                  <input type="date" className="input" value={form.discovered_at ? form.discovered_at.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, discovered_at: e.target.value || null }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Due date</label>
                  <input type="date" className="input" value={form.due_date ? form.due_date.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, due_date: e.target.value || null }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea className="input min-h-[70px]" value={form.description ?? ""} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Remediation notes</label>
                <textarea className="input min-h-[70px]" value={form.remediation_notes ?? ""} onChange={e => setForm(p => ({ ...p, remediation_notes: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Add vulnerability"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
