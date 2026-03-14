"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ComplianceScore, ManualControl } from "@/lib/types";
import {
  ShieldCheck,
  CheckCircle2,
  MinusCircle,
  Circle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa", label: "HIPAA" },
];

type Status = "pending" | "compliant" | "not_applicable";

const STATUS_CYCLE: Status[] = ["pending", "compliant", "not_applicable"];

function StatusIcon({ status }: { status: Status }) {
  if (status === "compliant")
    return <CheckCircle2 className="w-5 h-5 text-green-500 shrink-0" />;
  if (status === "not_applicable")
    return <MinusCircle className="w-5 h-5 text-gray-400 shrink-0" />;
  return <Circle className="w-5 h-5 text-gray-300 shrink-0" />;
}

function statusLabel(status: Status) {
  if (status === "compliant") return "Compliant";
  if (status === "not_applicable") return "N/A";
  return "Pending";
}

function statusBadge(status: string) {
  const base = "text-xs font-medium px-2 py-0.5 rounded-full";
  if (status === "passing") return <span className={`${base} bg-green-50 text-green-700`}>Passing</span>;
  if (status === "warning") return <span className={`${base} bg-yellow-50 text-yellow-700`}>Warning</span>;
  if (status === "failing") return <span className={`${base} bg-red-50 text-red-600`}>Failing</span>;
  return <span className={`${base} bg-gray-100 text-gray-500`}>No data</span>;
}

function scoreColor(score: number) {
  if (score >= 80) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-500";
}

function ManualControlRow({
  control,
  framework,
  onUpdate,
}: {
  control: ManualControl;
  framework: string;
  onUpdate: (updated: ManualControl) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [notes, setNotes] = useState(control.notes ?? "");
  const [saving, setSaving] = useState(false);

  const cycleStatus = async () => {
    const idx = STATUS_CYCLE.indexOf(control.status as Status);
    const next = STATUS_CYCLE[(idx + 1) % STATUS_CYCLE.length];
    setSaving(true);
    try {
      const updated = await api.updateManualControl(control.control_id, framework, next, notes || null);
      onUpdate(updated);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const saveNotes = async () => {
    setSaving(true);
    try {
      const updated = await api.updateManualControl(
        control.control_id,
        framework,
        control.status,
        notes || null,
      );
      onUpdate(updated);
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="border border-gray-200 rounded-xl overflow-hidden">
      <div
        className="flex items-center gap-3 p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <button
          onClick={(e) => { e.stopPropagation(); cycleStatus(); }}
          disabled={saving}
          className="shrink-0 disabled:opacity-40"
        >
          <StatusIcon status={control.status as Status} />
        </button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-800">{control.name}</p>
          <p className="text-xs text-gray-500 mt-0.5 truncate">{control.description}</p>
        </div>
        <span
          className={`text-xs font-medium shrink-0 ${
            control.status === "compliant"
              ? "text-green-600"
              : control.status === "not_applicable"
              ? "text-gray-400"
              : "text-yellow-600"
          }`}
        >
          {statusLabel(control.status as Status)}
        </span>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-400 shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-400 shrink-0" />
        )}
      </div>

      {expanded && (
        <div className="border-t border-gray-100 px-4 pb-4 pt-3 bg-gray-50">
          <p className="text-xs text-gray-600 mb-3">{control.description}</p>
          <div className="flex gap-2">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes, links to evidence, or context..."
              rows={2}
              className="flex-1 text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand-500 resize-none bg-white"
            />
            <button
              onClick={saveNotes}
              disabled={saving}
              className="self-end px-3 py-2 text-xs bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-40 transition-colors"
            >
              Save
            </button>
          </div>
          {control.updated_at && (
            <p className="text-xs text-gray-400 mt-2">
              Last updated {new Date(control.updated_at).toLocaleString()}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CompliancePage() {
  const [framework, setFramework] = useState("soc2");
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [manualControls, setManualControls] = useState<ManualControl[]>([]);
  const [loading, setLoading] = useState(true);

  const load = async (fw: string) => {
    setLoading(true);
    try {
      const [s, m] = await Promise.all([
        api.getComplianceScore(fw),
        api.getManualControls(fw),
      ]);
      setScore(s);
      setManualControls(m);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(framework); }, [framework]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleUpdate = (updated: ManualControl) => {
    setManualControls((prev) =>
      prev.map((c) => (c.control_id === updated.control_id ? { ...c, ...updated } : c))
    );
  };

  const manualCompliant = manualControls.filter((c) => c.status === "compliant").length;
  const manualTotal = manualControls.filter((c) => c.status !== "not_applicable").length;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
        <select
          value={framework}
          onChange={(e) => setFramework(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {FRAMEWORKS.map((f) => (
            <option key={f.value} value={f.value}>
              {f.label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : (
        <div className="space-y-8">
          {/* Automated controls */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <ShieldCheck className="w-4 h-4 text-gray-400" />
              <h2 className="font-semibold text-gray-800">Automated controls</h2>
              {score && (
                <span className={`ml-auto text-2xl font-bold ${scoreColor(score.overall_score)}`}>
                  {score.overall_score}%
                </span>
              )}
            </div>
            <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
              {score?.controls.map((c) => (
                <div key={c.category} className="px-5 py-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-800">{c.name}</span>
                      {statusBadge(c.status)}
                    </div>
                    <span className={`text-sm font-semibold ${scoreColor(c.score)}`}>{c.score}%</span>
                  </div>
                  <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        c.score >= 80 ? "bg-green-500" : c.score >= 50 ? "bg-yellow-400" : "bg-red-400"
                      }`}
                      style={{ width: `${c.score}%` }}
                    />
                  </div>
                  <div className="flex gap-4 mt-2">
                    {c.covered_types.length > 0 && (
                      <p className="text-xs text-gray-400">
                        Covered: <span className="text-green-600">{c.covered_types.join(", ")}</span>
                      </p>
                    )}
                    {c.missing_types.length > 0 && (
                      <p className="text-xs text-gray-400">
                        Missing: <span className="text-red-400">{c.missing_types.join(", ")}</span>
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Manual controls */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle2 className="w-4 h-4 text-gray-400" />
              <h2 className="font-semibold text-gray-800">Manual controls</h2>
              <span className="text-xs text-gray-500 ml-1">
                {manualCompliant}/{manualTotal} complete
              </span>
              <div className="ml-auto h-1.5 w-32 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500 rounded-full transition-all"
                  style={{ width: `${manualTotal > 0 ? (manualCompliant / manualTotal) * 100 : 0}%` }}
                />
              </div>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              Click the circle icon to cycle status: Pending → Compliant → N/A. Expand a row to add notes.
            </p>
            <div className="space-y-2">
              {manualControls.map((c) => (
                <ManualControlRow
                  key={c.control_id}
                  control={c}
                  framework={framework}
                  onUpdate={handleUpdate}
                />
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
