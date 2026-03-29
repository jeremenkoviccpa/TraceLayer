"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Policy } from "@/lib/types";
import { BookOpen, Save, CheckCircle2, Clock, FileText, Sparkles, Copy, Check, Loader2 } from "lucide-react";

function PolicyTemplateGenerator({ policy, onInsert }: { policy: Policy | null; onInsert: (content: string) => void }) {
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset when policy changes
  useEffect(() => {
    setGenerated(null);
    setError(null);
  }, [policy?.slug]);

  const handleGenerate = async () => {
    if (!policy || generating) return;
    setGenerating(true);
    setError(null);
    try {
      const { content } = await api.generatePolicy(policy.slug);
      setGenerated(content);
    } catch {
      setError("Generation failed. Please try again.");
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    if (!generated) return;
    navigator.clipboard.writeText(generated).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!policy) return null;

  return (
    <div className="rounded-2xl border border-violet-100 bg-white shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-violet-700 px-4 py-3 flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-none">AI Policy Template Generator</p>
          <p className="text-[10px] text-violet-200 mt-0.5">Generate a full {policy.title} document tailored to your stack</p>
        </div>
        <span className="text-xs text-violet-200">Llama 3.3 · Groq</span>
      </div>

      <div className="p-4 space-y-3">
        {!generated && !generating && (
          <div className="flex flex-col items-center text-center gap-3 py-4">
            <FileText className="w-8 h-8 text-violet-200" />
            <div>
              <p className="text-sm font-medium text-gray-700">Generate a complete {policy.title}</p>
              <p className="text-xs text-gray-400 mt-0.5">AI will write a full, framework-aligned policy document using your connected integrations</p>
            </div>
            <button
              onClick={handleGenerate}
              className="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Generate Policy Template
            </button>
            {error && <p className="text-xs text-red-500">{error}</p>}
          </div>
        )}

        {generating && (
          <div className="flex flex-col items-center gap-3 py-6">
            <Loader2 className="w-6 h-6 text-violet-400 animate-spin" />
            <p className="text-sm text-gray-500">Writing your {policy.title}…</p>
          </div>
        )}

        {generated && !generating && (
          <>
            <div className="bg-gray-50 border border-gray-100 rounded-xl p-3 max-h-64 overflow-y-auto">
              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">{generated}</pre>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { onInsert(generated); setGenerated(null); }}
                className="flex-1 inline-flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-medium px-3 py-2 rounded-xl transition-colors"
              >
                Use this template
              </button>
              <button
                onClick={handleCopy}
                className="inline-flex items-center gap-1.5 border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium px-3 py-2 rounded-xl transition-colors"
              >
                {copied ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</> : <><Copy className="w-3.5 h-3.5" /> Copy</>}
              </button>
              <button
                onClick={() => setGenerated(null)}
                className="inline-flex items-center gap-1.5 border border-gray-200 hover:bg-gray-50 text-gray-600 text-sm px-3 py-2 rounded-xl transition-colors"
              >
                Regenerate
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default function PoliciesPage() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [selected, setSelected] = useState<Policy | null>(null);
  const [content, setContent]   = useState("");
  const [loading, setLoading]   = useState(true);
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState(false);

  useEffect(() => {
    api.getPolicies()
      .then((ps) => {
        setPolicies(ps);
        if (ps.length > 0) { setSelected(ps[0]); setContent(ps[0].content); }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectPolicy = (p: Policy) => {
    setSelected(p);
    setContent(p.content);
    setSaved(false);
  };

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    try {
      const updated = await api.savePolicy(selected.slug, content);
      setPolicies((prev) => prev.map((p) => p.slug === updated.slug ? { ...p, ...updated } : p));
      setSelected((prev) => prev ? { ...prev, ...updated } : prev);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  const lastUpdatedLabel = (() => {
    const dates = policies
      .map((p) => p.updated_at ? new Date(p.updated_at).getTime() : null)
      .filter((d): d is number => d !== null);
    if (dates.length === 0) return "Never";
    return new Date(Math.max(...dates)).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  })();

  return (
    <div className="animate-fade-in flex h-full flex-col space-y-6 overflow-x-hidden">

      {/* ── Dark hero card ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        {/* subtle grid texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />

        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          {/* Left: icon + copy */}
          <div className="flex-1 space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-500/20 ring-1 ring-violet-500/30">
                <BookOpen className="h-5 w-5 text-violet-400" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white leading-tight">Policy Templates</h1>
                <p className="text-sm text-slate-400">Pre-written SOC 2 & ISO 27001 policies. Customize and adopt.</p>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap gap-4">
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Total policies</span>
                <span className="text-2xl font-black text-violet-400">{policies.length}</span>
              </div>
              <div className="w-px self-stretch bg-slate-700/60" />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Last updated</span>
                <span className="mt-0.5 text-sm font-semibold text-slate-300">{lastUpdatedLabel}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Mobile: policy select dropdown ── */}
      {!loading && policies.length > 0 && (
        <div className="md:hidden">
          <select
            value={selected?.slug ?? ""}
            onChange={(e) => {
              const p = policies.find((p) => p.slug === e.target.value);
              if (p) selectPolicy(p);
            }}
            className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm font-medium text-gray-800 bg-white focus:outline-none focus:ring-2 focus:ring-violet-500/30"
          >
            {policies.map((p) => (
              <option key={p.slug} value={p.slug}>{p.title}</option>
            ))}
          </select>
        </div>
      )}

      {/* ── Main 2-panel layout ── */}
      {loading ? (
        <div className="flex h-40 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
        </div>
      ) : (
        <div className="flex flex-col md:flex-row min-h-0 flex-1 gap-5 md:h-[calc(100vh-26rem)]">

          {/* ── Left sidebar: policy list (desktop only) ── */}
          <div className="hidden md:flex w-64 shrink-0 flex-col overflow-y-auto rounded-2xl border border-gray-100 bg-white p-2 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400">
              Policies
            </p>
            <div className="space-y-0.5">
              {policies.map((p) => {
                const isActive = selected?.slug === p.slug;
                return (
                  <button
                    key={p.slug}
                    onClick={() => selectPolicy(p)}
                    className={`w-full rounded-xl px-3 py-2.5 text-left transition-all ${
                      isActive
                        ? "bg-violet-600 shadow-sm shadow-violet-500/20"
                        : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <FileText
                        className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${
                          isActive ? "text-violet-200" : "text-gray-400"
                        }`}
                      />
                      <div className="min-w-0">
                        <p
                          className={`line-clamp-2 text-sm leading-snug ${
                            isActive ? "font-semibold text-white" : "font-medium text-gray-700"
                          }`}
                        >
                          {p.title}
                        </p>
                        {p.updated_at && (
                          <p
                            className={`mt-0.5 flex items-center gap-1 text-[10px] ${
                              isActive ? "text-violet-300" : "text-gray-400"
                            }`}
                          >
                            <Clock className="h-2.5 w-2.5" />
                            {new Date(p.updated_at).toLocaleDateString("en-US", {
                              month: "short",
                              day: "numeric",
                            })}
                          </p>
                        )}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* ── Editor panel ── */}
          {selected ? (
            <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.04)]" style={{ minHeight: "400px" }}>

              {/* Editor header */}
              <div className="flex shrink-0 items-center justify-between border-b border-gray-100 px-5 py-3.5 gap-3">
                <div className="min-w-0">
                  <h2 className="font-bold text-gray-900 truncate">{selected.title}</h2>
                  {selected.updated_at && (
                    <p className="mt-0.5 flex items-center gap-1 text-xs text-gray-400">
                      <Clock className="h-3 w-3 shrink-0" />
                      Last saved{" "}
                      {new Date(selected.updated_at).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                      })}
                    </p>
                  )}
                </div>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className={`shrink-0 flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50 ${
                    saved
                      ? "bg-emerald-500 shadow-emerald-500/20"
                      : "bg-violet-600 shadow-violet-500/20 hover:bg-violet-500"
                  }`}
                >
                  {saved ? (
                    <><CheckCircle2 className="h-3.5 w-3.5" /> Saved</>
                  ) : saving ? (
                    "Saving…"
                  ) : (
                    <><Save className="h-3.5 w-3.5" /> Save</>
                  )}
                </button>
              </div>

              {/* Textarea */}
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="flex-1 w-full resize-none px-5 py-4 font-mono text-sm leading-relaxed text-gray-800 focus:outline-none"
                style={{ minHeight: "300px" }}
                spellCheck={false}
              />

              {/* Footer */}
              <div className="flex shrink-0 items-center justify-between border-t border-gray-100 px-5 py-2.5">
                <p className="text-xs text-gray-400">{wordCount} words</p>
                <p className="text-xs text-gray-400 hidden sm:block">Plain text — copy into your policy doc or wiki</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-1 items-center justify-center rounded-2xl border border-gray-100 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.04)]" style={{ minHeight: "300px" }}>
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50">
                  <BookOpen className="h-6 w-6 text-violet-400" />
                </div>
                <p className="text-sm font-medium text-gray-600">Select a policy to start editing</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── AI Policy Template Generator ── */}
      {!loading && (
        <PolicyTemplateGenerator
          policy={selected}
          onInsert={(content) => {
            setContent(content);
          }}
        />
      )}
    </div>
  );
}
