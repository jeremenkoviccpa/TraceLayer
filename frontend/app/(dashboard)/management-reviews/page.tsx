"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ManagementReview } from "@/lib/types";
import { ClipboardCheck, Plus, Trash2, X, ChevronDown, ChevronUp, CalendarClock, RefreshCw } from "lucide-react";
import { toast } from "@/lib/toast";

type ActionItem = { item: string; owner: string; due_date: string | null; done: boolean };

const OUTCOME_STYLES: Record<string, string> = {
  satisfactory:       "bg-emerald-100 text-emerald-700",
  needs_improvement:  "bg-amber-100 text-amber-700",
  critical_findings:  "bg-red-100 text-red-700",
};

const OUTCOMES = ["satisfactory", "needs_improvement", "critical_findings"] as const;

const EMPTY: Partial<ManagementReview> = {
  review_date: new Date().toISOString(),
  outcome: "satisfactory",
  action_items: [],
  attendees: "", inputs_summary: "", decisions: "", notes: "",
};

function fmt(dt?: string | null) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString("en-GB", { year: "numeric", month: "long", day: "numeric" });
}

export default function ManagementReviewsPage() {
  const [reviews, setReviews]     = useState<ManagementReview[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<ManagementReview | null>(null);
  const [form, setForm]           = useState<Partial<ManagementReview>>(EMPTY);
  const [actionItems, setActionItems] = useState<ActionItem[]>([]);
  const [saving, setSaving]       = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [scheduling, setScheduling] = useState(false);

  useEffect(() => {
    api.getManagementReviews().then(setReviews).finally(() => setLoading(false));
  }, []);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY);
    setActionItems([]);
    setShowModal(true);
  };

  const openEdit = (r: ManagementReview) => {
    setEditing(r);
    setForm(r);
    setActionItems(r.action_items ?? []);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setEditing(null);
    setForm(EMPTY);
    setActionItems([]);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      const payload = { ...form, action_items: actionItems };
      if (editing) {
        const updated = await api.updateManagementReview(editing.id, payload);
        setReviews((prev) => prev.map((r) => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createManagementReview(payload);
        setReviews((prev) => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this review?")) return;
    await api.deleteManagementReview(id);
    setReviews((prev) => prev.filter((r) => r.id !== id));
  };

  const toggleActionDone = async (review: ManagementReview, idx: number) => {
    const newItems = review.action_items.map((a, i) => i === idx ? { ...a, done: !a.done } : a);
    const updated = await api.updateManagementReview(review.id, { ...review, action_items: newItems });
    setReviews((prev) => prev.map((r) => r.id === updated.id ? updated : r));
  };

  const addActionItem = () => setActionItems((a) => [...a, { item: "", owner: "", due_date: null, done: false }]);
  const removeActionItem = (idx: number) => setActionItems((a) => a.filter((_, i) => i !== idx));
  const updateActionItem = (idx: number, field: keyof ActionItem, value: string | boolean | null) => {
    setActionItems((a) => a.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  };

  const handleScheduleNext = async () => {
    setScheduling(true);
    try {
      const review = await api.scheduleNextManagementReview();
      setReviews((prev) => [review, ...prev]);
      toast("Scheduled management review for this quarter");
    } catch (err: unknown) {
      const msg = (err as Error)?.message;
      toast(msg ?? "A review for this quarter already exists", "error");
    }
    finally { setScheduling(false); }
  };

  const sf = (key: keyof ManagementReview) => ({
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
            <ClipboardCheck className="w-6 h-6 text-brand-600" />
            Management Reviews
          </h1>
          <p className="text-sm text-gray-500 mt-1">ISO 27001 Clause 9.3 · Annual review records</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleScheduleNext}
            disabled={scheduling}
            className="flex items-center gap-1.5 btn-secondary !px-3 !py-2 text-xs disabled:opacity-50"
          >
            {scheduling ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CalendarClock className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">Schedule this quarter</span>
          </button>
          <button onClick={openCreate} className="flex items-center gap-2 bg-brand-600 text-white text-sm font-semibold px-4 py-2 rounded-xl hover:bg-brand-700 transition-colors">
            <Plus className="w-4 h-4" /> Add Review
          </button>
        </div>
      </div>

      {/* Cards */}
      {reviews.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 text-center py-20">
          <ClipboardCheck className="w-10 h-10 mx-auto mb-3 text-gray-200" />
          <p className="text-sm text-gray-400">No management reviews recorded.</p>
          <button onClick={openCreate} className="mt-4 text-sm font-semibold text-brand-600 hover:text-brand-700">Record first review →</button>
        </div>
      ) : (
        <div className="space-y-3">
          {reviews.map((r) => {
            const doneCount  = r.action_items.filter((a) => a.done).length;
            const totalItems = r.action_items.length;
            return (
              <div key={r.id} className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                <div className="px-5 py-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-semibold text-gray-900 text-sm">{fmt(r.review_date)}</h3>
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${OUTCOME_STYLES[r.outcome] ?? "bg-gray-100 text-gray-500"}`}>
                        {r.outcome.replace(/_/g, " ")}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 mt-1 text-xs text-gray-400">
                      {r.attendees && <span>{r.attendees.split(",").length} attendee{r.attendees.split(",").length !== 1 ? "s" : ""}</span>}
                      {totalItems > 0 && <span>{doneCount}/{totalItems} actions done</span>}
                      {r.next_review_date && <span>Next: {fmt(r.next_review_date)}</span>}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => openEdit(r)} className="text-xs text-brand-600 hover:text-brand-700 font-medium px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors">Edit</button>
                    <button onClick={() => handleDelete(r.id)} className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"><Trash2 className="w-3.5 h-3.5" /></button>
                    <button onClick={() => setExpandedId(expandedId === r.id ? null : r.id)} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors">
                      {expandedId === r.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                {expandedId === r.id && (
                  <div className="px-5 pb-4 border-t border-gray-50 space-y-4">
                    {r.inputs_summary && (
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5 mt-3">What was reviewed</p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{r.inputs_summary}</p>
                      </div>
                    )}
                    {r.decisions && (
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5">Decisions</p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{r.decisions}</p>
                      </div>
                    )}
                    {r.action_items.length > 0 && (
                      <div>
                        <p className="text-xs text-gray-400 mb-1.5">Action Items</p>
                        <div className="space-y-1.5">
                          {r.action_items.map((a, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <button
                                onClick={() => toggleActionDone(r, i)}
                                className={`mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ${a.done ? "bg-brand-600 border-brand-600 text-white" : "border-gray-300 hover:border-brand-400"}`}
                              >
                                {a.done && <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                              </button>
                              <div className="flex-1">
                                <p className={`text-sm ${a.done ? "line-through text-gray-400" : "text-gray-700"}`}>{a.item}</p>
                                <p className="text-xs text-gray-400">{a.owner}{a.due_date ? ` · ${fmt(a.due_date)}` : ""}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {r.notes && (
                      <div>
                        <p className="text-xs text-gray-400 mb-0.5">Notes</p>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">{r.notes}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Review" : "New Management Review"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-700 p-1 rounded-lg hover:bg-gray-100 transition-colors"><X className="w-4 h-4" /></button>
            </div>
            <form onSubmit={handleSave} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Review Date *</label>
                  <input
                    type="date"
                    value={form.review_date ? new Date(form.review_date).toISOString().slice(0, 10) : ""}
                    onChange={(e) => setForm((f) => ({ ...f, review_date: e.target.value ? new Date(e.target.value).toISOString() : "" }))}
                    required
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Outcome</label>
                  <select {...sf("outcome")} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500">
                    {OUTCOMES.map((o) => <option key={o} value={o}>{o.replace(/_/g, " ")}</option>)}
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Attendees</label>
                  <textarea {...sf("attendees")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Names separated by commas" />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">What was reviewed</label>
                  <textarea {...sf("inputs_summary")} rows={3} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Audit results, incidents, risk changes, KPIs..." />
                </div>
                <div className="col-span-2">
                  <label className="text-xs font-medium text-gray-500 block mb-1">Decisions</label>
                  <textarea {...sf("decisions")} rows={3} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" placeholder="Key decisions made during the review" />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Next Review Date</label>
                  <input
                    type="date"
                    value={form.next_review_date ? new Date(form.next_review_date).toISOString().slice(0, 10) : ""}
                    onChange={(e) => setForm((f) => ({ ...f, next_review_date: e.target.value ? new Date(e.target.value).toISOString() : null }))}
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-500 block mb-1">Notes</label>
                  <textarea {...sf("notes")} rows={2} className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none" />
                </div>
              </div>

              {/* Action Items */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-500">Action Items</label>
                  <button type="button" onClick={addActionItem} className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
                    <Plus className="w-3 h-3" /> Add item
                  </button>
                </div>
                <div className="space-y-2">
                  {actionItems.map((a, i) => (
                    <div key={i} className="flex gap-2 items-start bg-gray-50 rounded-xl p-3">
                      <div className="flex-1 grid grid-cols-3 gap-2">
                        <input
                          value={a.item}
                          onChange={(e) => updateActionItem(i, "item", e.target.value)}
                          placeholder="Action item"
                          className="col-span-2 border border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                        />
                        <input
                          value={a.owner}
                          onChange={(e) => updateActionItem(i, "owner", e.target.value)}
                          placeholder="Owner"
                          className="border border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                        />
                        <input
                          type="date"
                          value={a.due_date ? new Date(a.due_date).toISOString().slice(0, 10) : ""}
                          onChange={(e) => updateActionItem(i, "due_date", e.target.value ? new Date(e.target.value).toISOString() : null)}
                          className="col-span-2 border border-gray-200 rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-brand-500"
                        />
                      </div>
                      <button type="button" onClick={() => removeActionItem(i)} className="text-gray-400 hover:text-red-500 p-1 transition-colors mt-0.5">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                  {actionItems.length === 0 && (
                    <p className="text-xs text-gray-400 text-center py-3 border border-dashed border-gray-200 rounded-xl">No action items yet</p>
                  )}
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={closeModal} className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 rounded-xl transition-colors">Cancel</button>
                <button type="submit" disabled={saving} className="px-4 py-2 text-sm font-semibold bg-brand-600 text-white rounded-xl hover:bg-brand-700 disabled:opacity-60 transition-colors">
                  {saving ? "Saving…" : editing ? "Save Changes" : "Create Review"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
