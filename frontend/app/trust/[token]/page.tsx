"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import type { PublicTrustPageView } from "@/lib/types";
import {
  ShieldCheck, CheckCircle2, AlertTriangle, Clock, ArrowRight,
  ExternalLink, Globe, Plug, BookOpen,
} from "lucide-react";

const FW_COLORS: Record<string, string> = {
  soc2:     "from-teal-500 to-emerald-500",
  iso27001: "from-blue-500 to-cyan-500",
  hipaa:    "from-violet-500 to-purple-500",
  gdpr:     "from-indigo-500 to-blue-500",
  pci_dss:  "from-amber-500 to-orange-500",
  ccpa:     "from-rose-500 to-pink-500",
  nist_csf: "from-cyan-500 to-teal-500",
};

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const r = size * 0.42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth={size*0.09}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.09}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.2s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-black leading-none" style={{ color, fontSize: size * 0.22 }}>{score}%</span>
      </div>
    </div>
  );
}

function ScoreRingLight({ score, size = 80 }: { score: number; size?: number }) {
  const r = size * 0.42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#f1f5f9" strokeWidth={size*0.09}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.09}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.2s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-black leading-none" style={{ color, fontSize: size * 0.22 }}>{score}%</span>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    passing:     "bg-emerald-50 text-emerald-700 border-emerald-100",
    warning:     "bg-amber-50 text-amber-700 border-amber-100",
    failing:     "bg-red-50 text-red-600 border-red-100",
    no_evidence: "bg-gray-100 text-gray-500 border-gray-200",
  };
  const labels: Record<string, string> = {
    passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
  };
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${styles[status] ?? "bg-gray-100 text-gray-500 border-gray-200"}`}>
      {labels[status] ?? status}
    </span>
  );
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-400";
  return "bg-red-400";
}

export default function TrustCenterPage() {
  const { token: slug } = useParams<{ token: string }>();
  const [data, setData]       = useState<PublicTrustPageView | null>(null);
  const [error, setError]     = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    api.getPublicTrustPage(slug)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, [slug]);

  return (
    <div className="min-h-screen bg-[#f7f1e8] font-[family:'Sora',_ui-sans-serif,_system-ui]">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
            <span className="text-gray-300 mx-1">·</span>
            <span className="text-xs text-gray-500 font-medium">Trust Center</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            Live · Updated continuously
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10 space-y-5">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="max-w-md mx-auto mt-20 text-center">
            <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-7 h-7 text-red-500" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Page unavailable</h1>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <Link href="/register" className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-colors">
              Create your own trust page <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Hero card — dark */}
            <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 overflow-hidden relative">
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-0 left-1/3 w-72 h-72 bg-teal-500/10 rounded-full blur-3xl -translate-y-1/2" />
                <div className="absolute bottom-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl translate-y-1/2" />
              </div>
              <div className="relative">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 mb-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-11 h-11 bg-teal-500/20 border border-teal-500/30 rounded-xl flex items-center justify-center shrink-0">
                        <ShieldCheck className="w-5 h-5 text-teal-400" />
                      </div>
                      <div>
                        <h1 className="text-2xl font-extrabold text-white leading-tight">{data.company_name}</h1>
                        {data.custom_headline && (
                          <p className="text-sm text-slate-400 mt-0.5">{data.custom_headline}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 flex-wrap mt-3">
                      <span className="bg-emerald-500/15 border border-emerald-500/25 text-emerald-300 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                        <CheckCircle2 className="w-3 h-3" /> Verified by TraceLayer
                      </span>
                      <span className="text-slate-500 text-xs flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Updated {new Date(data.generated_at).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {data.show_score && data.frameworks.length > 0 && (
                    <div className="flex gap-5 shrink-0 flex-wrap">
                      {data.frameworks.map((fw) => (
                        <div key={fw.framework} className="text-center">
                          <ScoreRing score={fw.overall_score} size={76} />
                          <p className="text-xs font-semibold text-slate-400 mt-1.5">{fw.label}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {data.custom_message && (
                  <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 mt-2">
                    <p className="text-sm text-slate-300 leading-relaxed">{data.custom_message}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Framework score cards */}
            {data.show_score && data.frameworks.length > 0 && (
              <div className={`grid gap-4 ${
                data.frameworks.length === 1 ? "grid-cols-1 max-w-md" :
                data.frameworks.length === 2 ? "grid-cols-1 sm:grid-cols-2" :
                "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
              }`}>
                {data.frameworks.map((fw) => (
                  <div key={fw.framework} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2.5">
                        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${FW_COLORS[fw.framework] ?? "from-gray-400 to-gray-500"} flex items-center justify-center shadow-sm shrink-0`}>
                          <ShieldCheck className="w-4 h-4 text-white" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-gray-900">{fw.label}</p>
                          <p className="text-xs text-gray-400">{fw.overall_score}% overall</p>
                        </div>
                      </div>
                      <ScoreRingLight score={fw.overall_score} size={48} />
                    </div>
                    <div className="space-y-2.5">
                      {fw.controls.map((c) => (
                        <div key={c.name}>
                          <div className="flex items-center justify-between text-xs mb-1">
                            <span className="text-gray-600 font-medium truncate flex-1 mr-2">{c.name}</span>
                            <div className="flex items-center gap-1.5 shrink-0">
                              <StatusBadge status={c.status} />
                              <span className="font-bold text-gray-700 w-9 text-right">{c.score}%</span>
                            </div>
                          </div>
                          <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full transition-all duration-700 ${scoreBarColor(c.score)}`}
                              style={{ width: `${c.score}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Adopted policies */}
            {data.show_policies && data.policies && data.policies.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-violet-50 flex items-center justify-center shrink-0">
                    <BookOpen className="w-4 h-4 text-violet-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-900">Security Policies</p>
                    <p className="text-xs text-gray-400">{data.policies.length} policies adopted</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {data.policies.map((p, i) => (
                    <div key={i} className="flex items-center gap-2.5 bg-gray-50 rounded-xl px-3 py-2.5">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                      <p className="text-xs font-semibold text-gray-800 truncate">
                        {p.slug.replace(/_/g, " ").replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connected integrations */}
            {data.show_integrations && data.integrations && data.integrations.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-8 h-8 rounded-lg bg-cyan-50 flex items-center justify-center shrink-0">
                    <Plug className="w-4 h-4 text-cyan-600" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-gray-900">Connected Integrations</p>
                    <p className="text-xs text-gray-400">
                      Evidence collected from {data.integrations.length} integration{data.integrations.length !== 1 ? "s" : ""}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {data.integrations.map((name) => (
                    <span key={name} className="inline-flex items-center gap-1.5 bg-gray-50 border border-gray-100 text-xs font-semibold text-gray-700 px-3 py-1.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* About */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-gray-400" />
                <p className="text-xs font-semibold text-gray-700">About this trust center</p>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">
                {data.company_name}&apos;s compliance data is automatically collected and verified by TraceLayer from
                their connected cloud infrastructure and SaaS tools. Evidence is gathered continuously —
                scores reflect real, live data, not self-reported claims.
              </p>
            </div>

            {/* CTA */}
            <div className="bg-slate-900 rounded-2xl p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
              <div>
                <p className="text-white font-bold mb-0.5">Build your own Trust Center</p>
                <p className="text-white/55 text-xs">Show customers your live compliance posture. Free to start.</p>
              </div>
              <Link href="/register" className="shrink-0 inline-flex items-center gap-2 bg-teal-500 hover:bg-teal-400 text-white font-bold px-5 py-2.5 rounded-xl text-sm transition-colors">
                Get started free <ExternalLink className="w-3.5 h-3.5" />
              </Link>
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-black/5 py-6 mt-4">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Image src="/logo-icon.png" alt="TraceLayer" width={20} height={20} className="rounded-md" />
            <span className="text-xs font-semibold text-gray-500">Powered by TraceLayer</span>
          </div>
          {data && (
            <div className="flex items-center gap-3 flex-wrap">
              {data.frameworks.map((fw) => (
                <span key={fw.framework} className="flex items-center gap-1 text-xs text-gray-400">
                  <CheckCircle2 className="w-3 h-3 text-teal-500" /> {fw.label}
                </span>
              ))}
            </div>
          )}
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
      `}</style>
    </div>
  );
}
