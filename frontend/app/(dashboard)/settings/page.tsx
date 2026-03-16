"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import type { AuditSession, BillingInfo, Company, NotificationSettings, TrustPageSettings } from "@/lib/types";
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
  Globe,
} from "lucide-react";
import React from "react";

// ── Toast ──────────────────────────────────────────────────────────────────────

function Toast({ msg, type = "success" }: { msg: string; type?: "success" | "error" }) {
  return (
    <div
      className={`fixed top-4 left-4 right-4 sm:top-5 sm:right-5 sm:left-auto sm:w-auto z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg border animate-slide-up text-sm font-medium
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

type SectionColor = "gray" | "brand" | "emerald" | "amber" | "red";
const sectionColorMap: Record<SectionColor, string> = {
  gray:    "bg-gray-50 border-gray-100 text-gray-500",
  brand:   "bg-brand-50 border-brand-100 text-brand-600",
  emerald: "bg-emerald-50 border-emerald-100 text-emerald-600",
  amber:   "bg-amber-50 border-amber-100 text-amber-600",
  red:     "bg-red-50 border-red-100 text-red-500",
};

function SectionHeader({
  icon: Icon,
  title,
  subtitle,
  color = "brand",
}: {
  icon: React.ElementType;
  title: string;
  subtitle?: string;
  color?: SectionColor;
}) {
  return (
    <div className="flex items-start gap-3 mb-5">
      <div className={`w-8 h-8 rounded-lg border flex items-center justify-center shrink-0 mt-0.5 ${sectionColorMap[color]}`}>
        <Icon className="w-4 h-4" />
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
  const defaultNotifSettings: NotificationSettings = {
    prefs: { training_overdue: true, access_review_overdue: true, vendor_needs_review: true, evidence_stale: true, weekly_digest: true },
    slack_webhook_url: null,
  };
  const [notifSettings, setNotifSettings] = useState<NotificationSettings>(defaultNotifSettings);
  const [notifLoading, setNotifLoading] = useState(false);

  useEffect(() => {
    api.getNotificationSettings().then(setNotifSettings).catch(() => {});
  }, []);

  const handleSaveNotifPrefs = async () => {
    setNotifLoading(true);
    try {
      await api.updateNotificationSettings(notifSettings);
      showToast("Notification preferences saved");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to save preferences", "error");
    } finally {
      setNotifLoading(false);
    }
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

  // ── Trust Center ───────────────────────────────────────────────────────────
  const [trustSettings, setTrustSettings] = useState<TrustPageSettings | null>(null);
  const [trustSaving, setTrustSaving] = useState(false);
  const [trustCopied, setTrustCopied] = useState(false);
  const [trustSlugInput, setTrustSlugInput] = useState("");

  useEffect(() => {
    if (!isAdmin) return;
    api.getTrustPageSettings().then((s) => {
      setTrustSettings(s);
      setTrustSlugInput(s.slug);
    }).catch(() => {});
  }, [isAdmin]);

  const handleSaveTrustSettings = async () => {
    if (!trustSettings) return;
    setTrustSaving(true);
    try {
      const updated = await api.updateTrustPageSettings({ ...trustSettings, slug: trustSlugInput });
      setTrustSettings(updated);
      setTrustSlugInput(updated.slug);
      showToast("Trust Center settings saved");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to save settings", "error");
    } finally {
      setTrustSaving(false);
    }
  };

  const copyTrustLink = () => {
    if (!trustSettings) return;
    navigator.clipboard.writeText(`${window.location.origin}/trust/${trustSettings.slug}`).then(() => {
      setTrustCopied(true);
      setTimeout(() => setTrustCopied(false), 2000);
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
    ...(isAdmin ? [{ id: "trust-center",  label: "Trust Center",   icon: Globe }] : []),
    { id: "your-data",     label: "Your Data",         icon: ShieldAlert },
  ];

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="overflow-x-hidden">
      {toast && <Toast msg={toast.msg} type={toast.type} />}

      {/* Page header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage your account and workspace.</p>
        </div>
        {billing && (
          <span className={`self-start sm:self-auto text-xs font-semibold px-3 py-1.5 rounded-full border ${
            billing.plan === "growth"
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-gray-50 text-gray-500 border-gray-200"
          }`}>
            {billing.plan === "growth" ? "✦ Growth" : "Free plan"}
          </span>
        )}
      </div>

      {/* ── Mobile / tablet horizontal section nav ────────────────────────── */}
      <div className="lg:hidden -mx-1 mb-5 overflow-x-auto no-scrollbar" style={{ maskImage: "linear-gradient(to right, black 88%, transparent 100%)" }}>
        <div className="flex gap-1.5 px-1 pb-0.5 w-max pr-6">
          {NAV.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => scrollTo(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                activeSection === id
                  ? "bg-gray-900 text-white shadow-sm"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200 hover:text-gray-700"
              }`}
            >
              <Icon className="w-3 h-3 shrink-0" />
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="lg:flex lg:gap-8 lg:items-start">

        {/* ── Desktop sticky sidebar nav ──────────────────────────────────── */}
        <aside className="hidden lg:block w-44 shrink-0 sticky top-8 self-start">
          <nav className="space-y-0.5">
            {NAV.map(({ id, label, icon: Icon }) => {
              const active = activeSection === id;
              return (
                <button
                  key={id}
                  onClick={() => scrollTo(id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm transition-all duration-100 text-left ${
                    active
                      ? "bg-white shadow-sm border border-gray-100 text-gray-900 font-semibold"
                      : "text-gray-500 hover:text-gray-800 font-medium hover:bg-white/60"
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
      <section id="profile" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
        <SectionHeader icon={UserIcon} title="Profile" color="brand" />
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
              className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {profileSaving ? "Saving…" : "Save profile"}
            </button>
          </div>
        </form>
      </section>

      {/* ── B. Security ─────────────────────────────────────────────────────── */}
      <section id="security" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
        <SectionHeader icon={Shield} title="Security" color="amber" />

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
              className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {pwSaving ? "Saving…" : "Update password"}
            </button>
          </div>
        </form>

        <div className="my-5 border-t border-gray-100" />

        {/* 2FA row */}
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800">Two-factor authentication</p>
            <p className="text-xs text-gray-500 mt-0.5">Add an extra layer of security to your account</p>
          </div>
          <span className="bg-gray-100 text-gray-500 text-xs px-2 py-0.5 rounded-full shrink-0">
            Coming soon
          </span>
        </div>
      </section>

      {/* ── C. Notifications ─────────────────────────────────────────────────── */}
      <section id="notifications" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
        <SectionHeader
          icon={Bell}
          title="Notifications"
          subtitle="Choose which alerts you receive from TraceLayer."
          color="brand"
        />

        <div className="space-y-4">
          {/* Weekly digest */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Weekly compliance digest</p>
              <p className="text-xs text-gray-500 mt-0.5">A compliance score briefing every Monday morning.</p>
            </div>
            <Toggle
              enabled={notifSettings.prefs.weekly_digest}
              onChange={(v) => setNotifSettings((s) => ({ ...s, prefs: { ...s.prefs, weekly_digest: v } }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Training overdue */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Training overdue</p>
              <p className="text-xs text-gray-500 mt-0.5">Alert when a training assignment is past its due date.</p>
            </div>
            <Toggle
              enabled={notifSettings.prefs.training_overdue}
              onChange={(v) => setNotifSettings((s) => ({ ...s, prefs: { ...s.prefs, training_overdue: v } }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Access review overdue */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Access review overdue</p>
              <p className="text-xs text-gray-500 mt-0.5">Alert when an access review passes its due date.</p>
            </div>
            <Toggle
              enabled={notifSettings.prefs.access_review_overdue}
              onChange={(v) => setNotifSettings((s) => ({ ...s, prefs: { ...s.prefs, access_review_overdue: v } }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Vendor needs review */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Vendor needs review</p>
              <p className="text-xs text-gray-500 mt-0.5">Alert when a vendor&apos;s review date has passed.</p>
            </div>
            <Toggle
              enabled={notifSettings.prefs.vendor_needs_review}
              onChange={(v) => setNotifSettings((s) => ({ ...s, prefs: { ...s.prefs, vendor_needs_review: v } }))}
            />
          </div>

          <div className="border-t border-gray-100" />

          {/* Evidence stale */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-800">Stale evidence</p>
              <p className="text-xs text-gray-500 mt-0.5">Alert when evidence hasn&apos;t been collected in over 7 days.</p>
            </div>
            <Toggle
              enabled={notifSettings.prefs.evidence_stale}
              onChange={(v) => setNotifSettings((s) => ({ ...s, prefs: { ...s.prefs, evidence_stale: v } }))}
            />
          </div>
        </div>

        {/* Slack webhook */}
        <div className="mt-5 pt-5 border-t border-gray-100">
          <p className="text-sm font-medium text-gray-800 mb-1">Slack webhook URL</p>
          <p className="text-xs text-gray-500 mb-2">Post alerts to a Slack channel. Leave blank to disable.</p>
          <input
            type="url"
            value={notifSettings.slack_webhook_url ?? ""}
            onChange={(e) => setNotifSettings((s) => ({ ...s, slack_webhook_url: e.target.value || null }))}
            placeholder="https://hooks.slack.com/services/…"
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
          />
        </div>

        <div className="flex justify-end mt-5">
          <button
            type="button"
            onClick={handleSaveNotifPrefs}
            disabled={notifLoading}
            className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {notifLoading ? "Saving…" : "Save preferences"}
          </button>
        </div>
      </section>

      {/* ── D. Weekly Compliance Report ──────────────────────────────────────── */}
      {isAdmin && (
        <section id="weekly-report" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader
            icon={Mail}
            title="Weekly Compliance Report"
            subtitle="Every Monday at 9 AM UTC all admins receive a compliance digest email with your scores, control status, and top action items."
            color="brand"
          />
          <div className="flex flex-wrap items-center justify-between gap-3 bg-brand-50 border border-brand-100 rounded-xl px-4 py-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-brand-800">Send preview to yourself</p>
              <p className="text-xs text-brand-600 mt-0.5">Get a sample of this week&apos;s report right now.</p>
            </div>
            <button
              onClick={handleSendPreview}
              disabled={weeklyLoading}
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              <Mail className="w-4 h-4" />
              {weeklyLoading ? "Sending…" : "Send preview"}
            </button>
          </div>
        </section>
      )}

      {/* ── E. Billing & Plan ────────────────────────────────────────────────── */}
      <section id="billing" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
        <SectionHeader icon={CreditCard} title="Billing &amp; Plan" color="emerald" />

        {billing ? (
          <div className="space-y-5">
            {/* Current plan status */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                {billing.plan === "growth" ? (
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold bg-emerald-100 text-emerald-700 px-3 py-1.5 rounded-full">
                    <Zap className="w-3 h-3" /> Growth
                  </span>
                ) : (
                  <span className="inline-flex items-center text-xs font-bold bg-gray-100 text-gray-500 px-3 py-1.5 rounded-full">
                    Free plan
                  </span>
                )}
                {billing.subscription_status && billing.plan === "growth" && (
                  <span className="text-xs text-gray-400 capitalize">
                    {billing.subscription_status.replace(/_/g, " ")}
                  </span>
                )}
              </div>
              {isAdmin && billing.plan === "growth" && (
                <button
                  onClick={handleManageBilling}
                  disabled={billingLoading}
                  className="text-sm font-medium text-gray-500 hover:text-gray-800 border border-gray-200 hover:border-gray-300 px-4 py-1.5 rounded-lg transition-colors disabled:opacity-60 shrink-0"
                >
                  {billingLoading ? "Loading…" : "Manage billing"}
                </button>
              )}
            </div>

            {/* Free plan upgrade card */}
            {billing.plan === "free" && (
              <div className="rounded-2xl border border-gray-100 bg-gradient-to-br from-slate-900 to-slate-800 overflow-hidden">
                {/* Header */}
                <div className="px-4 sm:px-6 pt-5 sm:pt-6 pb-4 border-b border-white/10">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-bold text-teal-400 uppercase tracking-widest mb-1">Growth Plan</p>
                      <div className="flex items-baseline gap-1">
                        <span className="text-3xl font-black text-white">$149</span>
                        <span className="text-sm text-white/40">/mo</span>
                      </div>
                    </div>
                    <div className="w-12 h-12 rounded-2xl bg-teal-500/15 border border-teal-500/30 flex items-center justify-center">
                      <Zap className="w-6 h-6 text-teal-400" />
                    </div>
                  </div>
                  <p className="text-sm text-white/50 mt-2">Everything you need to get certified and stay compliant.</p>
                </div>

                {/* Feature grid */}
                <div className="px-4 sm:px-6 py-4 grid grid-cols-1 sm:grid-cols-2 gap-y-2.5 gap-x-6">
                  {[
                    "Unlimited integrations",
                    "PDF & CSV reports",
                    "AI Compliance Advisor",
                    "AI Questionnaire Autofill",
                    "AI Audit Package",
                    "Trust Center (public page)",
                    "Unlimited team members",
                    "Priority support",
                  ].map((f) => (
                    <div key={f} className="flex items-center gap-2 text-sm text-white/70">
                      <div className="w-4 h-4 rounded-full bg-teal-500/20 flex items-center justify-center shrink-0">
                        <Zap className="w-2.5 h-2.5 text-teal-400" />
                      </div>
                      {f}
                    </div>
                  ))}
                </div>

                {/* CTA */}
                {isAdmin && (
                  <div className="px-4 sm:px-6 pb-5 sm:pb-6 pt-2">
                    <button
                      onClick={handleUpgrade}
                      disabled={billingLoading}
                      className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 disabled:opacity-60 text-white text-sm font-bold py-3 rounded-xl transition-all shadow-lg shadow-teal-900/30 hover:-translate-y-px active:translate-y-0"
                    >
                      <Zap className="w-4 h-4" />
                      {billingLoading ? "Opening checkout…" : "Upgrade to Growth — $149/mo"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Growth plan — current features summary */}
            {billing.plan === "growth" && (
              <div className="rounded-xl bg-emerald-50 border border-emerald-100 px-5 py-4">
                <p className="text-sm font-semibold text-emerald-800 mb-2">You&apos;re on Growth</p>
                <p className="text-xs text-emerald-700 leading-relaxed">
                  Unlimited integrations · PDF &amp; CSV reports · AI features · Trust Center · Unlimited team members
                </p>
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
        <section id="company" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader icon={Building2} title="Company" color="brand" />
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
                  className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
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
        <section id="auditor-access" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader
            icon={Eye}
            title="Auditor Access"
            subtitle="Generate read-only links you can share with auditors. No login required."
            color="brand"
          />

          {/* Create form */}
          <div className="flex flex-col sm:flex-row gap-2 mb-5">
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
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-3.5 py-2 rounded-lg transition-colors"
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
                <div key={s.id} className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-3 bg-gray-50 border border-gray-100 rounded-xl px-3.5 py-3">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{s.label || "Untitled link"}</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Created {new Date(s.created_at).toLocaleDateString()}
                      {s.expires_at && (
                        <> · Expires {new Date(s.expires_at).toLocaleDateString()}</>
                      )}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-1.5">
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

      {/* ── Trust Center (admin only) ────────────────────────────────────────── */}
      {isAdmin && (
        <section id="trust-center" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader
            icon={Globe}
            title="Trust Center"
            subtitle="A public page showing your live compliance posture to customers and investors."
            color="brand"
          />

          {trustSettings ? (
            <div className="space-y-5">
              {/* Enable toggle */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800">Enable Trust Center</p>
                  <p className="text-xs text-gray-500 mt-0.5">Make your compliance page publicly accessible.</p>
                </div>
                {billing?.plan === "growth" ? (
                  <Toggle
                    enabled={trustSettings.is_enabled}
                    onChange={(v) => setTrustSettings((s) => s ? { ...s, is_enabled: v } : s)}
                  />
                ) : (
                  <button
                    onClick={handleUpgrade}
                    className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    <Lock className="w-3 h-3" /> Growth only
                  </button>
                )}
              </div>

              <div className="border-t border-gray-100" />

              {/* Public URL */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Public URL</label>
                <div className="flex flex-wrap gap-2">
                  <div className="flex items-center border border-gray-200 rounded-lg overflow-hidden bg-white focus-within:ring-2 focus-within:ring-brand-500/30 focus-within:border-brand-400 transition-all flex-1 min-w-[160px]">
                    <span className="px-2.5 py-2 text-xs text-gray-400 bg-gray-50 border-r border-gray-200 whitespace-nowrap shrink-0">
                      /trust/
                    </span>
                    <input
                      type="text"
                      value={trustSlugInput}
                      onChange={(e) => setTrustSlugInput(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ""))}
                      className="flex-1 px-3 py-2 text-sm text-gray-900 bg-transparent outline-none min-w-0"
                      placeholder="your-company"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={copyTrustLink}
                      className="shrink-0 flex items-center gap-1.5 text-xs font-medium text-gray-600 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      {trustCopied
                        ? <><Check className="w-3.5 h-3.5 text-emerald-500" /> Copied</>
                        : <><Copy className="w-3.5 h-3.5" /> Copy</>
                      }
                    </button>
                    <a
                      href={`/trust/${trustSettings.slug}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="shrink-0 flex items-center gap-1.5 text-xs font-medium text-gray-600 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5" /> Preview
                    </a>
                  </div>
                </div>
              </div>

              <div className="border-t border-gray-100" />

              {/* Frameworks */}
              <div>
                <p className="text-xs font-medium text-gray-600 mb-2">Frameworks to display</p>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: "soc2", label: "SOC 2" },
                    { id: "iso27001", label: "ISO 27001" },
                    { id: "hipaa", label: "HIPAA" },
                    { id: "gdpr", label: "GDPR" },
                    { id: "pci_dss", label: "PCI DSS" },
                    { id: "ccpa", label: "CCPA" },
                    { id: "nist_csf", label: "NIST CSF" },
                  ].map((fw) => {
                    const active = trustSettings.frameworks.includes(fw.id);
                    return (
                      <button
                        key={fw.id}
                        type="button"
                        onClick={() => setTrustSettings((s) => {
                          if (!s) return s;
                          const next = active
                            ? s.frameworks.filter((f) => f !== fw.id)
                            : [...s.frameworks, fw.id];
                          return { ...s, frameworks: next.length > 0 ? next : s.frameworks };
                        })}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold transition-all border ${
                          active
                            ? "bg-brand-600 text-white border-brand-600"
                            : "bg-white text-gray-600 border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        {fw.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="border-t border-gray-100" />

              {/* Visibility toggles */}
              <div className="space-y-3.5">
                <p className="text-xs font-medium text-gray-600">What to show publicly</p>
                {(
                  [
                    { key: "show_score",        label: "Compliance scores",      desc: "Show framework scores and control breakdown" },
                    { key: "show_policies",     label: "Adopted policies",       desc: "List your security policy titles" },
                    { key: "show_integrations", label: "Connected integrations", desc: "Show which tools you use for evidence collection" },
                  ] as { key: keyof TrustPageSettings; label: string; desc: string }[]
                ).map(({ key, label, desc }) => (
                  <div key={key} className="flex items-center justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800">{label}</p>
                      <p className="text-xs text-gray-500">{desc}</p>
                    </div>
                    <Toggle
                      enabled={trustSettings[key] as boolean}
                      onChange={(v) => setTrustSettings((s) => s ? { ...s, [key]: v } : s)}
                    />
                  </div>
                ))}
              </div>

              <div className="border-t border-gray-100" />

              {/* Custom headline */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  Custom headline <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <input
                  type="text"
                  value={trustSettings.custom_headline ?? ""}
                  onChange={(e) => setTrustSettings((s) => s ? { ...s, custom_headline: e.target.value || null } : s)}
                  placeholder="e.g. Security-first cloud platform"
                  className={inputCls}
                  maxLength={120}
                />
              </div>

              {/* Custom message */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  Custom message <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <textarea
                  value={trustSettings.custom_message ?? ""}
                  onChange={(e) => setTrustSettings((s) => s ? { ...s, custom_message: e.target.value || null } : s)}
                  placeholder="Tell customers about your security program…"
                  className={`${inputCls} resize-none`}
                  rows={3}
                  maxLength={500}
                />
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={handleSaveTrustSettings}
                  disabled={trustSaving}
                  className="w-full sm:w-auto bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  {trustSaving ? "Saving…" : "Save Trust Center"}
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-16">
              <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </section>
      )}

      {/* ── H. Your Data (GDPR) ───────────────────────────────────────────────── */}
      <section id="your-data" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
        <SectionHeader icon={ShieldAlert} title="Your Data" color="red" />
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-800">Export all data</p>
              <p className="text-xs text-gray-500 mt-0.5">Download everything we hold about your account in JSON format.</p>
            </div>
            <button
              onClick={handleExport}
              disabled={gdprLoading}
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 text-sm font-medium text-gray-700 border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60"
            >
              <Download className="w-4 h-4" /> Export data
            </button>
          </div>

          {isAdmin && (
            <div className="border-t border-gray-100 pt-3">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-red-700">Delete account</p>
                  <p className="text-xs text-gray-500 mt-0.5">Permanently delete your company and all data. Irreversible.</p>
                </div>
                {deleteConfirm ? (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setDeleteConfirm(false)}
                      className="flex-1 sm:flex-none text-sm text-gray-500 hover:text-gray-700 border border-gray-200 px-3 py-2 rounded-lg"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDeleteAccount}
                      disabled={gdprLoading}
                      className="flex-1 sm:flex-none text-sm font-semibold text-white bg-red-600 hover:bg-red-700 px-3 py-2 rounded-lg disabled:opacity-60"
                    >
                      {gdprLoading ? "Deleting…" : "Confirm delete"}
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setDeleteConfirm(true)}
                    className="w-full sm:w-auto text-sm font-medium text-red-600 border border-red-200 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors"
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
