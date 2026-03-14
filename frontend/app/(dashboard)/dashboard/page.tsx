"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import type {
  ComplianceScore,
  Evidence,
  EvidenceActivityPoint,
  Integration,
  ScoreHistoryPoint,
} from "@/lib/types";
import Link from "next/link";
import {
  ShieldCheck,
  Plug,
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Activity,
  AlertTriangle,
  ArrowRight,
  X,
  PartyPopper,
  Database,
  ChevronRight,
} from "lucide-react";
import type { Report } from "@/lib/types";

function StatCard({
  label,
  value,
  sub,
  accent,
  icon: Icon,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "green" | "yellow" | "red" | "blue";
  icon: React.ElementType;
}) {
  const styles = {
    green:  { card: "border-emerald-100", iconBg: "bg-emerald-50", iconColor: "text-emerald-600", value: "text-emerald-600" },
    yellow: { card: "border-amber-100",   iconBg: "bg-amber-50",   iconColor: "text-amber-600",   value: "text-amber-600"  },
    red:    { card: "border-red-100",     iconBg: "bg-red-50",     iconColor: "text-red-500",     value: "text-red-500"    },
    blue:   { card: "border-brand-100",   iconBg: "bg-brand-50",   iconColor: "text-brand-600",   value: "text-gray-900"   },
  };
  const s = accent ? styles[accent] : styles.blue;
  return (
    <div className={`bg-white rounded-2xl border ${s.card} shadow-card p-5 flex flex-col gap-4`}>
      <div className={`w-9 h-9 rounded-xl ${s.iconBg} flex items-center justify-center`}>
        <Icon className={`w-5 h-5 ${s.iconColor}`} />
      </div>
      <div>
        <p className={`text-2xl font-bold ${s.value}`}>{value}</p>
        <p className="text-sm font-medium text-gray-600 mt-0.5">{label}</p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function statusIcon(status: string) {
  if (status === "active") return <CheckCircle2 className="w-4 h-4 text-green-500" />;
  if (status === "error") return <AlertCircle className="w-4 h-4 text-red-500" />;
  return <Clock className="w-4 h-4 text-gray-400" />;
}

function staleBadge(lastCollected: string | null) {
  if (!lastCollected) return <span className="text-xs text-gray-400">Never</span>;
  const hours = (Date.now() - new Date(lastCollected).getTime()) / 36e5;
  if (hours > 48)
    return <span className="text-xs font-medium text-red-500">{Math.floor(hours / 24)}d ago</span>;
  if (hours > 24)
    return <span className="text-xs font-medium text-yellow-600">{Math.floor(hours)}h ago</span>;
  return <span className="text-xs text-gray-400">{new Date(lastCollected).toLocaleString()}</span>;
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

function EvidenceDots({
  covered,
  missing,
}: {
  covered: string[];
  missing: string[];
}) {
  if (covered.length === 0 && missing.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {covered.map((t) => (
        <span
          key={`c-${t}`}
          className="inline-flex items-center gap-1 bg-emerald-50 border border-emerald-100 text-emerald-700 text-[11px] font-medium px-2 py-0.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
          {t}
        </span>
      ))}
      {missing.map((t) => (
        <span
          key={`m-${t}`}
          className="inline-flex items-center gap-1 bg-red-50 border border-red-100 text-red-600 text-[11px] font-medium px-2 py-0.5 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
          {t}
        </span>
      ))}
    </div>
  );
}

function statusBadge(status: string) {
  const base = "text-xs font-medium px-2 py-0.5 rounded-full";
  if (status === "passing") return <span className={`${base} bg-green-50 text-green-700`}>Passing</span>;
  if (status === "warning") return <span className={`${base} bg-yellow-50 text-yellow-700`}>Warning</span>;
  if (status === "failing") return <span className={`${base} bg-red-50 text-red-600`}>Failing</span>;
  return <span className={`${base} bg-gray-100 text-gray-500`}>No data</span>;
}

// ── Getting Started Checklist ─────────────────────────────────────────────────
const CHECKLIST_KEY = "tl_checklist_dismissed";

function GettingStarted({
  hasIntegration,
  hasEvidence,
  hasScore,
  hasReport,
}: {
  hasIntegration: boolean;
  hasEvidence: boolean;
  hasScore: boolean;
  hasReport: boolean;
}) {
  const [dismissed, setDismissed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(CHECKLIST_KEY) === "1";
  });

  const steps = [
    { label: "Create your account", done: true },
    { label: "Connect your first integration", done: hasIntegration, href: "/integrations" },
    { label: "Collect evidence automatically", done: hasEvidence, href: hasIntegration ? undefined : "/integrations" },
    { label: "View your compliance score", done: hasScore, href: "/compliance" },
    { label: "Generate a compliance report", done: hasReport, href: "/reports" },
  ];

  const completed = steps.filter((s) => s.done).length;
  const allDone = completed === steps.length;

  const handleDismiss = () => {
    localStorage.setItem(CHECKLIST_KEY, "1");
    setDismissed(true);
  };

  if (dismissed) return null;

  return (
    <div className="bg-white border border-brand-100 rounded-2xl shadow-card p-5 mb-6 bg-gradient-to-r from-brand-50/50 to-white">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            {allDone
              ? <PartyPopper className="w-5 h-5 text-emerald-500" />
              : <ShieldCheck className="w-5 h-5 text-brand-500" />
            }
            <h2 className="text-sm font-semibold text-gray-900">
              {allDone ? "Setup complete — you're all set!" : "Getting started"}
            </h2>
          </div>
          {!allDone && (
            <p className="text-xs text-gray-400 mt-0.5">{completed} of {steps.length} steps done</p>
          )}
        </div>
        <button
          onClick={handleDismiss}
          className="text-gray-300 hover:text-gray-500 transition-colors shrink-0 mt-0.5"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-gray-100 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-brand-500 rounded-full transition-all duration-500"
          style={{ width: `${(completed / steps.length) * 100}%` }}
        />
      </div>

      {/* Steps */}
      <div className="space-y-2">
        {steps.map((step) => (
          <div key={step.label} className="flex items-center gap-3">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
              step.done ? "bg-emerald-100" : "bg-gray-100"
            }`}>
              {step.done
                ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                : <div className="w-1.5 h-1.5 rounded-full bg-gray-300" />
              }
            </div>
            {step.href && !step.done ? (
              <Link href={step.href} className="text-sm text-brand-600 hover:underline">
                {step.label}
              </Link>
            ) : (
              <span className={`text-sm ${step.done ? "text-gray-400 line-through" : "text-gray-700"}`}>
                {step.label}
              </span>
            )}
          </div>
        ))}
      </div>

      {allDone && (
        <button
          onClick={handleDismiss}
          className="mt-4 text-xs text-gray-400 hover:text-gray-600 underline underline-offset-2"
        >
          Dismiss checklist
        </button>
      )}
    </div>
  );
}

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa", label: "HIPAA" },
];

function fmtDay(dateStr: string) {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [evidenceTotal, setEvidenceTotal] = useState(0);
  const [compliance, setCompliance] = useState<ComplianceScore | null>(null);
  const [framework, setFramework] = useState("soc2");
  const [scoreHistory, setScoreHistory] = useState<ScoreHistoryPoint[]>([]);
  const [evidenceActivity, setEvidenceActivity] = useState<EvidenceActivityPoint[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [scoreLoading, setScoreLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getIntegrations(),
      api.getEvidence({ page_size: 5 }),
      api.getComplianceScore(framework),
      api.getScoreHistory(framework, 30),
      api.getEvidenceActivity(14),
      api.getReports(1),
    ])
      .then(([ints, ev, score, history, activity, rpts]) => {
        setIntegrations(ints);
        setEvidence(ev.items);
        setEvidenceTotal(ev.total);
        setCompliance(score);
        setScoreHistory(history);
        setEvidenceActivity(activity);
        setReports(rpts.items);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleFrameworkChange = async (fw: string) => {
    setFramework(fw);
    setScoreLoading(true);
    try {
      const [score, history] = await Promise.all([
        api.getComplianceScore(fw),
        api.getScoreHistory(fw, 30),
      ]);
      setCompliance(score);
      setScoreHistory(history);
    } catch {
      /* ignore */
    } finally {
      setScoreLoading(false);
    }
  };

  const scoreAccent =
    compliance && compliance.overall_score >= 80
      ? "green"
      : compliance && compliance.overall_score >= 50
      ? "yellow"
      : "red";

  const activeIntegrations = integrations.filter((i) => i.status === "active").length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Fill missing days in score history for a smooth line
  const historyChartData = scoreHistory.map((p) => ({
    date: fmtDay(p.ts),
    score: p.score,
  }));

  // Fill missing days in evidence activity
  const activityChartData = evidenceActivity.map((p) => ({
    date: fmtDay(p.day),
    count: p.count,
  }));

  const failingControls = compliance?.controls.filter((c) => c.status === "failing" || c.status === "warning") ?? [];

  return (
    <div className="animate-fade-in">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {/* Getting started checklist */}
      <GettingStarted
        hasIntegration={integrations.length > 0}
        hasEvidence={evidenceTotal > 0}
        hasScore={!!compliance && compliance.controls.length > 0}
        hasReport={reports.length > 0}
      />

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
        <StatCard
          icon={ShieldCheck}
          label="Compliance score"
          value={compliance ? `${compliance.overall_score}%` : "—"}
          sub={
            compliance
              ? `${compliance.controls.filter((c) => c.status === "passing").length} / ${compliance.controls.length} controls passing`
              : "No data yet"
          }
          accent={scoreAccent}
        />
        <StatCard
          icon={Database}
          label="Evidence records"
          value={evidenceTotal.toLocaleString()}
          sub="across all integrations"
          accent="blue"
        />
        <StatCard
          icon={Plug}
          label="Active integrations"
          value={activeIntegrations}
          sub={`of ${integrations.length} connected`}
          accent={activeIntegrations > 0 ? "green" : "blue"}
        />
        <StatCard
          icon={Activity}
          label="Controls monitored"
          value={compliance?.controls.length ?? 0}
          sub={`${framework.toUpperCase()} framework`}
          accent="blue"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6 mb-6">
        {/* Score trend */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-500" />
              <span className="font-semibold text-gray-800 text-sm">Score trend</span>
            </div>
            <select
              value={framework}
              onChange={(e) => handleFrameworkChange(e.target.value)}
              disabled={scoreLoading}
              className="border border-gray-200 rounded-md px-2 py-1 text-xs text-gray-600 focus:outline-none focus:ring-1 focus:ring-brand-500 disabled:opacity-40"
            >
              {FRAMEWORKS.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
          {historyChartData.length > 1 ? (
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={historyChartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip
                  formatter={(v) => [`${v}%`, "Score"]}
                  contentStyle={{ fontSize: 12 }}
                />
                <Line
                  type="monotone"
                  dataKey="score"
                  stroke="#0f766e"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-sm text-gray-400">
              Not enough data yet — check back after a few collection runs.
            </div>
          )}
        </div>

        {/* Evidence activity */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-4 h-4 text-brand-500" />
            <span className="font-semibold text-gray-800 text-sm">Evidence activity (14d)</span>
          </div>
          {activityChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={activityChartData} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
                <Tooltip
                  formatter={(v) => [v, "Records"]}
                  contentStyle={{ fontSize: 12 }}
                />
                <Bar dataKey="count" fill="#0f766e" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-40 flex items-center justify-center text-sm text-gray-400">
              No evidence collected yet.
            </div>
          )}
        </div>
      </div>

      {/* Compliance breakdown */}
      {compliance && compliance.controls.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-gray-400" />
              <span className="font-semibold text-gray-800 text-sm">Control breakdown</span>
            </div>
            <span
              className={`text-2xl font-bold ${scoreLoading ? "opacity-40" : ""} ${scoreColor(
                compliance.overall_score
              )}`}
            >
              {compliance.overall_score}%
            </span>
          </div>
          <div className="space-y-3">
            {compliance.controls.map((c) => (
              <Link key={c.category} href={`/evidence?control=${c.category}`} className="block group">
                <div className="flex items-center justify-between text-sm mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-700 font-medium group-hover:text-brand-600 transition-colors">{c.name}</span>
                    {statusBadge(c.status)}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`font-semibold text-sm ${scoreColor(c.score)}`}>{c.score}%</span>
                    <ArrowRight className="w-3 h-3 text-gray-300 group-hover:text-brand-400 transition-colors" />
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${scoreBarColor(c.score)}`}
                    style={{ width: `${c.score}%` }}
                  />
                </div>
                <EvidenceDots covered={c.covered_types} missing={c.missing_types} />
              </Link>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
        {/* Integrations with staleness */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Plug className="w-4 h-4 text-brand-500" />
            <span className="font-semibold text-gray-800 text-sm">Integrations</span>
          </div>
          {integrations.length === 0 ? (
            <p className="text-sm text-gray-400">No integrations connected yet.</p>
          ) : (
            <div className="space-y-3">
              {integrations.map((i) => {
                const staleHours = i.last_collected_at
                  ? (Date.now() - new Date(i.last_collected_at).getTime()) / 36e5
                  : Infinity;
                return (
                  <div key={i.id} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {statusIcon(i.status)}
                      <span className="text-sm font-medium capitalize">{i.integration_type}</span>
                      {staleHours > 48 && (
                        <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
                      )}
                    </div>
                    {staleBadge(i.last_collected_at)}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Remediation hints */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="font-semibold text-gray-800 text-sm">Action items</span>
          </div>
          {failingControls.length === 0 ? (
            <p className="text-sm text-gray-400">All controls passing — great work.</p>
          ) : (
            <div className="space-y-3">
              {failingControls.slice(0, 5).map((c) => (
                <div key={c.category} className="flex gap-3">
                  <div className="mt-0.5 w-1.5 h-1.5 rounded-full bg-red-400 shrink-0 mt-2" />
                  <div>
                    <p className="text-sm font-medium text-gray-800">{c.name}</p>
                    {c.missing_types.length > 0 && (
                      <div className="mt-1.5">
                        <p className="text-[11px] text-gray-400 mb-1">Needs integration for:</p>
                        <div className="flex flex-wrap gap-1">
                          {c.missing_types.map((t) => (
                            <span
                              key={t}
                              className="inline-flex items-center gap-1 bg-red-50 border border-red-100 text-red-600 text-[11px] font-medium px-2 py-0.5 rounded-full"
                            >
                              <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
