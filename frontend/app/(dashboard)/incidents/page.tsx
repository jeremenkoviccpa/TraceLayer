"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Incident } from "@/lib/types";
import { Siren, Plus, Trash2, X, ChevronDown, Sparkles, RefreshCw, AlertOctagon } from "lucide-react";
import { toast } from "@/lib/toast";

const SEVERITIES = ["critical", "high", "medium", "low"] as const;
const STATUSES = ["open", "investigating", "resolved", "closed"] as const;

const SEV_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
};

const STATUS_STYLES: Record<string, string> = {
  open:          "bg-red-50 text-red-600",
  investigating: "bg-amber-50 text-amber-700",
  resolved:      "bg-emerald-50 text-emerald-700",
  closed:        "bg-gray-100 text-gray-500",
};

const EMPTY: Partial<Incident> = {
  title: "", description: "", severity: "medium", status: "open",
  detected_at: null, resolved_at: null, affected_systems: "", root_cause: "", lessons_learned: "",
};

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Incident | null>(null);
  const [form, setForm]           = useState<Partial<Incident>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [expanded, setExpanded]   = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [detectMsg] = useState<string | null>(null); // toasts used instead

  useEffect(() => {
    api.getIncidents().then(setIncidents).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm(EMPTY); setShowModal(true); };
  const openEdit   = (i: Incident) => { setEditing(i); setForm(i); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); setForm(EMPTY); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateIncident(editing.id, form);
        setIncidents(prev => prev.map(i => i.id === updated.id ? updated : i));
        toast("Incident updated");
      } else {
        const created = await api.createIncident(form);
        setIncidents(prev => [created, ...prev]);
        toast("Incident created");
      }
      closeModal();
    } catch { toast("Failed to save incident", "error"); } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this incident?")) return;
    try {
      await api.deleteIncident(id);
      setIncidents(prev => prev.filter(i => i.id !== id));
      toast("Incident deleted");
    } catch { toast("Failed to delete incident", "error"); }
  };

  const handleDetect = async () => {
    setDetecting(true);
    try {
      const result = await api.runIncidentDetection();
      const fresh = await api.getIncidents();
      setIncidents(fresh);
      toast(result.created > 0 ? `${result.created} incident${result.created > 1 ? "s" : ""} detected` : "No new incidents found");
    } catch {
      toast("Detection failed", "error");
    } finally {
      setDetecting(false);
    }
  };

  const open = incidents.filter(i => i.status === "open" || i.status === "investigating");
  const closed = incidents.filter(i => i.status === "resolved" || i.status === "closed");
  const certinOverdue = open.filter(i =>
    i.detected_at &&
    !i.certin_reported_at &&
    Math.floor((Date.now() - new Date(i.detected_at).getTime()) / 3600000) > 6
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          <Siren className="w-5 h-5 text-red-500 shrink-0" />
          <div className="min-w-0">
            <h1 className="text-lg sm:text-2xl font-bold text-gray-900 leading-tight truncate">Incident Management</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Track and manage security incidents</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
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
            <span className="hidden sm:inline">New Incident</span>
            <span className="sm:hidden">New</span>
          </button>
        </div>
      </div>

      {/* How detection works */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="grid sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-gray-50">
          <div className="p-5">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">Auto-detected from</p>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-orange-100 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700">Pen test findings</p>
                  <p className="text-xs text-gray-400 mt-0.5">Any completed pen test with critical or high severity findings auto-creates an incident.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-red-100 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-500" />
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700">Long-running critical vulnerabilities</p>
                  <p className="text-xs text-gray-400 mt-0.5">Critical vulnerabilities left open for 60+ days are automatically escalated to incidents.</p>
                </div>
              </div>
            </div>
          </div>
          <div className="p-5">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">How detection runs</p>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-violet-100 flex items-center justify-center shrink-0">
                  <Sparkles className="w-2.5 h-2.5 text-violet-500" />
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700">Runs nightly at 02:15 UTC</p>
                  <p className="text-xs text-gray-400 mt-0.5">The scheduler scans all pen tests and vulnerabilities automatically — no action needed.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span className="mt-0.5 w-5 h-5 rounded-full bg-gray-100 flex items-center justify-center shrink-0">
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-400" />
                </span>
                <div>
                  <p className="text-sm font-medium text-gray-700">Or trigger it manually</p>
                  <p className="text-xs text-gray-400 mt-0.5">Use <span className="font-semibold text-gray-600">Auto-detect</span> in the top bar to run detection immediately, or log incidents yourself.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {SEVERITIES.map(sev => {
          const count = incidents.filter(i => i.severity === sev && (i.status === "open" || i.status === "investigating")).length;
          return (
            <div key={sev} className="bg-white rounded-xl border border-gray-100 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold mb-1">{sev}</p>
              <p className={`text-2xl font-bold ${count > 0 ? SEV_STYLES[sev].split(" ")[1] : "text-gray-400"}`}>{count}</p>
              <p className="text-xs text-gray-400">open</p>
            </div>
          );
        })}
      </div>

      {certinOverdue.length > 0 && (
        <div className="flex items-center gap-3 bg-blue-700 text-white text-sm font-medium px-4 py-3 rounded-2xl shadow-sm">
          <AlertOctagon className="w-4 h-4 shrink-0" />
          <span>
            🇮🇳 {certinOverdue.length} incident{certinOverdue.length > 1 ? "s" : ""} past CERT-In 6-hour reporting deadline (Dir. 1) — log your CERT-In report reference in each incident
          </span>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : incidents.length === 0 ? (
        <div className="text-center py-14 bg-white rounded-2xl border border-gray-100">
          <Siren className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-700 font-semibold">No incidents recorded yet</p>
          <p className="text-sm text-gray-400 mt-1.5 max-w-sm mx-auto">
            SOC 2 CC7.3 requires you to document security incidents. Zero incidents looks suspicious to auditors — it means you&apos;re not monitoring, not that you&apos;re perfect.
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            <button onClick={openCreate} className="btn-primary gap-2 text-xs !py-2"><Plus className="w-3.5 h-3.5" /> New Incident</button>
            <button onClick={handleDetect} disabled={detecting} className="btn-secondary gap-2 text-xs !py-2 disabled:opacity-50">
              {detecting ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Auto-detect now
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {open.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Active ({open.length})</h2>
              <div className="space-y-2">
                {open.map(incident => (
                  <IncidentCard key={incident.id} incident={incident} expanded={expanded === incident.id} onToggle={() => setExpanded(p => p === incident.id ? null : incident.id)} onEdit={openEdit} onDelete={handleDelete} />
                ))}
              </div>
            </section>
          )}
          {closed.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Closed ({closed.length})</h2>
              <div className="space-y-2">
                {closed.map(incident => (
                  <IncidentCard key={incident.id} incident={incident} expanded={expanded === incident.id} onToggle={() => setExpanded(p => p === incident.id ? null : incident.id)} onEdit={openEdit} onDelete={handleDelete} />
                ))}
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
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Incident" : "New Incident"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
                <input className="input" value={form.title ?? ""} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required placeholder="e.g. Unauthorized access attempt" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
                  <select className="input" value={form.severity ?? "medium"} onChange={e => setForm(p => ({ ...p, severity: e.target.value as Incident["severity"] }))}>
                    {SEVERITIES.map(s => <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
                  <select className="input" value={form.status ?? "open"} onChange={e => setForm(p => ({ ...p, status: e.target.value as Incident["status"] }))}>
                    {STATUSES.map(s => <option key={s} value={s}>{s.replace("_", " ").replace(/\b\w/g, c => c.toUpperCase())}</option>)}
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
                <textarea className="input min-h-[80px]" value={form.description ?? ""} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} placeholder="What happened?" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Detected at</label>
                  <input type="datetime-local" className="input" value={form.detected_at ? form.detected_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, detected_at: e.target.value || null }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Resolved at</label>
                  <input type="datetime-local" className="input" value={form.resolved_at ? form.resolved_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, resolved_at: e.target.value || null }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Affected systems</label>
                <input className="input" value={form.affected_systems ?? ""} onChange={e => setForm(p => ({ ...p, affected_systems: e.target.value }))} placeholder="e.g. Production API, Auth service" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Root cause</label>
                <textarea className="input min-h-[60px]" value={form.root_cause ?? ""} onChange={e => setForm(p => ({ ...p, root_cause: e.target.value }))} />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Lessons learned</label>
                <textarea className="input min-h-[60px]" value={form.lessons_learned ?? ""} onChange={e => setForm(p => ({ ...p, lessons_learned: e.target.value }))} />
              </div>
              <div className="border-t border-gray-100 pt-3">
                <p className="text-xs font-semibold text-blue-700 mb-2">🇮🇳 CERT-In Reporting (Dir. 1) — 6-hour deadline</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Reported to CERT-In At</label>
                    <input type="datetime-local" className="input" value={form.certin_reported_at ? form.certin_reported_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, certin_reported_at: e.target.value || null }))} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">CERT-In Reference Number</label>
                    <input type="text" className="input" placeholder="e.g. CERTIN-2024-001234" value={form.certin_ref_number ?? ""} onChange={e => setForm(p => ({ ...p, certin_ref_number: e.target.value || null }))} />
                  </div>
                </div>
              </div>
              <div className="border-t border-gray-100 pt-3">
                <p className="text-xs font-semibold text-indigo-700 mb-2">🇪🇺 NIS2 Reporting (Art. 23) — 3-stage deadline</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Early Warning At <span className="text-gray-400 font-normal">(24h)</span></label>
                    <input type="datetime-local" className="input" value={form.nis2_early_warning_at ? form.nis2_early_warning_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, nis2_early_warning_at: e.target.value || null }))} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Incident Notification At <span className="text-gray-400 font-normal">(72h)</span></label>
                    <input type="datetime-local" className="input" value={form.nis2_notified_at ? form.nis2_notified_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, nis2_notified_at: e.target.value || null }))} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Final Report At <span className="text-gray-400 font-normal">(1 month)</span></label>
                    <input type="datetime-local" className="input" value={form.nis2_final_report_at ? form.nis2_final_report_at.substring(0, 16) : ""} onChange={e => setForm(p => ({ ...p, nis2_final_report_at: e.target.value || null }))} />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">CSIRT Reference Number</label>
                    <input type="text" className="input" placeholder="e.g. CSIRT-2024-001234" value={form.nis2_ref_number ?? ""} onChange={e => setForm(p => ({ ...p, nis2_ref_number: e.target.value || null }))} />
                  </div>
                </div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Create incident"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function IncidentCard({ incident, expanded, onToggle, onEdit, onDelete }: {
  incident: Incident;
  expanded: boolean;
  onToggle: () => void;
  onEdit: (i: Incident) => void;
  onDelete: (id: string) => void;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={onToggle}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${SEV_STYLES[incident.severity]}`}>
              {incident.severity}
            </span>
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[incident.status]}`}>
              {incident.status.replace("_", " ")}
            </span>
            <span className="text-sm font-medium text-gray-900 truncate">{incident.title}</span>
            {incident.auto_detected && (
              <span className="inline-flex items-center gap-1 rounded-full bg-violet-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wide text-violet-600 border border-violet-100 shrink-0">
                <Sparkles className="h-2.5 w-2.5" />Auto
              </span>
            )}
          </div>
          {incident.detected_at && (
            <p className="text-xs text-gray-400 mt-0.5">Detected {new Date(incident.detected_at).toLocaleDateString()}</p>
          )}
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </div>
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-50 space-y-3 pt-3">
          {incident.description && <p className="text-sm text-gray-600">{incident.description}</p>}
          {incident.affected_systems && (
            <div><p className="text-xs font-semibold text-gray-500 mb-1">Affected systems</p><p className="text-sm text-gray-700">{incident.affected_systems}</p></div>
          )}
          {incident.root_cause && (
            <div><p className="text-xs font-semibold text-gray-500 mb-1">Root cause</p><p className="text-sm text-gray-700">{incident.root_cause}</p></div>
          )}
          {incident.lessons_learned && (
            <div><p className="text-xs font-semibold text-gray-500 mb-1">Lessons learned</p><p className="text-sm text-gray-700">{incident.lessons_learned}</p></div>
          )}
          {(incident.certin_reported_at || incident.certin_ref_number) && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-blue-700 mb-1.5">🇮🇳 CERT-In Reported (Dir. 1)</p>
              <div className="flex flex-wrap gap-4">
                {incident.certin_reported_at && (
                  <div>
                    <p className="text-[10px] text-blue-500 mb-0.5">Reported at</p>
                    <p className="text-xs text-blue-800 font-medium">{new Date(incident.certin_reported_at).toLocaleString()}</p>
                  </div>
                )}
                {incident.certin_ref_number && (
                  <div>
                    <p className="text-[10px] text-blue-500 mb-0.5">Reference</p>
                    <p className="text-xs text-blue-800 font-medium">{incident.certin_ref_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          {(incident.nis2_early_warning_at || incident.nis2_notified_at || incident.nis2_final_report_at || incident.nis2_ref_number) && (
            <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-indigo-700 mb-1.5">🇪🇺 NIS2 Reporting (Art. 23)</p>
              <div className="flex flex-wrap gap-4">
                {incident.nis2_early_warning_at && (
                  <div>
                    <p className="text-[10px] text-indigo-500 mb-0.5">Early Warning (24h)</p>
                    <p className="text-xs text-indigo-800 font-medium">{new Date(incident.nis2_early_warning_at).toLocaleString()}</p>
                  </div>
                )}
                {incident.nis2_notified_at && (
                  <div>
                    <p className="text-[10px] text-indigo-500 mb-0.5">Notification (72h)</p>
                    <p className="text-xs text-indigo-800 font-medium">{new Date(incident.nis2_notified_at).toLocaleString()}</p>
                  </div>
                )}
                {incident.nis2_final_report_at && (
                  <div>
                    <p className="text-[10px] text-indigo-500 mb-0.5">Final Report (1 month)</p>
                    <p className="text-xs text-indigo-800 font-medium">{new Date(incident.nis2_final_report_at).toLocaleString()}</p>
                  </div>
                )}
                {incident.nis2_ref_number && (
                  <div>
                    <p className="text-[10px] text-indigo-500 mb-0.5">CSIRT Reference</p>
                    <p className="text-xs text-indigo-800 font-medium">{incident.nis2_ref_number}</p>
                  </div>
                )}
              </div>
            </div>
          )}
          <div className="flex gap-2 pt-1">
            <button onClick={() => onEdit(incident)} className="btn-secondary text-xs py-1.5 px-3">Edit</button>
            <button onClick={() => onDelete(incident.id)} className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
