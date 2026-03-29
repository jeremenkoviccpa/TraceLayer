"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Policy } from "@/lib/types";
import { BookOpen, Save, CheckCircle2, Clock, FileText, Sparkles, Send, Loader2, User as UserIcon } from "lucide-react";

type ChatMessage = { role: "bot" | "user"; content: string };

const POLICY_SUGGESTED: string[] = [
  "Is this policy complete for SOC 2?",
  "What's missing from this policy?",
  "How can I strengthen it?",
  "What controls does this policy cover?",
];

const POLICY_FOLLOWUP: string[] = [
  "Give me example language to add",
  "What else should I update?",
  "Which framework requires this policy?",
];

function PolicyAdvisorChat({ policy }: { policy: Policy | null }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMessages([]);
    if (!policy) return;
    setSending(true);
    const initMsg = `I'm looking at the "${policy.title}" policy. Give me a brief assessment: is it comprehensive for SOC 2 and ISO 27001 compliance? Name 2-3 specific things that could be added or improved.`;
    api.advisorChat("soc2", initMsg, [])
      .then(({ reply }) => setMessages([{ role: "bot", content: reply }]))
      .catch(() => setMessages([{ role: "bot", content: "Ask me anything about this policy and I'll help you improve it." }]))
      .finally(() => setSending(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [policy?.slug]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, sending]);

  const sendMessage = async (text: string) => {
    const msg = text.trim();
    if (!msg || sending) return;
    setInput("");
    const history = messages.map(m => ({ role: m.role === "bot" ? "assistant" : "user", content: m.content }));
    const policyCtx = policy ? `[Context: we're reviewing the "${policy.title}" policy] ` : "";
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setSending(true);
    try {
      const { reply } = await api.advisorChat("soc2", policyCtx + msg, history);
      setMessages(prev => [...prev, { role: "bot", content: reply }]);
    } catch {
      setMessages(prev => [...prev, { role: "bot", content: "Sorry, I had trouble responding. Please try again." }]);
    } finally {
      setSending(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const suggested = messages.length <= 1 && !sending ? POLICY_SUGGESTED : messages.length > 1 && !sending ? POLICY_FOLLOWUP : [];

  return (
    <div className="rounded-2xl border border-slate-200 overflow-hidden shadow-sm flex flex-col">
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 px-4 py-3 flex items-center gap-3 shrink-0">
        <div className="w-7 h-7 rounded-lg bg-white/10 border border-white/10 flex items-center justify-center shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-violet-300" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-none">Policy Advisor</p>
          <p className="text-[10px] text-slate-400 mt-0.5">
            {policy ? policy.title : "Select a policy"} · Ask how to improve it
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span className="text-xs text-slate-400">Llama 3.3 · Groq</span>
        </div>
      </div>

      <div ref={scrollRef} className="overflow-y-auto bg-white px-4 py-4 space-y-3" style={{ minHeight: 160, maxHeight: 300 }}>
        {messages.length === 0 && sending && (
          <div className="flex items-start gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
            </div>
            <div className="flex flex-col gap-2 flex-1">
              <div className="inline-flex items-center gap-1 bg-slate-50 border border-slate-100 rounded-2xl rounded-tl-sm px-4 py-3">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
              </div>
              <p className="text-[11px] text-gray-400 ml-1">Reviewing policy…</p>
            </div>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex items-end gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
            {msg.role === "bot" ? (
              <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center shrink-0 mb-0.5">
                <Sparkles className="w-3.5 h-3.5 text-violet-300" />
              </div>
            ) : (
              <div className="w-7 h-7 rounded-xl bg-violet-600 flex items-center justify-center shrink-0 mb-0.5">
                <UserIcon className="w-3.5 h-3.5 text-white" />
              </div>
            )}
            <div className={`max-w-[84%] px-3.5 py-2.5 rounded-2xl text-sm leading-relaxed ${
              msg.role === "bot"
                ? "bg-slate-50 border border-slate-100 rounded-bl-sm text-gray-800"
                : "bg-violet-600 text-white rounded-br-sm"
            }`}>
              <p className="whitespace-pre-line">{msg.content}</p>
            </div>
          </div>
        ))}
        {sending && messages.length > 0 && (
          <div className="flex items-end gap-2.5">
            <div className="w-7 h-7 rounded-xl bg-slate-900 flex items-center justify-center shrink-0 mb-0.5">
              <Sparkles className="w-3.5 h-3.5 text-violet-300" />
            </div>
            <div className="bg-slate-50 border border-slate-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
      </div>

      {suggested.length > 0 && (
        <div className="px-4 py-2.5 bg-gray-50 border-t border-gray-100 flex flex-wrap gap-1.5 shrink-0">
          {suggested.map((q) => (
            <button key={q} onClick={() => sendMessage(q)} disabled={sending}
              className="text-[11px] font-medium text-violet-600 bg-violet-50 hover:bg-violet-100 border border-violet-100 px-2.5 py-1 rounded-full transition-colors disabled:opacity-40 whitespace-nowrap">
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="px-4 py-3 bg-white border-t border-gray-100 flex items-center gap-2 shrink-0">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
          placeholder={policy ? `Ask about ${policy.title}…` : "Select a policy first…"}
          disabled={sending || !policy}
          className="flex-1 text-sm border border-gray-200 rounded-xl px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-violet-500/25 focus:border-violet-400 bg-white transition-all disabled:opacity-50 placeholder:text-gray-400"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || sending || !policy}
          className="w-9 h-9 rounded-xl bg-violet-600 hover:bg-violet-700 disabled:opacity-30 disabled:cursor-not-allowed text-white flex items-center justify-center shrink-0 transition-colors"
        >
          {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
        </button>
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

      {/* ── Policy Advisor Chatbot ── */}
      {!loading && <PolicyAdvisorChat policy={selected} />}
    </div>
  );
}
