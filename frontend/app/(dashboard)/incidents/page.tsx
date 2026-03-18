"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Incident } from "@/lib/types";
import { Siren, Plus, Trash2, X, ChevronDown } from "lucide-react";

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
      } else {
        const created = await api.createIncident(form);
        setIncidents(prev => [created, ...prev]);
      }
      closeModal();
    } catch { /* silent */ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this incident?")) return;
    await api.deleteIncident(id);
    setIncidents(prev => prev.filter(i => i.id !== id));
  };

  const open = incidents.filter(i => i.status === "open" || i.status === "investigating");
  const closed = incidents.filter(i => i.status === "resolved" || i.status === "closed");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <Siren className="w-6 h-6 text-red-500" /> Incident Management
          </h1>
          <p className="text-sm text-gray-500 mt-1">Track and manage security incidents</p>
        </div>
        <button onClick={openCreate} className="btn-primary gap-2">
          <Plus className="w-4 h-4" /> New Incident
        </button>
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

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : incidents.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <Siren className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No incidents recorded</p>
          <p className="text-sm text-gray-400 mt-1">Create an incident to start tracking security events</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> New Incident</button>
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
