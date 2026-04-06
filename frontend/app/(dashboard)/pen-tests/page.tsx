"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  ShieldAlert, Plus, Trash2, X, ChevronDown, ChevronUp,
  ExternalLink, Pencil, RotateCcw,
} from "lucide-react";
import { toast } from "@/lib/toast";

const STATUS_STYLES: Record<string, string> = {
  scheduled: "bg-blue-50 text-blue-700",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-teal-50 text-teal-700",
  remediated: "bg-emerald-50 text-emerald-700",
};
const STATUS_LABELS: Record<string, string> = {
  scheduled: "Scheduled", in_progress: "In Progress", completed: "Completed", remediated: "Remediated",
};
const TYPE_LABELS: Record<string, string> = {
  external: "External", internal: "Internal", web_app: "Web App", api: "API", cloud: "Cloud",
};

const SEVERITY_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high: "bg-orange-100 text-orange-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-yellow-100 text-yellow-700",
  info: "bg-blue-100 text-blue-700",
};
const FINDING_STATUS_STYLES: Record<string, string> = {
  open: "bg-red-50 text-red-700",
  in_remediation: "bg-amber-50 text-amber-700",
  remediated: "bg-emerald-50 text-emerald-700",
  accepted: "bg-gray-100 text-gray-600",
};
const FINDING_STATUS_NEXT: Record<string, string> = {
  open: "in_remediation",
  in_remediation: "remediated",
  remediated: "accepted",
  accepted: "open",
};
const FINDING_STATUS_LABELS: Record<string, string> = {
  open: "Open", in_remediation: "In Remediation", remediated: "Remediated", accepted: "Accepted",
};

function SeverityPill({ severity, count }: { severity: string; count: number }) {
  if (!count) return null;
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[severity] ?? ""}`}>
      {severity.charAt(0).toUpperCase()}: {count}
    </span>
  );
}

function LogTestModal({
  onClose,
  onSave,
  initial,
}: {
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
  initial?: any;
}) {
  const [form, setForm] = useState({
    name: initial?.name ?? "",
    vendor_name: initial?.vendor_name ?? "",
    test_type: initial?.test_type ?? "external",
    scope: initial?.scope ?? "",
    started_at: initial?.started_at ? initial.started_at.slice(0, 10) : "",
    completed_at: initial?.completed_at ? initial.completed_at.slice(0, 10) : "",
    report_url: initial?.report_url ?? "",
    executive_summary: initial?.executive_summary ?? "",
    agency_company_id: initial?.agency_company_id ?? "",
  });
  const [agencies, setAgencies] = useState<{ id: string; display_name: string }[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getPentestAgencyDirectory()
      .then((list) => setAgencies(list.map((a: any) => ({ id: a.company_id, display_name: a.display_name }))))
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      await onSave({
        name: form.name,
        vendor_name: form.vendor_name || undefined,
        test_type: form.test_type,
        scope: form.scope || undefined,
        started_at: form.started_at || undefined,
        completed_at: form.completed_at || undefined,
        report_url: form.report_url || undefined,
        executive_summary: form.executive_summary || undefined,
        agency_company_id: form.agency_company_id || undefined,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 space-y-4 my-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">{initial ? "Edit Pen Test" : "Log Pen Test"}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Test name *</label>
            <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="e.g. Q1 2026 External Network Test" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Vendor / firm</label>
              <input value={form.vendor_name} onChange={e => setForm(f => ({ ...f, vendor_name: e.target.value }))} placeholder="e.g. Cobalt.io" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Test type</label>
              <select value={form.test_type} onChange={e => setForm(f => ({ ...f, test_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30">
                <option value="external">External Network</option>
                <option value="internal">Internal Network</option>
                <option value="web_app">Web Application</option>
                <option value="api">API</option>
                <option value="cloud">Cloud Infrastructure</option>
              </select>
            </div>
          </div>
          {agencies.length > 0 && (
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Assign to agency <span className="font-normal text-gray-400">(optional)</span></label>
              <select value={form.agency_company_id} onChange={e => setForm(f => ({ ...f, agency_company_id: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30">
                <option value="">— None —</option>
                {agencies.map((a) => <option key={a.id} value={a.id}>{a.display_name}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Scope</label>
            <textarea value={form.scope} onChange={e => setForm(f => ({ ...f, scope: e.target.value }))} rows={2} placeholder="e.g. All public-facing IP ranges, API endpoints…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Started</label>
              <input type="date" value={form.started_at} onChange={e => setForm(f => ({ ...f, started_at: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Completed</label>
              <input type="date" value={form.completed_at} onChange={e => setForm(f => ({ ...f, completed_at: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Report URL</label>
            <input value={form.report_url} onChange={e => setForm(f => ({ ...f, report_url: e.target.value }))} placeholder="https://…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Executive summary</label>
            <textarea value={form.executive_summary} onChange={e => setForm(f => ({ ...f, executive_summary: e.target.value }))} rows={3} placeholder="High-level findings overview…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving || !form.name.trim()} className="flex-1 bg-rose-500 hover:bg-rose-600 text-white rounded-xl py-2 text-sm font-semibold disabled:opacity-50">
            {saving ? "Saving…" : initial ? "Save changes" : "Log Test"}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddFindingModal({
  onClose,
  onSave,
}: {
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState({
    title: "",
    severity: "medium",
    description: "",
    recommendation: "",
    cvss_score: "",
    cve_id: "",
    ticket_url: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try {
      await onSave({
        title: form.title,
        severity: form.severity,
        description: form.description || undefined,
        recommendation: form.recommendation || undefined,
        cvss_score: form.cvss_score ? parseFloat(form.cvss_score) : undefined,
        cve_id: form.cve_id || undefined,
        ticket_url: form.ticket_url || undefined,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4 my-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">Add Finding</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Title *</label>
            <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="e.g. SQL injection in /api/search" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="col-span-1">
              <label className="block text-xs font-semibold text-gray-600 mb-1">Severity</label>
              <select value={form.severity} onChange={e => setForm(f => ({ ...f, severity: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30">
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
                <option value="info">Info</option>
              </select>
            </div>
            <div className="col-span-1">
              <label className="block text-xs font-semibold text-gray-600 mb-1">CVSS</label>
              <input type="number" min="0" max="10" step="0.1" value={form.cvss_score} onChange={e => setForm(f => ({ ...f, cvss_score: e.target.value }))} placeholder="0-10" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
            </div>
            <div className="col-span-1">
              <label className="block text-xs font-semibold text-gray-600 mb-1">CVE ID</label>
              <input value={form.cve_id} onChange={e => setForm(f => ({ ...f, cve_id: e.target.value }))} placeholder="CVE-…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Description</label>
            <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Recommendation</label>
            <textarea value={form.recommendation} onChange={e => setForm(f => ({ ...f, recommendation: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Ticket URL</label>
            <input value={form.ticket_url} onChange={e => setForm(f => ({ ...f, ticket_url: e.target.value }))} placeholder="https://linear.app/…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-500/30" />
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSave} disabled={saving || !form.title.trim()} className="flex-1 bg-rose-500 hover:bg-rose-600 text-white rounded-xl py-2 text-sm font-semibold disabled:opacity-50">
            {saving ? "Adding…" : "Add Finding"}
          </button>
        </div>
      </div>
    </div>
  );
}

function TestCard({
  test,
  onUpdate,
  onDelete,
}: {
  test: any;
  onUpdate: (t: any) => void;
  onDelete: (id: string) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [findings, setFindings] = useState<any[]>([]);
  const [loadingFindings, setLoadingFindings] = useState(false);
  const [showAddFinding, setShowAddFinding] = useState(false);
  const [editing, setEditing] = useState(false);
  const [remNotes, setRemNotes] = useState<Record<string, string>>({});

  const toggleExpand = async () => {
    if (!expanded && findings.length === 0) {
      setLoadingFindings(true);
      try {
        const detail = await api.getPenTestV2(test.id);
        setFindings(detail.findings ?? []);
        const notes: Record<string, string> = {};
        (detail.findings ?? []).forEach((f: any) => { notes[f.id] = f.remediation_notes ?? ""; });
        setRemNotes(notes);
      } catch { } finally { setLoadingFindings(false); }
    }
    setExpanded(e => !e);
  };

  const handleAddFinding = async (data: any) => {
    const finding = await api.addPenTestFindingV2(test.id, data);
    setFindings(prev => [...prev, finding]);
    setRemNotes(prev => ({ ...prev, [finding.id]: "" }));
    toast("Finding added");
  };

  const handleCycleStatus = async (finding: any) => {
    const next = FINDING_STATUS_NEXT[finding.status] ?? "open";
    try {
      const updated = await api.updatePenTestFindingV2(test.id, finding.id, {
        status: next,
        remediation_notes: remNotes[finding.id] || undefined,
      });
      setFindings(prev => prev.map(f => f.id === updated.id ? updated : f));
    } catch { toast("Failed to update", "error"); }
  };

  const handleDeleteFinding = async (findingId: string) => {
    try {
      await api.deletePenTestFindingV2(test.id, findingId);
      setFindings(prev => prev.filter(f => f.id !== findingId));
      toast("Finding removed");
    } catch { toast("Failed to delete", "error"); }
  };

  const sc = test.severity_counts ?? {};
  const dateRange = test.started_at
    ? `${new Date(test.started_at).toLocaleDateString()} → ${test.completed_at ? new Date(test.completed_at).toLocaleDateString() : "Ongoing"}`
    : "Dates not set";

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
      <div className="px-4 sm:px-5 py-4 flex flex-col sm:flex-row sm:items-start gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className="font-bold text-gray-900">{test.name}</span>
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[test.status] ?? ""}`}>
              {STATUS_LABELS[test.status] ?? test.status}
            </span>
            <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              {TYPE_LABELS[test.test_type] ?? test.test_type}
            </span>
          </div>
          {test.vendor_name && <p className="text-xs text-gray-400 mb-1">{test.vendor_name}</p>}
          <p className="text-xs text-gray-400 mb-2">{dateRange}</p>
          <div className="flex items-center gap-1.5 flex-wrap">
            <SeverityPill severity="critical" count={sc.critical ?? 0} />
            <SeverityPill severity="high" count={sc.high ?? 0} />
            <SeverityPill severity="medium" count={sc.medium ?? 0} />
            <SeverityPill severity="low" count={sc.low ?? 0} />
            <SeverityPill severity="info" count={sc.info ?? 0} />
            {(test.total_findings ?? 0) === 0 && <span className="text-[10px] text-gray-300">No findings</span>}
            {(test.open_count ?? 0) > 0 && (
              <span className="text-[10px] font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-full ml-1">
                {test.open_count} open
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={toggleExpand}
            className="text-xs font-semibold text-gray-500 hover:text-gray-700 border border-gray-200 px-2.5 py-1 rounded-lg flex items-center gap-1"
          >
            Findings {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
          <button onClick={() => setEditing(true)} className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors">
            <Pencil className="w-3.5 h-3.5" />
          </button>
          <button onClick={() => onDelete(test.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-100 bg-gray-50/40">
          <div className="px-5 pt-3 pb-2 flex items-center justify-between">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Findings ({findings.length})</p>
            <button
              onClick={() => setShowAddFinding(true)}
              className="flex items-center gap-1 text-xs font-semibold text-rose-600 hover:text-rose-700"
            >
              <Plus className="w-3 h-3" /> Add Finding
            </button>
          </div>

          {loadingFindings ? (
            <div className="flex items-center justify-center py-6">
              <div className="w-4 h-4 border-2 border-rose-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : findings.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-6">No findings yet. Click "+ Add Finding" to log one.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left px-5 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Title</th>
                    <th className="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Severity</th>
                    <th className="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Status</th>
                    <th className="text-left px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden md:table-cell">CVSS</th>
                    <th className="px-3 py-2" />
                  </tr>
                </thead>
                <tbody>
                  {findings.map((f: any) => (
                    <tr key={f.id} className="border-b border-gray-50 hover:bg-white transition-colors">
                      <td className="px-5 py-2.5">
                        <p className="font-medium text-gray-800 text-sm">{f.title}</p>
                        {f.cve_id && <p className="text-[10px] text-gray-400">{f.cve_id}</p>}
                        {f.ticket_url && (
                          <a href={f.ticket_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-sky-500 hover:text-sky-600 flex items-center gap-0.5">
                            <ExternalLink className="w-2.5 h-2.5" /> Ticket
                          </a>
                        )}
                        {(f.status === "in_remediation" || f.status === "remediated") && (
                          <textarea
                            value={remNotes[f.id] ?? ""}
                            onChange={e => setRemNotes(prev => ({ ...prev, [f.id]: e.target.value }))}
                            rows={1}
                            placeholder="Remediation notes…"
                            className="mt-1 w-full text-xs border border-gray-200 rounded-lg px-2 py-1 resize-none focus:outline-none focus:ring-1 focus:ring-rose-400/40"
                          />
                        )}
                      </td>
                      <td className="px-3 py-2.5">
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${SEVERITY_STYLES[f.severity] ?? ""}`}>
                          {f.severity}
                        </span>
                      </td>
                      <td className="px-3 py-2.5">
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${FINDING_STATUS_STYLES[f.status] ?? ""}`}>
                          {FINDING_STATUS_LABELS[f.status] ?? f.status}
                        </span>
                      </td>
                      <td className="px-3 py-2.5 text-xs text-gray-400 hidden md:table-cell">
                        {f.cvss_score != null ? f.cvss_score.toFixed(1) : "—"}
                      </td>
                      <td className="px-3 py-2.5">
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => handleCycleStatus(f)}
                            title={`Advance to: ${FINDING_STATUS_LABELS[FINDING_STATUS_NEXT[f.status]]}`}
                            className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
                          >
                            <RotateCcw className="w-3.5 h-3.5" />
                          </button>
                          <button onClick={() => handleDeleteFinding(f.id)} className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="h-3" />
        </div>
      )}

      {editing && (
        <LogTestModal
          initial={test}
          onClose={() => setEditing(false)}
          onSave={async (data) => {
            const updated = await api.updatePenTestV2(test.id, data);
            onUpdate(updated);
            setEditing(false);
          }}
        />
      )}
      {showAddFinding && (
        <AddFindingModal onClose={() => setShowAddFinding(false)} onSave={handleAddFinding} />
      )}
    </div>
  );
}

export default function PenTestsPage() {
  const [tests, setTests] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showLog, setShowLog] = useState(false);

  useEffect(() => {
    api.getPenTestsV2().then(setTests).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (data: any) => {
    const created = await api.createPenTestV2(data);
    setTests(prev => [created, ...prev]);
    toast("Pen test logged");
  };

  const handleUpdate = (updated: any) => {
    setTests(prev => prev.map(t => t.id === updated.id ? { ...t, ...updated } : t));
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deletePenTestV2(id);
      setTests(prev => prev.filter(t => t.id !== id));
      toast("Pen test deleted");
    } catch { toast("Failed to delete", "error"); }
  };

  const allFindings = tests.reduce((acc, t) => {
    const sc = t.severity_counts ?? {};
    return acc + (sc.critical ?? 0) + (sc.high ?? 0) + (sc.medium ?? 0) + (sc.low ?? 0) + (sc.info ?? 0);
  }, 0);
  const openFindings = tests.reduce((acc, t) => acc + (t.open_count ?? 0), 0);
  const criticalHigh = tests.reduce((acc, t) => {
    const sc = t.severity_counts ?? {};
    return acc + (sc.critical ?? 0) + (sc.high ?? 0);
  }, 0);
  const allRemediated = tests.filter(t => t.status === "remediated").length;

  return (
    <div className="animate-fade-in space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-500/20 ring-1 ring-rose-500/30">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Penetration Tests</h1>
              <p className="text-sm text-slate-400">SOC 2 CC9.1 — track security tests, findings, and remediation.</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-white">{tests.length}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Tests</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-red-400">{openFindings}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Open</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className={`text-2xl font-black ${criticalHigh > 0 ? "text-orange-400" : "text-slate-400"}`}>{criticalHigh}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Crit+High</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{allRemediated}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Remediated</span>
            </div>
            <button
              onClick={() => setShowLog(true)}
              className="flex items-center gap-1.5 bg-rose-500 hover:bg-rose-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" /> Log Test
            </button>
          </div>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-rose-500 border-t-transparent" />
        </div>
      ) : tests.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-2xl border border-dashed border-gray-200 bg-white text-center">
          <ShieldAlert className="w-8 h-8 text-gray-200" />
          <p className="text-sm font-medium text-gray-500">No penetration tests logged yet</p>
          <p className="text-xs text-gray-400">Log your pen tests to track findings and demonstrate annual testing for SOC 2.</p>
          <button onClick={() => setShowLog(true)} className="text-xs font-semibold text-rose-600 hover:text-rose-700">+ Log first test</button>
        </div>
      ) : (
        <div className="space-y-3">
          {tests.map(test => (
            <TestCard key={test.id} test={test} onUpdate={handleUpdate} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showLog && <LogTestModal onClose={() => setShowLog(false)} onSave={handleCreate} />}
    </div>
  );
}
