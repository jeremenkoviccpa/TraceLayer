"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Integration } from "@/lib/types";
import { CheckCircle2, AlertCircle, Clock, RefreshCw, Trash2, Plus, X } from "lucide-react";

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
}: {
  def: (typeof INTEGRATION_DEFS)[0];
  onClose: () => void;
  onConnected: () => void;
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
      setError(err instanceof Error ? err.message : "Connection failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 relative">
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
              <input
                type={f.type ?? "text"}
                placeholder={f.placeholder}
                required
                value={fields[f.key] ?? ""}
                onChange={(e) => setFields((prev) => ({ ...prev, [f.key]: e.target.value }))}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
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
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [collecting, setCollecting] = useState<string | null>(null);
  const [toast, setToast] = useState("");

  const load = () =>
    api
      .getIntegrations()
      .then(setIntegrations)
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

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

      {connecting && (
        <ConnectModal
          def={INTEGRATION_DEFS.find((d) => d.type === connecting)!}
          onClose={() => setConnecting(null)}
          onConnected={load}
        />
      )}

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Integrations</h1>

      <div className="space-y-4">
        {INTEGRATION_DEFS.map((def) => {
          const connected = integrations.find((i) => i.integration_type === def.type);
          return (
            <div
              key={def.type}
              className="bg-white rounded-xl border border-gray-200 p-6 flex items-center justify-between"
            >
              <div>
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

              <div className="flex items-center gap-2 ml-4 shrink-0">
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
