"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Evidence, Integration } from "@/lib/types";
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

export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [evidenceTotal, setEvidenceTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getIntegrations(),
      api.getEvidence({ page_size: 5 }),
    ])
      .then(([ints, ev]) => {
        setIntegrations(ints);
        setEvidence(ev.items);
        setEvidenceTotal(ev.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

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
      <div className="grid grid-cols-3 gap-4 mb-8">
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
