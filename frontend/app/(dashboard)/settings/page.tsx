"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import type { AuditSession, BillingInfo, Company } from "@/lib/types";
import {
  CreditCard,
  Lock,
  Building2,
  Zap,
  ShieldAlert,
  Download,
  Mail,
  Bell,
  Shield,
  User as UserIcon,
  Eye,
  ExternalLink,
  Trash2,
  Plus,
  Copy,
  Check,
  Settings,
} from "lucide-react";
import React from "react";

// ── Toast ──────────────────────────────────────────────────────────────────────

function Toast({ msg, type = "success" }: { msg: string; type?: "success" | "error" }) {
  return (
    <div
      className={`fixed top-5 right-5 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border animate-slide-up text-sm font-medium
      ${type === "error" ? "bg-white border-red-200 text-red-700" : "bg-white border-emerald-200 text-emerald-700"}`}
    >
      {type === "error" ? (
        <span className="w-2 h-2 rounded-full bg-red-500 shrink-0" />
      ) : (
        <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" />
      )}
      {msg}
    </div>
  );
}

// ── Section Header ─────────────────────────────────────────────────────────────

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
}: {
  icon: React.ElementType;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className="w-8 h-8 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center shrink-0 mt-0.5">
        <Icon className="w-4 h-4 text-gray-500" />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
        {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
      </div>
    </div>
  );
}

// ── Toggle ─────────────────────────────────────────────────────────────────────

function Toggle({ enabled, onChange }: { enabled: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200 focus:outline-none ${
        enabled ? "bg-brand-600" : "bg-gray-200"
      }`}
    >
      <span
        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ${
          enabled ? "translate-x-4" : "translate-x-0"
        }`}
      />
    </button>
  );
}

// ── Notification prefs helpers ─────────────────────────────────────────────────

const NOTIF_KEY = "tl_notif_prefs";

interface NotifPrefs {
  failures: boolean;
  score_drops: boolean;
  updates: boolean;
}

function loadNotifPrefs(): NotifPrefs {
  if (typeof window === "undefined") return { failures: true, score_drops: true, updates: true };
  try {
    const raw = localStorage.getItem(NOTIF_KEY);
    if (raw) return { failures: true, score_drops: true, updates: true, ...JSON.parse(raw) };
  } catch {
    // ignore
  }
  return { failures: true, score_drops: true, updates: true };
}

// ── Main Page ──────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);
  const showToast = (msg: string, type: "success" | "error" = "success") => {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3500);
  };

  // ── Profile ──────────────────────────────────────────────────────────────
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [profileSaving, setProfileSaving] = useState(false);

  useEffect(() => {
    setFullName(user?.full_name ?? "");
  }, [user?.full_name]);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    try {
      await api.updateProfile(fullName);
      showToast("Profile updated");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to update profile", "error");
    } finally {
      setProfileSaving(false);
    }
  };

  // ── Change Password ────────────────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwSaving, setPwSaving] = useState(false);
  const pwMismatch = pwForm.confirm.length > 0 && pwForm.next !== pwForm.confirm;

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) {
      showToast("New passwords do not match", "error");
      return;
    }
    setPwSaving(true);
    try {
      await api.changePassword(pwForm.current, pwForm.next);
      setPwForm({ current: "", next: "", confirm: "" });
      showToast("Password updated");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to update password", "error");
    } finally {
      setPwSaving(false);
    }
  };

  // ── Notifications ─────────────────────────────────────────────────────────
  const [notifPrefs, setNotifPrefs] = useState<NotifPrefs>({ failures: true, score_drops: true, updates: true });

  useEffect(() => {
    setNotifPrefs(loadNotifPrefs());
  }, []);

  const handleSaveNotifPrefs = () => {
    localStorage.setItem(NOTIF_KEY, JSON.stringify(notifPrefs));
    showToast("Notification preferences saved");
  };

  // ── Weekly report preview ──────────────────────────────────────────────────
  const [weeklyLoading, setWeeklyLoading] = useState(false);

  const handleSendPreview = async () => {
    setWeeklyLoading(true);
    try {
      await api.sendWeeklyPreview();
      showToast("Preview sent — check your inbox");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to send preview", "error");
    } finally {
      setWeeklyLoading(false);
    }
  };

  // ── Billing ───────────────────────────────────────────────────────────────
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [billingLoading, setBillingLoading] = useState(false);

  useEffect(() => {
    api.getSubscription().then(setBilling).catch(console.error);
  }, []);

  const handleUpgrade = async () => {
    setBillingLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      window.location.href = checkout_url;
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Could not open checkout", "error");
    } finally {
      setBillingLoading(false);
    }
  };

  const handleManageBilling = async () => {
    setBillingLoading(true);
    try {
      const { portal_url } = await api.getBillingPortal();
      window.open(portal_url, "_blank");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Could not open billing portal", "error");
    } finally {
      setBillingLoading(false);
    }
  };

  // ── Company ───────────────────────────────────────────────────────────────
  const [company, setCompany] = useState<Company | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [companySaving, setCompanySaving] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    api
      .getCompany()
      .then((c) => {
        setCompany(c);
        setCompanyName(c.name);
      })
      .catch(console.error);
  }, [isAdmin]);

  const handleUpdateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    setCompanySaving(true);
    try {
      const updated = await api.updateCompany(companyName);
      setCompany(updated);
      showToast("Company name updated");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to update company", "error");
    } finally {
      setCompanySaving(false);
    }
  };

  // ── GDPR ──────────────────────────────────────────────────────────────────
  const [gdprLoading, setGdprLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const handleExport = async () => {
    setGdprLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/v1/org/account/export`,
        { headers: { Authorization: `Bearer ${token}` } },
      );
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "tracelayer-data-export.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      showToast("Export failed — please try again", "error");
    } finally {
      setGdprLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    setGdprLoading(true);
    try {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/v1/org/account`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      });
      localStorage.clear();
      window.location.href = "/";
    } catch {
      showToast("Deletion failed — please try again", "error");
      setGdprLoading(false);
    }
  };

  // ── Audit Sessions ─────────────────────────────────────────────────────────
  const [auditSessions, setAuditSessions] = useState<AuditSession[]>([]);
  const [auditLabel, setAuditLabel] = useState("");
  const [auditCreating, setAuditCreating] = useState(false);
  const [auditCopied, setAuditCopied] = useState<string | null>(null);

  useEffect(() => {
    if (!isAdmin) return;
    api.getAuditSessions().then(setAuditSessions).catch(() => {});
  }, [isAdmin]);

  const handleCreateAuditLink = async () => {
    setAuditCreating(true);
    try {
      const session = await api.createAuditSession(auditLabel || undefined, 90);
      setAuditSessions((prev) => [session, ...prev]);
      setAuditLabel("");
      showToast("Auditor link created");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to create link", "error");
    } finally {
      setAuditCreating(false);
    }
  };

  const handleRevokeAuditSession = async (id: string) => {
    try {
      await api.revokeAuditSession(id);
      setAuditSessions((prev) => prev.filter((s) => s.id !== id));
      showToast("Auditor link revoked");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to revoke link", "error");
    }
  };

  const copyAuditLink = (token: string) => {
    const url = `${window.location.origin}/auditor/${token}`;
    navigator.clipboard.writeText(url).then(() => {
      setAuditCopied(token);
      setTimeout(() => setAuditCopied(null), 2000);
    });
  };

  // ── Input class helper ────────────────────────────────────────────────────
  const inputCls =
    "w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400 bg-white text-gray-900 placeholder:text-gray-400 transition-all";

  // ── Desktop nav / active section tracking ────────────────────────────────
  const [activeSection, setActiveSection] = useState("profile");
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sections = contentRef.current?.querySelectorAll("section[id]");
    if (!sections) return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => { if (e.isIntersecting) setActiveSection(e.target.id); });
      },
      { rootMargin: "-20% 0px -70% 0px", threshold: 0 }
    );
    sections.forEach((s) => observer.observe(s));
    return () => observer.disconnect();
  }, [isAdmin]);

  const NAV = [
    { id: "profile",       label: "Profile",          icon: UserIcon  },
    { id: "security",      label: "Security",          icon: Shield    },
    { id: "notifications", label: "Notifications",     icon: Bell      },
    ...(isAdmin ? [{ id: "weekly-report", label: "Weekly Report", icon: Mail }] : []),
    { id: "billing",       label: "Billing & Plan",    icon: CreditCard },
    ...(isAdmin ? [{ id: "company", label: "Company", icon: Building2 }] : []),
    ...(isAdmin ? [{ id: "auditor-access", label: "Auditor Access", icon: Eye }] : []),
    { id: "your-data",     label: "Your Data",         icon: ShieldAlert },
  ];

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div>
      {toast && <Toast msg={toast.msg} type={toast.type} />}

      {/* Dark hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-5 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-slate-500/20 flex items-center justify-center shrink-0">
              <Settings className="w-5 h-5 text-slate-300"/>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white leading-tight">Settings</h1>
              <p className="text-sm text-slate-400">Manage your account and workspace.</p>
            </div>
          </div>
          {billing && (
            <span className={`text-xs font-bold px-3 py-1.5 rounded-full ${billing.plan === "growth" ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" : "bg-white/10 text-slate-400 border border-white/10"}`}>
              {billing.plan === "growth" ? "✦ Growth" : "Free plan"}
            </span>
          )}
        </div>
      </div>

      <div className="lg:flex lg:gap-8 lg:items-start">

        {/* ── Desktop sticky sidebar nav ──────────────────────────────────── */}
        <aside className="hidden lg:block w-48 shrink-0 sticky top-8 self-start">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3 px-2">Settings</p>
          <nav className="space-y-0.5">
            {NAV.map(({ id, label, icon: Icon }) => {
              const active = activeSection === id;
              return (
                <button
                  key={id}
                  onClick={() => scrollTo(id)}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-100 text-left ${
                    active
                      ? "bg-brand-50 text-brand-700"
                      : "text-gray-500 hover:text-gray-800 hover:bg-white"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 shrink-0 ${active ? "text-brand-600" : "text-gray-400"}`} />
                  {label}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* ── Main content ─────────────────────────────────────────────────── */}
        <div ref={contentRef} className="flex-1 min-w-0 max-w-2xl space-y-5">

      {/* ── A. Profile ──────────────────────────────────────────────────────── */}
      <section id="profile" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
        <SectionHeader icon={UserIcon} title="Profile" />
        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Full name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Your full name"
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">
              Email address
              <span className="ml-2">
                {user?.email_verified ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Verified
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                    Unverified
                  </span>
                )}
              </span>
            </label>
            <input
              type="email"
              value={user?.email ?? ""}
              readOnly
              className={`${inputCls} bg-gray-50 text-gray-500 cursor-default`}
            />
          </div>
          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={profileSaving}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {profileSaving ? "Saving…" : "Save profile"}
            </button>
          </div>
        </form>
      </section>

      {/* ── B. Security ─────────────────────────────────────────────────────── */}
      <section id="security" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
        <SectionHeader icon={Shield} title="Security" />

        {/* Change password */}
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Current password</label>
            <input
              type="password"
              required
              value={pwForm.current}
              onChange={(e) => setPwForm((f) => ({ ...f, current: e.target.value }))}
              className={inputCls}
              placeholder="••••••••"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">New password</label>
            <input
              type="password"
              required
              minLength={8}
              value={pwForm.next}
              onChange={(e) => setPwForm((f) => ({ ...f, next: e.target.value }))}
              className={inputCls}
              placeholder="Min. 8 characters"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1.5">Confirm new password</label>
            <input
              type="password"
              required
              minLength={8}
              value={pwForm.confirm}
              onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
              className={`${inputCls} ${pwMismatch ? "border-red-300 focus:ring-red-400" : ""}`}
              placeholder="Repeat new password"
            />
            {pwMismatch && (
              <p className="text-xs text-red-600 mt-1">Passwords do not match.</p>
            )}
          </div>
          <div className="flex justify-end pt-1">
            <button
              type="submit"
              disabled={pwSaving || pwMismatch}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {pwSaving ? "Saving…" : "Update password"}
            </button>
          </div>
        </form>

        <div className="my-5 border-t border-gray-100" />

        {/* 2FA row */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-gray-800">Two-factor authentication</p>
            <p className="text-xs text-gray-500 mt-0.5">Add an extra layer of security to your account</p>
          </div>
          <span className="bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full shrink-0">
            Coming soon
          </span>
        </div>
      </section>

      {/* ── C. Notifications ─────────────────────────────────────────────────── */}
      <section id="notifications" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
        <SectionHeader
          icon={Bell}
          title="Notifications"
          subtitle="Choose which emails you receive from TraceLayer."
        />

        <div className="space-y-4">
          {/* Weekly digest — locked ON */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1.5">
                <p className="text-sm font-medium text-gray-800">Weekly compliance digest</p>
                <Lock className="w-3 h-3 text-gray-400 shrink-0" />
              </div>
              <p className="text-xs text-gray-500 mt-0.5">A compliance score briefing every Monday morning.</p>
            </div>
            <Toggle enabled={true} onChange={() => {}} />
          </div>

          <div className="border-t border-gray-100" />

          {/* Collection failures */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Collection failures</p>
              <p className="text-xs text-gray-500 mt-0.5">Alert when an integration fails to collect evidence.</p>
            </div>
            <Toggle
              enabled={notifPrefs.failures}
              onChange={(v) => setNotifPrefs((p) => ({ ...p, failures: v }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Score drop alerts */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Score drop alerts</p>
              <p className="text-xs text-gray-500 mt-0.5">Email when your compliance score drops more than 10 points.</p>
            </div>
            <Toggle
              enabled={notifPrefs.score_drops}
              onChange={(v) => setNotifPrefs((p) => ({ ...p, score_drops: v }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Product updates */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Product updates</p>
              <p className="text-xs text-gray-500 mt-0.5">New features, improvements, and important announcements.</p>
            </div>
            <Toggle
              enabled={notifPrefs.updates}
              onChange={(v) => setNotifPrefs((p) => ({ ...p, updates: v }))}
            />
          </div>
        </div>

        <div className="flex justify-end mt-5">
          <button
            type="button"
            onClick={handleSaveNotifPrefs}
            className="bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Save preferences
          </button>
        </div>
      </section>

      {/* ── D. Weekly Compliance Report ──────────────────────────────────────── */}
      {isAdmin && (
        <section id="weekly-report" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
          <SectionHeader
            icon={Mail}
            title="Weekly Compliance Report"
            subtitle="Every Monday at 9 AM UTC all admins receive a compliance digest email with your scores, control status, and top action items."
          />
          <div className="flex items-center justify-between gap-4 bg-brand-50 border border-brand-100 rounded-xl px-4 py-3">
            <div>
              <p className="text-sm font-medium text-brand-800">Send preview to yourself</p>
              <p className="text-xs text-brand-600 mt-0.5">Get a sample of this week&apos;s report right now.</p>
            </div>
            <button
              onClick={handleSendPreview}
              disabled={weeklyLoading}
              className="shrink-0 flex items-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              <Mail className="w-4 h-4" />
              {weeklyLoading ? "Sending…" : "Send preview"}
            </button>
          </div>
        </section>
      )}

      {/* ── E. Billing & Plan ────────────────────────────────────────────────── */}
      <section id="billing" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
        <SectionHeader icon={CreditCard} title="Billing &amp; Plan" />

        {billing ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center gap-2">
                  {billing.plan === "growth" ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold bg-emerald-100 text-emerald-700 px-2.5 py-1 rounded-full">
                      <Zap className="w-3 h-3" /> Growth
                    </span>
                  ) : (
                    <span className="inline-flex items-center text-xs font-semibold bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
                      Free
                    </span>
                  )}
                  {billing.subscription_status && (
                    <span className="text-xs text-gray-400 capitalize">
                      {billing.subscription_status.replace("_", " ")}
                    </span>
                  )}
                </div>
                {billing.plan === "free" && (
                  <p className="text-sm text-gray-500 mt-1">Up to 3 integrations. Upgrade for unlimited access.</p>
                )}
                {billing.plan === "growth" && (
                  <p className="text-sm text-gray-500 mt-1">Unlimited integrations, AI advisor, priority support.</p>
                )}
              </div>

              {isAdmin &&
                (billing.plan === "free" ? (
                  <button
                    onClick={handleUpgrade}
                    disabled={billingLoading}
                    className="flex items-center gap-1.5 bg-[var(--accent)] hover:opacity-90 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-opacity"
                  >
                    <Zap className="w-4 h-4" />
                    {billingLoading ? "Loading…" : "Upgrade to Growth"}
                  </button>
                ) : (
                  <button
                    onClick={handleManageBilling}
                    disabled={billingLoading}
                    className="text-sm font-medium text-gray-600 hover:text-gray-900 border border-gray-300 px-4 py-2 rounded-lg transition-colors disabled:opacity-60"
                  >
                    {billingLoading ? "Loading…" : "Manage billing"}
                  </button>
                ))}
            </div>

            {billing.plan === "free" && (
              <div className="bg-gradient-to-r from-teal-50 to-emerald-50 border border-teal-200 rounded-lg p-4">
                <p className="text-sm font-semibold text-teal-800 mb-1">Growth plan — $49/mo</p>
                <ul className="text-sm text-teal-700 space-y-0.5">
                  <li>✓ Unlimited integrations</li>
                  <li>✓ AI Compliance Advisor</li>
                  <li>✓ SOC 2, ISO 27001 &amp; GDPR frameworks</li>
                  <li>✓ Priority support</li>
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center justify-center h-12">
            <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </section>

      {/* ── F. Company (admin only) ───────────────────────────────────────────── */}
      {isAdmin && (
        <section id="company" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
          <SectionHeader icon={Building2} title="Company" />
          {company ? (
            <form onSubmit={handleUpdateCompany} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Company name</label>
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className={inputCls}
                />
              </div>
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={companySaving}
                  className="bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  {companySaving ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          ) : (
            <div className="flex items-center justify-center h-16">
              <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </section>
      )}

      {/* ── G. Auditor Access (admin only) ───────────────────────────────────── */}
      {isAdmin && (
        <section id="auditor-access" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
          <SectionHeader
            icon={Eye}
            title="Auditor Access"
            subtitle="Generate read-only links you can share with auditors. No login required."
          />

          {/* Create form */}
          <div className="flex gap-2 mb-5">
            <input
              type="text"
              value={auditLabel}
              onChange={(e) => setAuditLabel(e.target.value)}
              placeholder="Label (e.g. SOC 2 Audit 2025)"
              className={`${inputCls} flex-1`}
              onKeyDown={(e) => { if (e.key === "Enter") handleCreateAuditLink(); }}
            />
            <button
              onClick={handleCreateAuditLink}
              disabled={auditCreating}
              className="shrink-0 flex items-center gap-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-3.5 py-2 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              {auditCreating ? "Creating…" : "Create link"}
            </button>
          </div>

          {/* Sessions list */}
          {auditSessions.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-4">No auditor links yet. Create one above.</p>
          ) : (
            <div className="space-y-2">
              {auditSessions.map((s) => (
                <div key={s.id} className="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl px-3.5 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{s.label || "Untitled link"}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Created {new Date(s.created_at).toLocaleDateString()}
                      {s.expires_at && (
                        <> · Expires {new Date(s.expires_at).toLocaleDateString()}</>
                      )}
                    </p>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => copyAuditLink(s.token)}
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 bg-white border border-gray-200 px-2.5 py-1.5 rounded-lg transition-colors"
                    >
                      {auditCopied === s.token
                        ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</>
                        : <><Copy className="w-3.5 h-3.5" /> Copy link</>
                      }
                    </button>
                    <a
                      href={`/auditor/${s.token}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 bg-white border border-gray-200 px-2.5 py-1.5 rounded-lg transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" /> Preview
                    </a>
                    <button
                      onClick={() => handleRevokeAuditSession(s.id)}
                      className="flex items-center gap-1 text-xs text-red-500 hover:text-red-700 bg-white border border-red-100 hover:border-red-200 px-2.5 py-1.5 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-3.5 h-3.5" /> Revoke
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ── H. Your Data (GDPR) ───────────────────────────────────────────────── */}
      <section id="your-data" className="rounded-2xl border border-gray-100 shadow-card bg-white p-6 scroll-mt-8">
        <SectionHeader icon={ShieldAlert} title="Your Data" />
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">Export all data</p>
              <p className="text-xs text-gray-500 mt-0.5">Download everything we hold about your account in JSON format.</p>
            </div>
            <button
              onClick={handleExport}
              disabled={gdprLoading}
              className="flex items-center gap-1.5 text-sm font-medium text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60 shrink-0 ml-4"
            >
              <Download className="w-4 h-4" /> Export
            </button>
          </div>

          {isAdmin && (
            <div className="border-t border-gray-100 pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-red-700">Delete account</p>
                  <p className="text-xs text-gray-500 mt-0.5">Permanently delete your company and all data. Irreversible.</p>
                </div>
                {deleteConfirm ? (
                  <div className="flex gap-2 ml-4 shrink-0">
                    <button
                      onClick={() => setDeleteConfirm(false)}
                      className="text-xs text-gray-500 hover:text-gray-700 px-2 py-1"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDeleteAccount}
                      disabled={gdprLoading}
                      className="text-xs font-semibold text-white bg-red-600 hover:bg-red-700 px-3 py-1.5 rounded-lg disabled:opacity-60"
                    >
                      {gdprLoading ? "Deleting…" : "Confirm delete"}
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(true)}
                    className="text-sm font-medium text-red-600 border border-red-200 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors shrink-0 ml-4"
                  >
                    Delete account
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </section>

        </div>{/* end content */}
      </div>{/* end lg:flex */}
    </div>
  );
}
