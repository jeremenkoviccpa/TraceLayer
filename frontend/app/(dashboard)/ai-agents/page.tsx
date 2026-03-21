"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { AiAgentEvent, AiAgentSession } from "@/lib/types";
import {
  Bot, AlertTriangle, Flag, CheckCircle2, X, Plus,
  ChevronRight, ArrowRight, Clock, Layers, Download,
  RefreshCw, Eye, Trash2, Filter,
} from "lucide-react";
import { toast } from "@/lib/toast";

// ── Constants ──────────────────────────────────────────────────────────────

const RISK_STYLES: Record<string, string> = {
  low:      "bg-emerald-50 text-emerald-700 border-emerald-200",
  medium:   "bg-amber-50 text-amber-700 border-amber-200",
  high:     "bg-orange-50 text-orange-700 border-orange-200",
  critical: "bg-red-50 text-red-600 border-red-200",
};

const RISK_DOT: Record<string, string> = {
  low:      "bg-emerald-500",
  medium:   "bg-amber-500",
  high:     "bg-orange-500",
  critical: "bg-red-500",
};

const ACTION_STYLES: Record<string, string> = {
  data_write:    "bg-red-50 text-red-700",
  data_delete:   "bg-red-100 text-red-800",
  api_call:      "bg-blue-50 text-blue-700",
  tool_use:      "bg-purple-50 text-purple-700",
  function_call: "bg-indigo-50 text-indigo-700",
  data_read:     "bg-gray-50 text-gray-600",
};

const AGENT_COLORS: Record<string, string> = {
  openai:    "bg-gray-900 text-white",
  anthropic: "bg-orange-700 text-white",
  gemini:    "bg-blue-600 text-white",
  custom:    "bg-brand-600 text-white",
};

const FLAG_LABELS: Record<string, string> = {
  pii_exfiltration:         "PII Exfiltration",
  unauthenticated_endpoint: "Unauth Endpoint",
  cross_border:             "Cross-border",
  chain_escalation:         "Chain Escalation",
  unreviewed_tool:          "Unreviewed Tool",
  high_volume:              "High Volume",
};

const RISK_ORDER: Record<string, number> = { critical: 3, high: 2, medium: 1, low: 0 };

// ── Detail modal ───────────────────────────────────────────────────────────

function EventDetailModal({
  event,
  onClose,
  onFlag,
  onReview,
}: {
  event: AiAgentEvent;
  onClose: () => void;
  onFlag: (flagged: boolean) => void;
  onReview: (by: string) => void;
}) {
  const [reviewName, setReviewName] = useState("");
  const [marking, setMarking] = useState(false);

  const handleReview = async () => {
    if (!reviewName.trim()) return;
    setMarking(true);
    try { await onReview(reviewName.trim()); } finally { setMarking(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <div className="flex items-center gap-2.5">
            <div className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${AGENT_COLORS[event.agent_type] ?? AGENT_COLORS.custom}`}>
              {event.agent_type.toUpperCase()}
            </div>
            <h2 className="font-bold text-gray-900 text-sm">{event.agent_name}</h2>
          </div>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>

        <div className="px-5 py-4 space-y-4">
          {/* Risk + status row */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs px-2.5 py-1 rounded-lg border font-semibold capitalize ${RISK_STYLES[event.risk_level]}`}>
              {event.risk_level} risk
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${event.status === "blocked" ? "bg-red-100 text-red-700" : event.status === "failed" ? "bg-orange-100 text-orange-700" : "bg-gray-100 text-gray-600"}`}>
              {event.status}
            </span>
            {event.is_flagged && (
              <span className="text-xs px-2 py-0.5 rounded-md font-medium bg-red-50 text-red-600 flex items-center gap-1">
                <Flag className="w-3 h-3" /> Flagged for review
              </span>
            )}
            {event.reviewed_by && (
              <span className="text-xs px-2 py-0.5 rounded-md font-medium bg-emerald-50 text-emerald-700 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Reviewed by {event.reviewed_by}
              </span>
            )}
          </div>

          {/* Action + Target */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1">Action</p>
              <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${ACTION_STYLES[event.action_type] ?? "bg-gray-100 text-gray-600"}`}>
                {event.action_type.replace(/_/g, " ")}
              </span>
            </div>
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1">Target</p>
              <p className="text-xs font-medium text-gray-800">{event.target_tool}</p>
              {event.target_url && <p className="text-[10px] text-gray-400 mt-0.5 truncate">{event.target_url}</p>}
            </div>
          </div>

          {/* Chain info */}
          {event.chain_depth > 0 && (
            <div className="flex items-center gap-2 bg-amber-50 border border-amber-100 rounded-xl px-3 py-2.5">
              <Layers className="w-3.5 h-3.5 text-amber-600 shrink-0" />
              <p className="text-xs text-amber-800">
                <span className="font-semibold">Chained call</span> — depth {event.chain_depth}
                {event.session_id && <span className="text-amber-600 ml-2">session: {event.session_id}</span>}
              </p>
            </div>
          )}

          {/* Data categories */}
          {event.data_categories.length > 0 && (
            <div>
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-2">Data categories involved</p>
              <div className="flex flex-wrap gap-1.5">
                {event.data_categories.map((c) => (
                  <span key={c} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-md font-medium capitalize">{c.replace(/_/g, " ")}</span>
                ))}
              </div>
            </div>
          )}

          {/* Risk flags */}
          {event.risk_flags.length > 0 && (
            <div>
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-2">Risk flags</p>
              <div className="flex flex-wrap gap-1.5">
                {event.risk_flags.map((f) => (
                  <span key={f} className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded-md font-medium flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" />
                    {FLAG_LABELS[f] ?? f.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Input / Output */}
          {(event.input_summary || event.output_summary) && (
            <div className="space-y-2">
              {event.input_summary && (
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1">Input (sanitized)</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{event.input_summary}</p>
                </div>
              )}
              {event.output_summary && (
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1">Output (sanitized)</p>
                  <p className="text-xs text-gray-700 leading-relaxed">{event.output_summary}</p>
                </div>
              )}
            </div>
          )}

          {/* Notes */}
          {event.notes && (
            <div className="bg-gray-50 rounded-xl p-3">
              <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider mb-1">Notes</p>
              <p className="text-xs text-gray-700">{event.notes}</p>
            </div>
          )}

          {/* Review action */}
          {!event.reviewed_by && (
            <div className="border border-gray-100 rounded-xl p-3">
              <p className="text-xs font-semibold text-gray-700 mb-2">Mark as reviewed</p>
              <div className="flex gap-2">
                <input
                  value={reviewName}
                  onChange={(e) => setReviewName(e.target.value)}
                  placeholder="Your name"
                  className="flex-1 text-xs border border-gray-200 rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                />
                <button
                  onClick={handleReview}
                  disabled={marking || !reviewName.trim()}
                  className="text-xs bg-brand-600 text-white px-3 py-1.5 rounded-lg hover:bg-brand-700 transition-colors disabled:opacity-50 font-medium"
                >
                  {marking ? "Saving…" : "Confirm"}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-between items-center px-5 pb-5">
          <button
            onClick={() => onFlag(!event.is_flagged)}
            className={`flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border font-medium transition-colors ${
              event.is_flagged
                ? "bg-red-50 text-red-700 border-red-200 hover:bg-red-100"
                : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"
            }`}
          >
            <Flag className="w-3.5 h-3.5" />
            {event.is_flagged ? "Unflag" : "Flag for review"}
          </button>
          <p className="text-[10px] text-gray-400">
            {new Date(event.created_at).toLocaleString()}
            {event.duration_ms && <span className="ml-2">{event.duration_ms}ms</span>}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Chain visualization ────────────────────────────────────────────────────

function ChainView({ session }: { session: AiAgentSession }) {
  const sorted = [...session.events].sort((a, b) => a.chain_depth - b.chain_depth || new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

  return (
    <div className="bg-gray-50 rounded-xl p-4 space-y-2">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-gray-400" />
          <span className="text-xs font-semibold text-gray-700">Chain: {session.session_id}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-2 py-0.5 rounded-md font-semibold border ${RISK_STYLES[session.max_risk_level]}`}>
            {session.max_risk_level}
          </span>
          <span className="text-[10px] text-gray-400">{session.total_events} calls · depth {session.max_chain_depth}</span>
        </div>
      </div>
      {sorted.map((e, i) => (
        <div key={e.id} className="flex items-center gap-2" style={{ paddingLeft: `${e.chain_depth * 20}px` }}>
          {e.chain_depth > 0 && <ArrowRight className="w-3 h-3 text-gray-300 shrink-0" />}
          <div className="flex items-center gap-2 bg-white rounded-lg px-2.5 py-1.5 border border-gray-100 flex-1 min-w-0">
            <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${RISK_DOT[e.risk_level]}`} />
            <span className="text-xs font-medium text-gray-700 truncate">{e.agent_name}</span>
            <ArrowRight className="w-3 h-3 text-gray-300 shrink-0" />
            <span className="text-xs text-gray-500 truncate">{e.target_tool}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium ml-auto shrink-0 ${ACTION_STYLES[e.action_type] ?? "bg-gray-100 text-gray-600"}`}>
              {e.action_type.replace(/_/g, " ")}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Log Event modal ────────────────────────────────────────────────────────

function LogModal({ onClose, onSave }: { onClose: () => void; onSave: (data: Partial<AiAgentEvent>) => Promise<void> }) {
  const [form, setForm] = useState({
    agent_name: "", agent_type: "custom", action_type: "api_call",
    target_tool: "", target_url: "", data_categories: [] as string[],
    input_summary: "", output_summary: "", session_id: "", chain_depth: 0,
    status: "completed", risk_flags: [] as string[], notes: "",
  });
  const [saving, setSaving] = useState(false);
  const catInput = useState("")[0];

  const toggleCat = (c: string) => setForm((p) => ({
    ...p,
    data_categories: p.data_categories.includes(c)
      ? p.data_categories.filter((x) => x !== c)
      : [...p.data_categories, c],
  }));

  const handleSave = async () => {
    if (!form.agent_name || !form.target_tool) return;
    setSaving(true);
    try {
      await onSave({ ...form, target_url: form.target_url || null, input_summary: form.input_summary || null, output_summary: form.output_summary || null, session_id: form.session_id || null, notes: form.notes || null });
      onClose();
    } finally { setSaving(false); }
  };

  const CATS = ["pii", "personal", "financial", "payment", "health", "biometric", "location", "credentials", "operational"];
  const AGENT_TYPES = ["openai", "anthropic", "gemini", "custom"];
  const ACTION_TYPES = ["api_call", "tool_use", "data_read", "data_write", "function_call", "data_delete"];

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 sticky top-0 bg-white rounded-t-2xl">
          <h2 className="font-bold text-gray-900">Log AI Agent Event</h2>
          <button onClick={onClose}><X className="w-4 h-4 text-gray-400" /></button>
        </div>
        <div className="px-5 py-4 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Agent name *</label>
              <input value={form.agent_name} onChange={(e) => setForm((p) => ({ ...p, agent_name: e.target.value }))} placeholder="e.g. GPT-4o, Claude 3.5" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Agent type</label>
              <select value={form.agent_type} onChange={(e) => setForm((p) => ({ ...p, agent_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
                {AGENT_TYPES.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Action type</label>
              <select value={form.action_type} onChange={(e) => setForm((p) => ({ ...p, action_type: e.target.value }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
                {ACTION_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Target tool *</label>
              <input value={form.target_tool} onChange={(e) => setForm((p) => ({ ...p, target_tool: e.target.value }))} placeholder="e.g. salesforce, stripe" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Target URL</label>
            <input value={form.target_url} onChange={(e) => setForm((p) => ({ ...p, target_url: e.target.value }))} placeholder="https://api.salesforce.com/..." className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Session ID</label>
              <input value={form.session_id} onChange={(e) => setForm((p) => ({ ...p, session_id: e.target.value }))} placeholder="Group chained calls" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Chain depth</label>
              <input type="number" min={0} max={10} value={form.chain_depth} onChange={(e) => setForm((p) => ({ ...p, chain_depth: parseInt(e.target.value) || 0 }))} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">Data categories</label>
            <div className="flex flex-wrap gap-1.5">
              {CATS.map((c) => (
                <button key={c} type="button" onClick={() => toggleCat(c)} className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition-colors ${form.data_categories.includes(c) ? "bg-brand-600 text-white border-brand-600" : "bg-white text-gray-600 border-gray-200 hover:border-brand-400"}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Input summary (sanitized)</label>
            <textarea value={form.input_summary} onChange={(e) => setForm((p) => ({ ...p, input_summary: e.target.value }))} rows={2} placeholder="What data was sent to the tool" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Output summary (sanitized)</label>
            <textarea value={form.output_summary} onChange={(e) => setForm((p) => ({ ...p, output_summary: e.target.value }))} rows={2} placeholder="What the tool returned" className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none" />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))} rows={2} className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 resize-none" />
          </div>
        </div>
        <div className="flex justify-end gap-2 px-5 pb-5">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">Cancel</button>
          <button onClick={handleSave} disabled={saving || !form.agent_name || !form.target_tool} className="px-4 py-2 text-sm bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors disabled:opacity-50 font-medium">
            {saving ? "Logging…" : "Log Event"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

export default function AiAgentsPage() {
  const [events, setEvents] = useState<AiAgentEvent[]>([]);
  const [sessions, setSessions] = useState<AiAgentSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"events" | "chains">("events");
  const [selected, setSelected] = useState<AiAgentEvent | null>(null);
  const [showLog, setShowLog] = useState(false);
  const [filterRisk, setFilterRisk] = useState("all");
  const [filterAgent, setFilterAgent] = useState("all");
  const [filterAction, setFilterAction] = useState("all");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
  const [search, setSearch] = useState("");

  const load = async () => {
    try {
      const [evts, sess] = await Promise.all([api.getAiAgentEvents(), api.getAiAgentSessions()]);
      setEvents(evts);
      setSessions(sess);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleLog = async (data: Partial<AiAgentEvent>) => {
    const created = await api.createAiAgentEvent(data);
    setEvents((p) => [created, ...p]);
    toast("Event logged");
    await load();
  };

  const handleFlag = async (flagged: boolean) => {
    if (!selected) return;
    const updated = await api.updateAiAgentEvent(selected.id, { is_flagged: flagged });
    setEvents((p) => p.map((e) => e.id === updated.id ? updated : e));
    setSelected(updated);
    toast(flagged ? "Flagged for review" : "Flag removed");
  };

  const handleReview = async (by: string) => {
    if (!selected) return;
    const updated = await api.updateAiAgentEvent(selected.id, { reviewed_by: by, is_flagged: false });
    setEvents((p) => p.map((e) => e.id === updated.id ? updated : e));
    setSelected(updated);
    toast("Marked as reviewed");
  };

  const handleDelete = async (id: string) => {
    await api.deleteAiAgentEvent(id);
    setEvents((p) => p.filter((e) => e.id !== id));
    if (selected?.id === id) setSelected(null);
    toast("Deleted");
  };

  const exportCsv = () => {
    const rows = [
      ["Time", "Agent", "Type", "Action", "Target", "Data Categories", "Risk", "Chain Depth", "Flags", "Status"],
      ...events.map((e) => [
        new Date(e.created_at).toISOString(),
        e.agent_name, e.agent_type, e.action_type.replace(/_/g, " "),
        e.target_tool,
        e.data_categories.join("; "),
        e.risk_level,
        String(e.chain_depth),
        e.risk_flags.join("; "),
        e.status,
      ]),
    ];
    const csv = rows.map((r) => r.map((c) => `"${c}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "ai-agent-events.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  // Summary stats
  const criticalHigh = events.filter((e) => e.risk_level === "critical" || e.risk_level === "high").length;
  const flagged = events.filter((e) => e.is_flagged).length;
  const uniqueAgents = new Set(events.map((e) => e.agent_name)).size;
  const maxDepth = events.length ? Math.max(...events.map((e) => e.chain_depth)) : 0;
  const chainedEvents = events.filter((e) => e.chain_depth > 0).length;

  // Filtered events
  const filtered = events.filter((e) => {
    if (filterRisk !== "all" && e.risk_level !== filterRisk) return false;
    if (filterAgent !== "all" && e.agent_type !== filterAgent) return false;
    if (filterAction !== "all" && e.action_type !== filterAction) return false;
    if (flaggedOnly && !e.is_flagged) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!e.agent_name.toLowerCase().includes(q) && !e.target_tool.toLowerCase().includes(q)) return false;
    }
    return true;
  });

  const agentTypes = Array.from(new Set(events.map((e) => e.agent_type)));
  const actionTypes = Array.from(new Set(events.map((e) => e.action_type)));

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-6">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-xl bg-brand-100 flex items-center justify-center shrink-0">
            <Bot className="w-4 h-4 text-brand-600" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight truncate">AI Agent Monitor</h1>
            <p className="text-xs sm:text-sm text-gray-500 hidden sm:block">Track every autonomous action your AI agents take across systems — what triggered, what data moved, and the full call chain.</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <button onClick={exportCsv} className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            <Download className="w-3.5 h-3.5" /><span className="hidden sm:inline">Export</span>
          </button>
          <button onClick={() => load()} className="flex items-center gap-1.5 px-3 py-2 text-xs text-gray-600 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors">
            <RefreshCw className="w-3.5 h-3.5" /><span className="hidden sm:inline">Refresh</span>
          </button>
          <button onClick={() => setShowLog(true)} className="flex items-center gap-1.5 px-3 py-2 text-xs bg-brand-600 text-white rounded-xl hover:bg-brand-700 transition-colors font-medium">
            <Plus className="w-3.5 h-3.5" /><span className="hidden sm:inline">Log Event</span><span className="sm:hidden">Log</span>
          </button>
        </div>
      </div>

      {/* Alert banner */}
      {criticalHigh > 0 && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-2xl px-4 py-3 mb-5">
          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <p className="text-sm text-red-700">
            <span className="font-semibold">{criticalHigh} high or critical risk event{criticalHigh > 1 ? "s" : ""}</span> require immediate review.
            {flagged > 0 && <span className="ml-2">{flagged} flagged for investigation.</span>}
          </p>
        </div>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-3 sm:grid-cols-5 gap-2 sm:gap-3 mb-6">
        {[
          { label: "Total Events",    value: events.length,     sub: "logged",          color: "text-gray-900" },
          { label: "Critical + High", value: criticalHigh,      sub: "risk events",     color: "text-red-600"  },
          { label: "Flagged",         value: flagged,           sub: "need review",     color: "text-orange-600" },
          { label: "Unique Agents",   value: uniqueAgents,      sub: "active",          color: "text-brand-600" },
          { label: "Deepest Chain",   value: maxDepth,          sub: `${chainedEvents} chained calls`, color: "text-purple-600" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-2xl border border-gray-100 p-3 sm:p-4">
            <p className="text-[10px] sm:text-xs text-gray-400 font-medium mb-1 leading-tight">{s.label}</p>
            <p className={`text-xl sm:text-2xl font-bold ${s.color}`}>{s.value}</p>
            <p className="text-[10px] text-gray-400 mt-0.5 hidden sm:block">{s.sub}</p>
          </div>
        ))}
      </div>

      {/* View toggle */}
      <div className="flex items-center gap-1 bg-gray-100 rounded-xl p-1 w-fit mb-5">
        {(["events", "chains"] as const).map((v) => (
          <button key={v} onClick={() => setView(v)} className={`text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors capitalize ${view === v ? "bg-white text-gray-900 shadow-sm" : "text-gray-500 hover:text-gray-700"}`}>
            {v === "chains" ? `Call Chains (${sessions.length})` : `All Events (${events.length})`}
          </button>
        ))}
      </div>

      {view === "chains" ? (
        /* ── Chain view ── */
        <div className="space-y-3">
          {sessions.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-100 text-center py-16">
              <Layers className="w-8 h-8 text-gray-200 mx-auto mb-3" />
              <p className="text-sm font-medium text-gray-500">No chained calls yet</p>
              <p className="text-xs text-gray-400 mt-1">Events with the same session_id will appear here.</p>
            </div>
          ) : (
            sessions
              .sort((a, b) => RISK_ORDER[b.max_risk_level] - RISK_ORDER[a.max_risk_level])
              .map((s) => <ChainView key={s.session_id} session={s} />)
          )}
        </div>
      ) : (
        /* ── Events view ── */
        <>
          {/* Filters */}
          <div className="flex items-center gap-2 mb-4 flex-wrap">
            <input
              type="search" placeholder="Search agent or tool…" value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 w-full sm:w-48"
            />
            <select value={filterRisk} onChange={(e) => setFilterRisk(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
              <option value="all">All risks</option>
              {["critical", "high", "medium", "low"].map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
            </select>
            <select value={filterAgent} onChange={(e) => setFilterAgent(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
              <option value="all">All agents</option>
              {agentTypes.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select value={filterAction} onChange={(e) => setFilterAction(e.target.value)} className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30">
              <option value="all">All actions</option>
              {actionTypes.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
            </select>
            <button
              onClick={() => setFlaggedOnly((v) => !v)}
              className={`flex items-center gap-1.5 text-xs px-3 py-2 rounded-xl border font-medium transition-colors ${flaggedOnly ? "bg-red-50 text-red-700 border-red-200" : "bg-white text-gray-600 border-gray-200 hover:bg-gray-50"}`}
            >
              <Flag className="w-3.5 h-3.5" />Flagged only
            </button>
            {(filterRisk !== "all" || filterAgent !== "all" || filterAction !== "all" || flaggedOnly || search) && (
              <button onClick={() => { setFilterRisk("all"); setFilterAgent("all"); setFilterAction("all"); setFlaggedOnly(false); setSearch(""); }} className="text-xs text-gray-500 hover:text-gray-700 underline underline-offset-2">
                Clear
              </button>
            )}
            <span className="ml-auto text-xs text-gray-400">{filtered.length} events</span>
          </div>

          {/* Table */}
          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-16">
                <Bot className="w-8 h-8 text-gray-200 mx-auto mb-3" />
                <p className="text-sm font-medium text-gray-500">{events.length === 0 ? "No agent events yet" : "No events match your filters"}</p>
                {events.length === 0 && <p className="text-xs text-gray-400 mt-1">Log an event manually or configure your AI agents to self-report via the API key ingest endpoint.</p>}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Agent</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Action</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Target</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Data</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Chain</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Risk</th>
                      <th className="text-left px-4 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Time</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {filtered.map((e) => (
                      <tr key={e.id} className="hover:bg-gray-50/60 transition-colors group cursor-pointer" onClick={() => setSelected(e)}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {e.is_flagged && <Flag className="w-3 h-3 text-red-500 shrink-0" />}
                            <div>
                              <p className="text-sm font-medium text-gray-900">{e.agent_name}</p>
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full ${AGENT_COLORS[e.agent_type] ?? AGENT_COLORS.custom}`}>
                                {e.agent_type}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-0.5 rounded-md font-medium ${ACTION_STYLES[e.action_type] ?? "bg-gray-100 text-gray-600"}`}>
                            {e.action_type.replace(/_/g, " ")}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <p className="text-sm text-gray-700 font-medium">{e.target_tool}</p>
                          {e.target_url && <p className="text-[10px] text-gray-400 truncate max-w-[140px]">{e.target_url}</p>}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {e.data_categories.slice(0, 2).map((c) => (
                              <span key={c} className="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-md font-medium capitalize">{c}</span>
                            ))}
                            {e.data_categories.length > 2 && <span className="text-[10px] text-gray-400">+{e.data_categories.length - 2}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-center">
                          {e.chain_depth > 0 ? (
                            <div className="flex items-center gap-1 justify-center">
                              <Layers className="w-3 h-3 text-amber-500" />
                              <span className="text-xs text-amber-700 font-semibold">{e.chain_depth}</span>
                            </div>
                          ) : (
                            <span className="text-xs text-gray-300">—</span>
                          )}
                        </td>
                        <td className="px-4 py-3">
                          <span className={`text-xs px-2 py-1 rounded-lg border font-semibold capitalize ${RISK_STYLES[e.risk_level] ?? "bg-gray-50 text-gray-600 border-gray-200"}`}>
                            {e.risk_level}
                          </span>
                          {e.risk_flags.length > 0 && (
                            <p className="text-[10px] text-red-500 mt-0.5">{e.risk_flags.length} flag{e.risk_flags.length > 1 ? "s" : ""}</p>
                          )}
                        </td>
                        <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">
                          {new Date(e.created_at).toLocaleDateString()}<br />
                          <span className="text-[10px]">{new Date(e.created_at).toLocaleTimeString()}</span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <button onClick={(ev) => { ev.stopPropagation(); setSelected(e); }} className="p-1 rounded-lg hover:bg-brand-50 text-gray-400 hover:text-brand-600 transition-colors">
                              <Eye className="w-3.5 h-3.5" />
                            </button>
                            <button onClick={(ev) => { ev.stopPropagation(); handleDelete(e.id); }} className="p-1 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors">
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Ingest tip */}
          {events.length === 0 && !loading && (
            <div className="mt-4 bg-gray-50 rounded-2xl border border-gray-100 px-5 py-4">
              <p className="text-xs font-semibold text-gray-700 mb-1">Self-reporting from your AI agents</p>
              <p className="text-xs text-gray-500 leading-relaxed">
                Configure your agents to POST to <code className="bg-gray-100 px-1.5 py-0.5 rounded font-mono text-xs">/v1/ai-agent-events/ingest-key?key=YOUR_API_KEY</code> after each tool call. Generate an API key in Settings → API Keys.
              </p>
            </div>
          )}
        </>
      )}

      {/* Modals */}
      {selected && (
        <EventDetailModal
          event={selected}
          onClose={() => setSelected(null)}
          onFlag={handleFlag}
          onReview={handleReview}
        />
      )}
      {showLog && <LogModal onClose={() => setShowLog(false)} onSave={handleLog} />}
    </div>
  );
}
