"use client";

import { useEffect, useRef, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { api } from "@/lib/api";
import type {
  ComplianceScore, EvidenceActivityPoint,
  Integration, ScoreHistoryPoint, ReadinessData,
} from "@/lib/types";
import Link from "next/link";
import {
  ShieldCheck, Plug, AlertCircle, CheckCircle2, Clock,
  TrendingUp, Activity, AlertTriangle, ArrowRight, X,
  PartyPopper, Database, Target, GraduationCap, Building2,
  UserCheck, ShieldAlert, BookOpen, ClipboardList, Zap,
  FileText, Globe, ChevronRight,
} from "lucide-react";
import type { Report } from "@/lib/types";

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({ score }: { score: number }) {
  const r = 48;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-28 h-28 shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 112 112">
        <circle cx="56" cy="56" r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="9" />
        <circle cx="56" cy="56" r={r} fill="none" stroke={color} strokeWidth="9"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.4s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-white leading-none">{score}</span>
        <span className="text-[11px] font-semibold text-white/40 mt-0.5">/ 100</span>
      </div>
    </div>
  );
}

// ── Tiny stat card ─────────────────────────────────────────────────────────────
function MiniStat({
  label, value, sub, icon: Icon, color = "brand",
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color?: "brand" | "green" | "amber" | "red";
}) {
  const colors = {
    brand: "bg-brand-50 text-brand-600",
    green: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    red:   "bg-red-50 text-red-500",
  };
  const valColors = {
    brand: "text-gray-900",
    green: "text-emerald-600",
    amber: "text-amber-600",
    red:   "text-red-500",
  };
  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-4 flex items-center gap-3.5">
      <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${colors[color]}`}>
        <Icon className="w-4.5 h-4.5 w-[18px] h-[18px]" />
      </div>
      <div className="min-w-0">
        <p className={`text-xl font-bold leading-none ${valColors[color]}`}>{value}</p>
        <p className="text-xs font-medium text-gray-500 mt-0.5 truncate">{label}</p>
        {sub && <p className="text-[10px] text-gray-400 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  );
}

// ── Status helpers ─────────────────────────────────────────────────────────────
function statusBadge(status: string) {
  const map: Record<string, string> = {
    passing:    "bg-emerald-50 text-emerald-700",
    warning:    "bg-amber-50 text-amber-700",
    failing:    "bg-red-50 text-red-600",
    no_evidence:"bg-gray-100 text-gray-500",
  };
  const labels: Record<string, string> = {
    passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
  };
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${map[status] ?? "bg-gray-100 text-gray-500"}`}>
      {labels[status] ?? status}
    </span>
  );
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-400";
  return "bg-red-400";
}

function staleBadge(lastCollected: string | null) {
  if (!lastCollected) return <span className="text-xs text-gray-400">Never synced</span>;
  const hours = (Date.now() - new Date(lastCollected).getTime()) / 36e5;
  if (hours > 48) return <span className="text-xs font-medium text-red-500">{Math.floor(hours / 24)}d ago</span>;
  if (hours > 24) return <span className="text-xs font-medium text-amber-600">{Math.floor(hours)}h ago</span>;
  return <span className="text-xs text-gray-400">{new Date(lastCollected).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>;
}

// ── Getting started checklist ─────────────────────────────────────────────────
const CHECKLIST_KEY = "tl_checklist_dismissed";

function GettingStarted({ hasIntegration, hasEvidence, hasScore, hasReport }: {
  hasIntegration: boolean; hasEvidence: boolean; hasScore: boolean; hasReport: boolean;
}) {
  const [dismissed, setDismissed] = useState(() =>
    typeof window !== "undefined" && localStorage.getItem(CHECKLIST_KEY) === "1"
  );
  const steps = [
    { label: "Create your account",          done: true },
    { label: "Connect your first integration", done: hasIntegration, href: "/integrations" },
    { label: "Collect evidence automatically", done: hasEvidence,    href: hasIntegration ? undefined : "/integrations" },
    { label: "View your compliance score",    done: hasScore,        href: "/compliance" },
    { label: "Generate a compliance report",  done: hasReport,       href: "/reports" },
  ];
  const completed = steps.filter((s) => s.done).length;
  const pct = Math.round((completed / steps.length) * 100);
  const allDone = completed === steps.length;
  const dismiss = () => { localStorage.setItem(CHECKLIST_KEY, "1"); setDismissed(true); };
  if (dismissed) return null;

  return (
    <div className="relative bg-gradient-to-r from-slate-900 to-slate-800 rounded-2xl p-5 mb-6 overflow-hidden">
      {/* decorative glow */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-brand-500/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
      <div className="relative">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-0.5">
              {allDone
                ? <PartyPopper className="w-4 h-4 text-emerald-400" />
                : <ShieldCheck className="w-4 h-4 text-brand-400" />}
              <span className="text-sm font-semibold text-white">
                {allDone ? "You're all set!" : "Getting started"}
              </span>
            </div>
            <p className="text-xs text-white/40">{completed} of {steps.length} steps complete</p>
          </div>
          <button onClick={dismiss} className="text-white/30 hover:text-white/60 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
        {/* Progress bar */}
        <div className="h-1 bg-white/10 rounded-full mb-4 overflow-hidden">
          <div className="h-full bg-brand-400 rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
        </div>
        <div className="grid sm:grid-cols-2 gap-x-6 gap-y-1.5">
          {steps.map((step) => (
            <div key={step.label} className="flex items-center gap-2.5">
              <div className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${step.done ? "bg-emerald-500" : "bg-white/10"}`}>
                {step.done && <CheckCircle2 className="w-3 h-3 text-white" />}
              </div>
              {step.href && !step.done ? (
                <Link href={step.href} className="text-xs text-brand-300 hover:text-brand-200 transition-colors">
                  {step.label}
                </Link>
              ) : (
                <span className={`text-xs ${step.done ? "text-white/30 line-through" : "text-white/70"}`}>{step.label}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Quick links ───────────────────────────────────────────────────────────────
const QUICK_LINKS = [
  { href: "/readiness",      label: "Readiness",      icon: Target,        bg: "bg-violet-50", fg: "text-violet-600" },
  { href: "/risks",          label: "Risk Register",  icon: AlertTriangle, bg: "bg-red-50",    fg: "text-red-600"    },
  { href: "/policies",       label: "Policies",       icon: BookOpen,      bg: "bg-sky-50",    fg: "text-sky-600"    },
  { href: "/training",       label: "Training",       icon: GraduationCap, bg: "bg-amber-50",  fg: "text-amber-600"  },
  { href: "/vendors",        label: "Vendors",        icon: Building2,     bg: "bg-teal-50",   fg: "text-teal-600"   },
  { href: "/pen-tests",      label: "Pen Tests",      icon: ShieldAlert,   bg: "bg-orange-50", fg: "text-orange-600" },
  { href: "/access-reviews", label: "Access Reviews", icon: UserCheck,     bg: "bg-emerald-50",fg: "text-emerald-600"},
  { href: "/questionnaire",  label: "Questionnaire",  icon: ClipboardList, bg: "bg-pink-50",   fg: "text-pink-600"   },
  { href: "/reports",        label: "Reports",        icon: FileText,      bg: "bg-brand-50",  fg: "text-brand-600"  },
];

const FRAMEWORKS = [
  { value: "soc2",     label: "SOC 2"     },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa",    label: "HIPAA"     },
  { value: "gdpr",     label: "GDPR"      },
  { value: "pci_dss",  label: "PCI DSS"   },
  { value: "ccpa",     label: "CCPA"      },
  { value: "nist_csf", label: "NIST CSF"  },
];

function fmtDay(dateStr: string) {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

// Custom tooltip
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: {value: number}[]; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-900 text-white text-xs px-3 py-2 rounded-xl shadow-lg">
      <p className="text-white/50 mb-0.5">{label}</p>
      <p className="font-bold">{payload[0].value}{payload[0].value <= 100 ? "%" : " records"}</p>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [evidenceTotal, setEvidenceTotal] = useState(0);
  const [compliance, setCompliance] = useState<ComplianceScore | null>(null);
  const [framework, setFramework] = useState("soc2");
  const [scoreHistory, setScoreHistory] = useState<ScoreHistoryPoint[]>([]);
  const [evidenceActivity, setEvidenceActivity] = useState<EvidenceActivityPoint[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoreLoading, setScoreLoading] = useState(false);

  useEffect(() => {
    Promise.all([
      api.getIntegrations(),
      api.getEvidence({ page_size: 1 }),
      api.getComplianceScore(framework),
      api.getScoreHistory(framework, 30),
      api.getEvidenceActivity(14),
      api.getReports(1),
      api.getReadiness(framework),
    ])
      .then(([ints, ev, score, history, activity, rpts, readinessData]) => {
        setIntegrations(ints);
        setEvidenceTotal(ev.total);
        setCompliance(score);
        setScoreHistory(history);
        setEvidenceActivity(activity);
        setReports(rpts.items);
        setReadiness(readinessData);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Touch swipe to switch frameworks (mobile only — touch events don't fire on desktop)
  const touchStartX = useRef<number | null>(null);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    if (touchStartX.current === null) return;
    const delta = e.changedTouches[0].clientX - touchStartX.current;
    touchStartX.current = null;
    if (Math.abs(delta) < 50) return;
    const idx = FRAMEWORKS.findIndex((f) => f.value === framework);
    if (delta < 0 && idx < FRAMEWORKS.length - 1) handleFrameworkChange(FRAMEWORKS[idx + 1].value);
    else if (delta > 0 && idx > 0) handleFrameworkChange(FRAMEWORKS[idx - 1].value);
  };

  const handleFrameworkChange = async (fw: string) => {
    setFramework(fw);
    setScoreLoading(true);
    try {
      const [score, history, readinessData] = await Promise.all([
        api.getComplianceScore(fw),
        api.getScoreHistory(fw, 30),
        api.getReadiness(fw),
      ]);
      setCompliance(score);
      setScoreHistory(history);
      setReadiness(readinessData);
    } catch { /* ignore */ }
    finally { setScoreLoading(false); }
  };

  if (loading) {
    return (
      <div className="animate-fade-in space-y-5">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="space-y-1.5">
            <div className="h-7 w-32 bg-gray-200 rounded-xl animate-pulse" />
            <div className="h-4 w-48 bg-gray-100 rounded-xl animate-pulse" />
          </div>
          <div className="flex gap-2">
            <div className="h-9 w-24 bg-gray-100 rounded-xl animate-pulse" />
            <div className="h-9 w-36 bg-gray-100 rounded-xl animate-pulse" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 h-52 bg-gray-200 rounded-2xl animate-pulse" />
          <div className="flex flex-col gap-3">
            {[0,1,2,3].map((i) => <div key={i} className="h-[52px] bg-gray-100 rounded-2xl animate-pulse" />)}
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="h-52 bg-gray-100 rounded-2xl animate-pulse" />
          <div className="h-52 bg-gray-100 rounded-2xl animate-pulse" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[0,1,2].map((i) => <div key={i} className="h-64 bg-gray-100 rounded-2xl animate-pulse" />)}
        </div>
      </div>
    );
  }

  const activeIntegrations = integrations.filter((i) => i.status === "active").length;
  const passingControls = compliance?.controls.filter((c) => c.status === "passing").length ?? 0;
  const failingControls = compliance?.controls.filter((c) => c.status === "failing" || c.status === "warning") ?? [];
  const score = compliance?.overall_score ?? 0;

  const historyData = scoreHistory.map((p) => ({ date: fmtDay(p.ts), score: p.score }));
  const activityData = evidenceActivity.map((p) => ({ date: fmtDay(p.day), count: p.count }));

  // Trend: compare last two snapshots
  const trend = historyData.length >= 2
    ? historyData[historyData.length - 1].score - historyData[historyData.length - 2].score
    : null;

  return (
    <div className="animate-fade-in space-y-5 overflow-x-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/reports"
            className="flex items-center gap-2 text-sm font-semibold text-gray-600 border border-gray-200 hover:border-gray-300 px-3 sm:px-3.5 py-2 rounded-xl hover:bg-gray-50 transition-all">
            <FileText className="w-4 h-4" /> <span className="hidden sm:inline">Report</span>
          </Link>
          <Link href="/compliance"
            className="flex items-center gap-2 text-sm font-semibold bg-brand-600 hover:bg-brand-700 text-white px-3 sm:px-3.5 py-2 rounded-xl transition-colors">
            <Zap className="w-4 h-4" /> <span className="hidden sm:inline">View compliance</span>
          </Link>
        </div>
      </div>

      {/* ── Getting started ── */}
      <GettingStarted
        hasIntegration={integrations.length > 0}
        hasEvidence={evidenceTotal > 0}
        hasScore={!!compliance && compliance.controls.length > 0}
        hasReport={reports.length > 0}
      />

      {/* ── Hero row: Score card + mini stats ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Score hero card */}
        <div
          className="md:col-span-2 lg:col-span-2 relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-4 sm:p-6 overflow-hidden"
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {/* Radial glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-48 bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="relative min-w-0 overflow-hidden">
            <div className="flex items-center gap-3 sm:gap-6">
              <ScoreRing score={scoreLoading ? score : score} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1 flex-wrap">
                  <span className="text-xs sm:text-sm font-semibold text-white/60">Compliance score</span>
                  {trend !== null && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${trend >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                      {trend >= 0 ? "+" : ""}{trend}% vs prev
                    </span>
                  )}
                </div>
                <p className="text-3xl sm:text-4xl font-black text-white mb-3">{score}<span className="text-xl text-white/30">%</span></p>

                {/* Framework tabs — desktop: scrollable pill row; mobile: active chip + swipe dots */}
                <div className="hidden sm:block overflow-x-auto no-scrollbar">
                  <div className="flex gap-1 bg-white/10 rounded-xl p-1 w-max">
                    {FRAMEWORKS.map((fw) => (
                      <button
                        key={fw.value}
                        onClick={() => handleFrameworkChange(fw.value)}
                        disabled={scoreLoading}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all disabled:opacity-50 whitespace-nowrap ${
                          framework === fw.value
                            ? "bg-white text-slate-900 shadow-sm"
                            : "text-white/50 hover:text-white/80"
                        }`}
                      >
                        {fw.label}
                      </button>
                    ))}
                  </div>
                </div>
                {/* Mobile: active framework chip + position dots */}
                <div className="sm:hidden">
                  <div className="flex items-center gap-2 mb-2 min-w-0 flex-nowrap">
                    <span className="bg-white text-slate-900 text-[11px] font-bold px-2.5 py-1.5 rounded-lg shadow-sm max-w-[140px] truncate">
                      {FRAMEWORKS.find((f) => f.value === framework)?.label}
                    </span>
                    <span className="text-[10px] text-white/30 shrink-0">← swipe →</span>
                  </div>
                  <div className="flex gap-1">
                    {FRAMEWORKS.map((fw) => (
                      <button
                        key={fw.value}
                        onClick={() => handleFrameworkChange(fw.value)}
                        disabled={scoreLoading}
                        className={`h-1 rounded-full transition-all duration-300 disabled:opacity-50 ${
                          framework === fw.value ? "bg-white w-4" : "bg-white/25 w-1.5"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
              {/* Readiness badge — desktop only */}
              {readiness && (
                <Link href="/readiness" className="hidden sm:flex shrink-0 flex-col items-center gap-1 bg-white/10 hover:bg-white/15 transition-colors rounded-2xl px-4 py-3 text-center">
                  <Target className="w-5 h-5 text-violet-300 mb-0.5" />
                  <span className="text-2xl font-black text-white">{readiness.readiness_score}%</span>
                  <span className="text-[10px] text-white/40 font-semibold uppercase tracking-wide">Readiness</span>
                  {readiness.weeks_estimate > 0 && (
                    <span className="text-[10px] text-amber-400 font-semibold">~{readiness.weeks_estimate}wk</span>
                  )}
                </Link>
              )}
            </div>
            {/* Readiness row — mobile only */}
            {readiness && (
              <Link href="/readiness" className="sm:hidden flex items-center justify-between gap-2 mt-4 pt-3 border-t border-white/10 min-w-0">
                <div className="flex items-center gap-1.5 min-w-0">
                  <Target className="w-4 h-4 text-violet-300 shrink-0" />
                  <span className="text-xs font-semibold text-white/50 uppercase tracking-wide truncate">Readiness</span>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-sm font-bold text-white">{readiness.readiness_score}%</span>
                  {readiness.weeks_estimate > 0 && (
                    <span className="text-xs text-amber-400 font-semibold">~{readiness.weeks_estimate}wk</span>
                  )}
                  <ArrowRight className="w-3.5 h-3.5 text-white/30" />
                </div>
              </Link>
            )}
          </div>
          {/* Bottom stat strip */}
          <div className="relative mt-5 pt-4 border-t border-white/10 grid grid-cols-3 gap-2 text-center">
            <div>
              <p className="text-lg font-bold text-white">{passingControls}</p>
              <p className="text-[10px] text-white/40 font-semibold uppercase tracking-wide whitespace-nowrap">Passing</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">{failingControls.length}</p>
              <p className="text-[10px] text-white/40 font-semibold uppercase tracking-wide whitespace-nowrap">Failing</p>
            </div>
            <div>
              <p className="text-lg font-bold text-white">{compliance?.controls.length ?? 0}</p>
              <p className="text-[10px] text-white/40 font-semibold uppercase tracking-wide whitespace-nowrap">Controls</p>
            </div>
          </div>
        </div>

        {/* Mini stat cards */}
        <div className="flex flex-col gap-3">
          <MiniStat
            icon={Database}
            label="Evidence records"
            value={evidenceTotal.toLocaleString()}
            sub="across all integrations"
            color="brand"
          />
          <MiniStat
            icon={Plug}
            label="Active integrations"
            value={activeIntegrations}
            sub={`of ${integrations.length} connected`}
            color={activeIntegrations > 0 ? "green" : "brand"}
          />
          <MiniStat
            icon={Activity}
            label="Controls monitored"
            value={compliance?.controls.length ?? 0}
            sub={`${FRAMEWORKS.find(f => f.value === framework)?.label ?? framework} framework`}
            color="brand"
          />
          <MiniStat
            icon={AlertTriangle}
            label="Action items"
            value={failingControls.length}
            sub={failingControls.length > 0 ? "controls need attention" : "All controls passing"}
            color={failingControls.length > 0 ? "amber" : "green"}
          />
        </div>
      </div>

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Score trend */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-brand-500" />
              <span className="text-sm font-semibold text-gray-800">Score trend</span>
              <span className="text-xs text-gray-400">30 days</span>
            </div>
            {trend !== null && (
              <span className={`text-xs font-bold ${trend >= 0 ? "text-emerald-600" : "text-red-500"}`}>
                {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)}%
              </span>
            )}
          </div>
          {historyData.length > 1 ? (
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={historyData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0f766e" stopOpacity={0.15} />
                    <stop offset="95%" stopColor="#0f766e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Area type="monotone" dataKey="score" stroke="#0f766e" strokeWidth={2}
                  fill="url(#scoreGrad)" dot={false} activeDot={{ r: 4, fill: "#0f766e" }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[150px] flex flex-col items-center justify-center text-center gap-2">
              <div className="w-10 h-10 rounded-2xl bg-gray-50 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-gray-300" />
              </div>
              <p className="text-xs text-gray-400">Not enough data yet — check back after a few collection runs.</p>
            </div>
          )}
        </div>

        {/* Evidence activity */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center gap-2 mb-5">
            <Activity className="w-4 h-4 text-brand-500" />
            <span className="text-sm font-semibold text-gray-800">Evidence activity</span>
            <span className="text-xs text-gray-400">14 days</span>
          </div>
          {activityData.length > 0 && activityData.some((d) => d.count > 0) ? (
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={activityData} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#9ca3af" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#9ca3af" }} allowDecimals={false} axisLine={false} tickLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="count" fill="#0f766e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[150px] flex flex-col items-center justify-center text-center gap-2">
              <div className="w-10 h-10 rounded-2xl bg-gray-50 flex items-center justify-center">
                <Activity className="w-5 h-5 text-gray-300" />
              </div>
              <p className="text-xs text-gray-400">No evidence collected yet. Connect an integration to get started.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── Control breakdown ── */}
      {compliance && compliance.controls.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-brand-500" />
              <span className="text-sm font-semibold text-gray-800">Control breakdown</span>
            </div>
            <Link href="/compliance" className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold transition-colors">
              Full view <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {compliance.controls.map((c) => (
              <Link key={c.category} href={`/compliance`} className="block group">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-semibold text-gray-700 truncate group-hover:text-brand-600 transition-colors">{c.name}</span>
                    {statusBadge(c.status)}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className={`text-xs font-bold ${c.score >= 80 ? "text-emerald-600" : c.score >= 50 ? "text-amber-600" : "text-red-500"}`}>
                      {c.score}%
                    </span>
                    <ArrowRight className="w-3 h-3 text-gray-200 group-hover:text-brand-400 transition-colors" />
                  </div>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(c.score)}`} style={{ width: `${c.score}%` }} />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Bottom row: Quick links + Integrations + Action items ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Quick links */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <p className="text-sm font-semibold text-gray-800 mb-4">Platform</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {QUICK_LINKS.map(({ href, label, icon: Icon, bg, fg }) => (
              <Link
                key={href}
                href={href}
                className="flex flex-col items-center gap-1.5 p-2.5 rounded-xl hover:bg-gray-50 transition-colors group text-center"
              >
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${bg}`}>
                  <Icon className={`w-4 h-4 ${fg}`} />
                </div>
                <span className="text-[10px] font-semibold text-gray-500 group-hover:text-gray-700 leading-tight">{label}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Integrations */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Plug className="w-4 h-4 text-brand-500" />
              <span className="text-sm font-semibold text-gray-800">Integrations</span>
            </div>
            <Link href="/integrations" className="text-xs text-brand-600 font-semibold hover:text-brand-700">Manage</Link>
          </div>
          {integrations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 gap-2 text-center">
              <div className="w-10 h-10 rounded-2xl bg-gray-50 flex items-center justify-center">
                <Plug className="w-5 h-5 text-gray-300" />
              </div>
              <p className="text-xs text-gray-400">No integrations yet.</p>
              <Link href="/integrations" className="text-xs text-brand-600 font-semibold hover:underline">Connect one →</Link>
            </div>
          ) : (
            <div className="space-y-3">
              {integrations.map((i) => {
                const staleHours = i.last_collected_at
                  ? (Date.now() - new Date(i.last_collected_at).getTime()) / 36e5
                  : Infinity;
                return (
                  <div key={i.id} className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${i.status === "active" ? "bg-emerald-500" : i.status === "error" ? "bg-red-500" : "bg-gray-300"}`} />
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-gray-700 capitalize truncate">{i.integration_type.replace("_", " ")}</p>
                        <p className={`text-[10px] ${i.status === "active" ? "text-emerald-600" : i.status === "error" ? "text-red-500" : "text-gray-400"}`}>{i.status}</p>
                      </div>
                      {staleHours > 48 && <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />}
                    </div>
                    {staleBadge(i.last_collected_at)}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Action items */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-semibold text-gray-800">Action items</span>
            {failingControls.length > 0 && (
              <span className="ml-auto text-xs font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full">{failingControls.length}</span>
            )}
          </div>
          {failingControls.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 gap-2 text-center">
              <div className="w-10 h-10 rounded-2xl bg-emerald-50 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              </div>
              <p className="text-xs text-gray-400">All controls passing — great work.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {failingControls.slice(0, 5).map((c) => (
                <Link key={c.category} href="/compliance" className="flex items-start gap-2.5 group">
                  <div className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${c.status === "failing" ? "bg-red-400" : "bg-amber-400"}`} />
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-gray-700 group-hover:text-brand-600 transition-colors truncate">{c.name}</p>
                    {c.missing_types.length > 0 && (
                      <p className="text-[10px] text-gray-400 mt-0.5 truncate">
                        Missing: {c.missing_types.slice(0, 2).join(", ")}{c.missing_types.length > 2 ? ` +${c.missing_types.length - 2}` : ""}
                      </p>
                    )}
                  </div>
                  <ChevronRight className="w-3 h-3 text-gray-200 group-hover:text-brand-400 shrink-0 mt-0.5 transition-colors" />
                </Link>
              ))}
              {failingControls.length > 5 && (
                <Link href="/compliance" className="text-xs text-brand-600 font-semibold hover:underline">
                  +{failingControls.length - 5} more →
                </Link>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
