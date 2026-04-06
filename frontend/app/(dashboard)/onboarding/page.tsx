"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { UserCheck, Plus, Trash2, Check, Clock, X, ChevronDown, ChevronUp, Users } from "lucide-react";
import { toast } from "@/lib/toast";

const TASK_FIELDS = [
  { field: "policy_ack_status",       label: "Policy Acknowledgment" },
  { field: "training_status",          label: "Security Training" },
  { field: "device_status",            label: "Device Enrollment" },
  { field: "background_check_status",  label: "Background Check" },
  { field: "access_provisioned_status",label: "Access Provisioning" },
];

function TaskDot({ status }: { status: string }) {
  if (status === "completed") return <div className="w-4 h-4 rounded-full bg-emerald-500 flex items-center justify-center"><Check className="w-2.5 h-2.5 text-white" /></div>;
  if (status === "skipped")   return <div className="w-4 h-4 rounded-full bg-gray-300 flex items-center justify-center"><X className="w-2.5 h-2.5 text-white" /></div>;
  return <div className="w-4 h-4 rounded-full border-2 border-gray-300 bg-white" />;
}

function ProgressBar({ record }: { record: any }) {
  const completed = TASK_FIELDS.filter(t => record[t.field] === "completed" || record[t.field] === "skipped").length;
  const pct = Math.round((completed / TASK_FIELDS.length) * 100);
  return (
    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden w-24">
      <div className={`h-full rounded-full transition-all ${pct === 100 ? "bg-emerald-500" : "bg-teal-500"}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function AddModal({ onClose, onCreated }: { onClose: () => void; onCreated: (r: any) => void }) {
  const [form, setForm] = useState({ employee_email: "", employee_name: "", department: "", role_title: "", hired_at: "" });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!form.employee_email) return;
    setSaving(true);
    try {
      const r = await api.createOnboarding({
        ...form,
        hired_at: form.hired_at ? new Date(form.hired_at).toISOString() : undefined,
        employee_name: form.employee_name || undefined,
        department: form.department || undefined,
        role_title: form.role_title || undefined,
      });
      onCreated(r);
      onClose();
    } catch (e: any) {
      toast(e?.message || "Failed to create", "error");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900">Add New Hire</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
        </div>
        {[
          { key: "employee_email", label: "Email *", type: "email", placeholder: "alice@example.com" },
          { key: "employee_name",  label: "Name",    type: "text",  placeholder: "Alice Smith" },
          { key: "department",     label: "Department", type: "text", placeholder: "Engineering" },
          { key: "role_title",     label: "Role",    type: "text",  placeholder: "Software Engineer" },
          { key: "hired_at",       label: "Start date", type: "date", placeholder: "" },
        ].map(({ key, label, type, placeholder }) => (
          <div key={key}>
            <label className="block text-xs font-semibold text-gray-600 mb-1">{label}</label>
            <input
              type={type}
              value={(form as any)[key]}
              onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
              placeholder={placeholder}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30"
            />
          </div>
        ))}
        <div className="flex gap-2 pt-1">
          <button onClick={onClose} className="flex-1 border border-gray-200 rounded-xl py-2 text-sm text-gray-600 hover:bg-gray-50">Cancel</button>
          <button onClick={handleSubmit} disabled={saving || !form.employee_email} className="flex-1 bg-teal-600 text-white rounded-xl py-2 text-sm font-semibold hover:bg-teal-700 disabled:opacity-50">
            {saving ? "Adding…" : "Add"}
          </button>
        </div>
      </div>
    </div>
  );
}

function RecordRow({ record, onUpdate, onDelete }: { record: any; onUpdate: (r: any) => void; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const [updating, setUpdating] = useState<string | null>(null);
  const completed = TASK_FIELDS.filter(t => record[t.field] === "completed" || record[t.field] === "skipped").length;
  const isComplete = record.overall_status === "completed";

  const toggle = async (field: string, currentStatus: string) => {
    const next = currentStatus === "completed" ? "pending" : "completed";
    setUpdating(field);
    try {
      const updated = await api.updateOnboardingTaskStatus(record.id, field, next);
      onUpdate(updated);
    } catch { } finally { setUpdating(null); }
  };

  return (
    <div className={`bg-white rounded-2xl border shadow-sm overflow-hidden ${isComplete ? "border-emerald-100" : "border-gray-100"}`}>
      <div className="flex items-center gap-3 px-4 py-3 cursor-pointer" onClick={() => setExpanded(v => !v)}>
        <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${isComplete ? "bg-emerald-50" : "bg-teal-50"}`}>
          <UserCheck className={`w-4 h-4 ${isComplete ? "text-emerald-500" : "text-teal-500"}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900 truncate">{record.employee_name || record.employee_email}</span>
            {record.employee_name && <span className="text-xs text-gray-400 truncate hidden sm:block">{record.employee_email}</span>}
            {record.role_title && <span className="text-[10px] font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md">{record.role_title}</span>}
          </div>
          <div className="flex items-center gap-2 mt-1">
            <ProgressBar record={record} />
            <span className="text-[10px] text-gray-400">{completed}/{TASK_FIELDS.length} tasks</span>
            {record.source !== "manual" && (
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-blue-50 text-blue-600">{record.source}</span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {isComplete
            ? <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">Complete</span>
            : <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">In progress</span>
          }
          {expanded ? <ChevronUp className="w-4 h-4 text-gray-300" /> : <ChevronDown className="w-4 h-4 text-gray-300" />}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-gray-50 px-4 py-3 bg-gray-50/40">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
            {TASK_FIELDS.map(({ field, label }) => {
              const status = record[field];
              return (
                <button
                  key={field}
                  onClick={() => toggle(field, status)}
                  disabled={updating === field}
                  className={`flex items-center gap-2.5 px-3 py-2 rounded-xl border transition-all text-left ${
                    status === "completed" ? "bg-emerald-50 border-emerald-200" :
                    status === "skipped"   ? "bg-gray-50 border-gray-200" :
                    "bg-white border-gray-200 hover:border-teal-200 hover:bg-teal-50/30"
                  }`}
                >
                  <TaskDot status={status} />
                  <span className={`text-xs font-medium ${status === "completed" ? "text-emerald-700" : "text-gray-600"}`}>{label}</span>
                </button>
              );
            })}
          </div>
          <div className="flex items-center justify-between">
            {record.hired_at && (
              <p className="text-xs text-gray-400 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                Started {new Date(record.hired_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
              </p>
            )}
            <button onClick={onDelete} className="ml-auto flex items-center gap-1 text-xs text-red-400 hover:text-red-600">
              <Trash2 className="w-3 h-3" /> Remove
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function OnboardingPage() {
  const [records, setRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  useEffect(() => {
    api.getOnboarding().then(setRecords).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const inProgress = records.filter(r => r.overall_status !== "completed");
  const completed  = records.filter(r => r.overall_status === "completed");

  const handleDelete = async (id: string) => {
    try {
      await api.deleteOnboarding(id);
      setRecords(prev => prev.filter(r => r.id !== id));
    } catch { }
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Hero */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div className="pointer-events-none absolute inset-0 opacity-[0.03]" style={{ backgroundImage: "linear-gradient(rgba(255,255,255,0.4) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.4) 1px,transparent 1px)", backgroundSize: "24px 24px" }} />
        <div className="relative flex items-start justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/20 ring-1 ring-teal-500/30">
              <UserCheck className="h-5 w-5 text-teal-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Onboarding</h1>
              <p className="text-sm text-slate-400">Track new-hire security tasks: policies, training, device, access.</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-teal-400">{inProgress.length}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">In progress</span>
            </div>
            <div className="w-px h-8 bg-slate-700" />
            <div className="flex flex-col items-center">
              <span className="text-2xl font-black text-emerald-400">{completed.length}</span>
              <span className="text-[10px] font-medium uppercase tracking-wider text-slate-500">Complete</span>
            </div>
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 bg-teal-500 hover:bg-teal-600 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors"
            >
              <Plus className="w-4 h-4" /> Add hire
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-teal-500 border-t-transparent" />
        </div>
      ) : records.length === 0 ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3 text-center rounded-2xl border border-dashed border-gray-200 bg-white">
          <Users className="w-8 h-8 text-gray-200" />
          <p className="text-sm font-medium text-gray-500">No onboarding records yet</p>
          <p className="text-xs text-gray-400">Add a new hire to track their security onboarding tasks.</p>
          <button onClick={() => setShowAdd(true)} className="text-xs font-semibold text-teal-600 hover:text-teal-700">+ Add first hire</button>
        </div>
      ) : (
        <div className="space-y-4">
          {inProgress.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 px-1">In progress — {inProgress.length}</p>
              {inProgress.map(r => (
                <RecordRow
                  key={r.id}
                  record={r}
                  onUpdate={updated => setRecords(prev => prev.map(x => x.id === updated.id ? updated : x))}
                  onDelete={() => handleDelete(r.id)}
                />
              ))}
            </div>
          )}
          {completed.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 px-1">Completed — {completed.length}</p>
              {completed.map(r => (
                <RecordRow
                  key={r.id}
                  record={r}
                  onUpdate={updated => setRecords(prev => prev.map(x => x.id === updated.id ? updated : x))}
                  onDelete={() => handleDelete(r.id)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {showAdd && <AddModal onClose={() => setShowAdd(false)} onCreated={r => setRecords(prev => [r, ...prev])} />}
    </div>
  );
}
