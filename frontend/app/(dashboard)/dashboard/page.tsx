"use client";

import { useEffect, useRef, useState } from "react";
import {
  AreaChart, Area, BarChart, Bar, LabelList,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { api } from "@/lib/api";
import type {
  AuditLog, ComplianceScore, DriftEvent, EvidenceActivityPoint,
  Integration, ScoreHistoryPoint, ReadinessData, TimeMachineResult,
} from "@/lib/types";
import Link from "next/link";
import { Tooltip } from "@/components/ui/tooltip";
import {
  ShieldCheck, Plug, AlertCircle, CheckCircle2, Clock, History,
  TrendingUp, Activity, AlertTriangle, ArrowRight, X,
  PartyPopper, Database, Target, GraduationCap, Building2,
  UserCheck, ShieldAlert, BookOpen, ClipboardList, Zap,
  FileText, Globe, ChevronRight, ChevronLeft, Lock, Sparkles,
} from "lucide-react";
import { usePlan } from "@/hooks/usePlan";
import { useUpgrade } from "@/components/plan-gate";
import type { Report } from "@/lib/types";

// ── Mini donut ring ────────────────────────────────────────────────────────────
function MiniRing({
  value, max, color, label, sub,
}: { value: number; max: number; color: string; label: string; sub?: string }) {
  const size = 72;
  const r = 28;
  const circ = 2 * Math.PI * r;
  const pct = max > 0 ? Math.min(value / max, 1) : 0;
  const offset = circ - pct * circ;
  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="-rotate-90" width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="6" />
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth="6"
            strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)" }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xl font-black leading-none" style={{ color }}>{value}</span>
        </div>
      </div>
      <div className="text-center">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-white/40">{label}</p>
        {sub && <p className="text-[9px] text-white/20 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

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
  label, value, sub, icon: Icon, color = "brand", tooltip,
}: {
  label: string; value: string | number; sub?: string;
  icon: React.ElementType; color?: "brand" | "green" | "amber" | "red"; tooltip?: string;
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
  const inner = (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-4 flex items-center gap-3.5 w-full">
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
  if (tooltip) return <Tooltip content={tooltip} side="right">{inner}</Tooltip>;
  return inner;
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

type OnboardingStatus = {
  has_integration: boolean; has_evidence: boolean; has_vendor: boolean;
  has_member: boolean; has_training: boolean; has_report: boolean; has_risk: boolean;
} | null;

function GettingStarted({ status }: { status: OnboardingStatus }) {
  const [dismissed, setDismissed] = useState(() =>
    typeof window !== "undefined" && localStorage.getItem(CHECKLIST_KEY) === "1"
  );
  const s = status;
  const steps = [
    { label: "Create your account",            done: true },
    { label: "Connect an integration",          done: s?.has_integration ?? false,  href: "/integrations" },
    { label: "Collect evidence automatically",  done: s?.has_evidence ?? false,     href: "/integrations" },
    { label: "Add a vendor",                    done: s?.has_vendor ?? false,       href: "/vendors" },
    { label: "Invite a team member",            done: s?.has_member ?? false,       href: "/team" },
    { label: "Assign security training",        done: s?.has_training ?? false,     href: "/training" },
    { label: "Generate a compliance report",    done: s?.has_report ?? false,       href: "/reports" },
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
  { value: "soc2",     label: "SOC 2",     region: "US"     },
  { value: "iso27001", label: "ISO 27001", region: "INTL"   },
  { value: "hipaa",    label: "HIPAA",     region: "US"     },
  { value: "gdpr",     label: "GDPR",      region: "EU"     },
  { value: "pci_dss",  label: "PCI DSS",   region: "INTL"   },
  { value: "ccpa",     label: "CCPA",      region: "US"     },
  { value: "nist_csf", label: "NIST CSF",  region: "US"     },
  { value: "dpdp",     label: "DPDP Act",  region: "IN"     },
  { value: "cert_in",  label: "CERT-In",   region: "IN"     },
];

function timeAgo(dateStr: string) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function ActivityIcon({ action }: { action: string }) {
  if (action.startsWith("evidence")) return <Database className="w-3.5 h-3.5 text-brand-500" />;
  if (action.startsWith("integration")) return <Plug className="w-3.5 h-3.5 text-teal-500" />;
  if (action.startsWith("user") || action.startsWith("login")) return <UserCheck className="w-3.5 h-3.5 text-violet-500" />;
  if (action.startsWith("plan")) return <Zap className="w-3.5 h-3.5 text-amber-500" />;
  if (action.startsWith("report")) return <FileText className="w-3.5 h-3.5 text-sky-500" />;
  if (action.startsWith("risk")) return <AlertTriangle className="w-3.5 h-3.5 text-red-400" />;
  if (action.startsWith("vendor")) return <Building2 className="w-3.5 h-3.5 text-teal-500" />;
  return <Activity className="w-3.5 h-3.5 text-gray-400" />;
}

function fmtDay(dateStr: string) {
  const d = new Date(dateStr);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

// Custom tooltip
function ChartTooltip({ active, payload, label, unit }: { active?: boolean; payload?: {value: number}[]; label?: string; unit?: string }) {
  if (!active || !payload?.length) return null;
  const val = payload[0].value;
  const display = unit ? `${val.toLocaleString()} ${unit}` : val <= 100 ? `${val}pts` : val.toLocaleString();
  return (
    <div className="bg-gray-900 text-white text-xs px-3 py-2 rounded-xl shadow-xl border border-white/10">
      <p className="text-white/50 text-[10px] mb-0.5">{label}</p>
      <p className="font-bold text-sm">{display}</p>
    </div>
  );
}

// ── Compliance Drift Feed ──────────────────────────────────────────────────────
const STATUS_ARROW: Record<string, string> = {
  passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
};

const STATUS_COLOR: Record<string, string> = {
  passing: "text-emerald-600", warning: "text-amber-600",
  failing: "text-red-500", no_evidence: "text-gray-400",
};

function DriftFeed({ events }: { events: DriftEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5 h-full flex flex-col">
        <div className="flex items-center gap-2 mb-5">
          <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-gray-900">Compliance Drift</h3>
          </div>
          <span className="ml-auto text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-100 px-2 py-0.5 rounded-full">All stable</span>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 flex items-center justify-center">
              <ShieldCheck className="w-7 h-7 text-emerald-500" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800">No drift detected</p>
              <p className="text-xs text-gray-400 mt-1">All control statuses are stable — no regressions in the last 30 days.</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center">
            <Activity className="w-3.5 h-3.5 text-red-500" />
          </div>
          <h3 className="text-sm font-semibold text-gray-900">Compliance Drift</h3>
          <span className="text-[10px] font-semibold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md">{events.length} change{events.length !== 1 ? "s" : ""}</span>
        </div>
        {events.some(e => e.is_regression) && (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-50 border border-red-100 text-red-600">
            {events.filter(e => e.is_regression).length} regression{events.filter(e => e.is_regression).length !== 1 ? "s" : ""}
          </span>
        )}
      </div>
      <div className="space-y-2">
        {events.slice(0, 8).map((e) => (
          <div key={e.id} className={`flex items-start gap-3 rounded-xl p-3 ${e.is_regression ? "bg-red-50/60" : "bg-emerald-50/60"}`}>
            <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${e.is_regression ? "bg-red-100" : "bg-emerald-100"}`}>
              {e.is_regression
                ? <AlertTriangle className="w-3 h-3 text-red-500" />
                : <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-gray-900 truncate">{e.control_name}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`text-[10px] font-medium ${STATUS_COLOR[e.previous_status] ?? "text-gray-500"}`}>
                  {STATUS_ARROW[e.previous_status] ?? e.previous_status}
                </span>
                <ArrowRight className="w-3 h-3 text-gray-400 shrink-0" />
                <span className={`text-[10px] font-semibold ${STATUS_COLOR[e.new_status] ?? "text-gray-500"}`}>
                  {STATUS_ARROW[e.new_status] ?? e.new_status}
                </span>
                <span className="text-[10px] text-gray-400 ml-1">· {e.framework.toUpperCase()}</span>
              </div>
              {e.trigger_integration && (
                <p className="text-[10px] text-gray-400 mt-0.5">via {e.trigger_integration}</p>
              )}
            </div>
            <p className="text-[10px] text-gray-400 shrink-0 mt-0.5">
              {new Date(e.detected_at).toLocaleDateString([], { month: "short", day: "numeric" })}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const { isPro } = usePlan();
  const { trigger: triggerUpgrade } = useUpgrade();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [evidenceTotal, setEvidenceTotal] = useState(0);
  const [compliance, setCompliance] = useState<ComplianceScore | null>(null);
  const [framework, setFramework] = useState("soc2");
  const [scoreHistory, setScoreHistory] = useState<ScoreHistoryPoint[]>([]);
  const [evidenceActivity, setEvidenceActivity] = useState<EvidenceActivityPoint[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [readiness, setReadiness] = useState<ReadinessData | null>(null);
  const [recentActivity, setRecentActivity] = useState<AuditLog[]>([]);
  const [driftEvents, setDriftEvents] = useState<DriftEvent[]>([]);
  const [integrationsExpanded, setIntegrationsExpanded] = useState(false);
  const [loading, setLoading] = useState(true);
  const [scoreLoading, setScoreLoading] = useState(false);
  const [tmDate, setTmDate] = useState<string | null>(null);
  const [tmData, setTmData] = useState<TimeMachineResult | null>(null);
  const [tmLoading, setTmLoading] = useState(false);
  const [tmPickerOpen, setTmPickerOpen] = useState(false);
  const [tmInputDate, setTmInputDate] = useState("");
  const [allScores, setAllScores] = useState<Record<string, number>>({});
  const [onboardingStatus, setOnboardingStatus] = useState<{
    has_integration: boolean; has_evidence: boolean; has_vendor: boolean;
    has_member: boolean; has_training: boolean; has_report: boolean; has_risk: boolean;
  } | null>(null);

  useEffect(() => {
    api.getOnboardingStatus().then(setOnboardingStatus).catch(() => {});
    api.driftEvents(20).then(setDriftEvents).catch(() => {});

    Promise.all([
      api.getIntegrations(),
      api.getEvidence({ page_size: 1 }),
      api.getComplianceScore(framework),
      api.getScoreHistory(framework, 30),
      api.getEvidenceActivity(14),
      api.getReports(1),
      api.getReadiness(framework),
      api.getAuditLog({ page_size: 6 }),
    ])
      .then(([ints, ev, score, history, activity, rpts, readinessData, auditLog]) => {
        setIntegrations(ints);
        setEvidenceTotal(ev.total);
        setCompliance(score);
        setAllScores(prev => ({ ...prev, soc2: score.overall_score }));
        setScoreHistory(history);
        setEvidenceActivity(activity);
        setReports(rpts.items);
        setReadiness(readinessData);
        setRecentActivity(auditLog.items);
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
      setAllScores(prev => ({ ...prev, [fw]: score.overall_score }));
      setScoreHistory(history);
      setReadiness(readinessData);
    } catch { /* ignore */ }
    finally { setScoreLoading(false); }
  };

  const handleTimeMachine = async (date: string) => {
    setTmDate(date);
    setTmLoading(true);
    try {
      const result = await api.timeMachine(date, framework);
      setTmData(result);
      setTmPickerOpen(false);
    } catch {
      setTmData(null);
      setTmDate(null);
    } finally {
      setTmLoading(false);
    }
  };

  const exitTimeMachine = () => {
    setTmDate(null);
    setTmData(null);
    setTmInputDate("");
    setTmPickerOpen(false);
  };

  // Background: load overview scores for all frameworks after initial load
  useEffect(() => {
    if (loading) return;
    for (const fw of FRAMEWORKS) {
      if (fw.value === "soc2") continue;
      api.getComplianceScore(fw.value)
        .then(s => setAllScores(prev => ({ ...prev, [fw.value]: s.overall_score })))
        .catch(() => {});
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loading]);

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
  const frameworkIdx = FRAMEWORKS.findIndex(f => f.value === framework);

  // Time machine: override ALL display values when viewing a historical date
  const activeCompliance: ComplianceScore | null = tmData ? tmData.historical : compliance;
  const activeScore = activeCompliance?.overall_score ?? 0;
  const activePassingControls = activeCompliance?.controls.filter((c) => c.status === "passing").length ?? 0;
  const activeFailingControls = activeCompliance?.controls.filter((c) => c.status === "failing" || c.status === "warning") ?? [];
  const activeEvidenceTotal = tmData ? tmData.evidence_count : evidenceTotal;
  const activeIntegrationCount = tmData ? tmData.integration_count : activeIntegrations;
  const activeIntegrationSub = tmData ? `connected as of ${tmDate}` : `of ${integrations.length} connected`;

  // Time machine: filter time-series data to the selected date
  const tmCutoff = tmData && tmDate ? new Date(tmDate + "T23:59:59Z") : null;
  const activeActivity       = tmCutoff ? recentActivity.filter((e) => new Date(e.created_at) <= tmCutoff!) : recentActivity;
  const activeDriftEvents    = tmCutoff ? driftEvents.filter((e) => new Date(e.detected_at) <= tmCutoff!) : driftEvents;
  const activeIntegrationsList = tmCutoff ? integrations.filter((i) => new Date(i.created_at) <= tmCutoff!) : integrations;

  const historyData = scoreHistory.map((p) => ({ date: fmtDay(p.ts), score: p.score }));
  // Trim leading zeros so the trend starts where evidence actually begins
  const firstMeaningfulIdx = historyData.findIndex((d) => d.score > 0);
  const trimmedHistory = firstMeaningfulIdx > 0
    ? historyData.slice(Math.max(0, firstMeaningfulIdx - 1))
    : historyData;

  const activityData = evidenceActivity.map((p) => ({ date: fmtDay(p.day), count: p.count }));
  const totalActivityRecords = activityData.reduce((s, d) => s + d.count, 0);

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
          {/* Time Machine toggle */}
          <button
            onClick={() => { setTmPickerOpen((p) => !p); if (tmData) exitTimeMachine(); }}
            title="Time Machine — view compliance at a past date"
            className={`flex items-center gap-2 text-sm font-semibold border px-3 sm:px-3.5 py-2 rounded-xl transition-all ${
              tmData || tmPickerOpen
                ? "bg-violet-600 border-violet-600 text-white hover:bg-violet-700"
                : "text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-50"
            }`}
          >
            <History className="w-4 h-4" />
            <span className="hidden sm:inline">Time Machine</span>
          </button>
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
      <GettingStarted status={onboardingStatus} />

      {/* ── Time Machine inline picker ── */}
      {tmPickerOpen && !tmData && (
        <div className="bg-violet-50 border border-violet-200 rounded-2xl p-4 sm:p-5">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-8 h-8 rounded-xl bg-violet-100 flex items-center justify-center shrink-0">
              <History className="w-4 h-4 text-violet-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-violet-900">Compliance Time Machine</p>
              <p className="text-xs text-violet-500 mt-0.5">View your full compliance posture — score, evidence, integrations — as it was on any past date.</p>
            </div>
            <button onClick={() => setTmPickerOpen(false)} className="text-violet-400 hover:text-violet-600 transition-colors shrink-0 mt-0.5">
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1">
              <label className="block text-xs font-semibold text-violet-700 mb-1.5">Select a date in the past</label>
              <input
                type="date"
                max={new Date(Date.now() - 86_400_000).toISOString().split("T")[0]}
                min="2020-01-01"
                value={tmInputDate}
                onChange={(e) => setTmInputDate(e.target.value)}
                className="w-full border border-violet-200 rounded-xl px-3 py-2.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-violet-400 bg-white"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={() => tmInputDate && handleTimeMachine(tmInputDate)}
                disabled={!tmInputDate || tmLoading}
                className="w-full sm:w-auto bg-violet-600 hover:bg-violet-700 disabled:opacity-40 text-white text-sm font-semibold px-5 py-2.5 rounded-xl transition-colors whitespace-nowrap"
              >
                {tmLoading ? "Loading…" : "Go back in time"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Time Machine banner ── */}
      {(tmData || tmLoading) && (
        <div className={`flex items-center gap-3 rounded-2xl px-4 py-3 border transition-all ${
          tmLoading
            ? "bg-violet-50 border-violet-100"
            : "bg-gradient-to-r from-violet-900 to-violet-800 border-violet-700/40"
        }`}>
          <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${tmLoading ? "bg-violet-100" : "bg-white/10"}`}>
            {tmLoading
              ? <Clock className="w-4 h-4 text-violet-500 animate-spin" />
              : <History className="w-4 h-4 text-violet-200" />}
          </div>
          {tmLoading ? (
            <p className="text-sm font-medium text-violet-600 flex-1">Loading historical data…</p>
          ) : tmData && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold text-white">
                  Viewing compliance as of{" "}
                  {new Date(tmDate! + "T00:00:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
                </p>
                <p className="text-xs text-violet-300 mt-0.5">
                  Score was <span className="font-bold text-white">{tmData.historical.overall_score}%</span>
                  {tmData.delta !== 0 && (
                    <span className={tmData.delta < 0 ? " text-emerald-300" : " text-red-300"}>
                      {" "}· {tmData.delta < 0 ? `${tmData.delta}pts` : `+${tmData.delta}pts`} vs today ({tmData.today_score}%)
                    </span>
                  )}
                  {tmData.delta === 0 && <span className="text-violet-300"> · same as today</span>}
                </p>
              </div>
              <button onClick={exitTimeMachine} className="shrink-0 text-violet-300 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10">
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      )}

      {/* ── Hero row: Score card + Quick Actions ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Score hero card */}
        <div
          id="tour-score"
          className="lg:col-span-2 relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-4 sm:p-6 overflow-hidden min-h-[220px] sm:min-h-[200px]"
          onTouchStart={handleTouchStart}
          onTouchEnd={handleTouchEnd}
        >
          {/* Radial glow */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-48 bg-brand-500/15 rounded-full blur-3xl pointer-events-none" />
          <div className="relative min-w-0 overflow-y-hidden">
            <div className="flex items-center gap-3 sm:gap-6">
              <ScoreRing score={activeScore} />
              <div className="flex-1 min-w-0">
                <div className="flex flex-col gap-0.5 mb-1">
                  <span className="text-xs sm:text-sm font-semibold text-white/60">
                    {tmData ? "Compliance score then" : "Compliance score"}
                  </span>
                  {!tmData && trend !== null && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full w-fit ${trend >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                      {trend >= 0 ? "+" : ""}{trend}% vs prev
                    </span>
                  )}
                  {tmData && (
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full w-fit ${tmData.delta <= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}>
                      {tmData.delta <= 0 ? "" : "+"}{tmData.delta}pts vs today
                    </span>
                  )}
                </div>
                <p className="text-3xl sm:text-4xl font-black text-white mb-3">{activeScore}<span className="text-xl text-white/30">%</span></p>

                {/* Framework navigation — prev/next carousel */}
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => { if (frameworkIdx > 0) { const fw = FRAMEWORKS[frameworkIdx - 1]; if (!isPro && fw.value !== "soc2") triggerUpgrade(); else if (!scoreLoading) handleFrameworkChange(fw.value); } }}
                      disabled={frameworkIdx === 0 || scoreLoading}
                      aria-label="Previous framework"
                      className="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center disabled:opacity-20 transition-colors shrink-0"
                    >
                      <ChevronLeft className="w-3.5 h-3.5 text-white" />
                    </button>
                    <div className="min-w-0 px-0.5">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-sm font-bold text-white leading-tight">
                          {FRAMEWORKS[frameworkIdx].label}
                        </span>
                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded leading-none uppercase tracking-wide ${
                          FRAMEWORKS[frameworkIdx].region === "IN"   ? "bg-orange-500/25 text-orange-300" :
                          FRAMEWORKS[frameworkIdx].region === "EU"   ? "bg-sky-500/25 text-sky-300" :
                          FRAMEWORKS[frameworkIdx].region === "INTL" ? "bg-purple-500/25 text-purple-300" :
                          "bg-brand-500/25 text-brand-300"
                        }`}>
                          {FRAMEWORKS[frameworkIdx].region}
                        </span>
                        {!isPro && framework !== "soc2" && (
                          <Lock className="w-3 h-3 text-amber-400 shrink-0" />
                        )}
                      </div>
                      <p className="text-[10px] text-white/30 mt-0.5 tabular-nums">{frameworkIdx + 1} / {FRAMEWORKS.length}</p>
                    </div>
                    <button
                      onClick={() => { if (frameworkIdx < FRAMEWORKS.length - 1) { const fw = FRAMEWORKS[frameworkIdx + 1]; if (!isPro && fw.value !== "soc2") triggerUpgrade(); else if (!scoreLoading) handleFrameworkChange(fw.value); } }}
                      disabled={frameworkIdx === FRAMEWORKS.length - 1 || scoreLoading}
                      aria-label="Next framework"
                      className="w-7 h-7 rounded-lg bg-white/10 hover:bg-white/20 flex items-center justify-center disabled:opacity-20 transition-colors shrink-0"
                    >
                      <ChevronRight className="w-3.5 h-3.5 text-white" />
                    </button>
                  </div>
                  {/* Dot strip */}
                  <div className="flex items-center gap-1 pl-9">
                    {FRAMEWORKS.map((fw, i) => {
                      const locked = !isPro && fw.value !== "soc2";
                      return (
                        <button
                          key={fw.value}
                          onClick={() => locked ? triggerUpgrade() : handleFrameworkChange(fw.value)}
                          disabled={scoreLoading}
                          title={fw.label}
                          className={`rounded-full transition-all duration-300 disabled:opacity-50 ${
                            i === frameworkIdx ? "bg-white w-5 h-1.5" : locked ? "bg-amber-400/40 w-1.5 h-1 hover:bg-amber-400/60" : "bg-white/25 w-1.5 h-1 hover:bg-white/40"
                          }`}
                        />
                      );
                    })}
                  </div>
                </div>
              </div>
              {/* Readiness badge — desktop only, hidden in time machine mode */}
              {readiness && !tmData && (
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
            {/* Readiness row — mobile only, hidden in time machine mode */}
            {readiness && !tmData && (
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
          {/* Mini donut rings */}
          <div className="relative mt-5 pt-4 border-t border-white/10 grid grid-cols-3 gap-2">
            <MiniRing
              value={activePassingControls}
              max={activeCompliance?.controls.length ?? 1}
              color="#10b981"
              label="Passing"
              sub={`of ${activeCompliance?.controls.length ?? 0}`}
            />
            <MiniRing
              value={activeFailingControls.length}
              max={activeCompliance?.controls.length ?? 1}
              color={activeFailingControls.length > 0 ? "#f87171" : "rgba(255,255,255,0.15)"}
              label="Failing"
              sub={activeFailingControls.length === 0 ? "none" : "need attention"}
            />
            <MiniRing
              value={activeScore}
              max={100}
              color="#818cf8"
              label="Score"
              sub="out of 100"
            />
          </div>
        </div>

        {/* Quick Actions panel */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] overflow-hidden flex flex-col">
          <div className="px-5 py-4 border-b border-gray-100">
            <p className="text-sm font-bold text-gray-900">Quick Actions</p>
            <p className="text-xs text-gray-400 mt-0.5">Jump to key tasks</p>
          </div>
          <div className="p-3 space-y-1 flex-1">
            <Link href="/audit-package"
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-violet-50 group transition-colors">
              <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center shrink-0 group-hover:bg-violet-100 transition-colors">
                <Sparkles className="w-4 h-4 text-violet-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 group-hover:text-violet-700 transition-colors">Run AI Audit Package</p>
                <p className="text-xs text-gray-400">Generate full audit prep docs</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-violet-400 shrink-0 transition-colors" />
            </Link>
            <Link href="/reports"
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-sky-50 group transition-colors">
              <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center shrink-0 group-hover:bg-sky-100 transition-colors">
                <FileText className="w-4 h-4 text-sky-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 group-hover:text-sky-700 transition-colors">Generate Report</p>
                <p className="text-xs text-gray-400">SOC 2, ISO 27001 &amp; more</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-sky-400 shrink-0 transition-colors" />
            </Link>
            <Link href="/integrations"
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-emerald-50 group transition-colors">
              <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center shrink-0 group-hover:bg-emerald-100 transition-colors">
                <Plug className="w-4 h-4 text-emerald-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 group-hover:text-emerald-700 transition-colors">Connect Integration</p>
                <p className="text-xs text-gray-400">GitHub, AWS, GCP &amp; more</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-emerald-400 shrink-0 transition-colors" />
            </Link>
            <Link href="/compliance"
              className="flex items-center gap-3 p-3 rounded-xl hover:bg-brand-50 group transition-colors">
              <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center shrink-0 group-hover:bg-brand-100 transition-colors">
                <ShieldCheck className="w-4 h-4 text-brand-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 transition-colors">Review Controls</p>
                <p className="text-xs text-gray-400">Check control health &amp; gaps</p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-300 group-hover:text-brand-400 shrink-0 transition-colors" />
            </Link>
          </div>
        </div>
      </div>

      {/* ── Stat cards row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MiniStat
          icon={Database}
          label="Evidence records"
          value={activeEvidenceTotal.toLocaleString()}
          sub={tmData ? `collected by ${tmDate}` : "across all integrations"}
          color="brand"
          tooltip="Total pieces of evidence collected from your connected tools"
        />
        <MiniStat
          icon={Plug}
          label="Active integrations"
          value={activeIntegrationCount}
          sub={activeIntegrationSub}
          color={activeIntegrationCount > 0 ? "green" : "brand"}
          tooltip="Integrations currently collecting evidence on schedule"
        />
        <MiniStat
          icon={Activity}
          label="Controls monitored"
          value={activeCompliance?.controls.length ?? 0}
          sub={`${FRAMEWORKS.find(f => f.value === framework)?.label ?? framework} framework`}
          color="brand"
          tooltip="Number of compliance controls being tracked for this framework"
        />
        <MiniStat
          icon={AlertTriangle}
          label="Action items"
          value={activeFailingControls.length}
          sub={activeFailingControls.length > 0 ? "controls need attention" : "All controls passing"}
          color={activeFailingControls.length > 0 ? "amber" : "green"}
          tooltip="Controls that are failing or missing evidence and need your attention"
        />
      </div>

      {/* ── Charts ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Score trend */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center">
                <TrendingUp className="w-3.5 h-3.5 text-brand-600" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Score trend</span>
            </div>
            {trend !== null && (
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${trend >= 0 ? "bg-emerald-50 text-emerald-600" : "bg-red-50 text-red-500"}`}>
                {trend >= 0 ? "↑" : "↓"}{Math.abs(trend)}pts
              </span>
            )}
          </div>
          <p className="text-[11px] text-gray-400 mb-4 ml-9">Last 30 days · {FRAMEWORKS.find(f => f.value === framework)?.label}</p>
          {historyData.length > 1 ? (
            <ResponsiveContainer width="100%" height={160}>
              <AreaChart data={historyData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0f766e" stopOpacity={0.18} />
                    <stop offset="100%" stopColor="#0f766e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false}
                  interval={Math.max(0, Math.floor(historyData.length / 6) - 1)} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} tickCount={5} />
                <RechartsTooltip content={<ChartTooltip unit="pts" />} cursor={{ stroke: "#e2e8f0", strokeWidth: 1 }} />
                {score > 0 && (
                  <ReferenceLine y={score} stroke="#0f766e" strokeDasharray="4 3" strokeWidth={1} strokeOpacity={0.4} />
                )}
                <Area type="monotone" dataKey="score" stroke="#0f766e" strokeWidth={2.5}
                  fill="url(#scoreGrad)" dot={false}
                  activeDot={{ r: 5, fill: "#0f766e", stroke: "#fff", strokeWidth: 2 }} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[160px] flex flex-col items-center justify-center text-center gap-2.5">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-gray-200" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">No trend yet</p>
                <p className="text-xs text-gray-400 mt-0.5">Check back after a few collection runs</p>
              </div>
            </div>
          )}
        </div>

        {/* Evidence activity */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center">
                <Activity className="w-3.5 h-3.5 text-brand-600" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Evidence activity</span>
            </div>
            {totalActivityRecords > 0 && (
              <span className="text-xs font-bold text-gray-700 bg-gray-50 px-2 py-0.5 rounded-full border border-gray-100">
                {totalActivityRecords.toLocaleString()} records
              </span>
            )}
          </div>
          <p className="text-[11px] text-gray-400 mb-4 ml-9">Last 14 days · records collected per day</p>
          {activityData.length > 0 && activityData.some((d) => d.count > 0) ? (
            <ResponsiveContainer width="100%" height={160}>
              <BarChart data={activityData} barCategoryGap="40%" margin={{ top: 18, right: 8, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#0f766e" stopOpacity={0.85} />
                    <stop offset="100%" stopColor="#0f766e" stopOpacity={0.4} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="2 4" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#94a3b8" }} axisLine={false} tickLine={false} interval="preserveStartEnd" />
                <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} allowDecimals={false} axisLine={false} tickLine={false} tickCount={4} />
                <RechartsTooltip content={<ChartTooltip unit="records" />} cursor={{ fill: "#f8fafc" }} />
                <Bar dataKey="count" fill="url(#barGrad)" radius={[5, 5, 0, 0]} maxBarSize={40}>
                  <LabelList dataKey="count" position="top"
                    formatter={(v: unknown) => (typeof v === "number" && v > 0) ? v.toLocaleString() : ""}
                    style={{ fontSize: "9px", fill: "#64748b", fontWeight: 700 }} />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[160px] flex flex-col items-center justify-center text-center gap-2.5">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
                <Activity className="w-5 h-5 text-gray-200" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">No evidence yet</p>
                <p className="text-xs text-gray-400 mt-0.5">Connect an integration to start collecting</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Control breakdown ── */}
      {activeCompliance && activeCompliance.controls.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${tmData ? "bg-violet-50" : "bg-brand-50"}`}>
                {tmData ? <History className="w-3.5 h-3.5 text-violet-600" /> : <ShieldCheck className="w-3.5 h-3.5 text-brand-600" />}
              </div>
              <span className="text-sm font-semibold text-gray-800">
                Control breakdown{tmData ? ` · ${new Date(tmDate! + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}` : ""}
              </span>
            </div>
            {!tmData && (
              <Link href="/compliance" className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-700 font-semibold transition-colors">
                Full view <ArrowRight className="w-3 h-3" />
              </Link>
            )}
          </div>
          <div className="space-y-4">
            {activeCompliance.controls.map((c) => (
              <Link key={c.category} href="/compliance" className="block group">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className="text-xs font-semibold text-gray-700 truncate group-hover:text-brand-600 transition-colors">{c.name}</span>
                    {statusBadge(c.status)}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    {c.evidence_count !== undefined && (
                      <span className="text-[10px] text-gray-400">{c.evidence_count} records</span>
                    )}
                    <span className={`text-xs font-bold tabular-nums ${c.score >= 80 ? "text-emerald-600" : c.score >= 50 ? "text-amber-600" : "text-red-500"}`}>
                      {c.score}%
                    </span>
                  </div>
                </div>
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(c.score)}`}
                    style={{ width: `${c.score}%` }}
                  />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* ── Framework overview ── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Globe className="w-4 h-4 text-brand-500" />
            <span className="text-sm font-semibold text-gray-800">Frameworks</span>
          </div>
          <Link href="/compliance" className="text-xs text-brand-600 font-semibold hover:text-brand-700 transition-colors">View all →</Link>
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2">
          {FRAMEWORKS.map((fw) => {
            const locked = !isPro && fw.value !== "soc2";
            const isActive = fw.value === framework;
            const displayScore = isActive ? activeScore : allScores[fw.value];
            const regionClass =
              fw.region === "IN"   ? "bg-orange-50 text-orange-400 border-orange-100" :
              fw.region === "EU"   ? "bg-sky-50 text-sky-400 border-sky-100" :
              fw.region === "INTL" ? "bg-purple-50 text-purple-400 border-purple-100" :
              "bg-brand-50 text-brand-500 border-brand-100";
            return (
              <button
                key={fw.value}
                onClick={() => locked ? triggerUpgrade() : handleFrameworkChange(fw.value)}
                disabled={scoreLoading}
                className={`relative flex flex-col items-start gap-1 p-2.5 rounded-xl border text-left transition-all disabled:opacity-60 ${
                  isActive
                    ? "border-brand-200 bg-brand-50 ring-1 ring-brand-200"
                    : locked
                    ? "border-gray-100 bg-gray-50"
                    : "border-gray-100 bg-white hover:border-gray-200 hover:bg-gray-50"
                }`}
              >
                <div className="flex items-start justify-between w-full gap-1">
                  <span className={`text-[9px] font-bold uppercase tracking-wide leading-tight ${isActive ? "text-brand-600" : "text-gray-500"}`}>
                    {fw.label}
                  </span>
                  {locked
                    ? <Lock className="w-2.5 h-2.5 text-gray-300 shrink-0 mt-px" />
                    : <span className={`text-[8px] font-bold px-1 py-px rounded border leading-none shrink-0 ${regionClass}`}>{fw.region}</span>
                  }
                </div>
                {locked ? (
                  <span className="text-[9px] text-amber-500 font-semibold mt-0.5">Upgrade</span>
                ) : displayScore !== undefined ? (
                  <>
                    <span className={`text-base font-black leading-none mt-0.5 ${displayScore >= 80 ? "text-emerald-600" : displayScore >= 50 ? "text-amber-600" : "text-gray-800"}`}>
                      {displayScore}<span className="text-[10px] font-bold text-gray-400">%</span>
                    </span>
                    <div className="w-full h-0.5 bg-gray-100 rounded-full overflow-hidden mt-1">
                      <div className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(displayScore)}`} style={{ width: `${displayScore}%` }} />
                    </div>
                  </>
                ) : (
                  <span className="text-xs font-bold text-gray-200 leading-none mt-0.5">—</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Recent activity + Recent reports ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Recent activity — timeline style */}
        <div className="md:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-sky-50 flex items-center justify-center">
                <Clock className="w-3.5 h-3.5 text-sky-600" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Recent activity</span>
            </div>
            <Link href="/audit" className="flex items-center gap-0.5 text-xs text-brand-600 font-semibold hover:text-brand-700 transition-colors">
              View all <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {activeActivity.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
                <Clock className="w-5 h-5 text-gray-200" />
              </div>
              <p className="text-sm text-gray-400">{tmData ? "No activity on this date" : "No activity logged yet"}</p>
            </div>
          ) : (
            <div className="relative">
              <div className="absolute left-[13px] top-2 bottom-2 w-px bg-gradient-to-b from-gray-200 via-gray-100 to-transparent pointer-events-none" />
              <div className="space-y-0.5">
                {activeActivity.map((entry) => (
                  <div key={entry.id} className="flex items-start gap-3 group rounded-xl hover:bg-gray-50/80 px-2 py-2.5 -mx-2 transition-colors cursor-default">
                    <div className="w-7 h-7 rounded-full bg-white border border-gray-200 flex items-center justify-center shrink-0 z-10 shadow-sm group-hover:border-brand-200 group-hover:shadow-none transition-all">
                      <ActivityIcon action={entry.action} />
                    </div>
                    <div className="min-w-0 flex-1 pt-0.5">
                      <p className="text-xs font-semibold text-gray-800 truncate">{entry.action_label}</p>
                      <p className="text-[10px] text-gray-400 truncate mt-0.5">{entry.user_email ?? "System"}</p>
                    </div>
                    <span className="text-[10px] text-gray-400 shrink-0 pt-1 tabular-nums">{timeAgo(entry.created_at)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent reports */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center">
                <FileText className="w-3.5 h-3.5 text-brand-600" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Reports</span>
            </div>
            <Link href="/reports" className="flex items-center gap-0.5 text-xs text-brand-600 font-semibold hover:text-brand-700 transition-colors">
              All <ArrowRight className="w-3 h-3" />
            </Link>
          </div>
          {reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
                <FileText className="w-5 h-5 text-gray-200" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">No reports yet</p>
                <p className="text-[11px] text-gray-400 mt-0.5">Generate your first compliance report</p>
              </div>
              <Link href="/reports" className="text-xs font-semibold text-brand-600 border border-brand-200 hover:bg-brand-50 px-4 py-1.5 rounded-xl transition-colors">
                Generate report
              </Link>
            </div>
          ) : (
            <div className="space-y-1.5">
              {reports.slice(0, 4).map((r) => (
                <div key={r.id} className="group flex items-center gap-2.5 p-2.5 rounded-xl hover:bg-gray-50 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
                    <FileText className="w-3.5 h-3.5 text-brand-500" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-gray-800 truncate capitalize">
                      {r.report_type.replace(/_/g, " ")} — {r.framework.toUpperCase()}
                    </p>
                    {r.generated_at ? (
                      <p className="text-[10px] text-gray-400 mt-0.5">{new Date(r.generated_at).toLocaleDateString()}</p>
                    ) : (
                      <p className="text-[10px] text-amber-600 font-medium mt-0.5 flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse inline-block" /> Processing…
                      </p>
                    )}
                  </div>
                  {r.file_url && (
                    <a href={r.file_url} target="_blank" rel="noopener noreferrer"
                      className="w-7 h-7 rounded-lg bg-brand-50 hover:bg-brand-100 flex items-center justify-center transition-colors shrink-0" title="Download">
                      <span className="text-brand-600 text-sm font-bold leading-none">↓</span>
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Status row: Drift (2/3) + Action Items (1/3) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <DriftFeed events={activeDriftEvents} />
        </div>

        {/* Action items */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center ${activeFailingControls.length > 0 ? "bg-amber-50" : "bg-emerald-50"}`}>
                <AlertTriangle className={`w-3.5 h-3.5 ${activeFailingControls.length > 0 ? "text-amber-500" : "text-emerald-500"}`} />
              </div>
              <span className="text-sm font-semibold text-gray-800">Action items</span>
            </div>
            {activeFailingControls.length > 0 && (
              <span className="text-xs font-bold text-amber-700 bg-amber-50 border border-amber-100 px-2 py-0.5 rounded-full">
                {activeFailingControls.length}
              </span>
            )}
          </div>
          {activeFailingControls.length === 0 ? (
            <div className="flex flex-col gap-3 py-2">
              <div className="flex items-center gap-2.5 p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <p className="text-xs font-semibold text-emerald-700">All controls passing</p>
              </div>
              <p className="text-[11px] text-gray-400 text-center leading-relaxed px-2">
                No issues detected. Keep collecting evidence daily to maintain your score.
              </p>
            </div>
          ) : (
            <div className="space-y-1.5">
              {activeFailingControls.slice(0, 5).map((c) => (
                <Link key={c.category} href="/compliance" className="flex items-start gap-2.5 group p-2.5 rounded-xl hover:bg-gray-50 transition-colors -mx-0.5">
                  <div className={`w-2 h-2 rounded-full mt-1.5 shrink-0 ${c.status === "failing" ? "bg-red-400" : "bg-amber-400"}`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold text-gray-800 group-hover:text-brand-600 transition-colors truncate">{c.name}</p>
                    {c.missing_types.length > 0 && (
                      <p className="text-[10px] text-gray-400 mt-0.5 truncate">
                        Missing: {c.missing_types.slice(0, 2).join(", ")}{c.missing_types.length > 2 ? ` +${c.missing_types.length - 2}` : ""}
                      </p>
                    )}
                  </div>
                  <ChevronRight className="w-3 h-3 text-gray-300 group-hover:text-brand-400 shrink-0 mt-1 transition-colors" />
                </Link>
              ))}
              {activeFailingControls.length > 5 && (
                <Link href="/compliance" className="block text-xs text-center text-brand-600 font-semibold hover:text-brand-700 pt-1">
                  +{activeFailingControls.length - 5} more →
                </Link>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Bottom row: Integrations (2/3) + Platform (1/3) ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">

        {/* Integrations — 2/3 with 2-col compact grid */}
        <div className="md:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-brand-50 flex items-center justify-center">
                <Plug className="w-3.5 h-3.5 text-brand-600" />
              </div>
              <span className="text-sm font-semibold text-gray-800">Integrations</span>
              {activeIntegrationsList.length > 0 && (
                <span className="text-[10px] font-bold text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md">{activeIntegrationsList.length}</span>
              )}
            </div>
            {!tmData && (
              <Link href="/integrations" className="flex items-center gap-0.5 text-xs text-brand-600 font-semibold hover:text-brand-700 transition-colors">
                Manage <ArrowRight className="w-3 h-3" />
              </Link>
            )}
          </div>
          {activeIntegrationsList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3 text-center">
              <div className="w-12 h-12 rounded-2xl bg-gray-50 flex items-center justify-center">
                <Plug className="w-5 h-5 text-gray-200" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-600">{tmData ? "No integrations on this date" : "No integrations yet"}</p>
                {!tmData && <p className="text-xs text-gray-400 mt-0.5">Connect your first tool to start collecting evidence — or <Link href="/integrations" className="text-brand-600 hover:underline">simulate a tool first</Link> to preview score impact.</p>}
              </div>
              {!tmData && (
                <Link href="/integrations" className="text-xs font-semibold bg-brand-600 hover:bg-brand-700 text-white px-4 py-1.5 rounded-xl transition-colors">
                  Connect a tool
                </Link>
              )}
            </div>
          ) : (() => {
            const LIMIT = 10;
            const visible = integrationsExpanded ? activeIntegrationsList : activeIntegrationsList.slice(0, LIMIT);
            const hidden = activeIntegrationsList.length - LIMIT;
            return (
              <>
                <div className="grid grid-cols-2 gap-1.5">
                  {visible.map((i) => {
                    const staleHours = i.last_collected_at
                      ? (Date.now() - new Date(i.last_collected_at).getTime()) / 36e5
                      : Infinity;
                    return (
                      <div key={i.id} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50/80 hover:bg-gray-100/60 transition-colors">
                        <div className={`w-2 h-2 rounded-full shrink-0 ${i.status === "active" ? "bg-emerald-500" : i.status === "error" ? "bg-red-500" : "bg-gray-300"}`} />
                        <p className="text-xs font-medium text-gray-700 truncate flex-1 capitalize">{i.integration_type.replace(/_/g, " ")}</p>
                        {staleHours > 48 && <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />}
                        {i.last_collected_at && (
                          <span className="text-[10px] text-gray-400 shrink-0 tabular-nums">
                            {new Date(i.last_collected_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
                {hidden > 0 && (
                  <button
                    onClick={() => setIntegrationsExpanded((v) => !v)}
                    className="w-full mt-3 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors py-2 border border-dashed border-brand-200 rounded-xl hover:bg-brand-50"
                  >
                    {integrationsExpanded ? "Show less ↑" : `+${hidden} more integrations`}
                  </button>
                )}
              </>
            );
          })()}
        </div>

        {/* Platform quick links — 1/3 */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-[0_2px_8px_rgba(15,23,42,0.06)] p-5">
          <p className="text-sm font-semibold text-gray-800 mb-4">Platform</p>
          <div className="grid grid-cols-3 gap-1.5">
            {QUICK_LINKS.map(({ href, label, icon: Icon, bg, fg }) => (
              <Link key={href} href={href}
                className="flex flex-col items-center gap-1.5 p-2.5 rounded-xl hover:bg-gray-50 transition-colors group text-center">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${bg} group-hover:scale-105 transition-transform`}>
                  <Icon className={`w-4 h-4 ${fg}`} />
                </div>
                <span className="text-[10px] font-semibold text-gray-500 group-hover:text-gray-700 leading-tight">{label}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
