"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { api } from "@/lib/api";
import type { PublicAuditView } from "@/lib/types";
import { ShieldCheck, ArrowRight, CheckCircle2, AlertTriangle, Clock } from "lucide-react";

function ScoreRing({ score }: { score: number }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const color = score >= 80 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-20 h-20 shrink-0">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 84 84">
        <circle cx="42" cy="42" r={r} fill="none" stroke="#f1f5f9" strokeWidth="8" />
        <circle
          cx="42" cy="42" r={r}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease-in-out" }}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-lg font-black" style={{ color }}>{score}%</span>
      </div>
    </div>
  );
}

function scoreColor(score: number) {
  if (score >= 80) return "text-emerald-600";
  if (score >= 50) return "text-amber-600";
  return "text-red-500";
}

function scoreBarColor(score: number) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-amber-400";
  return "bg-red-400";
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    passing:     "bg-emerald-50 text-emerald-700",
    warning:     "bg-amber-50 text-amber-700",
    failing:     "bg-red-50 text-red-600",
    no_evidence: "bg-gray-100 text-gray-500",
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

export default function AuditorPortalPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PublicAuditView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    api.getPublicAuditView(token)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load compliance data"))
      .finally(() => setLoading(false));
  }, [token]);

  return (
    <div className="min-h-screen bg-gray-50 font-[family:'Sora',_ui-sans-serif,_system-ui]">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-5xl mx-auto px-6 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={26} height={26} className="rounded-lg" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
            <span className="text-gray-200 mx-1">·</span>
            <span className="text-xs text-gray-500 font-medium">Auditor View</span>
          </div>
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            Read-only access
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
        {loading && (
          <div className="flex items-center justify-center h-64">
            <div className="w-6 h-6 border-2 border-teal-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {error && (
          <div className="max-w-md mx-auto mt-20 text-center">
            <div className="w-14 h-14 bg-red-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-7 h-7 text-red-500" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Link unavailable</h1>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <Link href="/register" className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold px-6 py-2.5 rounded-xl text-sm transition-colors">
              Create your own TraceLayer account <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Title */}
            <div className="mb-8">
              <div className="flex items-center gap-2 mb-1">
                <ShieldCheck className="w-5 h-5 text-teal-600" />
                <h1 className="text-2xl font-extrabold text-gray-900">{data.company_name}</h1>
              </div>
              <div className="flex items-center gap-4 flex-wrap text-xs text-gray-400 mt-1">
                {data.session_label && (
                  <span className="font-medium text-gray-600">{data.session_label}</span>
                )}
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Generated {new Date(data.generated_at).toLocaleString()}
                </span>
                <span className="bg-amber-50 text-amber-700 border border-amber-100 text-[10px] font-semibold px-2 py-0.5 rounded-full">
                  Read-only · No login required
                </span>
              </div>
            </div>

            {/* Framework score cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-8">
              {data.frameworks.map((fw) => (
                <div key={fw.framework} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest">{fw.label}</p>
                      <p className={`text-3xl font-black mt-0.5 ${scoreColor(fw.overall_score)}`}>{fw.overall_score}%</p>
                    </div>
                    <ScoreRing score={fw.overall_score} />
                  </div>
                  <div className="space-y-2">
                    {fw.controls.map((c) => (
                      <div key={c.name}>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-gray-600 font-medium truncate flex-1 mr-2">{c.name}</span>
                          <div className="flex items-center gap-1.5 shrink-0">
                            {statusBadge(c.status)}
                            <span className={`font-bold ${scoreColor(c.score)}`}>{c.score}%</span>
                          </div>
                        </div>
                        <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${scoreBarColor(c.score)}`}
                            style={{ width: `${c.score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Attestation note */}
            <div className="bg-white rounded-2xl border border-gray-100 p-5 mb-8">
              <p className="text-xs font-semibold text-gray-700 mb-2">About this report</p>
              <p className="text-xs text-gray-500 leading-relaxed">
                This compliance view is automatically generated by TraceLayer based on live evidence collected from {data.company_name}&apos;s connected infrastructure and SaaS tools. Evidence is collected continuously and scores are updated in real time. This is a point-in-time snapshot generated on {new Date(data.generated_at).toLocaleDateString()}.
              </p>
            </div>

            {/* CTA */}
            <div className="bg-teal-600 rounded-2xl p-6 text-center">
              <p className="text-white font-bold mb-1">Manage your own compliance with TraceLayer</p>
              <p className="text-white/70 text-xs mb-4">Automated evidence collection for SOC 2, ISO 27001 & HIPAA. Free to start.</p>
              <Link href="/register" className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-6 py-2.5 rounded-xl text-sm transition-colors">
                Get started free <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </>
        )}
      </main>

      <footer className="border-t border-gray-100 py-6 mt-10">
        <div className="max-w-5xl mx-auto px-6 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-2">
            <Image src="/logo-icon.png" alt="TraceLayer" width={20} height={20} className="rounded-md" />
            <span className="text-xs font-semibold text-gray-500">Powered by TraceLayer</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-gray-400">
            <CheckCircle2 className="w-3 h-3 text-teal-500" /> SOC 2
            <CheckCircle2 className="w-3 h-3 text-teal-500" /> ISO 27001
            <CheckCircle2 className="w-3 h-3 text-teal-500" /> HIPAA
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
      `}</style>
    </div>
  );
}
