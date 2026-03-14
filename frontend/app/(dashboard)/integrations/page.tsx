"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { BillingInfo, Integration } from "@/lib/types";
import { CheckCircle2, AlertCircle, Clock, RefreshCw, Trash2, Plus, X, Zap, Lock } from "lucide-react";

const FREE_LIMIT = 3;

// ── Upgrade Modal ─────────────────────────────────────────────────────────────
function UpgradeModal({ onClose }: { onClose: () => void }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      window.location.href = checkout_url;
    } catch {
      router.push("/settings");
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div className="bg-white rounded-t-2xl sm:rounded-xl shadow-xl w-full sm:max-w-md p-6 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-gray-400 hover:text-gray-600">
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-full bg-amber-100 flex items-center justify-center shrink-0">
            <Lock className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-gray-900">Integration limit reached</h2>
            <p className="text-sm text-gray-500">Free plan allows up to {FREE_LIMIT} integrations.</p>
          </div>
        </div>

        <div className="bg-gradient-to-br from-teal-50 to-emerald-50 border border-teal-200 rounded-xl p-4 mb-5">
          <p className="text-sm font-semibold text-teal-800 mb-2">Upgrade to Growth — $49/mo</p>
          <ul className="space-y-1 text-sm text-teal-700">
            <li className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 shrink-0" /> Unlimited integrations</li>
            <li className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 shrink-0" /> AI Compliance Advisor</li>
            <li className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 shrink-0" /> SOC 2, ISO 27001 &amp; GDPR</li>
            <li className="flex items-center gap-2"><Zap className="w-3.5 h-3.5 shrink-0" /> Priority support</li>
          </ul>
        </div>

        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="flex-1 flex items-center justify-center gap-1.5 bg-[var(--accent)] hover:opacity-90 disabled:opacity-60 text-white font-medium rounded-lg px-4 py-2 text-sm transition-opacity"
          >
            <Zap className="w-4 h-4" />
            {loading ? "Loading…" : "Upgrade now"}
          </button>
        </div>
      </div>
    </div>
  );
}

const INTEGRATION_DEFS = [
  {
    type: "aws",
    label: "Amazon Web Services",
    description: "Collect IAM users, policies, and CloudTrail logs",
    fields: [
      { key: "access_key_id", label: "Access Key ID", placeholder: "AKIAIOSFODNN7EXAMPLE" },
      { key: "secret_access_key", label: "Secret Access Key", placeholder: "••••••••••••", type: "password" },
      { key: "region", label: "Region", placeholder: "us-east-1" },
    ],
  },
  {
    type: "github",
    label: "GitHub",
    description: "Collect repositories, members, and admin users",
    fields: [
      { key: "token", label: "Personal Access Token", placeholder: "ghp_••••••••", type: "password" },
      { key: "org", label: "Organization", placeholder: "my-org" },
    ],
  },
  {
    type: "slack",
    label: "Slack",
    description: "Collect workspace users and admin users",
    fields: [
      { key: "bot_token", label: "Bot Token", placeholder: "xoxb-••••••••", type: "password" },
    ],
  },
  {
    type: "google_workspace",
    label: "Google Workspace",
    description: "Collect users, admin accounts, and groups via Admin SDK",
    fields: [
      { key: "admin_email", label: "Admin Email", placeholder: "admin@yourcompany.com" },
      { key: "service_account_json", label: "Service Account JSON", placeholder: '{"type":"service_account",...}', type: "textarea" },
    ],
  },
  {
    type: "jira",
    label: "Jira",
    description: "Collect projects and users for change management evidence",
    fields: [
      { key: "domain", label: "Domain", placeholder: "mycompany.atlassian.net" },
      { key: "email", label: "Admin Email", placeholder: "admin@mycompany.com" },
      { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
    ],
  },
  {
    type: "okta",
    label: "Okta",
    description: "Collect users, groups, and password policies",
    fields: [
      { key: "domain", label: "Okta Domain", placeholder: "mycompany.okta.com" },
      { key: "api_token", label: "API Token", placeholder: "••••••••••••", type: "password" },
    ],
  },
  {
    type: "azure_ad",
    label: "Azure AD",
    description: "Collect users, groups, and directory role assignments",
    fields: [
      { key: "tenant_id", label: "Tenant ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
      { key: "client_id", label: "Client ID", placeholder: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" },
      { key: "client_secret", label: "Client Secret", placeholder: "••••••••••••", type: "password" },
    ],
  },
];

function statusBadge(status: string) {
  if (status === "active")
    return (
      <span className="flex items-center gap-1 text-xs text-green-700 bg-green-50 border border-green-200 px-2 py-0.5 rounded-full">
        <CheckCircle2 className="w-3 h-3" /> Active
      </span>
    );
  if (status === "error")
    return (
      <span className="flex items-center gap-1 text-xs text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">
        <AlertCircle className="w-3 h-3" /> Error
      </span>
    );
  return (
    <span className="flex items-center gap-1 text-xs text-gray-600 bg-gray-100 border border-gray-200 px-2 py-0.5 rounded-full">
      <Clock className="w-3 h-3" /> Pending
    </span>
  );
}

function ConnectModal({
  def,
  onClose,
  onConnected,
  onUpgradeNeeded,
}: {
  def: (typeof INTEGRATION_DEFS)[0];
  onClose: () => void;
  onConnected: () => void;
  onUpgradeNeeded: () => void;
}) {
  const [fields, setFields] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.connectIntegration(def.type, fields);
      onConnected();
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Connection failed";
      // 402 = free plan limit hit → show upgrade modal
      if (msg.toLowerCase().includes("free plan") || msg.toLowerCase().includes("upgrade")) {
        onClose();
        onUpgradeNeeded();
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-end sm:items-center justify-center z-50 p-0 sm:p-4">
      <div className="bg-white rounded-t-2xl sm:rounded-xl shadow-xl w-full sm:max-w-md p-5 sm:p-6 relative max-h-[90vh] overflow-y-auto">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-5 h-5" />
        </button>

        <h2 className="text-lg font-semibold mb-1">Connect {def.label}</h2>
        <p className="text-sm text-gray-500 mb-5">{def.description}</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
              {error}
            </div>
          )}

          {def.fields.map((f) => (
            <div key={f.key}>
              <label className="block text-sm font-medium text-gray-700 mb-1">{f.label}</label>
              {f.type === "textarea" ? (
                <textarea
                  placeholder={f.placeholder}
                  required
                  rows={5}
                  value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((prev) => ({ ...prev, [f.key]: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
                />
              ) : (
                <input
                  type={f.type ?? "text"}
                  placeholder={f.placeholder}
                  required
                  value={fields[f.key] ?? ""}
                  onChange={(e) => setFields((prev) => ({ ...prev, [f.key]: e.target.value }))}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                />
              )}
            </div>
          ))}

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 rounded-lg px-4 py-2 text-sm hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white font-medium rounded-lg px-4 py-2 text-sm transition-colors"
            >
              {loading ? "Connecting…" : "Connect"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [collecting, setCollecting] = useState<string | null>(null);
  const [showUpgrade, setShowUpgrade] = useState(false);
  const [toast, setToast] = useState("");

  const load = () =>
    Promise.all([api.getIntegrations(), api.getSubscription()])
      .then(([ints, bill]) => { setIntegrations(ints); setBilling(bill); })
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  const handleCollect = async (type: string) => {
    setCollecting(type);
    try {
      await api.triggerCollect(type);
      showToast(`Collection started for ${type}`);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to trigger collection");
    } finally {
      setCollecting(null);
    }
  };

  const handleDisconnect = async (type: string) => {
    if (!confirm(`Disconnect ${type}? This will remove the stored credentials.`)) return;
    try {
      await api.disconnectIntegration(type);
      await load();
      showToast(`${type} disconnected`);
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to disconnect");
    }
  };

  const connectedTypes = new Set(integrations.map((i) => i.integration_type));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div>
      {toast && (
        <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}

      {showUpgrade && <UpgradeModal onClose={() => setShowUpgrade(false)} />}

      {connecting && (
        <ConnectModal
          def={INTEGRATION_DEFS.find((d) => d.type === connecting)!}
          onClose={() => setConnecting(null)}
          onConnected={load}
          onUpgradeNeeded={() => setShowUpgrade(true)}
        />
      )}

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Integrations</h1>

      {/* Usage bar — free plan only */}
      {billing?.plan === "free" && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-700">
              {integrations.length} / {FREE_LIMIT} integrations used
            </span>
            <button
              onClick={() => setShowUpgrade(true)}
              className="flex items-center gap-1 text-xs font-semibold text-[var(--accent)] hover:opacity-80 transition-opacity"
            >
              <Zap className="w-3.5 h-3.5" /> Upgrade for unlimited
            </button>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${
                integrations.length >= FREE_LIMIT ? "bg-red-400" : integrations.length >= 2 ? "bg-amber-400" : "bg-brand-500"
              }`}
              style={{ width: `${Math.min((integrations.length / FREE_LIMIT) * 100, 100)}%` }}
            />
          </div>
          {integrations.length >= FREE_LIMIT && (
            <p className="text-xs text-red-600 mt-1.5">Limit reached — upgrade to connect more integrations.</p>
          )}
        </div>
      )}

      <div className="space-y-4">
        {INTEGRATION_DEFS.map((def) => {
          const connected = integrations.find((i) => i.integration_type === def.type);
          return (
            <div
              key={def.type}
              className="bg-white rounded-xl border border-gray-200 p-4 md:p-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-3 mb-1">
                  <h3 className="font-semibold text-gray-900">{def.label}</h3>
                  {connected && statusBadge(connected.status)}
                </div>
                <p className="text-sm text-gray-500">{def.description}</p>
                {connected?.last_error && (
                  <p className="text-xs text-red-600 mt-1">{connected.last_error}</p>
                )}
                {connected?.last_collected_at && (
                  <p className="text-xs text-gray-400 mt-1">
                    Last collected: {new Date(connected.last_collected_at).toLocaleString()}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 sm:ml-4 shrink-0">
                {connected ? (
                  <>
                    <button
                      onClick={() => handleCollect(def.type)}
                      disabled={collecting === def.type}
                      title="Run collection now"
                      className="p-2 text-gray-500 hover:text-brand-600 hover:bg-brand-50 rounded-lg transition-colors disabled:opacity-40"
                    >
                      <RefreshCw className={`w-4 h-4 ${collecting === def.type ? "animate-spin" : ""}`} />
                    </button>
                    <button
                      onClick={() => setConnecting(def.type)}
                      title="Reconnect / update credentials"
                      className="px-3 py-1.5 text-sm border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                    >
                      Reconnect
                    </button>
                    <button
                      onClick={() => handleDisconnect(def.type)}
                      title="Disconnect"
                      className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </>
                ) : billing?.plan === "free" && integrations.length >= FREE_LIMIT ? (
                  <button
                    onClick={() => setShowUpgrade(true)}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 text-sm font-medium rounded-lg transition-colors"
                  >
                    <Lock className="w-4 h-4" /> Upgrade
                  </button>
                ) : (
                  <button
                    onClick={() => setConnecting(def.type)}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" /> Connect
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
