"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  GitMerge, Plus, Trash2, Pencil, X,
  ExternalLink, ChevronDown, ChevronUp,
} from "lucide-react";
import { toast } from "@/lib/toast";

// ── Style maps ────────────────────────────────────────────────────────────────

const RISK_STYLES: Record<string, string> = {
  critical: "bg-red-100 text-red-700",
  high:     "bg-orange-100 text-orange-700",
  medium:   "bg-amber-100 text-amber-700",
  low:      "bg-emerald-100 text-emerald-700",
};

const STATUS_STYLES: Record<string, string> = {
  draft:       "bg-gray-100 text-gray-600",
  submitted:   "bg-blue-100 text-blue-700",
  approved:    "bg-teal-100 text-teal-700",
  in_progress: "bg-violet-100 text-violet-700",
  deployed:    "bg-emerald-100 text-emerald-700",
  failed:      "bg-red-100 text-red-700",
  rejected:    "bg-red-100 text-red-700",
  closed:      "bg-slate-100 text-slate-600",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Draft", submitted: "Submitted", approved: "Approved",
  in_progress: "In Progress", deployed: "Deployed", failed: "Failed",
  rejected: "Rejected", closed: "Closed",
};

const TYPE_STYLES: Record<string, string> = {
  code:          "bg-violet-100 text-violet-700",
  infrastructure:"bg-blue-100 text-blue-700",
  configuration: "bg-amber-100 text-amber-700",
  access:        "bg-teal-100 text-teal-700",
  policy:        "bg-gray-100 text-gray-600",
  database:      "bg-orange-100 text-orange-700",
};

const TYPE_LABELS: Record<string, string> = {
  code: "Code", infrastructure: "Infrastructure", configuration: "Configuration",
  access: "Access", policy: "Policy", database: "Database",
};

const CHANGE_TYPES = ["code", "infrastructure", "configuration", "access", "policy", "database"];
const RISK_LEVELS = ["low", "medium", "high", "critical"];

const PIPELINE_STAGES = ["draft", "submitted", "approved", "in_progress", "deployed"];

// ── Modals ────────────────────────────────────────────────────────────────────

function RFCModal({
  initial,
  onClose,
  onSave,
}: {
  initial?: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [title, setTitle] = useState(initial?.title ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [changeType, setChangeType] = useState(initial?.change_type ?? "code");
  const [riskLevel, setRiskLevel] = useState(initial?.risk_level ?? "medium");
  const [requesterName, setRequesterName] = useState(initial?.requester_name ?? "");
  const [requesterEmail, setRequesterEmail] = useState(initial?.requester_email ?? "");
  const [scheduledAt, setScheduledAt] = useState(
    initial?.scheduled_at ? initial.scheduled_at.split("T")[0] : ""
  );
  const [rollbackPlan, setRollbackPlan] = useState(initial?.rollback_plan ?? "");
  const [ticketUrl, setTicketUrl] = useState(initial?.ticket_url ?? "");
  const [prUrl, setPrUrl] = useState(initial?.pr_url ?? "");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await onSave({
        title: title.trim(),
        description: description.trim() || undefined,
        change_type: changeType,
        risk_level: riskLevel,
        requester_name: requesterName.trim() || undefined,
        requester_email: requesterEmail.trim() || undefined,
        scheduled_at: scheduledAt || undefined,
        rollback_plan: rollbackPlan.trim() || undefined,
        ticket_url: ticketUrl.trim() || undefined,
        pr_url: prUrl.trim() || undefined,
      });
      onClose();
    } catch {
      toast("Failed to save RFC", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{initial ? "Edit RFC" : "New RFC"}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              placeholder="e.g. Deploy new authentication service"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Change Type</label>
              <select
                value={changeType}
                onChange={e => setChangeType(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {CHANGE_TYPES.map(t => <option key={t} value={t}>{TYPE_LABELS[t]}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
              <select
                value={riskLevel}
                onChange={e => setRiskLevel(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              >
                {RISK_LEVELS.map(r => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Requester Name</label>
              <input
                type="text"
                value={requesterName}
                onChange={e => setRequesterName(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Requester Email</label>
              <input
                type="email"
                value={requesterEmail}
                onChange={e => setRequesterEmail(e.target.value)}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scheduled Date</label>
            <input
              type="date"
              value={scheduledAt}
              onChange={e => setScheduledAt(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rollback Plan</label>
            <textarea
              value={rollbackPlan}
              onChange={e => setRollbackPlan(e.target.value)}
              rows={2}
              placeholder="Steps to revert if deployment fails..."
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Ticket URL</label>
              <input
                type="url"
                value={ticketUrl}
                onChange={e => setTicketUrl(e.target.value)}
                placeholder="https://jira.example.com/..."
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">PR URL</label>
              <input
                type="url"
                value={prUrl}
                onChange={e => setPrUrl(e.target.value)}
                placeholder="https://github.com/..."
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button
              type="submit"
              disabled={saving || !title.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-sky-600 text-white hover:bg-sky-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : initial ? "Save Changes" : "Create RFC"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ApproveModal({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (data: { approver_name: string; approver_email?: string }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onConfirm({ approver_name: name.trim(), approver_email: email.trim() || undefined });
      onClose();
    } catch {
      toast("Failed to approve", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-base font-semibold text-gray-900">Approve Change Request</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Approver Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
              required autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Approver Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50"
            >
              {saving ? "Approving..." : "Approve"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RejectModal({
  onClose,
  onConfirm,
}: {
  onClose: () => void;
  onConfirm: (data: { rejection_reason: string }) => Promise<void>;
}) {
  const [reason, setReason] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reason.trim()) return;
    setSaving(true);
    try {
      await onConfirm({ rejection_reason: reason.trim() });
      onClose();
    } catch {
      toast("Failed to reject", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-base font-semibold text-gray-900">Reject Change Request</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rejection Reason <span className="text-red-500">*</span></label>
            <textarea
              value={reason}
              onChange={e => setReason(e.target.value)}
              rows={3}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500 resize-none"
              required autoFocus
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600">Cancel</button>
            <button
              type="submit"
              disabled={saving || !reason.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 disabled:opacity-50"
            >
              {saving ? "Rejecting..." : "Reject"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Row ───────────────────────────────────────────────────────────────────────

function ChangeRow({
  cr,
  onRefresh,
  onEdit,
}: {
  cr: any;
  onRefresh: () => void;
  onEdit: (cr: any) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [acting, setActing] = useState(false);
  const [showApprove, setShowApprove] = useState(false);
  const [showReject, setShowReject] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function act(fn: () => Promise<any>, successMsg: string) {
    setActing(true);
    try {
      await fn();
      onRefresh();
      toast(successMsg);
    } catch {
      toast("Action failed", "error");
    } finally {
      setActing(false);
    }
  }

  return (
    <>
      <tr
        className={`border-b hover:bg-gray-50 transition-colors ${acting ? "opacity-60" : ""}`}
      >
        <td className="px-4 py-3">
          <button
            onClick={() => setExpanded(x => !x)}
            className="flex items-center gap-1.5 text-left"
          >
            {expanded ? <ChevronUp size={14} className="text-gray-400 shrink-0" /> : <ChevronDown size={14} className="text-gray-400 shrink-0" />}
            <span className="text-sm font-medium text-gray-900">{cr.title}</span>
          </button>
        </td>
        <td className="px-3 py-3">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${TYPE_STYLES[cr.change_type] ?? "bg-gray-100 text-gray-600"}`}>
            {TYPE_LABELS[cr.change_type] ?? cr.change_type}
          </span>
        </td>
        <td className="px-3 py-3">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${RISK_STYLES[cr.risk_level] ?? "bg-gray-100 text-gray-600"}`}>
            {cr.risk_level}
          </span>
        </td>
        <td className="px-3 py-3">
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[cr.status] ?? "bg-gray-100 text-gray-600"}`}>
            {STATUS_LABELS[cr.status] ?? cr.status}
          </span>
        </td>
        <td className="px-3 py-3 text-sm text-gray-500">{cr.requester_name || "—"}</td>
        <td className="px-3 py-3 text-xs text-gray-400">
          {cr.scheduled_at ? new Date(cr.scheduled_at).toLocaleDateString() : "—"}
        </td>
        <td className="px-3 py-3">
          <div className="flex items-center gap-1">
            {cr.ticket_url && (
              <a href={cr.ticket_url} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-sky-600" title="Ticket">
                <ExternalLink size={13} />
              </a>
            )}
            {cr.pr_url && (
              <a href={cr.pr_url} target="_blank" rel="noreferrer" className="text-gray-400 hover:text-violet-600" title="PR">
                <ExternalLink size={13} />
              </a>
            )}
          </div>
        </td>
        <td className="px-3 py-3">
          <div className="flex items-center gap-1 flex-wrap">
            {cr.status === "draft" && (
              <button
                onClick={() => act(() => api.submitChangeRequest(cr.id), "Submitted")}
                className="text-xs font-medium px-2 py-1 rounded bg-blue-100 text-blue-700 hover:bg-blue-200"
              >
                Submit
              </button>
            )}
            {cr.status === "submitted" && (
              <>
                <button
                  onClick={() => setShowApprove(true)}
                  className="text-xs font-medium px-2 py-1 rounded bg-teal-100 text-teal-700 hover:bg-teal-200"
                >
                  Approve
                </button>
                <button
                  onClick={() => setShowReject(true)}
                  className="text-xs font-medium px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
                >
                  Reject
                </button>
              </>
            )}
            {cr.status === "approved" && (
              <button
                onClick={() => act(() => api.startChangeRequest(cr.id), "Started")}
                className="text-xs font-medium px-2 py-1 rounded bg-violet-100 text-violet-700 hover:bg-violet-200"
              >
                Start
              </button>
            )}
            {cr.status === "in_progress" && (
              <>
                <button
                  onClick={() => act(() => api.deployChangeRequest(cr.id), "Deployed")}
                  className="text-xs font-medium px-2 py-1 rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200"
                >
                  Deployed
                </button>
                <button
                  onClick={() => act(() => api.failChangeRequest(cr.id), "Marked failed")}
                  className="text-xs font-medium px-2 py-1 rounded bg-red-100 text-red-700 hover:bg-red-200"
                >
                  Failed
                </button>
              </>
            )}
            {(cr.status === "deployed" || cr.status === "failed") && (
              <button
                onClick={() => act(() => api.closeChangeRequest(cr.id), "Closed")}
                className="text-xs font-medium px-2 py-1 rounded bg-slate-100 text-slate-600 hover:bg-slate-200"
              >
                Close
              </button>
            )}
            <button
              onClick={() => onEdit(cr)}
              className="p-1 text-gray-400 hover:text-sky-600 rounded"
              title="Edit"
            >
              <Pencil size={13} />
            </button>
            {cr.status === "draft" && (
              confirmDelete ? (
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => act(() => api.deleteChangeRequest(cr.id), "Deleted")}
                    className="text-xs text-red-600 font-medium px-1.5 py-0.5 border border-red-200 rounded"
                  >
                    Confirm
                  </button>
                  <button onClick={() => setConfirmDelete(false)} className="text-xs text-gray-400">Cancel</button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmDelete(true)}
                  className="p-1 text-gray-400 hover:text-red-500 rounded"
                  title="Delete"
                >
                  <Trash2 size={13} />
                </button>
              )
            )}
          </div>
        </td>
      </tr>

      {/* Expanded row */}
      {expanded && (
        <tr className="bg-slate-50">
          <td colSpan={8} className="px-8 py-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              {cr.description && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Description</p>
                  <p className="text-gray-700">{cr.description}</p>
                </div>
              )}
              {cr.rollback_plan && (
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Rollback Plan</p>
                  <p className="text-gray-700">{cr.rollback_plan}</p>
                </div>
              )}
              {cr.rejection_reason && (
                <div>
                  <p className="text-xs font-semibold text-red-400 uppercase tracking-wide mb-1">Rejection Reason</p>
                  <p className="text-red-700">{cr.rejection_reason}</p>
                </div>
              )}
              <div>
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-1">Timeline</p>
                <div className="space-y-0.5 text-xs text-gray-500">
                  <p>Created: {new Date(cr.created_at).toLocaleString()}</p>
                  {cr.approved_at && <p>Approved: {new Date(cr.approved_at).toLocaleString()} by {cr.approver_name}</p>}
                  {cr.rejected_at && <p>Rejected: {new Date(cr.rejected_at).toLocaleString()}</p>}
                  {cr.deployed_at && <p>Deployed: {new Date(cr.deployed_at).toLocaleString()}</p>}
                  {cr.closed_at && <p>Closed: {new Date(cr.closed_at).toLocaleString()}</p>}
                </div>
              </div>
            </div>
          </td>
        </tr>
      )}

      {showApprove && (
        <ApproveModal
          onClose={() => setShowApprove(false)}
          onConfirm={async data => {
            await api.approveChangeRequest(cr.id, data);
            onRefresh();
            toast("Approved");
          }}
        />
      )}
      {showReject && (
        <RejectModal
          onClose={() => setShowReject(false)}
          onConfirm={async data => {
            await api.rejectChangeRequest(cr.id, data);
            onRefresh();
            toast("Rejected");
          }}
        />
      )}
    </>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function ChangeManagementPage() {
  const [changeRequests, setChangeRequests] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [showNew, setShowNew] = useState(false);
  const [editCr, setEditCr] = useState<any>(null);

  async function load() {
    setLoading(true);
    try {
      const [crs, s] = await Promise.all([
        api.getChangeRequests(statusFilter ? { status: statusFilter } : undefined),
        api.getChangeRequestStats(),
      ]);
      setChangeRequests(crs);
      setStats(s);
    } catch {
      toast("Failed to load change requests", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [statusFilter]);

  async function handleCreate(data: any) {
    await api.createChangeRequest(data);
    await load();
    toast("RFC created");
  }

  async function handleUpdate(data: any) {
    await api.updateChangeRequest(editCr.id, data);
    await load();
    toast("RFC updated");
  }

  const openCount = stats?.open_count ?? 0;
  const deployedCount = stats?.by_status?.deployed ?? 0;
  const failedCount = stats?.by_status?.failed ?? 0;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 text-white">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-sky-600/30 rounded-xl">
                <GitMerge size={22} className="text-sky-400" />
              </div>
              <h1 className="text-2xl font-bold">Change Management</h1>
            </div>
            <p className="text-gray-400 text-sm">
              SOC 2 CC8.1 — track infrastructure and code changes from request to deployment
            </p>
            <div className="flex gap-6 mt-4">
              <div>
                <div className="text-xl font-bold text-sky-400">{openCount}</div>
                <div className="text-xs text-gray-400">Open</div>
              </div>
              <div>
                <div className="text-xl font-bold text-emerald-400">{deployedCount}</div>
                <div className="text-xs text-gray-400">Deployed</div>
              </div>
              <div>
                <div className="text-xl font-bold text-red-400">{failedCount}</div>
                <div className="text-xs text-gray-400">Failed</div>
              </div>
              <div>
                <div className="text-xl font-bold text-gray-400">—</div>
                <div className="text-xs text-gray-400">Avg Cycle</div>
              </div>
            </div>
          </div>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-700 text-white text-sm font-medium transition-colors shrink-0"
          >
            <Plus size={16} /> New RFC
          </button>
        </div>
      </div>

      {/* Pipeline bar */}
      {stats && (
        <div className="bg-white rounded-2xl border shadow-sm p-4">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Pipeline</p>
          <div className="flex items-center gap-1 flex-wrap">
            <button
              onClick={() => setStatusFilter(null)}
              className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${
                statusFilter === null ? "bg-sky-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              All ({stats.total})
            </button>
            {PIPELINE_STAGES.map((s, i) => (
              <div key={s} className="flex items-center gap-1">
                {i > 0 && <span className="text-gray-300 text-xs">→</span>}
                <button
                  onClick={() => setStatusFilter(statusFilter === s ? null : s)}
                  className={`text-xs font-medium px-3 py-1.5 rounded-full transition-colors ${
                    statusFilter === s ? "bg-sky-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {STATUS_LABELS[s]} ({stats.by_status[s] ?? 0})
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Table */}
      <div className="bg-white rounded-2xl border shadow-sm overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600" />
          </div>
        ) : changeRequests.length === 0 ? (
          <div className="p-16 text-center">
            <GitMerge size={40} className="mx-auto mb-4 text-sky-300" />
            <h2 className="text-lg font-semibold text-gray-700 mb-2">No change requests</h2>
            <p className="text-sm text-gray-400 mb-6">
              Log every code, infrastructure, and configuration change for SOC 2 CC8.1 compliance.
            </p>
            <button
              onClick={() => setShowNew(true)}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-600 text-white text-sm font-medium hover:bg-sky-700"
            >
              <Plus size={16} /> New RFC
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Title</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Risk</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Requester</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Scheduled</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Links</th>
                  <th className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">Actions</th>
                </tr>
              </thead>
              <tbody>
                {changeRequests.map(cr => (
                  <ChangeRow
                    key={cr.id}
                    cr={cr}
                    onRefresh={load}
                    onEdit={setEditCr}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showNew && (
        <RFCModal
          onClose={() => setShowNew(false)}
          onSave={handleCreate}
        />
      )}
      {editCr && (
        <RFCModal
          initial={editCr}
          onClose={() => setEditCr(null)}
          onSave={handleUpdate}
        />
      )}
    </div>
  );
}
