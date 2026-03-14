"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Evidence, Page } from "@/lib/types";
import { ChevronLeft, ChevronRight, ChevronDown, ChevronUp } from "lucide-react";

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

function EvidenceRow({ evidence }: { evidence: Evidence }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr className="hover:bg-gray-50 cursor-pointer" onClick={() => setExpanded((v) => !v)}>
        <td className="px-4 py-3 text-sm capitalize">{evidence.integration}</td>
        <td className="px-4 py-3 text-sm capitalize">{evidence.control.replace(/_/g, " ")}</td>
        <td className="px-4 py-3 text-sm text-gray-600">{evidence.evidence_type}</td>
        <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">{evidence.source_id}</td>
        <td className="px-4 py-3 text-sm text-gray-400">
          {new Date(evidence.timestamp).toLocaleDateString()}
        </td>
        <td className="px-4 py-3 text-gray-400">
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={6} className="px-4 pb-3 bg-gray-50">
            <pre className="text-xs text-gray-700 bg-white border border-gray-200 rounded-lg p-3 overflow-auto max-h-40">
              {JSON.stringify(evidence.data, null, 2)}
            </pre>
          </td>
        </tr>
      )}
    </>
  );
}

export default function EvidencePage() {
  const [data, setData] = useState<Page<Evidence> | null>(null);
  const [control, setControl] = useState("");
  const [integration, setIntegration] = useState("");
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    api
      .getEvidence({ control: control || undefined, integration: integration || undefined, page, page_size: 25 })
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

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Evidence</h1>

      {/* Filters */}
      <div className="flex gap-3 mb-5">
        <select
          value={control}
          onChange={(e) => setControl(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
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
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
        >
          {INTEGRATIONS.map((i) => (
            <option key={i.value} value={i.value}>
              {i.label}
            </option>
          ))}
        </select>

        {data && (
          <span className="ml-auto text-sm text-gray-500 self-center">
            {data.total} records
          </span>
        )}
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-40">
            <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="text-center text-gray-400 text-sm py-16">
            No evidence found. Connect an integration and trigger a collection.
          </div>
        ) : (
          <>
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Integration
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Control
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Source ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wide">
                    Date
                  </th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.items.map((e) => (
                  <EvidenceRow key={e.id} evidence={e} />
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {data.pages > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-40"
                >
                  <ChevronLeft className="w-4 h-4" /> Prev
                </button>
                <span className="text-sm text-gray-500">
                  Page {page} of {data.pages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                  disabled={page === data.pages}
                  className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-40"
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
