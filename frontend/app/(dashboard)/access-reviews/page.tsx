"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  UserCheck, Plus, Trash2, X, Check, ChevronLeft, Calendar,
  AlertTriangle, CheckCircle2, Clock, Users,
} from "lucide-react";
import { toast } from "@/lib/toast";

const FRAMEWORK_LABELS: Record<string, string> = {
  soc2: "SOC 2", iso27001: "ISO 27001", gdpr: "GDPR", hipaa: "HIPAA",
  pci_dss: "PCI DSS", ccpa: "CCPA", nist_csf: "NIST CSF",
  dpdp: "DPDP Act", cert_in: "CERT-In", lpdp: "Serbian LPDP",
  nis2: "NIS2", iso42001: "ISO 42001",
};
const PERIOD_LABELS: Record<string, string> = {
  monthly: "Monthly", quarterly: "Quarterly", semi_annual: "Semi-annual", annual: "Annual",
};
const SYSTEM_SUGGESTIONS = [
  "AWS Production", "GitHub", "Okta", "Google Workspace", "Slack", "Linear", "Jira",
];

function FrameworkBadge({ fw }: { fw: string }) {
  return (
    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 uppercase tracking-wide">
      {FRAMEWORK_LABELS[fw] ?? fw}
    </span>
  );
}

function PeriodBadge({ period }: { period: string }) {
  return (
    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
      {PERIOD_LABELS[period] ?? period}
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === "completed") {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
        <CheckCircle2 className="w-3 h-3" /> Completed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
      <Clock className="w-3 h-3" /> In Progress
    </span>
  );
}

function ProgressBar({ reviewed, total }: { reviewed: number; total: number }) {
  const pct = total === 0 ? 0 : Math.round((reviewed / total) * 100);
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${pct === 100 ? "bg-emerald-500" : "bg-sky-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-gray-500 shrink-0">{reviewed}/{total}</span>
    </div>
  );
}

function DecisionButton({
  decision,
  current,
  onClick,
}: {
  decision: "approved" | "revoked" | "pending";
  current: string;
  onClick: () => void;
}) {
  const isActive = current === decision;
  const styles: Record<string, string> = {
    approved: isActive
      ? "bg-emerald-500 text-white"
      : "text-gray-400 hover:bg-emerald-50 hover:text-emerald-600 border border-gray-200",
    revoked: isActive
      ? "bg-red-500 text-white"
      : "text-gray-400 hover:bg-red-50 hover:text-red-600 border border-gray-200",
    pending: isActive
      ? "bg-gray-200 text-gray-600"
      : "text-gray-300 hover:bg-gray-100 hover:text-gray-500 border border-gray-200",
  };
  const labels: Record<string, string> = { approved: "✓ Approve", revoked: "✗ Revoke", pending: "— Pending" };
  return (
    <button
      onClick={onClick}
      className={`text-[11px] font-semibold px-2 py-1 rounded-lg transition-all ${styles[decision]}`}
    >
      {labels[decision]}
    </button>
  );
}

function NewReviewModal({
  onClose,
  onSave,
}: {
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState({
    name: "",
    framework: "soc2",
    review_period: "quarterly",
    due_date: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      await onSave({
        name: form.name,
        framework: form.framework,
        review_period: form.review_period,
        due_date: form.due_date || undefined,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">New Access Review</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Review name *</label>
            <input
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
              placeholder="e.g. Q2 2026 Access Review"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Framework</label>
              <select value={form.framework} onChange={e => setForm(f => ({ ...f, framework: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30">
                <option value="soc2">SOC 2</option>
                <option value="iso27001">ISO 27001</option>
                <option value="gdpr">GDPR</option>
                <option value="hipaa">HIPAA</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Period</label>
              <select value={form.review_period} onChange={e => setForm(f => ({ ...f, review_period: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30">
                <option value="monthly">Monthly</option>
                <option value="quarterly">Quarterly</option>
                <option value="semi_annual">Semi-annual</option>
                <option value="annual">Annual</option>
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Due date</label>
            <input
              type="date"
              value={form.due_date}
              onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button
            onClick={handleSave}
            disabled={saving || !form.name.trim()}
            className="flex-1 bg-sky-500 hover:bg-sky-600 text-white rounded-xl py-2 text-sm font-semibold disabled:opacity-50"
          >
            {saving ? "Creating…" : "Create Review"}
          </button>
        </div>
      </div>
    </div>
  );
}

function AddUserModal({
  onClose,
  onSave,
}: {
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState({
    user_email: "",
    user_name: "",
    system_name: "",
    role_or_permission: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.user_email.trim() || !form.system_name.trim()) return;
    setSaving(true);
    try {
      await onSave({
        user_email: form.user_email,
        user_name: form.user_name || undefined,
        system_name: form.system_name,
        role_or_permission: form.role_or_permission || undefined,
      });
      onClose();
    } catch { } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">Add User to Review</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">User email *</label>
            <input
              type="email"
              value={form.user_email}
              onChange={e => setForm(f => ({ ...f, user_email: e.target.value }))}
              placeholder="alice@company.com"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">User name</label>
            <input
              value={form.user_name}
              onChange={e => setForm(f => ({ ...f, user_name: e.target.value }))}
              placeholder="Alice Johnson"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">System *</label>
            <input
              value={form.system_name}
              onChange={e => setForm(f => ({ ...f, system_name: e.target.value }))}
              placeholder="e.g. AWS Production"
              list="system-suggestions"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
            <datalist id="system-suggestions">
              {SYSTEM_SUGGESTIONS.map(s => <option key={s} value={s} />)}
            </datalist>
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Role / permission</label>
            <input
              value={form.role_or_permission}
              onChange={e => setForm(f => ({ ...f, role_or_permission: e.target.value }))}
              placeholder="e.g. Admin, ReadOnly, Deploy"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
            />
          </div>
        </div>

        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button
            onClick={handleSave}
            disabled={saving || !form.user_email.trim() || !form.system_name.trim()}
            className="flex-1 bg-sky-500 hover:bg-sky-600 text-white rounded-xl py-2 text-sm font-semibold disabled:opacity-50"
          >
            {saving ? "Adding…" : "Add User"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AccessReviewsPage() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewModal, setShowNewModal] = useState(false);
  const [showAddUser, setShowAddUser] = useState(false);
  const [selectedReview, setSelectedReview] = useState<any | null>(null);
  const [reviewDetail, setReviewDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [completing, setCompleting] = useState(false);

  useEffect(() => {
    api.getAccessReviewsV2().then(setReviews).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const openDetail = async (review: any) => {
    setSelectedReview(review);
    setDetailLoading(true);
    try {
      const detail = await api.getAccessReviewV2(review.id);
      setReviewDetail(detail);
    } catch { } finally { setDetailLoading(false); }
  };

  const handleCreate = async (data: any) => {
    const created = await api.createAccessReviewV2(data);
    setReviews(prev => [created, ...prev]);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteAccessReviewV2(id);
      setReviews(prev => prev.filter(r => r.id !== id));
      toast("Review deleted");
    } catch { toast("Failed to delete", "error"); }
  };

  const handleAddUser = async (data: any) => {
    if (!selectedReview) return;
    const item = await api.addAccessReviewItemV2(selectedReview.id, data);
    setReviewDetail((prev: any) => prev ? { ...prev, items: [...(prev.items ?? []), item], total_items: (prev.total_items ?? 0) + 1 } : prev);
  };

  const handleDecision = async (itemId: string, decision: string, notes?: string) => {
    if (!selectedReview) return;
    try {
      const updated = await api.updateAccessReviewItemV2(selectedReview.id, itemId, { decision, notes });
      setReviewDetail((prev: any) => {
        if (!prev) return prev;
        const items = prev.items.map((i: any) => i.id === itemId ? updated : i);
        const reviewed = items.filter((i: any) => i.decision !== "pending").length;
        return { ...prev, items, reviewed_items: reviewed };
      });
      setReviews(rList => rList.map(r => {
        if (r.id !== selectedReview.id) return r;
        const reviewed = (reviewDetail?.items ?? []).filter((i: any) => i.decision !== "pending").length;
        return { ...r, reviewed_items: reviewed };
      }));
    } catch { toast("Failed to update", "error"); }
  };

  const handleDeleteItem = async (itemId: string) => {
    if (!selectedReview) return;
    try {
      await api.deleteAccessReviewItemV2(selectedReview.id, itemId);
      setReviewDetail((prev: any) => {
        if (!prev) return prev;
        const items = prev.items.filter((i: any) => i.id !== itemId);
        return { ...prev, items, total_items: items.length, reviewed_items: items.filter((i: any) => i.decision !== "pending").length };
      });
    } catch { toast("Failed to delete item", "error"); }
  };

  const handleComplete = async () => {
    if (!selectedReview) return;
    setCompleting(true);
    try {
      const updated = await api.completeAccessReviewV2(selectedReview.id);
      setReviewDetail((prev: any) => prev ? { ...prev, ...updated } : prev);
      setReviews(prev => prev.map(r => r.id === updated.id ? { ...r, status: "completed", completed_at: updated.completed_at } : r));
      toast("Review completed");
    } catch (e: any) {
      toast(e?.message ?? "Cannot complete review", "error");
    } finally { setCompleting(false); }
  };

  const stats = {
    total: reviews.length,
    inProgress: reviews.filter(r => r.status === "in_progress").length,
    completed: reviews.filter(r => r.status === "completed").length,
  };

  // ── Detail view ──────────────────────────────────────────────────────────
  if (selectedReview) {
    const items: any[] = reviewDetail?.items ?? [];
    const pending = items.filter(i => i.decision === "pending").length;
    const canComplete = items.length > 0 && pending === 0 && reviewDetail?.status !== "completed";

    return (
      <div className="animate-fade-in space-y-5">
        <button
          onClick={() => { setSelectedReview(null); setReviewDetail(null); }}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" /> All Reviews
        </button>

        {/* Review header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
          <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
          <div className="relative flex items-start justify-between gap-4 flex-wrap">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <FrameworkBadge fw={selectedReview.framework} />
                <PeriodBadge period={selectedReview.review_period} />
                <StatusBadge status={reviewDetail?.status ?? selectedReview.status} />
              </div>
              <h1 className="text-xl font-bold text-white">{selectedReview.name}</h1>
              {selectedReview.due_date && (
                <p className="text-sm text-slate-400 mt-1 flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5" />
                  Due {new Date(selectedReview.due_date).toLocaleDateString()}
                  {new Date(selectedReview.due_date) < new Date() && reviewDetail?.status !== "completed" && (
                    <span className="text-amber-400 flex items-center gap-1"><AlertTriangle className="w-3 h-3" /> Overdue</span>
                  )}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <p className="text-2xl font-black text-sky-400">{reviewDetail?.reviewed_items ?? selectedReview.reviewed_items}</p>
                <p className="text-[10px] text-slate-500 uppercase tracking-wide">/ {reviewDetail?.total_items ?? selectedReview.total_items} reviewed</p>
              </div>
              <div className="flex flex-col gap-2">
                {canComplete && (
                  <button
                    onClick={handleComplete}
                    disabled={completing}
                    className="flex items-center gap-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors disabled:opacity-50"
                  >
                    <CheckCircle2 className="w-4 h-4" /> {completing ? "Completing…" : "Complete Review"}
                  </button>
                )}
                <button
                  onClick={() => setShowAddUser(true)}
                  className="flex items-center gap-1.5 bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
                >
                  <Plus className="w-4 h-4" /> Add User
                </button>
              </div>
            </div>
          </div>
          {(reviewDetail?.total_items ?? 0) > 0 && (
            <div className="relative mt-4">
              <ProgressBar reviewed={reviewDetail?.reviewed_items ?? 0} total={reviewDetail?.total_items ?? 0} />
            </div>
          )}
        </div>

        {/* Items table */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          {detailLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-5 h-5 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : items.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 text-center gap-2">
              <Users className="w-8 h-8 text-gray-200" />
              <p className="text-sm text-gray-500">No users added yet</p>
              <button onClick={() => setShowAddUser(true)} className="text-xs font-semibold text-sky-600 hover:text-sky-700">+ Add first user</button>
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50/60">
                  <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">User</th>
                  <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden sm:table-cell">System</th>
                  <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden md:table-cell">Role</th>
                  <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Decision</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {items.map((item: any) => (
                  <tr
                    key={item.id}
                    className={`border-b border-gray-50 transition-colors ${
                      item.decision === "approved" ? "bg-emerald-50/30 hover:bg-emerald-50/50" :
                      item.decision === "revoked" ? "bg-red-50/30 hover:bg-red-50/50" :
                      "hover:bg-gray-50/40"
                    }`}
                  >
                    <td className="px-4 py-3">
                      <p className="font-semibold text-gray-800 text-sm">{item.user_email}</p>
                      {item.user_name && <p className="text-xs text-gray-400">{item.user_name}</p>}
                    </td>
                    <td className="px-4 py-3 text-gray-600 hidden sm:table-cell">
                      <span className="text-sm font-medium">{item.system_name}</span>
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs hidden md:table-cell">
                      {item.role_or_permission || <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <DecisionButton decision="approved" current={item.decision} onClick={() => handleDecision(item.id, "approved")} />
                        <DecisionButton decision="revoked" current={item.decision} onClick={() => handleDecision(item.id, "revoked")} />
                        {item.decision !== "pending" && (
                          <DecisionButton decision="pending" current={item.decision} onClick={() => handleDecision(item.id, "pending")} />
                        )}
                      </div>
                      {item.reviewed_by && (
                        <p className="text-[10px] text-gray-400 mt-1">by {item.reviewed_by}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDeleteItem(item.id)}
                        className="p-1.5 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {showAddUser && (
          <AddUserModal onClose={() => setShowAddUser(false)} onSave={handleAddUser} />
        )}
      </div>
    );
  }

  // ── List view ────────────────────────────────────────────────────────────
  return (
    <div className="animate-fade-in space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/20 ring-1 ring-sky-500/30">
              <UserCheck className="h-5 w-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Access Reviews</h1>
              <p className="text-sm text-slate-400">SOC 2 CC6.3 — periodic review of who has access to critical systems.</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-sky-400">{stats.total}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Total</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-amber-400">{stats.inProgress}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">In Progress</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{stats.completed}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Completed</span>
            </div>
            <button
              onClick={() => setShowNewModal(true)}
              className="flex items-center gap-1.5 bg-sky-500 hover:bg-sky-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" /> New Review
            </button>
          </div>
        </div>
      </div>

      {/* List */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-sky-500 border-t-transparent" />
        </div>
      ) : reviews.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 rounded-2xl border border-dashed border-gray-200 bg-white text-center">
          <UserCheck className="w-8 h-8 text-gray-200" />
          <p className="text-sm font-medium text-gray-500">No access reviews yet</p>
          <p className="text-xs text-gray-400">Create quarterly reviews to track who has access to critical systems.</p>
          <button onClick={() => setShowNewModal(true)} className="text-xs font-semibold text-sky-600 hover:text-sky-700">+ Create first review</button>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 bg-gray-50/60">
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Review</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden sm:table-cell">Due date</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400 hidden md:table-cell">Progress</th>
                <th className="text-left px-4 py-3 text-[11px] font-semibold uppercase tracking-wider text-gray-400">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {reviews.map(review => {
                const isOverdue = review.due_date && new Date(review.due_date) < new Date() && review.status !== "completed";
                return (
                  <tr key={review.id} className="border-b border-gray-50 hover:bg-gray-50/40 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-gray-900">{review.name}</span>
                        <FrameworkBadge fw={review.framework} />
                        <PeriodBadge period={review.review_period} />
                      </div>
                    </td>
                    <td className="px-4 py-3 hidden sm:table-cell">
                      {review.due_date ? (
                        <span className={`text-xs font-medium flex items-center gap-1 ${isOverdue ? "text-amber-600" : "text-gray-500"}`}>
                          {isOverdue && <AlertTriangle className="w-3 h-3" />}
                          {new Date(review.due_date).toLocaleDateString()}
                        </span>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell w-36">
                      <ProgressBar reviewed={review.reviewed_items} total={review.total_items} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={review.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => openDetail(review)}
                          className="text-xs font-semibold text-sky-600 hover:text-sky-700 border border-sky-200 hover:border-sky-300 px-2.5 py-1 rounded-lg transition-colors"
                        >
                          Review
                        </button>
                        <button
                          onClick={() => handleDelete(review.id)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-gray-300 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {showNewModal && <NewReviewModal onClose={() => setShowNewModal(false)} onSave={handleCreate} />}
    </div>
  );
}
