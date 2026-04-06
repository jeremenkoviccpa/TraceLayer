"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import type { PublicTrustPageView } from "@/lib/types";
import {
  ShieldCheck, CheckCircle2, AlertTriangle, Clock, ArrowRight,
  ExternalLink, Globe, Plug, BookOpen, FileText, Zap,
} from "lucide-react";

const FW_COLORS: Record<string, string> = {
  soc2:     "from-teal-500 to-emerald-500",
  iso27001: "from-blue-500 to-cyan-500",
  hipaa:    "from-violet-500 to-purple-500",
  gdpr:     "from-indigo-500 to-blue-500",
  pci_dss:  "from-amber-500 to-orange-500",
  ccpa:     "from-rose-500 to-pink-500",
  nist_csf: "from-cyan-500 to-teal-500",
  dpdp:     "from-orange-500 to-amber-500",
  certin:   "from-red-500 to-rose-500",
  lpdp:     "from-blue-500 to-indigo-500",
  nis2:     "from-indigo-500 to-violet-500",
};

function ScoreRing({ score, size = 80 }: { score: number; size?: number }) {
  const r = size * 0.42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={size*0.09}/>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={color} strokeWidth={size*0.09}
          strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1.2s ease-in-out", filter: `drop-shadow(0 0 6px ${color}60)` }}
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
    passing:     "bg-emerald-500/15 text-emerald-300 border-emerald-500/20",
    warning:     "bg-amber-500/15 text-amber-300 border-amber-500/20",
    failing:     "bg-red-500/15 text-red-300 border-red-500/20",
    no_evidence: "bg-white/5 text-white/30 border-white/10",
  };
  const labels: Record<string, string> = {
    passing: "Passing", warning: "Warning", failing: "Failing", no_evidence: "No data",
  };
  return (
    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${styles[status] ?? "bg-white/5 text-white/30 border-white/10"}`}>
      {labels[status] ?? status}
    </span>
  );
}

function scoreBarGradient(score: number) {
  if (score >= 80) return "from-emerald-500 to-teal-400";
  if (score >= 50) return "from-amber-400 to-yellow-400";
  return "from-red-500 to-rose-400";
}

function titleCase(s: string) {
  return s.replace(/[_-]/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
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

  const totalControls   = data ? data.frameworks.reduce((acc, fw) => acc + fw.controls.length, 0) : 0;
  const passingControls = data ? data.frameworks.reduce((acc, fw) => acc + fw.controls.filter(c => c.status === "passing").length, 0) : 0;
  const integrationCount = data?.integrations?.length ?? 0;

  return (
    <div
      className="min-h-screen text-white font-[family:'Sora',_ui-sans-serif,_system-ui]"
      style={{
        backgroundColor: "#030712",
        backgroundImage:
          "radial-gradient(ellipse at 20% 0%, rgba(15,41,66,0.9) 0%, transparent 55%), radial-gradient(ellipse at 80% 90%, rgba(10,31,46,0.7) 0%, transparent 50%)",
      }}
    >
      {/* Dot grid overlay */}
      <div
        className="fixed inset-0 pointer-events-none z-0"
        style={{
          backgroundImage: "radial-gradient(rgba(255,255,255,0.025) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-white/8 bg-black/50 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-white">TraceLayer</span>
            <span className="text-white/20 mx-1">·</span>
            <span className="text-xs text-white/40 font-medium">Trust Center</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-semibold">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            Live · Updated continuously
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 py-12 space-y-6">
        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="max-w-md mx-auto mt-20 text-center">
            <div className="w-14 h-14 bg-red-500/10 border border-red-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-7 h-7 text-red-400" />
            </div>
            <h1 className="text-xl font-bold text-white mb-2">Page unavailable</h1>
            <p className="text-sm text-white/40 mb-6">{error}</p>
            <Link href="/register" className="inline-flex items-center gap-2 bg-teal-500 hover:bg-teal-400 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-colors">
              Create your own trust page <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Hero — inline on dark bg */}
            <div className="py-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-12 h-12 bg-teal-500/15 border border-teal-500/25 rounded-2xl flex items-center justify-center shrink-0">
                      <ShieldCheck className="w-6 h-6 text-teal-400" />
                    </div>
                    <div>
                      <h1 className="text-3xl font-black text-white leading-tight">{data.company_name}</h1>
                      {data.custom_headline && (
                        <p className="text-sm text-white/50 mt-0.5">{data.custom_headline}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="bg-emerald-500/15 border border-emerald-500/25 text-emerald-300 text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1.5">
                      <CheckCircle2 className="w-3 h-3" /> Verified by TraceLayer
                    </span>
                    <span className="text-white/30 text-xs flex items-center gap-1.5">
                      <Clock className="w-3 h-3" /> Updated {timeAgo(data.generated_at)}
                    </span>
                  </div>
                </div>

                {data.show_score && data.frameworks.length > 0 && (
                  <div className="flex gap-6 shrink-0 flex-wrap">
                    {data.frameworks.map((fw) => (
                      <div key={fw.framework} className="text-center">
                        <ScoreRing score={fw.overall_score} size={80} />
                        <p className="text-xs font-semibold text-white/40 mt-2">{fw.label}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {data.custom_message && (
                <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-3 mb-5">
                  <p className="text-sm text-white/60 leading-relaxed">{data.custom_message}</p>
                </div>
              )}

              {/* Stats bar */}
              <div className="flex flex-wrap gap-3">
                {data.show_score && data.frameworks.length > 0 && (
                  <>
                    <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-center">
                      <p className="text-lg font-black text-white">{data.frameworks.length}</p>
                      <p className="text-[10px] text-white/40 font-medium mt-0.5">Framework{data.frameworks.length !== 1 ? "s" : ""}</p>
                    </div>
                    <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-center">
                      <p className="text-lg font-black text-white">{totalControls}</p>
                      <p className="text-[10px] text-white/40 font-medium mt-0.5">Controls Verified</p>
                    </div>
                    <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-xl px-4 py-2.5 text-center">
                      <p className="text-lg font-black text-emerald-300">{passingControls}/{totalControls}</p>
                      <p className="text-[10px] text-emerald-400/60 font-medium mt-0.5">Controls Passing</p>
                    </div>
                  </>
                )}
                {integrationCount > 0 && (
                  <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-center">
                    <p className="text-lg font-black text-white">{integrationCount}</p>
                    <p className="text-[10px] text-white/40 font-medium mt-0.5">Integrations</p>
                  </div>
                )}
                <div className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 flex items-center gap-2">
                  <Zap className="w-3.5 h-3.5 text-teal-400" />
                  <p className="text-[10px] text-white/50 font-medium">Real data, not self-reported</p>
                </div>
              </div>
            </div>

            {/* Framework score cards */}
            {data.show_score && data.frameworks.length > 0 && (
              <div className={`grid gap-4 ${
                data.frameworks.length === 1 ? "grid-cols-1 max-w-lg" :
                data.frameworks.length === 2 ? "grid-cols-1 sm:grid-cols-2" :
                "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
              }`}>
                {data.frameworks.map((fw) => {
                  const fwPassing = fw.controls.filter(c => c.status === "passing").length;
                  return (
                    <div key={fw.framework} className="bg-white/[0.04] backdrop-blur border border-white/10 rounded-2xl p-5">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center gap-2.5">
                          <div className={`w-9 h-9 rounded-xl bg-gradient-to-br ${FW_COLORS[fw.framework] ?? "from-gray-500 to-gray-600"} flex items-center justify-center shadow-lg shrink-0`}>
                            <ShieldCheck className="w-4 h-4 text-white" />
                          </div>
                          <div>
                            <p className="text-sm font-bold text-white">{fw.label}</p>
                            <p className="text-xs text-white/40">{fw.overall_score}% overall</p>
                          </div>
                        </div>
                        <ScoreRing score={fw.overall_score} size={52} />
                      </div>
                      <div className="space-y-2.5">
                        {fw.controls.map((c) => (
                          <div key={c.name}>
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-white/60 font-medium truncate flex-1 mr-2">{c.name}</span>
                              <div className="flex items-center gap-1.5 shrink-0">
                                <StatusBadge status={c.status} />
                                <span className="font-bold text-white/70 w-9 text-right">{c.score}%</span>
                              </div>
                            </div>
                            <div className="h-1 bg-white/8 rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full bg-gradient-to-r ${scoreBarGradient(c.score)} transition-all duration-700`}
                                style={{ width: `${c.score}%` }}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 pt-3 border-t border-white/8 flex items-center justify-between">
                        <span className="text-[10px] text-white/30 font-medium">{fwPassing}/{fw.controls.length} controls passing</span>
                        <span className={`text-[10px] font-bold ${fw.overall_score >= 80 ? "text-emerald-400" : fw.overall_score >= 50 ? "text-amber-400" : "text-red-400"}`}>
                          {fw.overall_score >= 80 ? "Compliant" : fw.overall_score >= 50 ? "In Progress" : "Needs Work"}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Adopted policies */}
            {data.show_policies && data.policies && data.policies.length > 0 && (
              <div className="bg-white/[0.04] backdrop-blur border border-white/10 rounded-2xl p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-9 h-9 rounded-xl bg-violet-500/15 border border-violet-500/20 flex items-center justify-center shrink-0">
                    <BookOpen className="w-4 h-4 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">Security Policies</p>
                    <p className="text-xs text-white/40">{data.policies.length} policies adopted &amp; maintained</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {data.policies.map((p, i) => (
                    <div key={i} className="flex items-center gap-3 bg-white/[0.03] border border-white/8 rounded-xl px-4 py-3">
                      <div className="w-7 h-7 bg-violet-500/15 rounded-lg flex items-center justify-center shrink-0">
                        <FileText className="w-3.5 h-3.5 text-violet-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-xs font-semibold text-white/90 truncate">{titleCase(p.slug)}</p>
                        <p className="text-[10px] text-white/30 mt-0.5">Policy active</p>
                      </div>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Connected integrations */}
            {data.show_integrations && data.integrations && data.integrations.length > 0 && (
              <div className="bg-white/[0.04] backdrop-blur border border-white/10 rounded-2xl p-5">
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-9 h-9 rounded-xl bg-cyan-500/15 border border-cyan-500/20 flex items-center justify-center shrink-0">
                    <Plug className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-white">Connected Integrations</p>
                    <p className="text-xs text-white/40">
                      Evidence automatically collected from {data.integrations.length} tool{data.integrations.length !== 1 ? "s" : ""}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {data.integrations.map((name) => (
                    <span key={name} className="inline-flex items-center gap-1.5 bg-white/[0.05] border border-white/10 text-xs font-semibold text-white/60 px-3 py-1.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* About */}
            <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-5">
              <div className="flex items-center gap-2 mb-3">
                <Globe className="w-4 h-4 text-white/30" />
                <p className="text-xs font-semibold text-white/50">About this trust center</p>
              </div>
              <p className="text-xs text-white/35 leading-relaxed">
                {data.company_name}&apos;s compliance data is automatically collected and verified by TraceLayer from
                their connected cloud infrastructure and SaaS tools. Evidence is gathered continuously —
                scores reflect real, live data, not self-reported claims.
              </p>
            </div>

            {/* CTA */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-teal-600 via-teal-500 to-cyan-500 p-8">
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute -top-12 right-1/4 w-72 h-72 bg-white/10 rounded-full blur-3xl" />
                <div className="absolute bottom-0 left-0 w-48 h-48 bg-black/10 rounded-full blur-3xl" />
              </div>
              <div className="relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5">
                <div>
                  <p className="text-xl font-black text-white mb-1.5">Build your own Trust Center</p>
                  <p className="text-white/70 text-sm max-w-sm">Show customers your live compliance posture — automated, verified, always up-to-date. Free to start.</p>
                </div>
                <Link href="/register" className="shrink-0 inline-flex items-center gap-2 bg-white text-teal-700 font-bold px-6 py-3 rounded-xl text-sm hover:bg-teal-50 transition-colors shadow-lg">
                  Get started free <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          </>
        )}
      </main>

      <footer className="relative z-10 border-t border-white/8 py-6 mt-4">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Image src="/logo-icon.png" alt="TraceLayer" width={20} height={20} className="rounded-md" />
            <span className="text-xs font-semibold text-white/25">Powered by TraceLayer</span>
          </div>
          {data && (
            <div className="flex items-center gap-3 flex-wrap">
              {data.frameworks.map((fw) => (
                <span key={fw.framework} className="flex items-center gap-1 text-xs text-white/25">
                  <CheckCircle2 className="w-3 h-3 text-teal-500/70" /> {fw.label}
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
