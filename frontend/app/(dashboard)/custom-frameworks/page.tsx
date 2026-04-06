"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import {
  Layers, Plus, Trash2, Pencil, X, ChevronLeft,
  Tag, CheckCircle2, Circle,
} from "lucide-react";
import { toast } from "@/lib/toast";

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORY_SUGGESTIONS = [
  "access_control", "change_management", "logging", "encryption",
  "vulnerability_management", "incident_response", "vendor_management",
  "training", "backup", "policy",
];

const EVIDENCE_TYPE_OPTIONS = [
  "iam_users", "iam_policies", "cloudtrail_logs", "github_members",
  "github_repos", "okta_users", "vulnerability_scans", "firewall_rules",
  "audit_logs", "mfa_settings", "encryption_configs", "backup_configs",
  "incident_records", "training_records", "access_reviews", "policies", "documents",
];

// ── Small helpers ─────────────────────────────────────────────────────────────

function ScoreRing({ score }: { score: number }) {
  const r = 18;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 75 ? "#22c55e" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <svg width={44} height={44} viewBox="0 0 44 44" className="shrink-0">
      <circle cx={22} cy={22} r={r} fill="none" stroke="#334155" strokeWidth={4} />
      <circle
        cx={22} cy={22} r={r} fill="none"
        stroke={color} strokeWidth={4}
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 22 22)"
      />
      <text x={22} y={27} textAnchor="middle" fontSize={10} fontWeight="bold" fill={color}>
        {score}%
      </text>
    </svg>
  );
}

function CategoryBadge({ cat }: { cat: string }) {
  return (
    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-violet-100 text-violet-700 capitalize">
      {cat.replace(/_/g, " ")}
    </span>
  );
}

function StatusDot({ status }: { status: string }) {
  return status === "passing"
    ? <CheckCircle2 size={14} className="text-emerald-500" />
    : <Circle size={14} className="text-gray-400" />;
}

// ── Modals ────────────────────────────────────────────────────────────────────

function NewFrameworkModal({
  onClose,
  onSave,
}: {
  onClose: () => void;
  onSave: (data: { name: string; description?: string; version: string }) => Promise<void>;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [version, setVersion] = useState("1.0");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSave({ name: name.trim(), description: description.trim() || undefined, version: version.trim() || "1.0" });
      onClose();
    } catch {
      toast("Failed to create framework", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">New Framework</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Internal Security Controls"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={3}
              placeholder="What this framework covers..."
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Version</label>
            <input
              type="text"
              value={version}
              onChange={e => setVersion(e.target.value)}
              placeholder="1.0"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {saving ? "Creating..." : "Create Framework"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ControlModal({
  frameworkId,
  initial,
  onClose,
  onSave,
}: {
  frameworkId: string;
  initial?: any;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [name, setName] = useState(initial?.name ?? "");
  const [category, setCategory] = useState(initial?.category ?? "");
  const [externalId, setExternalId] = useState(initial?.external_id ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [evidenceTypes, setEvidenceTypes] = useState<string[]>(initial?.evidence_types ?? []);
  const [sortOrder, setSortOrder] = useState<number>(initial?.sort_order ?? 0);
  const [saving, setSaving] = useState(false);

  function toggleType(t: string) {
    setEvidenceTypes(prev => prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSave({
        name: name.trim(),
        category: category.trim() || "general",
        external_id: externalId.trim() || undefined,
        description: description.trim() || undefined,
        evidence_types: evidenceTypes,
        sort_order: sortOrder,
      });
      onClose();
    } catch {
      toast("Failed to save control", "error");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{initial ? "Edit Control" : "Add Control"}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20} /></button>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name <span className="text-red-500">*</span></label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. MFA Enforcement"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <input
              type="text"
              value={category}
              onChange={e => setCategory(e.target.value)}
              placeholder="access_control"
              list="cat-suggestions"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <datalist id="cat-suggestions">
              {CATEGORY_SUGGESTIONS.map(c => <option key={c} value={c} />)}
            </datalist>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">External ID</label>
            <input
              type="text"
              value={externalId}
              onChange={e => setExternalId(e.target.value)}
              placeholder="e.g. CC6.1"
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              rows={2}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500 resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Evidence Types</label>
            <div className="flex flex-wrap gap-2">
              {EVIDENCE_TYPE_OPTIONS.map(t => {
                const selected = evidenceTypes.includes(t);
                return (
                  <button
                    key={t}
                    type="button"
                    onClick={() => toggleType(t)}
                    className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                      selected
                        ? "bg-violet-600 border-violet-600 text-white"
                        : "bg-white border-gray-300 text-gray-600 hover:border-violet-400"
                    }`}
                  >
                    {t}
                  </button>
                );
              })}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
            <input
              type="number"
              value={sortOrder}
              onChange={e => setSortOrder(parseInt(e.target.value, 10) || 0)}
              className="w-24 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancel</button>
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-violet-600 text-white hover:bg-violet-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Control"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Builder view ──────────────────────────────────────────────────────────────

function FrameworkBuilder({
  frameworkId,
  onBack,
}: {
  frameworkId: string;
  onBack: () => void;
}) {
  const [fw, setFw] = useState<any>(null);
  const [score, setScore] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [showAddControl, setShowAddControl] = useState(false);
  const [editControl, setEditControl] = useState<any>(null);
  const [deletingControl, setDeletingControl] = useState<string | null>(null);
  const [editingName, setEditingName] = useState(false);
  const [nameVal, setNameVal] = useState("");
  const [editingDesc, setEditingDesc] = useState(false);
  const [descVal, setDescVal] = useState("");

  async function load() {
    setLoading(true);
    try {
      const [fwData, scoreData] = await Promise.all([
        api.getCustomFramework(frameworkId),
        api.getCustomFrameworkScore(frameworkId),
      ]);
      setFw(fwData);
      setScore(scoreData);
      setNameVal(fwData.name);
      setDescVal(fwData.description ?? "");
    } catch {
      toast("Failed to load framework", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [frameworkId]);

  async function saveName() {
    if (!nameVal.trim()) return;
    try {
      const updated = await api.updateCustomFramework(frameworkId, { name: nameVal.trim() });
      setFw({ ...fw, name: updated.name });
      setEditingName(false);
      toast("Name updated");
    } catch {
      toast("Failed to update", "error");
    }
  }

  async function saveDesc() {
    try {
      await api.updateCustomFramework(frameworkId, { description: descVal });
      setFw({ ...fw, description: descVal });
      setEditingDesc(false);
    } catch {
      toast("Failed to update", "error");
    }
  }

  async function handleAddControl(data: any) {
    await api.addCustomControl(frameworkId, data);
    await load();
    toast("Control added");
  }

  async function handleEditControl(data: any) {
    await api.updateCustomControl(frameworkId, editControl.id, data);
    await load();
    toast("Control updated");
  }

  async function handleDeleteControl(controlId: string) {
    setDeletingControl(controlId);
    try {
      await api.deleteCustomControl(frameworkId, controlId);
      await load();
      toast("Control deleted");
    } catch {
      toast("Failed to delete", "error");
    } finally {
      setDeletingControl(null);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600" />
      </div>
    );
  }

  if (!fw) return null;

  const scoreColor = !score ? "text-gray-400" : score.overall_score >= 75 ? "text-emerald-600" : score.overall_score >= 50 ? "text-amber-600" : "text-red-500";
  const scoreMap: Record<string, any> = {};
  if (score?.controls) {
    for (const sc of score.controls) scoreMap[sc.id] = sc;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Back + Header */}
      <div>
        <button
          onClick={onBack}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-4"
        >
          <ChevronLeft size={16} /> All Frameworks
        </button>

        <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 text-white">
          <div className="flex flex-col sm:flex-row sm:items-start gap-4">
            <div className="flex-1 min-w-0">
              {editingName ? (
                <div className="flex items-center gap-2">
                  <input
                    value={nameVal}
                    onChange={e => setNameVal(e.target.value)}
                    className="text-xl font-bold bg-white/10 rounded-lg px-3 py-1 text-white focus:outline-none focus:ring-2 focus:ring-violet-400 w-full"
                    autoFocus
                    onKeyDown={e => e.key === "Enter" && saveName()}
                  />
                  <button onClick={saveName} className="text-xs bg-violet-600 px-3 py-1 rounded-lg hover:bg-violet-700">Save</button>
                  <button onClick={() => setEditingName(false)} className="text-xs text-gray-400 hover:text-white">Cancel</button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold truncate">{fw.name}</h1>
                  <span className="text-xs bg-violet-600 px-2 py-0.5 rounded-full">v{fw.version}</span>
                  <button onClick={() => setEditingName(true)} className="text-gray-400 hover:text-white">
                    <Pencil size={14} />
                  </button>
                </div>
              )}
              {editingDesc ? (
                <div className="mt-2 flex items-start gap-2">
                  <textarea
                    value={descVal}
                    onChange={e => setDescVal(e.target.value)}
                    rows={2}
                    className="text-sm bg-white/10 rounded-lg px-3 py-1 text-gray-200 focus:outline-none focus:ring-2 focus:ring-violet-400 w-full resize-none"
                    autoFocus
                  />
                  <div className="flex flex-col gap-1">
                    <button onClick={saveDesc} className="text-xs bg-violet-600 px-3 py-1 rounded-lg hover:bg-violet-700">Save</button>
                    <button onClick={() => setEditingDesc(false)} className="text-xs text-gray-400 hover:text-white">Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-start gap-2 mt-1">
                  <p className="text-sm text-gray-300">{fw.description || "No description"}</p>
                  <button onClick={() => setEditingDesc(true)} className="text-gray-500 hover:text-white shrink-0 mt-0.5">
                    <Pencil size={12} />
                  </button>
                </div>
              )}
            </div>
            {score && (
              <div className="flex items-center gap-3 shrink-0">
                <ScoreRing score={score.overall_score} />
                <div>
                  <div className={`text-2xl font-bold ${scoreColor}`}>{score.overall_score}%</div>
                  <div className="text-xs text-gray-400">{score.passing_controls}/{score.total_controls} passing</div>
                </div>
              </div>
            )}
          </div>
          {/* Progress bar */}
          {score && score.total_controls > 0 && (
            <div className="mt-4">
              <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                <div
                  className="h-full bg-violet-500 rounded-full transition-all duration-500"
                  style={{ width: `${(score.passing_controls / score.total_controls) * 100}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-1">{score.passing_controls} of {score.total_controls} controls have recent evidence</p>
            </div>
          )}
        </div>
      </div>

      {/* Controls list */}
      <div className="bg-white rounded-2xl shadow-sm border">
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-sm font-semibold text-gray-700">Controls ({fw.controls?.length ?? 0})</h2>
          <button
            onClick={() => setShowAddControl(true)}
            className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg bg-violet-600 text-white hover:bg-violet-700"
          >
            <Plus size={14} /> Add Control
          </button>
        </div>

        {(!fw.controls || fw.controls.length === 0) ? (
          <div className="p-12 text-center text-gray-400">
            <Layers size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No controls yet. Add your first control.</p>
          </div>
        ) : (
          <div className="divide-y">
            {fw.controls.map((ctrl: any) => {
              const ctrlScore = scoreMap[ctrl.id];
              return (
                <div key={ctrl.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-start gap-3 min-w-0">
                      <StatusDot status={ctrlScore?.status ?? "no_evidence"} />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-sm font-medium text-gray-900">{ctrl.name}</span>
                          {ctrl.external_id && (
                            <span className="text-[10px] font-mono bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
                              {ctrl.external_id}
                            </span>
                          )}
                          <CategoryBadge cat={ctrl.category} />
                        </div>
                        {ctrl.description && (
                          <p className="text-xs text-gray-400 mt-0.5">{ctrl.description}</p>
                        )}
                        {ctrl.evidence_types && ctrl.evidence_types.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1.5">
                            {ctrl.evidence_types.map((t: string) => (
                              <span key={t} className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 flex items-center gap-1">
                                <Tag size={8} />
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                        {ctrlScore && (
                          <p className={`text-xs mt-1 ${ctrlScore.status === "passing" ? "text-emerald-600" : "text-gray-400"}`}>
                            {ctrlScore.status === "passing"
                              ? `${ctrlScore.evidence_count} evidence item(s) in last 30 days`
                              : "No recent evidence"}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        onClick={() => setEditControl(ctrl)}
                        className="text-gray-400 hover:text-violet-600 p-1 rounded"
                        title="Edit"
                      >
                        <Pencil size={14} />
                      </button>
                      <button
                        onClick={() => handleDeleteControl(ctrl.id)}
                        disabled={deletingControl === ctrl.id}
                        className="text-gray-400 hover:text-red-500 p-1 rounded disabled:opacity-50"
                        title="Delete"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {showAddControl && (
        <ControlModal
          frameworkId={frameworkId}
          onClose={() => setShowAddControl(false)}
          onSave={handleAddControl}
        />
      )}
      {editControl && (
        <ControlModal
          frameworkId={frameworkId}
          initial={editControl}
          onClose={() => setEditControl(null)}
          onSave={handleEditControl}
        />
      )}
    </div>
  );
}

// ── List view ─────────────────────────────────────────────────────────────────

function FrameworkCard({
  fw,
  onOpen,
  onDelete,
}: {
  fw: any;
  onOpen: () => void;
  onDelete: () => void;
}) {
  const [confirming, setConfirming] = useState(false);

  return (
    <div className="bg-white rounded-2xl border shadow-sm hover:shadow-md transition-shadow p-5">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-sm font-semibold text-gray-900 truncate">{fw.name}</h3>
            <span className="text-[10px] bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full font-medium">v{fw.version}</span>
            {fw.is_active
              ? <span className="text-[10px] bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">Active</span>
              : <span className="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-medium">Inactive</span>
            }
          </div>
          {fw.description && (
            <p className="text-xs text-gray-400 mt-1 line-clamp-2">{fw.description}</p>
          )}
        </div>
        <ScoreRing score={0} />
      </div>
      <p className="text-xs text-gray-500 mb-4">
        {fw.control_count} control{fw.control_count !== 1 ? "s" : ""}
      </p>
      <div className="flex items-center gap-2">
        <button
          onClick={onOpen}
          className="flex-1 text-sm font-medium py-1.5 rounded-lg bg-violet-600 text-white hover:bg-violet-700 transition-colors"
        >
          Open
        </button>
        {confirming ? (
          <div className="flex items-center gap-1">
            <button
              onClick={onDelete}
              className="text-xs text-red-600 font-medium px-2 py-1 border border-red-200 rounded-lg hover:bg-red-50"
            >
              Confirm
            </button>
            <button
              onClick={() => setConfirming(false)}
              className="text-xs text-gray-500 px-2 py-1"
            >
              Cancel
            </button>
          </div>
        ) : (
          <button
            onClick={() => setConfirming(true)}
            className="p-1.5 text-gray-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition-colors"
            title="Delete framework"
          >
            <Trash2 size={15} />
          </button>
        )}
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function CustomFrameworksPage() {
  const [frameworks, setFrameworks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [openFrameworkId, setOpenFrameworkId] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const data = await api.getCustomFrameworks();
      setFrameworks(data);
    } catch {
      toast("Failed to load frameworks", "error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(data: { name: string; description?: string; version: string }) {
    const created = await api.createCustomFramework(data);
    setFrameworks(prev => [created, ...prev]);
    toast("Framework created");
  }

  async function handleDelete(id: string) {
    try {
      await api.deleteCustomFramework(id);
      setFrameworks(prev => prev.filter(f => f.id !== id));
      toast("Framework deleted");
    } catch {
      toast("Failed to delete framework", "error");
    }
  }

  if (openFrameworkId) {
    return (
      <div className="p-6 max-w-4xl mx-auto">
        <FrameworkBuilder
          frameworkId={openFrameworkId}
          onBack={() => { setOpenFrameworkId(null); load(); }}
        />
      </div>
    );
  }

  const total = frameworks.length;
  const active = frameworks.filter(f => f.is_active).length;
  const totalControls = frameworks.reduce((s, f) => s + (f.control_count ?? 0), 0);

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6 animate-fade-in">
      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 text-white">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-violet-600/30 rounded-xl">
                <Layers size={22} className="text-violet-400" />
              </div>
              <h1 className="text-2xl font-bold">Custom Frameworks</h1>
            </div>
            <p className="text-gray-400 text-sm">
              Build internal control frameworks and map your own security policies — SOC 2 CC1, ISO A.5
            </p>
            <div className="flex gap-6 mt-4">
              <div>
                <div className="text-xl font-bold">{total}</div>
                <div className="text-xs text-gray-400">Total</div>
              </div>
              <div>
                <div className="text-xl font-bold text-emerald-400">{active}</div>
                <div className="text-xs text-gray-400">Active</div>
              </div>
              <div>
                <div className="text-xl font-bold text-violet-400">{totalControls}</div>
                <div className="text-xs text-gray-400">Total Controls</div>
              </div>
            </div>
          </div>
          <button
            onClick={() => setShowNew(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium transition-colors shrink-0"
          >
            <Plus size={16} /> New Framework
          </button>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600" />
        </div>
      ) : frameworks.length === 0 ? (
        <div className="bg-white rounded-2xl border shadow-sm p-16 text-center">
          <Layers size={40} className="mx-auto mb-4 text-violet-300" />
          <h2 className="text-lg font-semibold text-gray-700 mb-2">Build your first framework</h2>
          <p className="text-sm text-gray-400 mb-6">
            Create custom control frameworks for internal policies, niche regulations, or client-specific requirements.
          </p>
          <button
            onClick={() => setShowNew(true)}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-medium hover:bg-violet-700"
          >
            <Plus size={16} /> New Framework
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {frameworks.map(fw => (
            <FrameworkCard
              key={fw.id}
              fw={fw}
              onOpen={() => setOpenFrameworkId(fw.id)}
              onDelete={() => handleDelete(fw.id)}
            />
          ))}
        </div>
      )}

      {showNew && (
        <NewFrameworkModal
          onClose={() => setShowNew(false)}
          onSave={handleCreate}
        />
      )}
    </div>
  );
}
