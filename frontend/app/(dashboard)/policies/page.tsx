"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Policy } from "@/lib/types";
import { BookOpen, Save, CheckCircle2, Clock, FileText, Sparkles, Copy, Check, Loader2, CalendarDays, AlertTriangle, X, Users, PenLine } from "lucide-react";

// ── Expiry helpers ─────────────────────────────────────────────────────────────
function getDaysRemaining(expires_at: string | null): number | null {
  if (!expires_at) return null;
  const now = new Date();
  const exp = new Date(expires_at);
  return Math.ceil((exp.getTime() - now.setHours(0, 0, 0, 0)) / 86_400_000);
}

type ExpiryStatus = "expired" | "critical" | "warning" | "ok";

function getExpiryStatus(days: number | null): ExpiryStatus | null {
  if (days === null) return null;
  if (days < 0) return "expired";
  if (days <= 7) return "critical";
  if (days <= 30) return "warning";
  return "ok";
}

function ExpiryBadge({ days, compact = false }: { days: number | null; compact?: boolean }) {
  const status = getExpiryStatus(days);
  if (status === null) return null;

  const cfg = {
    expired:  { bg: "bg-red-100",    text: "text-red-700",    label: days! < -1 ? `Expired ${Math.abs(days!)}d ago` : "Expired" },
    critical: { bg: "bg-orange-100", text: "text-orange-700", label: days === 0 ? "Expires today" : `Expires in ${days}d` },
    warning:  { bg: "bg-amber-100",  text: "text-amber-700",  label: compact ? `${days}d` : `Expires in ${days} days` },
    ok:       { bg: "bg-gray-100",   text: "text-gray-500",   label: compact ? `${days}d` : `Expires in ${days} days` },
  }[status];

  return (
    <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-md ${cfg.bg} ${cfg.text}`}>
      <CalendarDays className="w-2.5 h-2.5 shrink-0" />
      {cfg.label}
    </span>
  );
}

// ── Expiry date picker panel ───────────────────────────────────────────────────
function ExpiryPanel({
  policy,
  onUpdate,
}: {
  policy: Policy;
  onUpdate: (updated: Policy) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(
    policy.expires_at ? policy.expires_at.slice(0, 10) : ""
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Sync when policy changes
  useEffect(() => {
    setValue(policy.expires_at ? policy.expires_at.slice(0, 10) : "");
    setEditing(false);
    setError(null);
  }, [policy.slug]);

  const days = getDaysRemaining(policy.expires_at);
  const status = getExpiryStatus(days);

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.setPolicyExpiry(
        policy.slug,
        value ? new Date(value).toISOString() : null
      );
      onUpdate(updated);
      setEditing(false);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const handleClear = async () => {
    setSaving(true);
    setError(null);
    try {
      const updated = await api.setPolicyExpiry(policy.slug, null);
      onUpdate(updated);
      setValue("");
      setEditing(false);
    } catch {
      setError("Failed to clear.");
    } finally {
      setSaving(false);
    }
  };

  const alertBg = status === "expired" ? "bg-red-50 border-red-200"
    : status === "critical" ? "bg-orange-50 border-orange-200"
    : status === "warning" ? "bg-amber-50 border-amber-200"
    : null;

  return (
    <div className="border-t border-gray-100 px-5 py-3">
      {/* Alert banner for expiring/expired */}
      {alertBg && (
        <div className={`flex items-start gap-2 rounded-xl border px-3 py-2.5 mb-3 ${alertBg}`}>
          <AlertTriangle className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
            status === "expired" ? "text-red-600" : status === "critical" ? "text-orange-600" : "text-amber-600"
          }`}/>
          <p className={`text-xs font-medium ${
            status === "expired" ? "text-red-700" : status === "critical" ? "text-orange-700" : "text-amber-700"
          }`}>
            {status === "expired"
              ? `This policy expired ${Math.abs(days!)} day${Math.abs(days!) !== 1 ? "s" : ""} ago. Review and renew it to maintain compliance.`
              : status === "critical"
              ? `This policy expires ${days === 0 ? "today" : `in ${days} day${days !== 1 ? "s" : ""}`}. Renew it before it lapses.`
              : `This policy expires in ${days} days. Plan your renewal now.`}
          </p>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 min-w-0">
          <CalendarDays className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span className="text-xs font-medium text-gray-600">Review date</span>
          {policy.expires_at && !editing && (
            <span className="text-xs text-gray-500">
              {new Date(policy.expires_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
            </span>
          )}
          {policy.expires_at && !editing && <ExpiryBadge days={days} />}
          {!policy.expires_at && !editing && (
            <span className="text-xs text-gray-400 italic">Not set</span>
          )}
        </div>

        {!editing ? (
          <button
            onClick={() => setEditing(true)}
            className="text-xs font-semibold text-violet-600 hover:text-violet-700 shrink-0"
          >
            {policy.expires_at ? "Change" : "Set date"}
          </button>
        ) : (
          <div className="flex items-center gap-2">
            <input
              type="date"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              min={new Date().toISOString().slice(0, 10)}
              className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-2 focus:ring-violet-500/30"
            />
            <button
              onClick={handleSave}
              disabled={saving || !value}
              className="text-xs font-semibold text-white bg-violet-600 hover:bg-violet-700 px-2.5 py-1 rounded-lg transition-colors disabled:opacity-50"
            >
              {saving ? "…" : "Save"}
            </button>
            {policy.expires_at && (
              <button
                onClick={handleClear}
                disabled={saving}
                title="Remove expiry date"
                className="p-1 text-gray-400 hover:text-red-500 rounded-lg transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={() => { setEditing(false); setValue(policy.expires_at?.slice(0, 10) ?? ""); }}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
      {error && <p className="text-xs text-red-500 mt-1.5">{error}</p>}
    </div>
  );
}

// ── Policy acknowledgment panel ────────────────────────────────────────────────
function AcknowledgmentPanel({ policy, currentUserEmail }: { policy: Policy; currentUserEmail?: string }) {
  const [data, setData] = useState<{
    signed: Array<{ user_id: string; email: string; name: string; signed_at: string }>;
    unsigned: Array<{ user_id: string; email: string; name: string }>;
  } | null>(null);
  const [loading, setLoading] = useState(false);
  const [signing, setSigning] = useState(false);
  const [open, setOpen] = useState(false);

  const myEntry = data?.signed.find((s) => s.email === currentUserEmail);
  const iSigned = !!myEntry;

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.getPolicyAcknowledgments(policy.slug);
      setData(res);
    } catch { /* ignore */ } finally { setLoading(false); }
  };

  useEffect(() => {
    setData(null);
    setOpen(false);
  }, [policy.slug]);

  const handleToggleSign = async () => {
    setSigning(true);
    try {
      if (iSigned) {
        await api.revokeAcknowledgement(policy.slug);
      } else {
        await api.acknowledgePolicy(policy.slug);
      }
      await load();
    } catch { /* ignore */ } finally { setSigning(false); }
  };

  const handleOpen = async () => {
    setOpen((v) => !v);
    if (!data) await load();
  };

  const signedCount = data?.signed.length ?? 0;
  const unsignedCount = data?.unsigned.length ?? 0;
  const total = signedCount + unsignedCount;

  return (
    <div className="border-t border-gray-100">
      <button
        onClick={handleOpen}
        className="w-full flex items-center justify-between px-5 py-3 text-left hover:bg-gray-50/60 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Users className="w-3.5 h-3.5 text-gray-400 shrink-0" />
          <span className="text-xs font-medium text-gray-600">Acknowledgments</span>
          {data && (
            <span className="text-xs text-gray-400">
              {signedCount}/{total} signed
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {iSigned && (
            <span className="inline-flex items-center gap-1 text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700">
              <Check className="w-2.5 h-2.5" /> Acknowledged
            </span>
          )}
          {open ? <X className="w-3.5 h-3.5 text-gray-400" /> : <PenLine className="w-3.5 h-3.5 text-gray-400" />}
        </div>
      </button>

      {open && (
        <div className="px-5 pb-4 space-y-3">
          {/* My acknowledgment */}
          <button
            onClick={handleToggleSign}
            disabled={signing}
            className={`w-full flex items-center justify-center gap-2 rounded-xl py-2 text-sm font-semibold transition-all ${
              iSigned
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200 hover:bg-red-50 hover:text-red-600 hover:border-red-200"
                : "bg-violet-600 text-white hover:bg-violet-700 shadow-sm shadow-violet-500/20"
            }`}
          >
            {signing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : iSigned ? <CheckCircle2 className="w-3.5 h-3.5" /> : <PenLine className="w-3.5 h-3.5" />}
            {signing ? "…" : iSigned ? "Acknowledged — click to withdraw" : "Acknowledge this policy"}
          </button>

          {/* Signature list */}
          {loading ? (
            <div className="flex justify-center py-2">
              <Loader2 className="w-4 h-4 animate-spin text-gray-300" />
            </div>
          ) : data && (
            <div className="space-y-1.5">
              {data.signed.map((s) => (
                <div key={s.user_id} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-emerald-50/60">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
                  <span className="text-xs font-medium text-gray-700 flex-1 truncate">{s.name || s.email}</span>
                  <span className="text-[10px] text-gray-400 shrink-0">
                    {new Date(s.signed_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                  </span>
                </div>
              ))}
              {data.unsigned.map((u) => (
                <div key={u.user_id} className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-gray-50">
                  <div className="w-3 h-3 rounded-full border border-gray-300 shrink-0" />
                  <span className="text-xs text-gray-400 flex-1 truncate">{u.name || u.email}</span>
                  <span className="text-[10px] text-gray-400 shrink-0">Pending</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── AI template generator ──────────────────────────────────────────────────────
function PolicyTemplateGenerator({ policy, onInsert }: { policy: Policy | null; onInsert: (content: string) => void }) {
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      <div className="bg-gradient-to-r from-violet-600 to-violet-700 px-4 py-3 flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-white/15 flex items-center justify-center shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-white leading-none">AI Policy Template Generator</p>
          <p className="text-[10px] text-violet-200 mt-0.5">Generate a full {policy.title} document tailored to your stack</p>
        </div>
        <span className="text-xs text-violet-200">Claude · Anthropic</span>
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
  const [currentUserEmail, setCurrentUserEmail] = useState<string | undefined>(undefined);

  useEffect(() => {
    api.getPolicies()
      .then((ps) => {
        setPolicies(ps);
        if (ps.length > 0) { setSelected(ps[0]); setContent(ps[0].content); }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
    api.me().then((u) => setCurrentUserEmail(u.email)).catch(() => {});
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
      const merged = { ...updated, expires_at: selected.expires_at };
      setPolicies((prev) => prev.map((p) => p.slug === merged.slug ? merged : p));
      setSelected(merged);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch { /* ignore */ } finally { setSaving(false); }
  };

  const handleExpiryUpdate = (updated: Policy) => {
    setPolicies((prev) => prev.map((p) => p.slug === updated.slug ? { ...p, expires_at: updated.expires_at } : p));
    setSelected((prev) => prev ? { ...prev, expires_at: updated.expires_at } : prev);
  };

  const wordCount = content.trim().split(/\s+/).filter(Boolean).length;

  const lastUpdatedLabel = (() => {
    const dates = policies
      .map((p) => p.updated_at ? new Date(p.updated_at).getTime() : null)
      .filter((d): d is number => d !== null);
    if (dates.length === 0) return "Never";
    return new Date(Math.max(...dates)).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  })();

  // Expiry summary stats for the hero card
  const expirySummary = (() => {
    const expiredCount  = policies.filter((p) => { const d = getDaysRemaining(p.expires_at); return d !== null && d < 0; }).length;
    const criticalCount = policies.filter((p) => { const d = getDaysRemaining(p.expires_at); return d !== null && d >= 0 && d <= 7; }).length;
    const warningCount  = policies.filter((p) => { const d = getDaysRemaining(p.expires_at); return d !== null && d > 7 && d <= 30; }).length;
    return { expiredCount, criticalCount, warningCount };
  })();

  return (
    <div className="animate-fade-in flex h-full flex-col space-y-6 overflow-x-hidden">

      {/* ── Dark hero card ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 shadow-xl">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.4) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.4) 1px, transparent 1px)",
            backgroundSize: "24px 24px",
          }}
        />
        <div className="relative flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
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
              {(expirySummary.expiredCount > 0 || expirySummary.criticalCount > 0 || expirySummary.warningCount > 0) && (
                <>
                  <div className="w-px self-stretch bg-slate-700/60" />
                  <div className="flex flex-col">
                    <span className="text-[11px] font-medium uppercase tracking-wider text-slate-500">Expiring</span>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      {expirySummary.expiredCount > 0 && (
                        <span className="text-xs font-bold text-red-400">{expirySummary.expiredCount} expired</span>
                      )}
                      {expirySummary.criticalCount > 0 && (
                        <span className="text-xs font-bold text-orange-400">{expirySummary.criticalCount} &lt;7d</span>
                      )}
                      {expirySummary.warningCount > 0 && (
                        <span className="text-xs font-bold text-amber-400">{expirySummary.warningCount} &lt;30d</span>
                      )}
                    </div>
                  </div>
                </>
              )}
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

          {/* ── Left sidebar ── */}
          <div className="hidden md:flex w-64 shrink-0 flex-col overflow-y-auto rounded-2xl border border-gray-100 bg-white p-2 shadow-[0_1px_3px_rgba(0,0,0,0.04)]">
            <p className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-widest text-gray-400">Policies</p>
            <div className="space-y-0.5">
              {policies.map((p) => {
                const isActive = selected?.slug === p.slug;
                const days = getDaysRemaining(p.expires_at);
                const status = getExpiryStatus(days);
                return (
                  <button
                    key={p.slug}
                    onClick={() => selectPolicy(p)}
                    className={`w-full rounded-xl px-3 py-2.5 text-left transition-all ${
                      isActive ? "bg-violet-600 shadow-sm shadow-violet-500/20" : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <FileText className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${isActive ? "text-violet-200" : "text-gray-400"}`}/>
                      <div className="min-w-0 flex-1">
                        <p className={`line-clamp-2 text-sm leading-snug ${isActive ? "font-semibold text-white" : "font-medium text-gray-700"}`}>
                          {p.title}
                        </p>
                        <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
                          {p.updated_at && (
                            <p className={`flex items-center gap-1 text-[10px] ${isActive ? "text-violet-300" : "text-gray-400"}`}>
                              <Clock className="h-2.5 w-2.5" />
                              {new Date(p.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                            </p>
                          )}
                          {status === "expired" && (
                            <span className={`text-[10px] font-bold ${isActive ? "text-red-300" : "text-red-600"}`}>Expired</span>
                          )}
                          {status === "critical" && (
                            <span className={`text-[10px] font-bold ${isActive ? "text-orange-300" : "text-orange-600"}`}>{days}d left</span>
                          )}
                          {status === "warning" && (
                            <span className={`text-[10px] font-semibold ${isActive ? "text-amber-300" : "text-amber-600"}`}>{days}d left</span>
                          )}
                        </div>
                      </div>
                      {(status === "expired" || status === "critical") && (
                        <AlertTriangle className={`w-3 h-3 shrink-0 mt-0.5 ${
                          isActive
                            ? status === "expired" ? "text-red-300" : "text-orange-300"
                            : status === "expired" ? "text-red-500" : "text-orange-500"
                        }`}/>
                      )}
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
                      {new Date(selected.updated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                    </p>
                  )}
                </div>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className={`shrink-0 flex items-center gap-1.5 rounded-xl px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50 ${
                    saved ? "bg-emerald-500 shadow-emerald-500/20" : "bg-violet-600 shadow-violet-500/20 hover:bg-violet-500"
                  }`}
                >
                  {saved ? <><CheckCircle2 className="h-3.5 w-3.5" /> Saved</> : saving ? "Saving…" : <><Save className="h-3.5 w-3.5" /> Save</>}
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

              {/* Expiry panel */}
              <ExpiryPanel policy={selected} onUpdate={handleExpiryUpdate} />

              {/* Acknowledgment panel */}
              <AcknowledgmentPanel policy={selected} currentUserEmail={currentUserEmail} />
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
        <PolicyTemplateGenerator policy={selected} onInsert={(c) => setContent(c)} />
      )}
    </div>
  );
}
