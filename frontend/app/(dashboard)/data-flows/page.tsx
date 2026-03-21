"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { DataFlow } from "@/lib/types";
import {
  Workflow,
  RefreshCw,
  Plus,
  Trash2,
  X,
  ChevronDown,
  AlertTriangle,
  Globe,
  ArrowRight,
  Download,
} from "lucide-react";
import { toast } from "@/lib/toast";

// ── Constants ──────────────────────────────────────────────────────────────

const RISK_STYLES: Record<string, string> = {
  low: "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium: "bg-amber-50 text-amber-700 border-amber-200",
  high: "bg-orange-50 text-orange-700 border-orange-200",
  critical: "bg-red-50 text-red-600 border-red-200",
};

const CATEGORY_STYLES: Record<string, string> = {
  personal: "bg-blue-50 text-blue-700",
  sensitive: "bg-purple-50 text-purple-700",
  financial: "bg-emerald-50 text-emerald-700",
  operational: "bg-gray-50 text-gray-600",
};

const REGION_LABELS: Record<string, string> = {
  us: "United States",
  eu: "European Union",
  global: "Global",
  unknown: "Unknown",
};

const REGULATION_LABELS: Record<string, string> = {
  gdpr: "GDPR",
  ccpa: "CCPA",
  hipaa: "HIPAA",
  pci_dss: "PCI DSS",
  soc2: "SOC 2",
};

const DATA_CATEGORIES = ["personal", "sensitive", "financial", "operational"];
const RISK_LEVELS = ["low", "medium", "high", "critical"];
const REGIONS = ["us", "eu", "global", "unknown"];
const REGULATIONS = ["gdpr", "ccpa", "hipaa", "pci_dss", "soc2"];

// ── Sankey-style flow viz ──────────────────────────────────────────────────

function FlowSummary({ flows }: { flows: DataFlow[] }) {
  const byTool = flows.reduce<Record<string, { label: string; count: number; risk: string }>>((acc, f) => {
    if (!acc[f.tool]) acc[f.tool] = { label: f.tool_label, count: 0, risk: "low" };
    acc[f.tool].count++;
    const order = ["low", "medium", "high", "critical"];
    if (order.indexOf(f.risk_level) > order.indexOf(acc[f.tool].risk)) {
      acc[f.tool].risk = f.risk_level;
    }
    return acc;
  }, {});

  const byCategory = flows.reduce<Record<string, number>>((acc, f) => {
    acc[f.data_category] = (acc[f.data_category] || 0) + 1;
    return acc;
  }, {});

  const byRegulation = flows.reduce<Record<string, number>>((acc, f) => {
    f.regulations.forEach((r) => { acc[r] = (acc[r] || 0) + 1; });
    return acc;
  }, {});

  const crossBorder = flows.filter((f) => f.is_cross_border).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className="bg-white rounded-2xl border border-gray-100 p-4">
        <p className="text-xs text-gray-400 font-medium mb-1">Total Data Flows</p>
        <p className="text-3xl font-bold text-gray-900">{flows.length}</p>
        <p className="text-xs text-gray-400 mt-1">{Object.keys(byTool).length} tools</p>
      </div>
      <div className="bg-white rounded-2xl border border-gray-100 p-4">
        <p className="text-xs text-gray-400 font-medium mb-2">By Category</p>
        <div className="space-y-1">
          {Object.entries(byCategory).map(([cat, count]) => (
            <div key={cat} className="flex items-center justify-between">
              <span className={`text-xs px-1.5 py-0.5 rounded-md font-medium capitalize ${CATEGORY_STYLES[cat] ?? "bg-gray-50 text-gray-600"}`}>{cat}</span>
              <span className="text-xs font-semibold text-gray-700">{count}</span>
            </div>
          ))}
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-100 p-4">
        <p className="text-xs text-gray-400 font-medium mb-2">Regulations Triggered</p>
        <div className="space-y-1">
          {Object.entries(byRegulation).map(([reg, count]) => (
            <div key={reg} className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-700">{REGULATION_LABELS[reg] ?? reg.toUpperCase()}</span>
              <span className="text-xs font-semibold text-gray-500">{count} flows</span>
            </div>
          ))}
          {Object.keys(byRegulation).length === 0 && <p className="text-xs text-gray-400">None detected</p>}
        </div>
      </div>
      <div className="bg-white rounded-2xl border border-gray-100 p-4">
        <p className="text-xs text-gray-400 font-medium mb-1">Cross-Border Transfers</p>
        <p className="text-3xl font-bold text-gray-900">{crossBorder}</p>
        <p className="text-xs text-gray-400 mt-1">of {flows.length} flows</p>
        {crossBorder > 0 && (
          <div className="flex items-center gap-1 mt-2">
            <Globe className="w-3 h-3 text-amber-500" />
            <span className="text-xs text-amber-600 font-medium">Review SCCs / BCRs</span>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Flow row ───────────────────────────────────────────────────────────────

function FlowRow({ flow, onDelete, onEdit }: { flow: DataFlow; onDelete: () => void; onEdit: () => void }) {
  return (
    <tr className="hover:bg-gray-50/60 transition-colors group">
      <td className="px-4 py-3 text-sm">
        <div className="flex items-center gap-2">
          <span className="font-medium text-gray-900">{flow.tool_label}</span>
          {flow.is_auto_detected && (
            <span className="text-[10px] bg-brand-50 text-brand-600 px-1.5 py-0.5 rounded-md font-medium">Auto</span>
          )}
        </div>
        <p className="text-xs text-gray-400 mt-0.5">{flow.tool}</p>
      </td>
      <td className="px-4 py-3 text-sm">
        <div className="flex items-center gap-1.5 text-gray-600">
          <span className="font-medium capitalize">{flow.data_type.replace(/_/g, " ")}</span>
        </div>
        <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium capitalize ${CATEGORY_STYLES[flow.data_category] ?? "bg-gray-50 text-gray-600"}`}>
          {flow.data_category}
        </span>
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {REGION_LABELS[flow.region] ?? flow.region}
        {flow.is_cross_border && (
          <Globe className="inline-block w-3 h-3 ml-1 text-amber-500" />
        )}
      </td>
      <td className="px-4 py-3">
        <span className={`text-xs px-2 py-1 rounded-lg border font-semibold capitalize ${RISK_STYLES[flow.risk_level] ?? "bg-gray-50 text-gray-600 border-gray-200"}`}>
          {flow.risk_level}
        </span>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        <div className="flex flex-wrap gap-1">
          {flow.regulations.map((r) => (
            <span key={r} className="bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded-md font-medium">
              {REGULATION_LABELS[r] ?? r.toUpperCase()}
            </span>
          ))}
        </div>
      </td>
      <td className="px-4 py-3 text-xs text-gray-400 max-w-[140px] truncate">{flow.purpose ?? "—"}</td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={onEdit}
            className="text-xs text-brand-600 hover:text-brand-700 px-2 py-1 rounded-lg hover:bg-brand-50 transition-colors font-medium"
          >
            Edit
          </button>
          <button
            onClick={onDelete}
            className="text-gray-400 hover:text-red-500 p-1 rounded-lg hover:bg-red-50 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        </div>
      </td>
    </tr>
  );
}

// ── Add/Edit Modal ─────────────────────────────────────────────────────────

function FlowModal({
  initial,
  onClose,
  onSave,
}: {
  initial?: DataFlow;
  onClose: () => void;
  onSave: (data: Partial<DataFlow>) => Promise<void>;
}) {
  const [form, setForm] = useState({
    data_type: initial?.data_type ?? "",
    data_category: initial?.data_category ?? "personal",
    tool: initial?.tool ?? "",
    tool_label: initial?.tool_label ?? "",
    region: initial?.region ?? "unknown",
    risk_level: initial?.risk_level ?? "medium",
    regulations: initial?.regulations ?? [],
    purpose: initial?.purpose ?? "",
    legal_basis: initial?.legal_basis ?? "",
    is_cross_border: initial?.is_cross_border ?? false,
    notes: initial?.notes ?? "",
  });
  const [saving, setSaving] = useState(false);

  const toggleReg = (r: string) => {
    setForm((p) => ({
      ...p,
      regulations: p.regulations.includes(r) ? p.regulations.filter((x) => x !== r) : [...p.regulations, r],
    }));
  };

  const handleSave = async () => {
    if (!form.data_type || !form.tool || !form.tool_label) return;
    setSaving(true);
    try {
      await onSave({
        ...form,
        purpose: form.purpose || null,
        legal_basis: form.legal_basis || null,
        notes: form.notes || null,
      });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <h2 className="font-bold text-gray-900">{initial ? "Edit Data Flow" : "Add Data Flow"}</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tool / Service *</label>
              <input
                value={form.tool_label}
                onChange={(e) => setForm((p) => ({ ...p, tool_label: e.target.value }))}
                placeholder="e.g. Salesforce"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Tool key *</label>
              <input
                value={form.tool}
                onChange={(e) => setForm((p) => ({ ...p, tool: e.target.value }))}
                placeholder="e.g. salesforce"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Data type *</label>
              <input
                value={form.data_type}
                onChange={(e) => setForm((p) => ({ ...p, data_type: e.target.value }))}
                placeholder="e.g. email_address"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
              <select
                value={form.data_category}
                onChange={(e) => setForm((p) => ({ ...p, data_category: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {DATA_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Region</label>
              <select
                value={form.region}
                onChange={(e) => setForm((p) => ({ ...p, region: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {REGIONS.map((r) => (
                  <option key={r} value={r}>{REGION_LABELS[r] ?? r}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Risk level</label>
              <select
                value={form.risk_level}
                onChange={(e) => setForm((p) => ({ ...p, risk_level: e.target.value }))}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
              >
                {RISK_LEVELS.map((r) => (
                  <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">Applicable regulations</label>
            <div className="flex flex-wrap gap-2">
              {REGULATIONS.map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => toggleReg(r)}
                  className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition-colors ${
                    form.regulations.includes(r)
                      ? "bg-brand-600 text-white border-brand-600"
                      : "bg-white text-gray-600 border-gray-200 hover:border-brand-400"
                  }`}
                >
                  {REGULATION_LABELS[r] ?? r.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="cross_border"
              checked={form.is_cross_border}
              onChange={(e) => setForm((p) => ({ ...p, is_cross_border: e.target.checked }))}
              className="rounded"
            />
            <label htmlFor="cross_border" className="text-sm text-gray-700">Cross-border transfer</label>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Purpose</label>
            <input
              value={form.purpose}
              onChange={(e) => setForm((p) => ({ ...p, purpose: e.target.value }))}
              placeholder="e.g. CRM, analytics, billing"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Legal basis (GDPR)</label>
            <input
              value={form.legal_basis}
              onChange={(e) => setForm((p) => ({ ...p, legal_basis: e.target.value }))}
              placeholder="e.g. legitimate_interest, contract"
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
              rows={2}
              className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 px-5 pb-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !form.data_type || !form.tool || !form.tool_label}
            className="px-4 py-2 text-sm bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors disabled:opacity-50 font-medium"
          >
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function DataFlowsPage() {
  const [flows, setFlows] = useState<DataFlow[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editFlow, setEditFlow] = useState<DataFlow | null>(null);
  const [filterRisk, setFilterRisk] = useState("all");
  const [filterCat, setFilterCat] = useState("all");
  const [search, setSearch] = useState("");

  useEffect(() => {
    api.getDataFlows().then(setFlows).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleScan = async () => {
    setScanning(true);
    try {
      const updated = await api.scanDataFlows();
      setFlows(updated);
      toast(`Scanned — ${updated.length} data flows mapped`);
    } catch {
      toast("Scan failed", "error");
    } finally {
      setScanning(false);
    }
  };

  const handleCreate = async (data: Partial<DataFlow>) => {
    const created = await api.createDataFlow(data);
    setFlows((prev) => [created, ...prev]);
    toast("Data flow added");
  };

  const handleUpdate = async (data: Partial<DataFlow>) => {
    if (!editFlow) return;
    const updated = await api.updateDataFlow(editFlow.id, data);
    setFlows((prev) => prev.map((f) => (f.id === updated.id ? updated : f)));
    toast("Updated");
  };

  const handleDelete = async (id: string) => {
    await api.deleteDataFlow(id);
    setFlows((prev) => prev.filter((f) => f.id !== id));
    toast("Removed");
  };

  const exportCsv = () => {
    const rows = [
      ["Tool", "Data Type", "Category", "Region", "Risk", "Regulations", "Cross-border", "Purpose", "Legal Basis"],
      ...flows.map((f) => [
        f.tool_label,
        f.data_type.replace(/_/g, " "),
        f.data_category,
        REGION_LABELS[f.region] ?? f.region,
        f.risk_level,
        f.regulations.map((r) => REGULATION_LABELS[r] ?? r).join("; "),
        f.is_cross_border ? "Yes" : "No",
        f.purpose ?? "",
        f.legal_basis ?? "",
      ]),
    ];
    const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "data-flow-map.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  const filtered = flows.filter((f) => {
    if (filterRisk !== "all" && f.risk_level !== filterRisk) return false;
    if (filterCat !== "all" && f.data_category !== filterCat) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!f.tool_label.toLowerCase().includes(q) && !f.data_type.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const criticalCount = flows.filter((f) => f.risk_level === "critical").length;
  const highCount = flows.filter((f) => f.risk_level === "high").length;

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-brand-100 flex items-center justify-center shrink-0">
            <Workflow className="w-4 h-4 text-brand-600" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight truncate">Data Flow Map</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Auto-mapped from your connected integrations. Visualize what data flows where, and which regulations apply.</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button
            onClick={exportCsv}
            className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export CSV</span>
          </button>
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">{scanning ? "Scanning…" : "Re-scan"}</span>
          </button>
          <button
            onClick={() => { setEditFlow(null); setShowModal(true); }}
            className="flex items-center gap-1.5 px-3 py-2 text-xs bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors font-medium"
          >
            <Plus className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Add Flow</span>
            <span className="sm:hidden">Add</span>
          </button>
        </div>
      </div>

      {/* Alerts */}
      {(criticalCount > 0 || highCount > 0) && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-2xl px-4 py-3 mb-5">
          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <p className="text-sm text-red-700">
            <span className="font-semibold">Attention: </span>
            {criticalCount > 0 && <>{criticalCount} critical</>}
            {criticalCount > 0 && highCount > 0 && " and "}
            {highCount > 0 && <>{highCount} high-risk</>}
            {" "}data {criticalCount + highCount === 1 ? "flow requires" : "flows require"} review.
          </p>
        </div>
      )}

      {/* Summary cards */}
      {!loading && flows.length > 0 && <FlowSummary flows={flows} />}

      {/* Flow path legend */}
      {!loading && flows.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-5">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">Data Flow Path</p>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="flex items-center gap-1.5 bg-blue-50 border border-blue-100 rounded-xl px-3 py-1.5">
              <span className="w-2 h-2 rounded-full bg-blue-400" />
              <span className="text-xs font-medium text-blue-700">Data Subject</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-gray-300" />
            <div className="flex items-center gap-1.5 bg-brand-50 border border-brand-100 rounded-xl px-3 py-1.5">
              <span className="w-2 h-2 rounded-full bg-brand-500" />
              <span className="text-xs font-medium text-brand-700">Your Systems</span>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-gray-300" />
            {Array.from(new Set(flows.map((f) => f.tool_label))).slice(0, 4).map((label) => (
              <div key={label} className="flex items-center gap-1">
                <div className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-xl px-3 py-1.5">
                  <span className="w-2 h-2 rounded-full bg-gray-400" />
                  <span className="text-xs font-medium text-gray-600">{label}</span>
                </div>
                <ArrowRight className="w-3 h-3 text-gray-200" />
              </div>
            ))}
            {flows.length > 4 && (
              <span className="text-xs text-gray-400">+{Array.from(new Set(flows.map((f) => f.tool_label))).length - 4} more</span>
            )}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-2 mb-4 flex-wrap">
        <input
          type="search"
          placeholder="Search tool or data type…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 w-full sm:w-52"
        />
        <select
          value={filterRisk}
          onChange={(e) => setFilterRisk(e.target.value)}
          className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        >
          <option value="all">All risks</option>
          {RISK_LEVELS.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
        </select>
        <select
          value={filterCat}
          onChange={(e) => setFilterCat(e.target.value)}
          className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        >
          <option value="all">All categories</option>
          {DATA_CATEGORIES.map((c) => <option key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</option>)}
        </select>
        {(filterRisk !== "all" || filterCat !== "all" || search) && (
          <button
            onClick={() => { setFilterRisk("all"); setFilterCat("all"); setSearch(""); }}
            className="text-xs text-gray-500 hover:text-gray-700 underline underline-offset-2"
          >
            Clear filters
          </button>
        )}
        <span className="ml-auto text-xs text-gray-400">{filtered.length} of {flows.length} flows</span>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <Workflow className="w-8 h-8 text-gray-200 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-500">
              {flows.length === 0 ? "No data flows yet" : "No flows match your filters"}
            </p>
            {flows.length === 0 && (
              <p className="text-xs text-gray-400 mt-1 mb-4">
                Connect integrations and click Re-scan, or add a flow manually.
              </p>
            )}
            {flows.length === 0 && (
              <button
                onClick={handleScan}
                disabled={scanning}
                className="text-sm text-brand-600 hover:text-brand-700 font-medium"
              >
                {scanning ? "Scanning…" : "Scan now →"}
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Tool</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Data</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Region</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Risk</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Regulations</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Purpose</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.map((flow) => (
                  <FlowRow
                    key={flow.id}
                    flow={flow}
                    onDelete={() => handleDelete(flow.id)}
                    onEdit={() => { setEditFlow(flow); setShowModal(true); }}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <FlowModal
          initial={editFlow ?? undefined}
          onClose={() => { setShowModal(false); setEditFlow(null); }}
          onSave={editFlow ? handleUpdate : handleCreate}
        />
      )}
    </div>
  );
}
