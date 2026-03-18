"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ChecklistItem, Offboarding } from "@/lib/types";
import { UserMinus, Plus, Trash2, X, Check, ChevronDown } from "lucide-react";

const DEFAULT_CHECKLIST: ChecklistItem[] = [
  { item: "Revoke all system access", done: false },
  { item: "Collect company equipment", done: false },
  { item: "Transfer knowledge/files", done: false },
  { item: "Remove from Slack/communication tools", done: false },
  { item: "Remove from GitHub/code repos", done: false },
  { item: "Disable email account", done: false },
  { item: "Update password manager", done: false },
  { item: "Remove from cloud accounts (AWS/Azure/GCP)", done: false },
  { item: "Return access badges/keys", done: false },
  { item: "Conduct exit interview", done: false },
];

const STATUS_STYLES: Record<string, string> = {
  pending:     "bg-gray-100 text-gray-500",
  in_progress: "bg-amber-50 text-amber-700",
  completed:   "bg-emerald-50 text-emerald-700",
};

const EMPTY: Partial<Offboarding> = {
  employee_name: "", employee_email: "", department: "", status: "pending",
  checklist: DEFAULT_CHECKLIST, notes: "",
};

export default function OffboardingPage() {
  const [records, setRecords]     = useState<Offboarding[]>([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState<Offboarding | null>(null);
  const [form, setForm]           = useState<Partial<Offboarding>>(EMPTY);
  const [saving, setSaving]       = useState(false);
  const [expanded, setExpanded]   = useState<string | null>(null);

  useEffect(() => {
    api.getOffboardings().then(setRecords).finally(() => setLoading(false));
  }, []);

  const openCreate = () => { setEditing(null); setForm({ ...EMPTY, checklist: DEFAULT_CHECKLIST.map(i => ({ ...i })) }); setShowModal(true); };
  const openEdit   = (r: Offboarding) => { setEditing(r); setForm({ ...r }); setShowModal(true); };
  const closeModal = () => { setShowModal(false); setEditing(null); };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault(); setSaving(true);
    try {
      if (editing) {
        const updated = await api.updateOffboarding(editing.id, form);
        setRecords(prev => prev.map(r => r.id === updated.id ? updated : r));
      } else {
        const created = await api.createOffboarding(form);
        setRecords(prev => [created, ...prev]);
      }
      closeModal();
    } catch { /**/ } finally { setSaving(false); }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this offboarding record?")) return;
    await api.deleteOffboarding(id);
    setRecords(prev => prev.filter(r => r.id !== id));
  };

  const toggleChecklistItem = (record: Offboarding, idx: number) => {
    const newChecklist = record.checklist.map((item, i) => i === idx ? { ...item, done: !item.done } : item);
    const allDone = newChecklist.every(i => i.done);
    api.updateOffboarding(record.id, {
      checklist: newChecklist,
      status: allDone ? "completed" : newChecklist.some(i => i.done) ? "in_progress" : "pending",
    }).then(updated => setRecords(prev => prev.map(r => r.id === updated.id ? updated : r)));
  };

  const active = records.filter(r => r.status !== "completed");
  const done   = records.filter(r => r.status === "completed");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <UserMinus className="w-6 h-6 text-brand-600" /> Employee Offboarding
          </h1>
          <p className="text-sm text-gray-500 mt-1">Ensure complete access revocation when employees leave</p>
        </div>
        <button onClick={openCreate} className="btn-primary gap-2">
          <Plus className="w-4 h-4" /> New Offboarding
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" /></div>
      ) : records.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-gray-100">
          <UserMinus className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 font-medium">No offboarding records</p>
          <button onClick={openCreate} className="btn-primary mt-4 gap-2"><Plus className="w-4 h-4" /> New Offboarding</button>
        </div>
      ) : (
        <div className="space-y-6">
          {active.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Active ({active.length})</h2>
              <div className="space-y-3">
                {active.map(record => <OffboardingCard key={record.id} record={record} expanded={expanded === record.id} onToggle={() => setExpanded(p => p === record.id ? null : record.id)} onEdit={openEdit} onDelete={handleDelete} onToggleItem={toggleChecklistItem} />)}
              </div>
            </section>
          )}
          {done.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Completed ({done.length})</h2>
              <div className="space-y-3">
                {done.map(record => <OffboardingCard key={record.id} record={record} expanded={expanded === record.id} onToggle={() => setExpanded(p => p === record.id ? null : record.id)} onEdit={openEdit} onDelete={handleDelete} onToggleItem={toggleChecklistItem} />)}
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
              <h2 className="font-semibold text-gray-900">{editing ? "Edit Offboarding" : "New Offboarding"}</h2>
              <button onClick={closeModal} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <form onSubmit={handleSave} className="px-6 py-5 space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Employee name *</label>
                  <input className="input" value={form.employee_name ?? ""} onChange={e => setForm(p => ({ ...p, employee_name: e.target.value }))} required />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input type="email" className="input" value={form.employee_email ?? ""} onChange={e => setForm(p => ({ ...p, employee_email: e.target.value }))} />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Department</label>
                  <input className="input" value={form.department ?? ""} onChange={e => setForm(p => ({ ...p, department: e.target.value }))} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Last day</label>
                  <input type="date" className="input" value={form.last_day ? form.last_day.substring(0, 10) : ""} onChange={e => setForm(p => ({ ...p, last_day: e.target.value || null }))} />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Checklist items</label>
                <div className="space-y-1.5 max-h-48 overflow-y-auto bg-gray-50 rounded-xl p-3">
                  {(form.checklist ?? []).map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <input type="text" className="input text-xs flex-1 py-1.5" value={item.item} onChange={e => {
                        const next = [...(form.checklist ?? [])];
                        next[idx] = { ...next[idx], item: e.target.value };
                        setForm(p => ({ ...p, checklist: next }));
                      }} />
                      <button type="button" onClick={() => setForm(p => ({ ...p, checklist: (p.checklist ?? []).filter((_, i) => i !== idx) }))} className="text-red-400 hover:text-red-600 shrink-0">
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
                <button type="button" onClick={() => setForm(p => ({ ...p, checklist: [...(p.checklist ?? []), { item: "", done: false }] }))}
                  className="mt-2 text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
                  <Plus className="w-3.5 h-3.5" /> Add item
                </button>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
                <textarea className="input min-h-[60px]" value={form.notes ?? ""} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} />
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={closeModal} className="btn-secondary flex-1">Cancel</button>
                <button type="submit" disabled={saving} className="btn-primary flex-1 justify-center">
                  {saving ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : editing ? "Save changes" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function OffboardingCard({ record, expanded, onToggle, onEdit, onDelete, onToggleItem }: {
  record: Offboarding; expanded: boolean; onToggle: () => void;
  onEdit: (r: Offboarding) => void; onDelete: (id: string) => void;
  onToggleItem: (record: Offboarding, idx: number) => void;
}) {
  const done = record.checklist.filter(i => i.done).length;
  const total = record.checklist.length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;

  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors" onClick={onToggle}>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[record.status]}`}>{record.status.replace("_", " ")}</span>
            <span className="font-medium text-gray-900">{record.employee_name}</span>
            {record.department && <span className="text-xs text-gray-400">· {record.department}</span>}
          </div>
          <div className="flex items-center gap-3 mt-1.5">
            <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
              <div className={`h-1.5 rounded-full transition-all ${pct === 100 ? "bg-emerald-500" : "bg-brand-500"}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs text-gray-400 shrink-0">{done}/{total}</span>
            {record.last_day && <span className="text-xs text-gray-400">Last day: {new Date(record.last_day).toLocaleDateString()}</span>}
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-gray-400 shrink-0 transition-transform ${expanded ? "rotate-180" : ""}`} />
      </div>
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-50 pt-3 space-y-2">
          {record.checklist.map((item, idx) => (
            <label key={idx} className="flex items-center gap-3 cursor-pointer group py-1">
              <div
                onClick={() => onToggleItem(record, idx)}
                className={`w-5 h-5 rounded-md border-2 flex items-center justify-center shrink-0 transition-all cursor-pointer ${item.done ? "bg-emerald-500 border-emerald-500" : "border-gray-300 group-hover:border-brand-400"}`}
              >
                {item.done && <Check className="w-3 h-3 text-white" />}
              </div>
              <span className={`text-sm ${item.done ? "line-through text-gray-400" : "text-gray-700"}`}>{item.item}</span>
            </label>
          ))}
          <div className="flex gap-2 pt-2">
            <button onClick={() => onEdit(record)} className="btn-secondary text-xs py-1.5 px-3">Edit</button>
            <button onClick={() => onDelete(record.id)} className="text-xs text-red-500 hover:text-red-700 flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors">
              <Trash2 className="w-3.5 h-3.5" /> Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
