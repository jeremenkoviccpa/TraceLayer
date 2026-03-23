"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { openPaddleCheckout } from "@/lib/paddle";
import { useAuth } from "@/components/auth-provider";
import type { ApiKey, AuditSession, BillingInfo, Company, NotificationSettings, TrustAnalytics, TrustPageSettings } from "@/lib/types";
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
  Smartphone,
  KeyRound,
  Key,
  AlertCircle,
  LogIn,
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

  // ── SSO ───────────────────────────────────────────────────────────────────
  const [ssoConfig, setSsoConfig] = useState<{ id: string; enabled: boolean; domain: string; issuer: string; client_id: string; scopes: string } | null>(null);
  const [ssoLoading, setSsoLoading] = useState(false);
  const [ssoSaving, setSsoSaving] = useState(false);
  const [ssoForm, setSsoForm] = useState({ domain: "", issuer: "", client_id: "", client_secret: "", scopes: "openid email profile" });
  const [ssoShowForm, setSsoShowForm] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    api.getSSOConfig().then(setSsoConfig).catch(() => setSsoConfig(null));
  }, [isAdmin]);

  const handleSSOSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSsoSaving(true);
    try {
      const saved = await api.upsertSSOConfig(ssoForm) as { id: string; enabled: boolean; domain: string; issuer: string; client_id: string; scopes: string };
      setSsoConfig(saved);
      setSsoShowForm(false);
      setSsoForm({ domain: "", issuer: "", client_id: "", client_secret: "", scopes: "openid email profile" });
      showToast("SSO configured successfully");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to save SSO config", "error");
    } finally {
      setSsoSaving(false);
    }
  };

  const handleSSOToggle = async () => {
    if (!ssoConfig) return;
    setSsoLoading(true);
    try {
      await api.toggleSSO(!ssoConfig.enabled);
      setSsoConfig({ ...ssoConfig, enabled: !ssoConfig.enabled });
    } catch {
      showToast("Failed to update SSO", "error");
    } finally {
      setSsoLoading(false);
    }
  };

  const handleSSODelete = async () => {
    if (!confirm("Remove SSO configuration? Users will fall back to password or Google login.")) return;
    setSsoLoading(true);
    try {
      await api.deleteSSOConfig();
      setSsoConfig(null);
      showToast("SSO configuration removed");
    } catch {
      showToast("Failed to remove SSO", "error");
    } finally {
      setSsoLoading(false);
    }
  };

  // ── 2FA ───────────────────────────────────────────────────────────────────
  const [twoFAEnabled, setTwoFAEnabled] = useState(user?.totp_enabled ?? false);
  const [twoFAStep, setTwoFAStep] = useState<"idle" | "setup" | "enable-confirm" | "disable-confirm" | "backup-regen">("idle");
  const [twoFASetupData, setTwoFASetupData] = useState<{ secret: string; qr_uri: string; backup_codes: string[] } | null>(null);
  const [twoFACode, setTwoFACode] = useState("");
  const [twoFAPassword, setTwoFAPassword] = useState("");
  const [twoFALoading, setTwoFALoading] = useState(false);
  const [twoFABackupCodes, setTwoFABackupCodes] = useState<string[] | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null);
  const [twoFACodeCopied, setTwoFACodeCopied] = useState(false);

  useEffect(() => {
    setTwoFAEnabled(user?.totp_enabled ?? false);
  }, [user?.totp_enabled]);

  useEffect(() => {
    if (!twoFASetupData?.qr_uri) { setQrDataUrl(null); return; }
    import("qrcode").then((QRCode) => {
      QRCode.toDataURL(twoFASetupData.qr_uri, { width: 200, margin: 1 }).then(setQrDataUrl);
    }).catch(() => setQrDataUrl(null));
  }, [twoFASetupData?.qr_uri]);

  const handleSetup2FA = useCallback(async () => {
    setTwoFALoading(true);
    try {
      const data = await api.setup2FA();
      setTwoFASetupData(data);
      setTwoFAStep("setup");
      setTwoFACode("");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to set up 2FA", "error");
    } finally {
      setTwoFALoading(false);
    }
  }, []);

  const handleEnable2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setTwoFALoading(true);
    try {
      await api.enable2FA(twoFACode);
      setTwoFAEnabled(true);
      setTwoFAStep("idle");
      setTwoFASetupData(null);
      setTwoFACode("");
      showToast("Two-factor authentication enabled");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Invalid code — try again", "error");
    } finally {
      setTwoFALoading(false);
    }
  };

  const handleDisable2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setTwoFALoading(true);
    try {
      await api.disable2FA(twoFAPassword);
      setTwoFAEnabled(false);
      setTwoFAStep("idle");
      setTwoFAPassword("");
      showToast("Two-factor authentication disabled");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Incorrect password", "error");
    } finally {
      setTwoFALoading(false);
    }
  };

  const handleRegenBackupCodes = async (e: React.FormEvent) => {
    e.preventDefault();
    setTwoFALoading(true);
    try {
      const data = await api.regenerateBackupCodes(twoFAPassword);
      setTwoFABackupCodes(data.backup_codes);
      setTwoFAStep("idle");
      setTwoFAPassword("");
      showToast("New backup codes generated — save them now");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Incorrect password", "error");
    } finally {
      setTwoFALoading(false);
    }
  };

  // ── Notifications ─────────────────────────────────────────────────────────
  const defaultNotifSettings: NotificationSettings = {
    prefs: { training_overdue: true, access_review_overdue: true, vendor_needs_review: true, evidence_stale: true, weekly_digest: true },
    slack_webhook_url: null,
    teams_webhook_url: null,
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
      await openPaddleCheckout(checkout_url);
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
      const data = await api.exportAccountData();
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
      await api.deleteAccount();
      localStorage.clear();
      window.location.href = "/";
    } catch {
      showToast("Deletion failed — please try again", "error");
      setGdprLoading(false);
    }
  };

  // ── API Keys ──────────────────────────────────────────────────────────────
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [apiKeyName, setApiKeyName] = useState("");
  const [apiKeyCreating, setApiKeyCreating] = useState(false);
  const [newRawKey, setNewRawKey] = useState<string | null>(null);
  const [apiKeyCopied, setApiKeyCopied] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    api.getApiKeys().then(setApiKeys).catch(() => {});
  }, [isAdmin]);

  const handleCreateApiKey = async () => {
    if (!apiKeyName.trim()) return;
    setApiKeyCreating(true);
    try {
      const data = await api.createApiKey(apiKeyName.trim());
      const newKey: ApiKey = { id: data.id, name: data.name, key_prefix: data.key_prefix, created_at: data.created_at, last_used_at: null };
      setApiKeys((prev) => [newKey, ...prev]);
      setApiKeyName("");
      setNewRawKey(data.raw_key);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to create API key", "error");
    } finally {
      setApiKeyCreating(false);
    }
  };

  const handleRevokeApiKey = async (id: string) => {
    if (!confirm("Revoke this API key? This cannot be undone.")) return;
    try {
      await api.revokeApiKey(id);
      setApiKeys((prev) => prev.filter((k) => k.id !== id));
      showToast("API key revoked");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to revoke key", "error");
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
  const [trustDomainInput, setTrustDomainInput] = useState("");
  const [trustAnalytics, setTrustAnalytics] = useState<TrustAnalytics | null>(null);
  const [trustAnalyticsOpen, setTrustAnalyticsOpen] = useState(false);
  const [domainVerifying, setDomainVerifying] = useState(false);
  const [slackConfig, setSlackConfig] = useState<import("@/lib/types").SlackConfig | null>(null);
  const [slackWebhook, setSlackWebhook] = useState("");
  const [slackChannel, setSlackChannel] = useState("");
  const [slackEnabled, setSlackEnabled] = useState(true);
  const [slackSaving, setSlackSaving] = useState(false);
  const [slackTesting, setSlackTesting] = useState(false);
  const [slackSending, setSlackSending] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    api.getSlackConfig().then(cfg => {
      if (cfg) {
        setSlackConfig(cfg);
        setSlackWebhook(cfg.webhook_url);
        setSlackChannel(cfg.channel_name ?? "");
        setSlackEnabled(cfg.reminder_enabled);
      }
    }).catch(() => {});
  }, [isAdmin]);

  const handleSaveSlack = async () => {
    if (!slackWebhook.trim()) return;
    setSlackSaving(true);
    try {
      const cfg = await api.saveSlackConfig({ webhook_url: slackWebhook.trim(), channel_name: slackChannel.trim() || undefined, reminder_enabled: slackEnabled });
      setSlackConfig(cfg);
      showToast("Slack config saved");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Save failed", "error");
    } finally {
      setSlackSaving(false);
    }
  };

  const handleTestSlack = async () => {
    setSlackTesting(true);
    try {
      const res = await api.testSlackWebhook();
      showToast(res.message, res.ok ? "success" : "error");
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Test failed", "error");
    } finally {
      setSlackTesting(false);
    }
  };

  const handleSendReminders = async () => {
    setSlackSending(true);
    try {
      const res = await api.sendSlackReminders();
      showToast(res.message, res.ok ? "success" : "error");
      if (res.ok) {
        const cfg = await api.getSlackConfig();
        if (cfg) setSlackConfig(cfg);
      }
    } catch (e: unknown) {
      showToast(e instanceof Error ? e.message : "Send failed", "error");
    } finally {
      setSlackSending(false);
    }
  };

  useEffect(() => {
    if (!isAdmin) return;
    api.getTrustPageSettings().then((s) => {
      setTrustSettings(s);
      setTrustSlugInput(s.slug);
      setTrustDomainInput(s.custom_domain ?? "");
    }).catch(() => {});
  }, [isAdmin]);

  const loadTrustAnalytics = async () => {
    try {
      const a = await api.getTrustAnalytics();
      setTrustAnalytics(a);
      setTrustAnalyticsOpen(true);
    } catch {
      showToast("Failed to load analytics", "error");
    }
  };

  const handleVerifyDomain = async () => {
    if (!trustSettings?.custom_domain) return;
    setDomainVerifying(true);
    try {
      const result = await api.verifyTrustDomain();
      showToast(result.message, result.verified ? undefined : "error");
      if (result.verified) {
        setTrustSettings(s => s ? { ...s, domain_verified: true } : s);
      }
    } catch {
      showToast("Verification failed", "error");
    } finally {
      setDomainVerifying(false);
    }
  };

  const handleSaveTrustSettings = async () => {
    if (!trustSettings) return;
    setTrustSaving(true);
    try {
      const updated = await api.updateTrustPageSettings({
        ...trustSettings,
        slug: trustSlugInput,
        custom_domain: trustDomainInput.trim() || null,
      });
      setTrustSettings(updated);
      setTrustSlugInput(updated.slug);
      setTrustDomainInput(updated.custom_domain ?? "");
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
    ...(isAdmin ? [{ id: "sso", label: "Single Sign-On", icon: LogIn }] : []),
    { id: "notifications", label: "Notifications",     icon: Bell      },
    ...(isAdmin ? [{ id: "weekly-report", label: "Weekly Report", icon: Mail }] : []),
    { id: "billing",       label: "Billing & Plan",    icon: CreditCard },
    ...(isAdmin ? [{ id: "company", label: "Company", icon: Building2 }] : []),
    ...(isAdmin ? [{ id: "auditor-access", label: "Auditor Access", icon: Eye }] : []),
    ...(isAdmin ? [{ id: "trust-center",  label: "Trust Center",   icon: Globe }] : []),
    ...(isAdmin ? [{ id: "slack-bot",     label: "Slack Bot",       icon: Bell  }] : []),
    { id: "your-data",     label: "Your Data",         icon: ShieldAlert },
  ];

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="overflow-x-hidden">
      {toast && <Toast msg={toast.msg} type={toast.type} />}

      {/* Page header */}
      <div className="flex items-start justify-between gap-3 mb-6">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-gray-900">Settings</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage your account and workspace.</p>
        </div>
        {billing && (
          <span className={`shrink-0 mt-0.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${
            billing.plan === "growth"
              ? "bg-emerald-50 text-emerald-700 border-emerald-200"
              : "bg-gray-50 text-gray-500 border-gray-200"
          }`}>
            {billing.plan === "growth" ? "✦ Growth" : "Free"}
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

        {/* 2FA section */}
        <div className="rounded-xl border border-gray-100 bg-gray-50/50 overflow-hidden">

          {/* Header row */}
          <div className="flex items-center justify-between gap-4 px-4 py-3.5">
            <div className="flex items-center gap-3 min-w-0">
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${twoFAEnabled ? "bg-emerald-100 text-emerald-600" : "bg-gray-100 text-gray-400"}`}>
                <Smartphone className="w-4 h-4" />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900">Two-factor authentication</p>
                <p className="text-xs text-gray-500 mt-0.5 leading-snug">
                  {twoFAEnabled
                    ? <span className="inline-flex items-center gap-1.5 text-emerald-600 font-medium"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />Authenticator app enabled</span>
                    : "Protect your account with an authenticator app"}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              {twoFAEnabled ? (
                <>
                  <button
                    onClick={() => { setTwoFAStep("backup-regen"); setTwoFAPassword(""); setTwoFABackupCodes(null); }}
                    className="text-xs text-gray-500 hover:text-gray-800 px-3 py-1.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 transition-colors font-medium"
                  >
                    Backup codes
                  </button>
                  <button
                    onClick={() => { setTwoFAStep("disable-confirm"); setTwoFAPassword(""); }}
                    className="text-xs text-red-500 hover:text-red-700 px-3 py-1.5 rounded-lg border border-red-100 bg-white hover:bg-red-50 transition-colors font-medium"
                  >
                    Disable
                  </button>
                </>
              ) : (
                <button
                  onClick={handleSetup2FA}
                  disabled={twoFALoading}
                  className="text-xs bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white px-4 py-1.5 rounded-lg transition-colors font-semibold shadow-sm"
                >
                  {twoFALoading ? "Loading…" : "Set up 2FA"}
                </button>
              )}
            </div>
          </div>

          {/* Setup panel */}
          {twoFAStep === "setup" && twoFASetupData && (
            <div className="border-t border-gray-100 bg-white">
              {/* Step indicators */}
              <div className="flex items-center gap-0 px-5 pt-5 pb-4">
                {["Scan QR code", "Save backup codes", "Verify"].map((s, i) => (
                  <React.Fragment key={s}>
                    <div className="flex items-center gap-2">
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 ${i === 0 ? "bg-brand-600 text-white" : i === 1 ? (twoFACode.length > 0 ? "bg-brand-600 text-white" : "bg-gray-200 text-gray-500") : "bg-gray-200 text-gray-500"}`}>{i + 1}</div>
                      <span className="text-xs text-gray-500 hidden sm:block whitespace-nowrap">{s}</span>
                    </div>
                    {i < 2 && <div className="flex-1 h-px bg-gray-200 mx-2 min-w-[16px]" />}
                  </React.Fragment>
                ))}
              </div>

              <div className="px-5 pb-5 space-y-5">
                {/* QR + key */}
                <div className="flex flex-col sm:flex-row gap-5">
                  {/* QR code */}
                  <div className="shrink-0 flex flex-col items-center gap-2">
                    {qrDataUrl ? (
                      <div className="p-2 bg-white rounded-xl border border-gray-200 shadow-sm">
                        <img src={qrDataUrl} alt="TOTP QR code" className="w-40 h-40 block" />
                      </div>
                    ) : (
                      <div className="w-44 h-44 rounded-xl border border-gray-200 bg-gray-50 flex items-center justify-center">
                        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
                      </div>
                    )}
                    <p className="text-[10px] text-gray-400 text-center">Scan with Google Authenticator,<br />Authy, or 1Password</p>
                  </div>

                  {/* Manual key + backup codes */}
                  <div className="flex-1 space-y-4 min-w-0">
                    <div>
                      <p className="text-xs font-semibold text-gray-700 mb-1.5">Can&apos;t scan? Enter this key manually</p>
                      <div className="flex items-center gap-2">
                        <code className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs font-mono text-gray-800 break-all leading-relaxed">{twoFASetupData.secret}</code>
                        <button
                          type="button"
                          onClick={() => { navigator.clipboard.writeText(twoFASetupData.secret); setTwoFACodeCopied(true); setTimeout(() => setTwoFACodeCopied(false), 2000); }}
                          className="shrink-0 w-8 h-8 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 text-gray-400 hover:text-gray-700 transition-colors flex items-center justify-center"
                          title="Copy secret"
                        >
                          {twoFACodeCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <p className="text-xs font-semibold text-gray-700">Backup codes</p>
                        <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">Save these — shown once</span>
                      </div>
                      <div className="grid grid-cols-2 gap-1.5 p-3 bg-gray-50 rounded-xl border border-gray-200">
                        {twoFASetupData.backup_codes.map((code, i) => (
                          <code key={i} className="text-xs font-mono bg-white border border-gray-200 rounded-md px-2.5 py-1.5 text-gray-700 tracking-wider text-center">{code}</code>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Verify form */}
                <div className="border-t border-gray-100 pt-4">
                  <form onSubmit={handleEnable2FA} className="flex flex-col sm:flex-row items-end gap-3">
                    <div className="flex-1 w-full">
                      <label className="block text-xs font-semibold text-gray-700 mb-1.5">Enter the 6-digit code from your authenticator app</label>
                      <input
                        className={`${inputCls} text-center text-lg tracking-[0.4em] font-mono`}
                        value={twoFACode}
                        onChange={(e) => setTwoFACode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                        placeholder="000 000"
                        maxLength={6}
                        inputMode="numeric"
                        autoFocus
                        required
                      />
                    </div>
                    <div className="flex gap-2 shrink-0 w-full sm:w-auto">
                      <button type="button" onClick={() => setTwoFAStep("idle")} className="flex-1 sm:flex-none text-xs text-gray-500 hover:text-gray-900 px-4 py-2.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 font-medium transition-colors">Cancel</button>
                      <button type="submit" disabled={twoFALoading || twoFACode.length !== 6} className="flex-1 sm:flex-none text-sm bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg font-semibold transition-colors shadow-sm">
                        {twoFALoading ? "Verifying…" : "Activate 2FA"}
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          )}

          {/* Disable confirm */}
          {twoFAStep === "disable-confirm" && (
            <div className="border-t border-gray-100 bg-white px-5 py-4">
              <div className="flex items-start gap-3 mb-4 p-3 bg-red-50 rounded-xl border border-red-100">
                <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700 leading-snug">Disabling 2FA reduces your account security. Confirm your password to proceed.</p>
              </div>
              <form onSubmit={handleDisable2FA} className="flex flex-col sm:flex-row items-end gap-3">
                <div className="flex-1 w-full">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">Current password</label>
                  <input type="password" className={inputCls} value={twoFAPassword} onChange={(e) => setTwoFAPassword(e.target.value)} placeholder="••••••••" required />
                </div>
                <div className="flex gap-2 shrink-0 w-full sm:w-auto">
                  <button type="button" onClick={() => setTwoFAStep("idle")} className="flex-1 sm:flex-none text-xs text-gray-500 hover:text-gray-900 px-4 py-2.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 font-medium">Cancel</button>
                  <button type="submit" disabled={twoFALoading || !twoFAPassword} className="flex-1 sm:flex-none text-sm bg-red-500 hover:bg-red-600 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg font-semibold transition-colors">
                    {twoFALoading ? "Disabling…" : "Disable 2FA"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Backup code regen */}
          {twoFAStep === "backup-regen" && (
            <div className="border-t border-gray-100 bg-white px-5 py-4">
              <div className="flex items-start gap-3 mb-4 p-3 bg-amber-50 rounded-xl border border-amber-100">
                <KeyRound className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p className="text-sm text-amber-800 leading-snug">Your existing backup codes will be invalidated. Make sure to save the new ones.</p>
              </div>
              <form onSubmit={handleRegenBackupCodes} className="flex flex-col sm:flex-row items-end gap-3">
                <div className="flex-1 w-full">
                  <label className="block text-xs font-semibold text-gray-700 mb-1.5">Current password</label>
                  <input type="password" className={inputCls} value={twoFAPassword} onChange={(e) => setTwoFAPassword(e.target.value)} placeholder="••••••••" required />
                </div>
                <div className="flex gap-2 shrink-0 w-full sm:w-auto">
                  <button type="button" onClick={() => setTwoFAStep("idle")} className="flex-1 sm:flex-none text-xs text-gray-500 hover:text-gray-900 px-4 py-2.5 rounded-lg border border-gray-200 bg-white hover:bg-gray-50 font-medium">Cancel</button>
                  <button type="submit" disabled={twoFALoading || !twoFAPassword} className="flex-1 sm:flex-none text-sm bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-lg font-semibold transition-colors">
                    {twoFALoading ? "Regenerating…" : "Regenerate"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* New backup codes display */}
          {twoFABackupCodes && (
            <div className="border-t border-gray-100 bg-white px-5 py-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center"><Check className="w-3 h-3 text-emerald-600" /></div>
                  <p className="text-sm font-semibold text-gray-900">New backup codes generated</p>
                </div>
                <span className="text-[10px] bg-amber-50 text-amber-700 border border-amber-200 px-1.5 py-0.5 rounded font-medium">Save these now</span>
              </div>
              <div className="grid grid-cols-2 gap-1.5 p-3 bg-gray-50 rounded-xl border border-gray-200 mb-3">
                {twoFABackupCodes.map((code, i) => (
                  <code key={i} className="text-xs font-mono bg-white border border-gray-200 rounded-md px-2.5 py-1.5 text-gray-700 tracking-wider text-center">{code}</code>
                ))}
              </div>
              <button onClick={() => setTwoFABackupCodes(null)} className="text-xs text-gray-500 hover:text-gray-800 font-medium transition-colors">Dismiss</button>
            </div>
          )}
        </div>
      </section>

      {/* ── C. Single Sign-On (admin only) ───────────────────────────────────── */}
      {isAdmin && (
        <section id="sso" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader icon={LogIn} title="Single Sign-On (SSO)" color="brand" />
          <p className="text-xs text-gray-500 mb-5">
            Allow team members to log in using your company's identity provider (Okta, Azure AD, Google Workspace, or any OIDC-compatible IdP).
            SSO is available on the Growth plan.
          </p>

          {ssoConfig ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-100">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{ssoConfig.domain}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{ssoConfig.issuer}</p>
                  <p className="text-xs text-gray-500">Client ID: {ssoConfig.client_id}</p>
                </div>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${ssoConfig.enabled ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
                  {ssoConfig.enabled ? "Active" : "Disabled"}
                </span>
              </div>

              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={handleSSOToggle}
                  disabled={ssoLoading}
                  className="btn-secondary text-xs py-1.5 px-3"
                >
                  {ssoConfig.enabled ? "Disable" : "Enable"}
                </button>
                <button
                  onClick={() => { setSsoShowForm(true); setSsoForm({ domain: ssoConfig.domain, issuer: ssoConfig.issuer, client_id: ssoConfig.client_id, client_secret: "", scopes: ssoConfig.scopes }); }}
                  className="btn-secondary text-xs py-1.5 px-3"
                >
                  Edit
                </button>
                <button
                  onClick={handleSSODelete}
                  disabled={ssoLoading}
                  className="text-xs py-1.5 px-3 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
                >
                  Remove
                </button>
              </div>
            </div>
          ) : (
            !ssoShowForm && (
              <button onClick={() => setSsoShowForm(true)} className="btn-secondary text-sm gap-2">
                <LogIn className="w-4 h-4" /> Configure SSO
              </button>
            )
          )}

          {ssoShowForm && (
            <form onSubmit={handleSSOSave} className="mt-4 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Email domain</label>
                <input
                  className="input text-sm"
                  placeholder="acme.com"
                  value={ssoForm.domain}
                  onChange={(e) => setSsoForm((f) => ({ ...f, domain: e.target.value }))}
                  required
                />
                <p className="text-[11px] text-gray-400 mt-1">Users whose email ends in this domain will see the SSO button.</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Issuer URL</label>
                <input
                  className="input text-sm"
                  placeholder="https://dev-xxx.okta.com/oauth2/default"
                  value={ssoForm.issuer}
                  onChange={(e) => setSsoForm((f) => ({ ...f, issuer: e.target.value }))}
                  required
                />
                <p className="text-[11px] text-gray-400 mt-1">Found in your IdP's OIDC settings. Must expose a <code>/.well-known/openid-configuration</code> endpoint.</p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Client ID</label>
                <input
                  className="input text-sm font-mono"
                  placeholder="0oa1abc2def3GHI"
                  value={ssoForm.client_id}
                  onChange={(e) => setSsoForm((f) => ({ ...f, client_id: e.target.value }))}
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Client secret</label>
                <input
                  type="password"
                  className="input text-sm font-mono"
                  placeholder={ssoConfig ? "Leave blank to keep existing secret" : "••••••••••••"}
                  value={ssoForm.client_secret}
                  onChange={(e) => setSsoForm((f) => ({ ...f, client_secret: e.target.value }))}
                  required={!ssoConfig}
                />
              </div>
              <div className="flex gap-2 pt-1">
                <button type="submit" disabled={ssoSaving} className="btn-primary text-sm py-2 px-4">
                  {ssoSaving ? "Saving…" : "Save SSO"}
                </button>
                <button type="button" onClick={() => setSsoShowForm(false)} className="btn-secondary text-sm py-2 px-4">
                  Cancel
                </button>
              </div>
            </form>
          )}
        </section>
      )}

      {/* ── D. Notifications ─────────────────────────────────────────────────── */}
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

        {/* Microsoft Teams webhook */}
        <div className="mt-5 pt-5 border-t border-gray-100">
          <p className="text-sm font-medium text-gray-800 mb-1">Microsoft Teams webhook URL</p>
          <p className="text-xs text-gray-500 mb-2">Post alerts to a Teams channel. Leave blank to disable.</p>
          <input
            type="url"
            value={notifSettings.teams_webhook_url ?? ""}
            onChange={(e) => setNotifSettings((s) => ({ ...s, teams_webhook_url: e.target.value || null }))}
            placeholder="https://outlook.office.com/webhook/…"
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
                    "Trust Center analytics",
                    "Custom trust domain",
                    "Device monitoring",
                    "Questionnaire collaboration",
                    "Excel/CSV upload & AI autofill",
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
                  Unlimited integrations · PDF &amp; CSV reports · AI features · Trust Center + analytics + custom domain · Device monitoring · Questionnaire collaboration · Excel/CSV autofill · Unlimited team members
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

              <div className="border-t border-gray-100" />

              {/* Custom domain */}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Custom domain <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <p className="text-xs text-gray-400 mb-2">
                  Host your trust page at <code className="bg-gray-100 px-1 rounded">trust.yourcompany.com</code> by adding a CNAME record pointing to <code className="bg-gray-100 px-1 rounded">tracelayer.app</code>
                </p>
                <div className="flex gap-2 flex-wrap">
                  <input
                    type="text"
                    value={trustDomainInput}
                    onChange={(e) => setTrustDomainInput(e.target.value.toLowerCase().trim())}
                    placeholder="trust.yourcompany.com"
                    className={`${inputCls} flex-1 min-w-[200px]`}
                  />
                  {trustSettings.custom_domain && (
                    <button
                      onClick={handleVerifyDomain}
                      disabled={domainVerifying}
                      className="shrink-0 flex items-center gap-1.5 text-xs font-semibold border border-gray-200 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                      {domainVerifying ? "Checking…" : trustSettings.domain_verified ? "✓ Verified" : "Verify DNS"}
                    </button>
                  )}
                </div>
                {trustSettings.custom_domain && trustSettings.domain_verification_token && !trustSettings.domain_verified && (
                  <div className="mt-2 bg-amber-50 border border-amber-100 rounded-lg p-3 text-xs text-amber-700 space-y-1">
                    <p className="font-semibold">DNS setup required:</p>
                    <p>Add this TXT record: <code className="bg-white border border-amber-200 px-1.5 py-0.5 rounded font-mono">_tracelayer-verify.{trustSettings.custom_domain}</code></p>
                    <p>Value: <code className="bg-white border border-amber-200 px-1.5 py-0.5 rounded font-mono break-all">{trustSettings.domain_verification_token}</code></p>
                  </div>
                )}
                {trustSettings.domain_verified && (
                  <p className="mt-1.5 text-xs text-emerald-600 font-medium">✓ Domain verified — trust page accessible at {trustSettings.custom_domain}</p>
                )}
              </div>

              <div className="border-t border-gray-100" />

              {/* Analytics */}
              <div>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">Trust Center Analytics</p>
                    <p className="text-xs text-gray-500">See who&apos;s viewing your public trust page</p>
                  </div>
                  <button
                    onClick={loadTrustAnalytics}
                    className="text-xs font-semibold text-brand-600 hover:text-brand-700 border border-brand-200 hover:border-brand-300 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    {trustAnalyticsOpen ? "Refresh" : "View analytics"}
                  </button>
                </div>

                {trustAnalyticsOpen && trustAnalytics && (
                  <div className="mt-3 space-y-3">
                    <div className="grid grid-cols-3 gap-3">
                      <div className="bg-gray-50 rounded-xl p-3 text-center">
                        <p className="text-2xl font-bold text-gray-900">{trustAnalytics.total_views}</p>
                        <p className="text-xs text-gray-500 mt-0.5">Total views</p>
                      </div>
                      <div className="bg-gray-50 rounded-xl p-3 text-center">
                        <p className="text-2xl font-bold text-gray-900">
                          {trustAnalytics.views_last_30_days.reduce((s, d) => s + d.count, 0)}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">Last 30 days</p>
                      </div>
                      <div className="bg-gray-50 rounded-xl p-3 text-center">
                        <p className="text-2xl font-bold text-gray-900">{trustAnalytics.recent_views.length}</p>
                        <p className="text-xs text-gray-500 mt-0.5">Recent visitors</p>
                      </div>
                    </div>

                    {/* Sparkline */}
                    {trustAnalytics.views_last_30_days.some(d => d.count > 0) && (
                      <div className="bg-gray-50 rounded-xl p-3">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mb-2">Daily views — last 30 days</p>
                        <div className="flex items-end gap-0.5 h-12">
                          {(() => {
                            const maxVal = Math.max(...trustAnalytics.views_last_30_days.map(d => d.count), 1);
                            return trustAnalytics.views_last_30_days.map((d, i) => (
                              <div
                                key={i}
                                title={`${d.date}: ${d.count} view${d.count !== 1 ? "s" : ""}`}
                                className="flex-1 bg-brand-500 rounded-sm min-h-[2px] transition-all hover:bg-brand-600"
                                style={{ height: `${Math.max((d.count / maxVal) * 100, d.count > 0 ? 8 : 0)}%` }}
                              />
                            ));
                          })()}
                        </div>
                      </div>
                    )}

                    {/* Recent visitors */}
                    {trustAnalytics.recent_views.length > 0 && (
                      <div className="bg-gray-50 rounded-xl p-3">
                        <p className="text-[10px] font-semibold uppercase tracking-wide text-gray-400 mb-2">Recent visitors</p>
                        <div className="space-y-1.5 max-h-48 overflow-y-auto">
                          {trustAnalytics.recent_views.map((v, i) => (
                            <div key={i} className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-2 min-w-0">
                                <span className="text-gray-500 truncate">{v.user_agent_summary || "Unknown browser"}</span>
                                {v.referrer && <span className="text-gray-400 truncate">· from {new URL(v.referrer).hostname}</span>}
                              </div>
                              <span className="text-gray-400 shrink-0 ml-2">{new Date(v.viewed_at).toLocaleString()}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
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

      {/* ── H. API Keys ───────────────────────────────────────────────────────── */}
      {isAdmin && (
        <section id="api-keys" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader
            icon={Key}
            title="API Keys"
            subtitle="Create API keys to access the TraceLayer API programmatically."
            color="gray"
          />

          {/* Existing keys */}
          {apiKeys.length > 0 && (
            <div className="mb-5 space-y-2">
              {apiKeys.map((k) => (
                <div key={k.id} className="flex items-center justify-between gap-3 bg-gray-50 border border-gray-100 rounded-xl px-4 py-3">
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 truncate">{k.name}</p>
                    <p className="text-xs text-gray-400 font-mono mt-0.5">{k.key_prefix}****</p>
                    <p className="text-xs text-gray-400 mt-0.5">
                      Created {new Date(k.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      {" · "}
                      Last used: {k.last_used_at ? new Date(k.last_used_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "Never"}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRevokeApiKey(k.id)}
                    className="shrink-0 text-xs font-medium text-red-600 border border-red-200 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    Revoke
                  </button>
                </div>
              ))}
            </div>
          )}

          {apiKeys.length === 0 && (
            <p className="text-sm text-gray-400 mb-5">No API keys yet.</p>
          )}

          {/* Create new key */}
          <div className="flex gap-2">
            <input
              type="text"
              value={apiKeyName}
              onChange={(e) => setApiKeyName(e.target.value)}
              placeholder="Key name (e.g. CI pipeline)"
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500/30 focus:border-brand-400"
              onKeyDown={(e) => { if (e.key === "Enter") handleCreateApiKey(); }}
            />
            <button
              onClick={handleCreateApiKey}
              disabled={apiKeyCreating || !apiKeyName.trim()}
              className="flex items-center gap-1.5 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              {apiKeyCreating ? "Creating…" : "Create"}
            </button>
          </div>

          {/* One-time raw key modal */}
          {newRawKey && (
            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4">
              <p className="text-xs font-bold text-amber-700 mb-2">Save this key now — it won&apos;t be shown again</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs font-mono text-gray-800 bg-white border border-gray-200 rounded-lg px-3 py-2 break-all select-all">
                  {newRawKey}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(newRawKey);
                    setApiKeyCopied(true);
                    setTimeout(() => setApiKeyCopied(false), 2000);
                  }}
                  className="shrink-0 flex items-center gap-1 px-3 py-2 border border-gray-200 bg-white hover:bg-gray-50 text-xs font-medium text-gray-700 rounded-lg transition-colors"
                >
                  {apiKeyCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                  {apiKeyCopied ? "Copied" : "Copy"}
                </button>
              </div>
              <button
                onClick={() => setNewRawKey(null)}
                className="mt-3 text-xs text-amber-600 hover:underline"
              >
                I&apos;ve saved it — dismiss
              </button>
            </div>
          )}
        </section>
      )}

      {/* ── H2. Slack Bot (admin only) ────────────────────────────────────────── */}
      {isAdmin && (
        <section id="slack-bot" className="rounded-2xl border border-gray-100 shadow-card bg-white p-5 sm:p-6 scroll-mt-20 lg:scroll-mt-8">
          <SectionHeader icon={Bell} title="Slack Compliance Bot" color="brand" />
          <p className="text-xs text-gray-500 mb-5">
            Send weekly compliance reminders to your team via Slack. Employees are prompted to sign policies and attest their devices.
          </p>

          <div className="space-y-4">
            {/* Webhook URL */}
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                Incoming Webhook URL
              </label>
              <input
                type="url"
                value={slackWebhook}
                onChange={e => setSlackWebhook(e.target.value)}
                placeholder="https://hooks.slack.com/services/..."
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <p className="text-[11px] text-gray-400 mt-1">
                Create an incoming webhook at <span className="font-mono">api.slack.com/apps</span> → Incoming Webhooks.
              </p>
            </div>

            {/* Channel name */}
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1.5">
                Channel (optional, for display only)
              </label>
              <input
                type="text"
                value={slackChannel}
                onChange={e => setSlackChannel(e.target.value)}
                placeholder="#compliance-reminders"
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
            </div>

            {/* Reminder toggle */}
            <label className="flex items-center gap-3 cursor-pointer">
              <div
                onClick={() => setSlackEnabled(e => !e)}
                className={`relative w-9 h-5 rounded-full transition-colors ${slackEnabled ? "bg-brand-500" : "bg-gray-200"}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${slackEnabled ? "translate-x-4" : "translate-x-0"}`} />
              </div>
              <span className="text-sm text-gray-700">Enable weekly automated reminders</span>
            </label>

            {/* Actions */}
            <div className="flex flex-wrap gap-2 pt-1">
              <button
                onClick={handleSaveSlack}
                disabled={slackSaving || !slackWebhook.trim()}
                className="px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 text-white text-xs font-semibold rounded-lg transition-colors"
              >
                {slackSaving ? "Saving…" : "Save"}
              </button>
              <button
                onClick={handleTestSlack}
                disabled={slackTesting || !slackConfig}
                className="px-4 py-2 border border-gray-200 hover:border-gray-300 disabled:opacity-40 text-gray-700 text-xs font-semibold rounded-lg transition-colors"
              >
                {slackTesting ? "Testing…" : "Test webhook"}
              </button>
              <button
                onClick={handleSendReminders}
                disabled={slackSending || !slackConfig}
                className="px-4 py-2 border border-gray-200 hover:border-gray-300 disabled:opacity-40 text-gray-700 text-xs font-semibold rounded-lg transition-colors"
              >
                {slackSending ? "Sending…" : "Send reminders now"}
              </button>
            </div>

            {/* Last sent */}
            {slackConfig?.last_sent_at && (
              <p className="text-xs text-gray-400">
                Last sent: {new Date(slackConfig.last_sent_at).toLocaleString()}
              </p>
            )}
          </div>
        </section>
      )}

      {/* ── I. Your Data (GDPR) ───────────────────────────────────────────────── */}
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
