"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReadinessData, ComplianceScore } from "@/lib/types";
import { Target, CheckCircle2, AlertTriangle, Clock, ArrowRight, TrendingUp, Zap, Lock, XCircle, MinusCircle } from "lucide-react";
import Link from "next/link";
import { usePlan } from "@/hooks/usePlan";
import { useUpgrade } from "@/components/plan-gate";

const STAGE_META: Record<string, { label: string; color: string; bar: string; desc: string }> = {
  ready:       { label: "Audit Ready",  color: "text-emerald-400", bar: "bg-emerald-500", desc: "You're ready to start your audit!" },
  final_push:  { label: "Final Push",   color: "text-teal-400",    bar: "bg-teal-500",    desc: "Almost there — close out remaining controls." },
  in_progress: { label: "In Progress",  color: "text-amber-400",   bar: "bg-amber-500",   desc: "Good progress — keep building your evidence." },
  early:       { label: "Early Stage",  color: "text-orange-400",  bar: "bg-orange-500",  desc: "Solid start — focus on high-impact controls first." },
  just_started:{ label: "Just Started", color: "text-red-400",     bar: "bg-red-500",     desc: "Connect integrations to start collecting evidence." },
};

const FRAMEWORKS = [
  { id: "soc2",     label: "SOC 2"     },
  { id: "iso27001", label: "ISO 27001" },
  { id: "hipaa",    label: "HIPAA"     },
  { id: "gdpr",     label: "GDPR"      },
  { id: "pci_dss",  label: "PCI DSS"   },
  { id: "ccpa",     label: "CCPA"      },
  { id: "nist_csf", label: "NIST CSF"  },
  { id: "dpdp",     label: "DPDP Act"  },
  { id: "cert_in",  label: "CERT-In"   },
  { id: "lpdp",     label: "Serbian LPDP" },
  { id: "nis2",     label: "NIS2 Directive" },
  { id: "iso42001", label: "ISO 42001" },
];

const ACTION_ITEMS: { stage: string; items: { href: string; label: string; desc: string; icon: React.ElementType }[] }[] = [
  { stage: "just_started", items: [
    { href: "/integrations", label: "Connect integrations",  desc: "Link AWS, GitHub, Okta to auto-collect evidence", icon: Zap },
    { href: "/compliance",   label: "Review controls",       desc: "See which controls need attention",               icon: Target },
    { href: "/policies",     label: "Set up policies",       desc: "Adopt pre-written security policies",             icon: CheckCircle2 },
  ]},
  { stage: "early", items: [
    { href: "/compliance",   label: "Complete manual controls", desc: "Mark policy, training, BCP as compliant",   icon: CheckCircle2 },
    { href: "/risks",        label: "Log your risks",           desc: "Document and mitigate open risks",          icon: AlertTriangle },
    { href: "/training",     label: "Assign security training", desc: "Ensure all staff complete awareness training", icon: TrendingUp },
  ]},
  { stage: "in_progress", items: [
    { href: "/pen-tests",      label: "Schedule a pen test",  desc: "Annual penetration test demonstrates security posture to auditors", icon: Target },
    { href: "/vendors",        label: "Review vendors",       desc: "Assess third-party vendors and document risk levels",               icon: CheckCircle2 },
    { href: "/access-reviews", label: "Run access reviews",   desc: "Periodic access reviews satisfy access control requirements",       icon: TrendingUp },
  ]},
  { stage: "final_push", items: [
    { href: "/audit-log",  label: "Check audit log",        desc: "Ensure all actions are being logged",            icon: Clock },
    { href: "/compliance", label: "Close failing controls", desc: "Push remaining controls to passing",             icon: Target },
    { href: "/reports",    label: "Generate audit report",  desc: "Share your compliance posture with auditors",    icon: TrendingUp },
  ]},
  { stage: "ready", items: [
    { href: "/reports",   label: "Generate full report",       desc: "Create an audit-ready compliance report",     icon: TrendingUp },
    { href: "/settings",  label: "Create auditor access link", desc: "Give your auditor read-only access",          icon: CheckCircle2 },
  ]},
];

function ScoreRing({ score, size = 120 }: { score: number; size?: number }) {
  const r = size * 0.42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 55 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={size*0.078}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.078}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.4s ease-in-out" }}/>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-black text-white leading-none" style={{ fontSize: size * 0.28 }}>{score}</span>
        <span className="text-slate-400 font-semibold" style={{ fontSize: size * 0.1 }}>/ 100</span>
      </div>
    </div>
  );
}

export default function ReadinessPage() {
  const { isPro } = usePlan();
  const { trigger: triggerUpgrade } = useUpgrade();
  const [framework, setFramework] = useState("soc2");
  const [data, setData] = useState<ReadinessData | null>(null);
  const [score, setScore] = useState<ComplianceScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [socType, setSocType] = useState<"type1" | "type2">("type1");
  const [periodStart, setPeriodStart] = useState(() => {
    const d = new Date(); d.setMonth(d.getMonth() - 6); return d.toISOString().split("T")[0];
  });
  const [periodEnd, setPeriodEnd] = useState(() => new Date().toISOString().split("T")[0]);

  useEffect(() => {
    setLoading(true);
    setData(null);
    setScore(null);
    Promise.all([
      api.getReadiness(framework),
      api.getComplianceScore(framework),
    ]).then(([r, s]) => { setData(r); setScore(s); }).catch(() => {}).finally(() => setLoading(false));
  }, [framework]);

  const stage = data?.stage ?? "just_started";
  const meta = STAGE_META[stage] ?? STAGE_META.just_started;
  const actionItems = ACTION_ITEMS.find((a) => a.stage === stage)?.items ?? ACTION_ITEMS[0].items;
  const fwLabel = FRAMEWORKS.find((f) => f.id === framework)?.label ?? "SOC 2";

  return (
    <div className="animate-fade-in overflow-x-hidden">
      {/* Dark hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 mb-6 overflow-hidden relative">
        {/* bg glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 w-64 h-64 bg-teal-500/10 rounded-full blur-3xl -translate-y-1/2"/>
        </div>

        <div className="relative">
          {/* Header row */}
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-teal-500/20 flex items-center justify-center shrink-0">
              <Target className="w-5 h-5 text-teal-400"/>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Readiness Timeline</h1>
              <p className="text-sm text-slate-400">See how ready you are for certification.</p>
            </div>
          </div>

          {/* Framework selector — single scrollable row */}
          <div
            className="flex gap-1.5 overflow-x-auto mb-6 pb-0.5"
            style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
          >
            {FRAMEWORKS.map((fw) => {
              const locked = !isPro && fw.id !== "soc2";
              const active = framework === fw.id;
              return (
                <button
                  key={fw.id}
                  onClick={() => locked ? triggerUpgrade() : setFramework(fw.id)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap shrink-0 transition-all ${
                    active
                      ? "bg-teal-500 text-white shadow-md shadow-teal-500/30"
                      : locked
                      ? "bg-amber-500/15 text-amber-300 border border-amber-500/20 hover:bg-amber-500/25"
                      : "bg-white/8 text-slate-400 border border-white/10 hover:bg-white/15 hover:text-white"
                  }`}
                >
                  {locked && <Lock className="w-2.5 h-2.5 shrink-0" />}
                  {fw.label}
                </button>
              );
            })}
          </div>

          {/* SOC 2 Type selector */}
          {framework === "soc2" && (
            <div className="mb-5">
              <div className="flex gap-2 flex-wrap">
                {(["type1", "type2"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setSocType(t)}
                    className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${
                      socType === t
                        ? "bg-teal-500 text-white border-teal-500 shadow-sm"
                        : "bg-white/10 text-slate-300 border-white/20 hover:bg-white/20"
                    }`}
                  >
                    {t === "type1" ? "Type I — Point in time" : "Type II — 6-month period"}
                  </button>
                ))}
              </div>

              {socType === "type2" && (
                <div className="mt-3 space-y-3">
                  <div className="flex flex-wrap gap-3">
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Period start</label>
                      <input
                        type="date"
                        value={periodStart}
                        onChange={(e) => setPeriodStart(e.target.value)}
                        className="bg-white/10 border border-white/20 text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-400/50"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-400 block mb-1">Period end</label>
                      <input
                        type="date"
                        value={periodEnd}
                        onChange={(e) => setPeriodEnd(e.target.value)}
                        className="bg-white/10 border border-white/20 text-white text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-teal-400/50"
                      />
                    </div>
                  </div>
                  <div className="flex items-start gap-2 bg-teal-500/10 border border-teal-500/25 rounded-xl px-3 py-2.5">
                    <Clock className="w-3.5 h-3.5 text-teal-400 mt-0.5 shrink-0" />
                    <p className="text-xs text-teal-300 leading-relaxed">
                      Type II requires evidence collected continuously over the audit period. Your current evidence spans{" "}
                      <span className="font-bold">
                        {Math.max(0, Math.floor((new Date(periodEnd).getTime() - new Date(periodStart).getTime()) / 86400000))}
                      </span>{" "}
                      days.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Main hero content */}
          {loading ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-teal-400 border-t-transparent rounded-full animate-spin"/>
            </div>
          ) : data ? (
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6">
              <ScoreRing score={data.readiness_score} size={120}/>
              <div className="flex-1 text-center sm:text-left">
                <div className="flex items-center gap-3 mb-2 justify-center sm:justify-start flex-wrap">
                  <span className={`text-2xl font-black ${meta.color}`}>{meta.label}</span>
                  {data.weeks_estimate > 0
                    ? <span className="inline-flex items-center gap-1.5 bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold px-2.5 py-1 rounded-full">
                        <Clock className="w-3 h-3"/> ~{data.weeks_estimate}wk to {fwLabel}
                      </span>
                    : <span className="inline-flex items-center gap-1.5 bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-xs font-semibold px-2.5 py-1 rounded-full">
                        <CheckCircle2 className="w-3 h-3"/> Audit ready
                      </span>
                  }
                </div>
                <p className="text-slate-400 text-sm mb-5">{meta.desc}</p>

                {/* Stats grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { label: "Readiness", value: `${data.readiness_score}%`, color: "text-teal-400" },
                    { label: "Automated", value: `${data.automated_score}%`, color: "text-cyan-400" },
                    { label: "Manual",    value: `${data.manual_score}%`,    color: "text-blue-400" },
                    { label: "Passing",   value: data.controls_passing,      color: "text-emerald-400" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 text-center sm:text-left">
                      <p className={`text-xl font-black ${color}`}>{value}</p>
                      <p className="text-xs text-slate-500">{label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <AlertTriangle className="w-8 h-8 text-slate-500 mx-auto mb-2"/>
              <p className="text-sm text-slate-400">Could not load readiness data.</p>
            </div>
          )}
        </div>
      </div>

      {data && !loading && (
        <>
          {/* Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            {/* Automated */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-cyan-50 flex items-center justify-center">
                    <TrendingUp className="w-3.5 h-3.5 text-cyan-600"/>
                  </div>
                  <p className="text-sm font-semibold text-gray-900">Automated Controls</p>
                </div>
                <span className="text-2xl font-black text-cyan-600">{data.automated_score}%</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mt-3 mb-4">
                <div className={`h-full rounded-full transition-all duration-700 ${data.automated_score >= 80 ? "bg-emerald-500" : data.automated_score >= 50 ? "bg-amber-400" : "bg-red-400"}`}
                  style={{ width: `${data.automated_score}%` }}/>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="bg-emerald-50 rounded-xl py-2">
                  <p className="text-lg font-black text-emerald-600">{data.controls_passing}</p>
                  <p className="text-[10px] text-emerald-600/70 font-medium">Passing</p>
                </div>
                <div className="bg-red-50 rounded-xl py-2">
                  <p className="text-lg font-black text-red-500">{data.controls_failing}</p>
                  <p className="text-[10px] text-red-500/70 font-medium">Failing</p>
                </div>
                <div className="bg-gray-50 rounded-xl py-2">
                  <p className="text-lg font-black text-gray-400">{data.controls_no_evidence}</p>
                  <p className="text-[10px] text-gray-400/70 font-medium">No data</p>
                </div>
              </div>
            </div>

            {/* Manual */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-lg bg-teal-50 flex items-center justify-center">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-600"/>
                  </div>
                  <p className="text-sm font-semibold text-gray-900">Manual Controls</p>
                </div>
                <span className="text-2xl font-black text-teal-600">{data.manual_score}%</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden mt-3 mb-4">
                <div className={`h-full rounded-full transition-all duration-700 ${data.manual_score >= 80 ? "bg-emerald-500" : data.manual_score >= 50 ? "bg-amber-400" : "bg-red-400"}`}
                  style={{ width: `${data.manual_score}%` }}/>
              </div>
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-3xl font-black text-gray-900">{data.manual_compliant}<span className="text-base font-semibold text-gray-400">/{data.manual_total}</span></p>
                  <p className="text-xs text-gray-500 mt-0.5">controls marked compliant</p>
                </div>
                <Link href="/compliance" className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 px-3 py-2 rounded-xl transition-colors">
                  Review <ArrowRight className="w-3 h-3"/>
                </Link>
              </div>
            </div>
          </div>

          {/* Next actions */}
          <div className="bg-white rounded-2xl border border-gray-100 p-5">
            <p className="text-sm font-bold text-gray-900 mb-4">Recommended next steps</p>
            <div className="space-y-2">
              {actionItems.map(({ href, label, desc, icon: Icon }) => (
                <Link key={href} href={href}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-slate-50 transition-colors group border border-transparent hover:border-slate-100">
                  <div className="w-9 h-9 rounded-xl bg-teal-50 flex items-center justify-center shrink-0 group-hover:bg-teal-100 transition-colors">
                    <Icon className="w-4 h-4 text-teal-600"/>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900">{label}</p>
                    <p className="text-xs text-gray-400">{desc}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-teal-500 shrink-0 transition-colors"/>
                </Link>
              ))}
            </div>
          </div>

          {/* Gap Analysis */}
          {score && score.controls.some((c) => c.status !== "passing") && (
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-1">
                <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0"/>
                <p className="text-sm font-bold text-gray-900">Gap Analysis</p>
                <span className="text-xs text-gray-400 ml-1">
                  {score.controls.filter((c) => c.status !== "passing").length} controls need attention
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-4">
                Controls that are failing or missing evidence — fix these to improve your score.
              </p>
              <div className="space-y-2">
                {score.controls
                  .filter((c) => c.status !== "passing")
                  .sort((a, b) => {
                    const order = { failing: 0, warning: 1, no_evidence: 2 };
                    return (order[a.status as keyof typeof order] ?? 3) - (order[b.status as keyof typeof order] ?? 3);
                  })
                  .map((c) => (
                    <div key={c.category} className={`rounded-xl border px-4 py-3 ${
                      c.status === "failing"     ? "border-red-100 bg-red-50/50" :
                      c.status === "warning"     ? "border-amber-100 bg-amber-50/50" :
                      "border-gray-100 bg-gray-50/50"
                    }`}>
                      <div className="flex items-start gap-2.5">
                        <div className="mt-0.5 shrink-0">
                          {c.status === "failing"     && <XCircle className="w-4 h-4 text-red-500"/>}
                          {c.status === "warning"     && <AlertTriangle className="w-4 h-4 text-amber-500"/>}
                          {c.status === "no_evidence" && <MinusCircle className="w-4 h-4 text-gray-400"/>}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <p className="text-sm font-semibold text-gray-800">{c.name}</p>
                            <span className={`text-xs font-bold shrink-0 ${
                              c.status === "failing"     ? "text-red-500" :
                              c.status === "warning"     ? "text-amber-600" :
                              "text-gray-400"
                            }`}>{c.score}%</span>
                          </div>
                          {c.missing_types.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              <span className="text-[11px] text-gray-400 mr-0.5">Missing:</span>
                              {c.missing_types.map((t) => (
                                <span key={t} className="inline-flex items-center gap-1 bg-red-100 text-red-600 text-[11px] font-medium px-2 py-0.5 rounded-full">
                                  <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0"/>
                                  {t}
                                </span>
                              ))}
                            </div>
                          )}
                          {c.status === "no_evidence" && c.missing_types.length === 0 && (
                            <p className="text-[11px] text-gray-400 mt-1">No evidence collected yet — connect an integration.</p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
              <Link href="/compliance" className="flex items-center justify-center gap-1.5 mt-4 text-xs font-semibold text-teal-600 hover:text-teal-700 bg-teal-50 hover:bg-teal-100 py-2.5 rounded-xl transition-colors">
                Fix in compliance dashboard <ArrowRight className="w-3.5 h-3.5"/>
              </Link>
            </div>
          )}
        </>
      )}
    </div>
  );
}
