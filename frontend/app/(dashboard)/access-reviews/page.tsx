"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AccessReview, Member } from "@/lib/types";
import { UserCheck, Plus, Trash2, X, CheckCircle2, Clock, PlayCircle, ChevronDown, ChevronUp } from "lucide-react";

const STATUS_STYLES: Record<string, string> = {
  open: "bg-gray-100 text-gray-600",
  in_progress: "bg-amber-50 text-amber-700",
  completed: "bg-emerald-50 text-emerald-700",
};

const STATUS_LABELS: Record<string, string> = {
  open: "Open",
  in_progress: "In Progress",
  completed: "Completed",
};

const STATUS_ICONS: Record<string, React.ElementType> = {
  open: Clock,
  in_progress: PlayCircle,
  completed: CheckCircle2,
};

function currentQuarter(): string {
  const now = new Date();
  const q = Math.ceil((now.getMonth() + 1) / 3);
  return `Q${q} ${now.getFullYear()}`;
}

function Modal({
  onClose,
  onSave,
  members,
}: {
  onClose: () => void;
  onSave: (data: Partial<AccessReview>) => Promise<void>;
  members: Member[];
}) {
  const [form, setForm] = useState({
    title: "Quarterly Access Review",
    period: currentQuarter(),
    reviewer_user_id: "",
    due_date: "",
    scope: "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.title || !form.period) return;
    setSaving(true);
    try {
      await onSave({
        title: form.title,
        period: form.period,
        reviewer_user_id: form.reviewer_user_id || null,
        due_date: form.due_date || null,
        scope: form.scope || null,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-bold text-gray-900">New Access Review</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Title *</label>
            <input value={form.title} onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Period *</label>
              <input value={form.period} onChange={(e) => setForm((p) => ({ ...p, period: e.target.value }))} placeholder="Q1 2026" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Due date</label>
              <input type="date" value={form.due_date} onChange={(e) => setForm((p) => ({ ...p, due_date: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Reviewer</label>
            <select value={form.reviewer_user_id} onChange={(e) => setForm((p) => ({ ...p, reviewer_user_id: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30">
              <option value="">Unassigned</option>
              {members.map((m) => <option key={m.id} value={m.id}>{m.email}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Scope</label>
            <textarea value={form.scope} onChange={(e) => setForm((p) => ({ ...p, scope: e.target.value }))} rows={2} placeholder="e.g. All production system access, GitHub org members, AWS IAM users…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-xl">Cancel</button>
          <button onClick={handleSubmit} disabled={saving || !form.title || !form.period} className="px-4 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl disabled:opacity-40">
            {saving ? "Creating…" : "Create review"}
          </button>
        </div>
      </div>
    </div>
  );
}

function UpdateModal({
  review,
  onClose,
  onSave,
  members,
}: {
  review: AccessReview;
  onClose: () => void;
  onSave: (data: Partial<AccessReview>) => Promise<void>;
  members: Member[];
}) {
  const [form, setForm] = useState({
    status: review.status,
    users_reviewed: review.users_reviewed,
    access_changes: review.access_changes,
    findings: review.findings ?? "",
    notes: review.notes ?? "",
    completed_at: review.completed_at ? review.completed_at.slice(0, 10) : "",
    reviewer_user_id: review.reviewer_user_id ?? "",
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    setSaving(true);
    try {
      const completed_at =
        form.status === "completed"
          ? form.completed_at || new Date().toISOString().slice(0, 10)
          : form.completed_at || null;
      await onSave({
        status: form.status,
        users_reviewed: form.users_reviewed,
        access_changes: form.access_changes,
        findings: form.findings || null,
        notes: form.notes || null,
        completed_at,
        reviewer_user_id: form.reviewer_user_id || null,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <h2 className="font-bold text-gray-900">Update Review</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select value={form.status} onChange={(e) => setForm((p) => ({ ...p, status: e.target.value as "open" | "in_progress" | "completed" }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30">
              {["open", "in_progress", "completed"].map((s) => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Reviewer</label>
            <select value={form.reviewer_user_id} onChange={(e) => setForm((p) => ({ ...p, reviewer_user_id: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30">
              <option value="">Unassigned</option>
              {members.map((m) => <option key={m.id} value={m.id}>{m.email}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Users reviewed</label>
              <input type="number" min={0} value={form.users_reviewed} onChange={(e) => setForm((p) => ({ ...p, users_reviewed: parseInt(e.target.value) || 0 }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Access changes made</label>
              <input type="number" min={0} value={form.access_changes} onChange={(e) => setForm((p) => ({ ...p, access_changes: parseInt(e.target.value) || 0 }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
          </div>
          {form.status === "completed" && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Completion date</label>
              <input type="date" value={form.completed_at} onChange={(e) => setForm((p) => ({ ...p, completed_at: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Findings</label>
            <textarea value={form.findings} onChange={(e) => setForm((p) => ({ ...p, findings: e.target.value }))} rows={3} placeholder="Document any access anomalies or policy violations found…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} rows={2} placeholder="Additional context…" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/30" />
          </div>
        </div>
        <div className="px-5 py-4 border-t border-gray-100 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-xl">Cancel</button>
          <button onClick={handleSubmit} disabled={saving} className="px-4 py-2 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl disabled:opacity-40">
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function AccessReviewsPage() {
  const [reviews, setReviews] = useState<AccessReview[]>([]);
  const [members, setMembers] = useState<Member[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [updating, setUpdating] = useState<AccessReview | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getAccessReviews(),
      api.getMembers(),
    ]).then(([r, m]) => { setReviews(r); setMembers(m); }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (data: Partial<AccessReview>) => {
    const r = await api.createAccessReview(data);
    setReviews((prev) => [r, ...prev]);
  };

  const handleUpdate = async (data: Partial<AccessReview>) => {
    if (!updating) return;
    const r = await api.updateAccessReview(updating.id, data);
    setReviews((prev) => prev.map((x) => x.id === updating.id ? r : x));
    setUpdating(null);
  };

  const handleDelete = async (id: string) => {
    await api.deleteAccessReview(id);
    setReviews((prev) => prev.filter((r) => r.id !== id));
  };

  const completed = reviews.filter((r) => r.status === "completed").length;
  const open = reviews.filter((r) => r.status === "open").length;
  const inProgress = reviews.filter((r) => r.status === "in_progress").length;

  return (
    <div className="animate-fade-in">

      {/* Dark hero card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6">
        {/* Row 1: icon + title + action */}
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center shrink-0">
              <UserCheck className="w-5 h-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white leading-tight">Access Reviews</h1>
              <p className="text-sm text-slate-400 mt-0.5">Quarterly access review workflows with documented sign-off for CC6.3.</p>
            </div>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 rounded-xl text-sm transition-colors shrink-0"
          >
            <Plus className="w-4 h-4" /> New review
          </button>
        </div>

        {/* Row 2: stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <p className="text-3xl font-bold text-blue-400">{reviews.length}</p>
            <p className="text-xs text-slate-400 mt-1">Total reviews</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${open > 0 ? "text-amber-400" : "text-blue-400"}`}>{open}</p>
            <p className="text-xs text-slate-400 mt-1">Open</p>
          </div>
          <div>
            <p className={`text-3xl font-bold ${inProgress > 0 ? "text-sky-400" : "text-blue-400"}`}>{inProgress}</p>
            <p className="text-xs text-slate-400 mt-1">In progress</p>
          </div>
          <div>
            <p className="text-3xl font-bold text-blue-400">{completed}</p>
            <p className="text-xs text-slate-400 mt-1">Completed</p>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : reviews.length === 0 ? (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <UserCheck className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-600 mb-1">No access reviews yet</p>
          <p className="text-xs text-gray-400 mb-4">Create quarterly reviews to document formal sign-off on user access for SOC 2 CC6.3.</p>
          <button onClick={() => setShowModal(true)} className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-xl text-sm">
            <Plus className="w-4 h-4" /> Create first review
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => {
            const StatusIcon = STATUS_ICONS[r.status] ?? Clock;
            return (
              <div key={r.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className="font-semibold text-gray-900">{r.title}</span>
                      <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full font-medium">{r.period}</span>
                      <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full ${STATUS_STYLES[r.status]}`}>
                        <StatusIcon className="w-3 h-3" />
                        {STATUS_LABELS[r.status]}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400 flex-wrap">
                      {r.reviewer_name && <span>Reviewer: {r.reviewer_name}</span>}
                      {r.due_date && <span>Due {new Date(r.due_date).toLocaleDateString()}</span>}
                      {r.users_reviewed > 0 && <span>{r.users_reviewed} users reviewed</span>}
                      {r.access_changes > 0 && <span>{r.access_changes} access changes</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <button onClick={() => setUpdating(r)} className="text-xs font-semibold text-gray-500 hover:text-gray-700 border border-gray-200 px-2.5 py-1 rounded-lg">Update</button>
                    {deletingId === r.id ? (
                      <>
                        <button onClick={() => setDeletingId(null)} className="text-xs text-gray-400 hover:text-gray-600 px-2 py-1 rounded-lg">Cancel</button>
                        <button onClick={() => { handleDelete(r.id); setDeletingId(null); }} className="text-xs font-semibold text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded-lg">Delete</button>
                      </>
                    ) : (
                      <button onClick={() => setDeletingId(r.id)} className="text-gray-300 hover:text-red-400 p-1"><Trash2 className="w-4 h-4" /></button>
                    )}
                    <button onClick={() => setExpanded(expanded === r.id ? null : r.id)} className="text-gray-400 hover:text-gray-600 p-1">
                      {expanded === r.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                {expanded === r.id && (
                  <div className="border-t border-gray-100 px-5 py-4 bg-gray-50/50 space-y-3">
                    {r.scope && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Scope</p><p className="text-sm text-gray-700">{r.scope}</p></div>}
                    {r.findings && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Findings</p><p className="text-sm text-gray-700">{r.findings}</p></div>}
                    {r.notes && <div><p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wide mb-1">Notes</p><p className="text-sm text-gray-700">{r.notes}</p></div>}
                    {r.completed_at && <p className="text-xs text-emerald-600 font-medium">Completed on {new Date(r.completed_at).toLocaleDateString()}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showModal && <Modal onClose={() => setShowModal(false)} onSave={handleCreate} members={members} />}
      {updating && <UpdateModal review={updating} onClose={() => setUpdating(null)} onSave={handleUpdate} members={members} />}
    </div>
  );
}
