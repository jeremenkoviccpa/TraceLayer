"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ComplianceScore, Evidence, Integration } from "@/lib/types";
import { ShieldCheck, Plug, AlertCircle, CheckCircle2, Clock } from "lucide-react";

function StatCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: string | number;
  sub?: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function statusIcon(status: string) {
  if (status === "active") return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === "error") return <AlertCircle className="w-4 h-4 text-red-500" />;
  return <Clock className="w-4 h-4 text-gray-400" />;
}

function fmtDate(d: string | null) {
  if (!d) return "Never";
  return new Date(d).toLocaleString();
}

function scoreColor(score: number) {
  if (score >= 80) return "text-green-600";
  if (score >= 50) return "text-yellow-600";
  return "text-red-500";
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-green-500";
  if (score >= 50) return "bg-yellow-400";
  return "bg-red-400";
}

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa", label: "HIPAA" },
];

export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [evidenceTotal, setEvidenceTotal] = useState(0);
  const [compliance, setCompliance] = useState<ComplianceScore | null>(null);
  const [framework, setFramework] = useState("soc2");
  const [loading, setLoading] = useState(true);
  const [scoreLoading, setScoreLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getIntegrations(),
      api.getEvidence({ page_size: 5 }),
      api.getComplianceScore(framework),
    ])
      .then(([ints, ev, score]) => {
        setIntegrations(ints);
        setEvidence(ev.items);
        setEvidenceTotal(ev.total);
        setCompliance(score);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleFrameworkChange = async (fw: string) => {
    setFramework(fw);
    setScoreLoading(true);
    try {
      setCompliance(await api.getComplianceScore(fw));
    } catch { /* ignore */ } finally {
      setScoreLoading(false);
    }
  };

  // Group evidence by control
  const byControl = evidence.reduce<Record<string, number>>((acc, e) => {
    acc[e.control] = (acc[e.control] ?? 0) + 1;
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard
          label="SOC 2 score"
          value={compliance ? `${compliance.overall_score}%` : "—"}
          sub={compliance ? `${compliance.controls.filter(c => c.status === "passing").length} / ${compliance.controls.length} controls passing` : "No data yet"}
        />
        <StatCard
          label="Total evidence records"
          value={evidenceTotal}
          sub="across all integrations"
        />
        <StatCard
          label="Connected integrations"
          value={integrations.filter((i) => i.status === "active").length}
          sub={`of ${integrations.length} total`}
        />
        <StatCard
          label="Controls monitored"
          value={Object.keys(byControl).length}
          sub="SOC 2 framework"
        />
      </div>

      {/* Compliance score breakdown */}
      {compliance && compliance.controls.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-gray-400" />
              <h2 className="font-semibold text-gray-800">Compliance Score</h2>
              <select
                value={framework}
                onChange={(e) => handleFrameworkChange(e.target.value)}
                className="ml-2 border border-gray-200 rounded-md px-2 py-1 text-xs text-gray-600 focus:outline-none focus:ring-1 focus:ring-brand-500"
              >
                {FRAMEWORKS.map((f) => (
                  <option key={f.value} value={f.value}>{f.label}</option>
                ))}
              </select>
            </div>
            <span className={`text-2xl font-bold ${scoreLoading ? "opacity-40" : ""} ${scoreColor(compliance.overall_score)}`}>
              {compliance.overall_score}%
            </span>
          </div>
          <div className="space-y-3">
            {compliance.controls.map((c) => (
              <div key={c.category}>
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-700 font-medium">{c.name}</span>
                  <span className={`font-semibold ${scoreColor(c.score)}`}>{c.score}%</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${scoreBarColor(c.score)}`}
                    style={{ width: `${c.score}%` }}
                  />
                </div>
                {c.missing_types.length > 0 && (
                  <p className="text-xs text-gray-400 mt-0.5">
                    Missing: {c.missing_types.join(", ")}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        {/* Integration statuses */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Plug className="w-4 h-4 text-gray-400" />
            <h2 className="font-semibold text-gray-800">Integrations</h2>
          </div>
          {integrations.length === 0 ? (
            <p className="text-sm text-gray-400">No integrations connected yet.</p>
          ) : (
            <div className="space-y-3">
              {integrations.map((i) => (
                <div key={i.id} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {statusIcon(i.status)}
                    <span className="text-sm font-medium capitalize">{i.integration_type}</span>
                  </div>
                  <span className="text-xs text-gray-400">{fmtDate(i.last_collected_at)}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent evidence */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-4 h-4 text-gray-400" />
            <h2 className="font-semibold text-gray-800">Recent evidence</h2>
          </div>
          {evidence.length === 0 ? (
            <p className="text-sm text-gray-400">No evidence collected yet.</p>
          ) : (
            <div className="space-y-2">
              {evidence.map((e) => (
                <div
                  key={e.id}
                  className="flex items-center justify-between py-1 border-b border-gray-100 last:border-0"
                >
                  <div>
                    <span className="text-sm font-medium">{e.evidence_type}</span>
                    <span className="text-xs text-gray-400 ml-2">via {e.integration}</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {new Date(e.timestamp).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
