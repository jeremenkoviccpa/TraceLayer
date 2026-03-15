"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReadinessData } from "@/lib/types";
import { Target, CheckCircle2, AlertTriangle, Clock, ArrowRight, TrendingUp } from "lucide-react";
import Link from "next/link";

const STAGE_LABELS: Record<string, { label: string; color: string; desc: string }> = {
  ready: { label: "Audit Ready", color: "text-emerald-600", desc: "You're ready to start your SOC 2 Type I audit!" },
  final_push: { label: "Final Push", color: "text-teal-600", desc: "Almost there — close out remaining controls." },
  in_progress: { label: "In Progress", color: "text-amber-600", desc: "Good progress — keep building your evidence." },
  early: { label: "Early Stage", color: "text-orange-600", desc: "Solid start — focus on high-impact controls first." },
  just_started: { label: "Just Started", color: "text-red-500", desc: "Set up integrations to start collecting evidence automatically." },
};

const FRAMEWORKS = [
  { id: "soc2", label: "SOC 2" },
  { id: "iso27001", label: "ISO 27001" },
  { id: "hipaa", label: "HIPAA" },
];

function ReadinessRing({ score }: { score: number }) {
  const r = 56;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 55 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-36 h-36">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 128 128">
        <circle cx="64" cy="64" r={r} fill="none" stroke="#f1f5f9" strokeWidth="10" />
        <circle cx="64" cy="64" r={r} fill="none" stroke={color} strokeWidth="10"
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.4s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black" style={{ color }}>{score}</span>
        <span className="text-[11px] font-semibold text-gray-400">/ 100</span>
      </div>
    </div>
  );
}

const ACTION_ITEMS: { stage: string; items: { href: string; label: string; desc: string }[] }[] = [
  { stage: "just_started", items: [
    { href: "/integrations", label: "Connect integrations", desc: "Link AWS, GitHub, Okta to auto-collect evidence" },
    { href: "/compliance", label: "Review controls", desc: "See which controls need attention" },
    { href: "/policies", label: "Set up policies", desc: "Adopt pre-written security policies" },
  ]},
  { stage: "early", items: [
    { href: "/compliance", label: "Complete manual controls", desc: "Mark policy, training, BCP as compliant" },
    { href: "/risks", label: "Log your risks", desc: "Document and mitigate open risks" },
    { href: "/training", label: "Assign security training", desc: "Ensure all staff complete awareness training" },
  ]},
  { stage: "in_progress", items: [
    { href: "/pen-tests", label: "Schedule a pen test", desc: "Annual pen test is required for SOC 2" },
    { href: "/vendors", label: "Review vendors", desc: "Assess third-party vendors for CC9.2" },
    { href: "/access-reviews", label: "Run access reviews", desc: "Quarterly reviews satisfy CC6.3" },
  ]},
  { stage: "final_push", items: [
    { href: "/audit-log", label: "Check audit log", desc: "Ensure all actions are being logged" },
    { href: "/compliance", label: "Close failing controls", desc: "Push remaining controls to passing" },
    { href: "/reports", label: "Generate audit report", desc: "Share your compliance posture with auditors" },
  ]},
  { stage: "ready", items: [
    { href: "/reports", label: "Generate full report", desc: "Create an audit-ready compliance report" },
    { href: "/settings", label: "Create auditor access link", desc: "Give your auditor read-only access" },
    { href: "/trust", label: "Publish trust page", desc: "Share your compliance posture publicly" },
  ]},
];

export default function ReadinessPage() {
  const [framework, setFramework] = useState("soc2");
  const [data, setData] = useState<ReadinessData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setData(null);
    api.getReadiness(framework).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [framework]);

  const stageInfo = data ? (STAGE_LABELS[data.stage] ?? STAGE_LABELS.just_started) : null;
  const actionItems = data ? (ACTION_ITEMS.find((a) => a.stage === data.stage)?.items ?? ACTION_ITEMS[0].items) : [];

  return (
    <div className="animate-fade-in">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Readiness Timeline</h1>
          <p className="text-sm text-gray-500 mt-0.5">See how ready you are for certification and what to do next.</p>
        </div>
        <div className="flex gap-1 bg-gray-100 rounded-xl p-1">
          {FRAMEWORKS.map((fw) => (
            <button
              key={fw.id}
              onClick={() => setFramework(fw.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${framework === fw.id ? "bg-white shadow-sm text-gray-900" : "text-gray-500 hover:text-gray-700"}`}
            >
              {fw.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
        </div>
      ) : data ? (
        <>
          {/* Hero card */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-6 mb-6">
            <div className="flex flex-col sm:flex-row items-center gap-6">
              <ReadinessRing score={data.readiness_score} />
              <div className="flex-1 text-center sm:text-left">
                <p className={`text-lg font-bold mb-1 ${stageInfo?.color}`}>{stageInfo?.label}</p>
                <p className="text-sm text-gray-600 mb-3">{stageInfo?.desc}</p>
                {data.weeks_estimate > 0 ? (
                  <div className="inline-flex items-center gap-2 bg-amber-50 border border-amber-100 rounded-xl px-4 py-2">
                    <Clock className="w-4 h-4 text-amber-500 shrink-0" />
                    <span className="text-sm font-semibold text-amber-800">
                      ~{data.weeks_estimate} weeks to {FRAMEWORKS.find((f) => f.id === framework)?.label} Type I at current pace
                    </span>
                  </div>
                ) : (
                  <div className="inline-flex items-center gap-2 bg-emerald-50 border border-emerald-100 rounded-xl px-4 py-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span className="text-sm font-semibold text-emerald-800">Ready for Type I audit</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Breakdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
            {/* Automated controls */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp className="w-4 h-4 text-brand-500" />
                <p className="text-sm font-semibold text-gray-800">Automated Controls</p>
                <span className="ml-auto text-lg font-bold text-gray-900">{data.automated_score}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${data.automated_score >= 80 ? "bg-emerald-500" : data.automated_score >= 50 ? "bg-amber-400" : "bg-red-400"}`}
                  style={{ width: `${data.automated_score}%` }}
                />
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center">
                  <p className="text-lg font-bold text-emerald-600">{data.controls_passing}</p>
                  <p className="text-[10px] text-gray-400">Passing</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-red-500">{data.controls_failing}</p>
                  <p className="text-[10px] text-gray-400">Failing</p>
                </div>
                <div className="text-center">
                  <p className="text-lg font-bold text-gray-400">{data.controls_no_evidence}</p>
                  <p className="text-[10px] text-gray-400">No evidence</p>
                </div>
              </div>
            </div>

            {/* Manual controls */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-4 h-4 text-brand-500" />
                <p className="text-sm font-semibold text-gray-800">Manual Controls</p>
                <span className="ml-auto text-lg font-bold text-gray-900">{data.manual_score}%</span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-3">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${data.manual_score >= 80 ? "bg-emerald-500" : data.manual_score >= 50 ? "bg-amber-400" : "bg-red-400"}`}
                  style={{ width: `${data.manual_score}%` }}
                />
              </div>
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-500">{data.manual_compliant} of {data.manual_total} controls marked compliant</p>
                <Link href="/compliance" className="text-xs text-brand-600 hover:text-brand-700 font-semibold flex items-center gap-1">
                  Review <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            </div>
          </div>

          {/* Next actions */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-card p-5">
            <p className="text-sm font-semibold text-gray-800 mb-4">Recommended next steps</p>
            <div className="space-y-2">
              {actionItems.map(({ href, label, desc }) => (
                <Link
                  key={href}
                  href={href}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl hover:bg-gray-50 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center shrink-0">
                    <Target className="w-4 h-4 text-brand-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900">{label}</p>
                    <p className="text-xs text-gray-400">{desc}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 shrink-0 transition-colors" />
                </Link>
              ))}
            </div>
          </div>
        </>
      ) : (
        <div className="bg-white rounded-2xl border border-dashed border-gray-200 p-12 text-center">
          <AlertTriangle className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-sm text-gray-500">Could not load readiness data.</p>
        </div>
      )}
    </div>
  );
}
