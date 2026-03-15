"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Evidence, Page } from "@/lib/types";
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Database,
  RefreshCw,
} from "lucide-react";

const CONTROLS = [
  { value: "", label: "All controls" },
  { value: "access_control", label: "Access Control" },
  { value: "logging_monitoring", label: "Logging & Monitoring" },
  { value: "change_management", label: "Change Management" },
];

const INTEGRATIONS = [
  { value: "", label: "All integrations" },
  { value: "aws", label: "AWS" },
  { value: "github", label: "GitHub" },
  { value: "slack", label: "Slack" },
];

function IntegrationBadge({ name }: { name: string }) {
  const colors: Record<string, string> = {
    aws: "bg-orange-50 text-orange-700 border-orange-200",
    github: "bg-gray-50 text-gray-700 border-gray-200",
    slack: "bg-purple-50 text-purple-700 border-purple-200",
  };
  const cls = colors[name.toLowerCase()] ?? "bg-cyan-50 text-cyan-700 border-cyan-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border capitalize ${cls}`}>
      {name}
    </span>
  );
}

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="hover:bg-gray-50/80 cursor-pointer transition-colors duration-100"
        onClick={() => setExpanded((v) => !v)}
      >
        <td className="px-5 py-3.5 text-sm">
          <IntegrationBadge name={evidence.integration} />
        </td>
        <td className="px-5 py-3.5 text-sm font-medium text-gray-800 capitalize">
          {evidence.control.replace(/_/g, " ")}
        </td>
        <td className="px-5 py-3.5 text-sm text-gray-500">{evidence.evidence_type}</td>
        <td className="px-5 py-3.5 text-sm text-gray-400 max-w-xs truncate font-mono text-xs">
          {evidence.source_id}
        </td>
        <td className="px-5 py-3.5 text-sm text-gray-400">
          {new Date(evidence.timestamp).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </td>
        <td className="px-5 py-3.5 text-gray-300">
          {expanded ? (
            <ChevronUp className="w-4 h-4 text-cyan-500" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} className="px-5 pb-4 bg-slate-50/60">
            <div className="border-l-2 border-cyan-400 pl-4 mt-1">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                Raw Evidence Data
              </p>
              <pre className="text-xs text-gray-700 bg-white border border-gray-100 rounded-xl p-4 overflow-auto max-h-48 shadow-sm">
                {JSON.stringify(evidence.data, null, 2)}
              </pre>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function StatCard({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: string | number;
  colorClass: string;
}) {
  return (
    <div className="flex flex-col">
      <span className={`text-2xl font-bold tabular-nums ${colorClass}`}>{value}</span>
      <span className="text-slate-400 text-xs mt-0.5 whitespace-nowrap">{label}</span>
    </div>
  );
}

export default function EvidencePage() {
  const searchParams = useSearchParams();
  const [data, setData] = useState<Page<Evidence> | null>(null);
  const [control, setControl] = useState(searchParams.get("control") ?? "");
  const [integration, setIntegration] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .getEvidence({
        control: control || undefined,
        integration: integration || undefined,
        page,
        page_size: 25,
      })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    setPage(1);
  }, [control, integration]);

  useEffect(() => {
    load();
  }, [control, integration, page]); // eslint-disable-line react-hooks/exhaustive-deps

  // Derived hero stats — approximated from loaded data
  const totalRecords = data?.total ?? 0;
  const todayCount = data
    ? data.items.filter((e) => {
        const d = new Date(e.timestamp);
        const now = new Date();
        return (
          d.getFullYear() === now.getFullYear() &&
          d.getMonth() === now.getMonth() &&
          d.getDate() === now.getDate()
        );
      }).length
    : 0;
  const activeIntegrations = data
    ? new Set(data.items.map((e) => e.integration)).size
    : 0;
  const frameworks = data
    ? new Set(data.items.map((e) => e.control.split("_")[0])).size
    : 0;

  return (
    <div className="space-y-6">
      {/* ── Dark Hero Card ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
        {/* Subtle grid texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        {/* Cyan glow blob */}
        <div className="pointer-events-none absolute -top-16 -left-16 w-72 h-72 rounded-full bg-cyan-500/10 blur-3xl" />

        <div className="relative px-7 py-7 flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
          {/* Left — icon + copy */}
          <div className="flex items-start gap-5">
            <div className="shrink-0 flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/15 border border-cyan-500/30 shadow-lg shadow-cyan-500/10">
              <Database className="w-7 h-7 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                Evidence Library
              </h1>
              <p className="text-slate-400 text-sm mt-1 max-w-md leading-relaxed">
                Automatically collected compliance evidence from your integrations.
              </p>
              {/* Stats row */}
              <div className="flex flex-wrap gap-6 mt-4">
                <StatCard
                  label="Total records"
                  value={totalRecords.toLocaleString()}
                  colorClass="text-cyan-400"
                />
                <div className="w-px bg-slate-700 self-stretch" />
                <StatCard
                  label="Collected today"
                  value={todayCount}
                  colorClass="text-teal-400"
                />
                <div className="w-px bg-slate-700 self-stretch" />
                <StatCard
                  label="Integrations active"
                  value={activeIntegrations}
                  colorClass="text-blue-400"
                />
                <div className="w-px bg-slate-700 self-stretch" />
                <StatCard
                  label="Frameworks covered"
                  value={frameworks}
                  colorClass="text-indigo-400"
                />
              </div>
            </div>
          </div>

          {/* Right — action */}
          <button
            onClick={load}
            disabled={loading}
            className="shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-sm font-medium hover:bg-cyan-500/25 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Filter Bar + Table Card ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        {/* Filter bar */}
        <div className="flex flex-wrap items-center gap-2 px-5 py-4 border-b border-gray-100 bg-gray-50/50">
          <select
            value={control}
            onChange={(e) => setControl(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400 transition-colors"
          >
            {CONTROLS.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>

          <select
            value={integration}
            onChange={(e) => setIntegration(e.target.value)}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-cyan-400/50 focus:border-cyan-400 transition-colors"
          >
            {INTEGRATIONS.map((i) => (
              <option key={i.value} value={i.value}>
                {i.label}
              </option>
            ))}
          </select>

          {data && (
            <span className="ml-auto text-sm text-gray-400 self-center">
              {data.total.toLocaleString()} records
            </span>
          )}
        </div>

        {/* Content */}
        {loading ? (
          <div className="flex flex-col items-center justify-center h-48 gap-3">
            <div className="w-7 h-7 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-gray-400">Loading evidence…</p>
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
            <div className="w-14 h-14 rounded-2xl bg-cyan-50 border border-cyan-100 flex items-center justify-center mb-4">
              <Database className="w-7 h-7 text-cyan-300" />
            </div>
            <p className="text-gray-700 font-medium">No evidence found</p>
            <p className="text-gray-400 text-sm mt-1 max-w-xs">
              Connect an integration and trigger a collection to start gathering evidence.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[620px]">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                      Integration
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                      Control
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                      Type
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                      Source ID
                    </th>
                    <th className="px-5 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wide">
                      Date
                    </th>
                    <th className="px-5 py-3" />
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {data.items.map((e) => (
                    <EvidenceRow key={e.id} evidence={e} />
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between px-5 py-3.5 border-t border-gray-100 bg-gray-50/30">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 disabled:opacity-30 font-medium transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" /> Prev
                </button>
                <span className="text-sm text-gray-400">
                  Page{" "}
                  <span className="font-semibold text-gray-700">{page}</span>
                  {" "}of{" "}
                  <span className="font-semibold text-gray-700">{data.pages}</span>
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900 disabled:opacity-30 font-medium transition-colors"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
