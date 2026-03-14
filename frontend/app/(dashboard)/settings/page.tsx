"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import type { BillingInfo, Company } from "@/lib/types";
import { CreditCard, Lock, Building2, Zap, ShieldAlert, Download, Mail } from "lucide-react";

function Toast({ msg }: { msg: string }) {
  return (
    <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
      {msg}
    </div>
  );
}

export default function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [toast, setToast] = useState("");
  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  // ── Change Password ────────────────────────────────────────────────────
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwSaving, setPwSaving] = useState(false);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (pwForm.next !== pwForm.confirm) {
      showToast("New passwords do not match");
      return;
    }
    setPwSaving(true);
    try {
      await api.changePassword(pwForm.current, pwForm.next);
      setPwForm({ current: "", next: "", confirm: "" });
      showToast("Password updated");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to update password");
    } finally {
      setPwSaving(false);
    }
  };

  // ── Company ────────────────────────────────────────────────────────────
  const [company, setCompany] = useState<Company | null>(null);
  const [companyName, setCompanyName] = useState("");
  const [companySaving, setCompanySaving] = useState(false);

  useEffect(() => {
    if (!isAdmin) return;
    api.getCompany().then((c) => {
      setCompany(c);
      setCompanyName(c.name);
    }).catch(console.error);
  }, [isAdmin]);

  // ── Billing ────────────────────────────────────────────────────────────
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
      showToast(err instanceof Error ? err.message : "Could not open checkout");
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
      showToast(err instanceof Error ? err.message : "Could not open billing portal");
    } finally {
      setBillingLoading(false);
    }
  };

  const handleUpdateCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    setCompanySaving(true);
    try {
      const updated = await api.updateCompany(companyName);
      setCompany(updated);
      showToast("Company name updated");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to update company");
    } finally {
      setCompanySaving(false);
    }
  };

  // ── GDPR ───────────────────────────────────────────────────────────────────
  // ── Weekly report preview ─────────────────────────────────────────────────
  const [weeklyLoading, setWeeklyLoading] = useState(false);

  const handleSendPreview = async () => {
    setWeeklyLoading(true);
    try {
      await api.sendWeeklyPreview();
      showToast("Preview sent — check your inbox");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to send preview");
    } finally {
      setWeeklyLoading(false);
    }
  };

  // ── GDPR ───────────────────────────────────────────────────────────────────
  const [gdprLoading, setGdprLoading] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState(false);

  const handleExport = async () => {
    setGdprLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/v1/org/account/export`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "tracelayer-data-export.json";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      showToast("Export failed — please try again");
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
      showToast("Deletion failed — please try again");
      setGdprLoading(false);
    }
  };

  return (
    <div className="max-w-2xl">
      {toast && <Toast msg={toast} />}

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Change Password */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Lock className="w-5 h-5 text-gray-400" />
          <h2 className="text-base font-semibold text-gray-900">Change Password</h2>
        </div>
        <form onSubmit={handleChangePassword} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Current password
            </label>
            <input
              type="password"
              required
              value={pwForm.current}
              onChange={(e) => setPwForm((f) => ({ ...f, current: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              New password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={pwForm.next}
              onChange={(e) => setPwForm((f) => ({ ...f, next: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confirm new password
            </label>
            <input
              type="password"
              required
              minLength={8}
              value={pwForm.confirm}
              onChange={(e) => setPwForm((f) => ({ ...f, confirm: e.target.value }))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={pwSaving}
              className="bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              {pwSaving ? "Saving…" : "Update password"}
            </button>
          </div>
        </form>
      </div>

      {/* Billing */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <CreditCard className="w-5 h-5 text-gray-400" />
          <h2 className="text-base font-semibold text-gray-900">Billing &amp; Plan</h2>
        </div>

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
                    <span className="text-xs text-gray-400 capitalize">{billing.subscription_status.replace("_", " ")}</span>
                  )}
                </div>
                {billing.plan === "free" && (
                  <p className="text-sm text-gray-500 mt-1">Up to 3 integrations. Upgrade for unlimited access.</p>
                )}
                {billing.plan === "growth" && (
                  <p className="text-sm text-gray-500 mt-1">Unlimited integrations, AI advisor, priority support.</p>
                )}
              </div>

              {isAdmin && (
                billing.plan === "free" ? (
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
                )
              )}
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
      </div>

      {/* Weekly compliance report */}
      {isAdmin && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-1">
            <Mail className="w-5 h-5 text-brand-500" />
            <h2 className="text-base font-semibold text-gray-900">Weekly Compliance Report</h2>
          </div>
          <p className="text-sm text-gray-500 mb-4">
            Every Monday at 9 AM UTC all admins receive a compliance digest email with your scores, control status, and top action items.
          </p>
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
        </div>
      )}

      {/* GDPR */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <ShieldAlert className="w-5 h-5 text-gray-400" />
          <h2 className="text-base font-semibold text-gray-900">Your Data</h2>
        </div>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">Export all data</p>
              <p className="text-xs text-gray-500">Download everything we hold about your account in JSON format.</p>
            </div>
            <button
              onClick={handleExport}
              disabled={gdprLoading}
              className="flex items-center gap-1.5 text-sm font-medium text-gray-700 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-60 shrink-0 ml-4"
            >
              <Download className="w-4 h-4" /> Export
            </button>
          </div>

          {isAdmin && (
            <div className="border-t border-gray-100 pt-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-red-700">Delete account</p>
                  <p className="text-xs text-gray-500">Permanently delete your company and all data. Irreversible.</p>
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
                    className="text-sm font-medium text-red-600 border border-red-300 hover:bg-red-50 px-3 py-1.5 rounded-lg transition-colors shrink-0 ml-4"
                  >
                    Delete account
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Company Settings — admin only */}
      {isAdmin && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Building2 className="w-5 h-5 text-gray-400" />
            <h2 className="text-base font-semibold text-gray-900">Company</h2>
          </div>
          {company ? (
            <form onSubmit={handleUpdateCompany} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Company name
                </label>
                <input
                  type="text"
                  required
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
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
        </div>
      )}
    </div>
  );
}
