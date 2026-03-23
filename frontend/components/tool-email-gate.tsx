"use client";

import { useState } from "react";
import { ArrowRight, CheckCircle2, Lock } from "lucide-react";

interface TeaserStat {
  label: string;
  value: string;
  valueColor?: string; // tailwind text color class, e.g. "text-red-600"
}

interface Props {
  toolName: string;
  headline: string;
  subline: string;
  teasers: TeaserStat[];
  onUnlocked: () => void;
}

export function ToolEmailGate({ toolName, headline, subline, teasers, onUnlocked }: Props) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError("");
    try {
      await fetch("/api/capture-lead", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, tool: toolName }),
      });
      onUnlocked();
    } catch {
      // Unlock even on network error — don't punish the user
      onUnlocked();
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <div className="bg-white rounded-2xl shadow-2xl overflow-hidden border border-white/20">

        {/* Teaser header — visible stats to create desire */}
        <div className="px-7 pt-7 pb-5 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
            <span className="text-xs font-bold text-teal-600 uppercase tracking-widest">
              Your results are ready
            </span>
          </div>
          <h3 className="text-xl font-extrabold text-gray-900 mb-1">{headline}</h3>
          <p className="text-sm text-gray-500">{subline}</p>

          {teasers.length > 0 && (
            <div className="flex flex-wrap gap-6 mt-5">
              {teasers.map((t) => (
                <div key={t.label}>
                  <div className={`text-3xl font-black ${t.valueColor ?? "text-gray-900"}`}>
                    {t.value}
                  </div>
                  <div className="text-xs text-gray-400 mt-0.5">{t.label}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Blurred locked section */}
        <div className="relative px-7 py-5 overflow-hidden select-none">
          {/* Fake blurred content rows */}
          <div className="space-y-2.5 blur-sm">
            <div className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-xl px-4 py-3">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="h-3 bg-red-200 rounded w-2/3" />
              <div className="h-3 bg-red-100 rounded w-1/4 ml-auto" />
            </div>
            <div className="flex items-center gap-3 bg-orange-50 border border-orange-100 rounded-xl px-4 py-3">
              <div className="w-3 h-3 rounded-full bg-orange-400" />
              <div className="h-3 bg-orange-200 rounded w-1/2" />
              <div className="h-3 bg-orange-100 rounded w-1/4 ml-auto" />
            </div>
            <div className="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
              <div className="w-3 h-3 rounded-full bg-gray-300" />
              <div className="h-3 bg-gray-200 rounded w-3/5" />
              <div className="h-3 bg-gray-100 rounded w-1/4 ml-auto" />
            </div>
          </div>
          {/* Lock overlay */}
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/60 backdrop-blur-[2px]">
            <div className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 bg-gray-100 rounded-full flex items-center justify-center">
                <Lock className="w-4 h-4 text-gray-500" />
              </div>
              <p className="text-sm font-semibold text-gray-700">Full report locked</p>
              <p className="text-xs text-gray-400">Enter your email to unlock</p>
            </div>
          </div>
        </div>

        {/* Email form */}
        <div className="px-7 pb-7 pt-4">
          <p className="text-sm font-bold text-gray-900 mb-1">
            Unlock your full report — free
          </p>
          <p className="text-xs text-gray-400 mb-4">
            Get the detailed breakdown + a free SOC 2 remediation checklist emailed to you.
          </p>
          <form onSubmit={submit} className="flex flex-col sm:flex-row gap-2">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@yourcompany.com"
              className="flex-1 text-sm border border-gray-200 rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400 placeholder:text-gray-300"
            />
            <button
              type="submit"
              disabled={loading}
              className="inline-flex items-center justify-center gap-1.5 bg-teal-600 hover:bg-teal-700 disabled:opacity-60 text-white font-semibold px-5 py-2.5 rounded-xl transition-colors text-sm whitespace-nowrap"
            >
              {loading ? (
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>Unlock results <ArrowRight className="w-3.5 h-3.5" /></>
              )}
            </button>
          </form>
          {error && <p className="text-xs text-red-500 mt-2">{error}</p>}
          <p className="text-[11px] text-gray-400 mt-3 flex items-center gap-1.5">
            <CheckCircle2 className="w-3 h-3 text-gray-300 shrink-0" />
            No spam. One email with your results. Unsubscribe anytime.
          </p>
        </div>
      </div>
    </div>
  );
}
