"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { api } from "@/lib/api";
import type { PartnerClient } from "@/lib/types";
import {
  Plus,
  ExternalLink,
  Shield,
  Building2,
  AlertCircle,
  X,
  Loader2,
  ArrowRight,
  Copy,
  Check,
  Calendar,
} from "lucide-react";

function AddClientModal({ onClose, onSuccess }: { onClose: () => void; onSuccess: () => void }) {
  const [clientName, setClientName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!clientName.trim()) return;
    setError("");
    setLoading(true);
    try {
      const { checkout_url } = await api.createPartnerClientCheckout(clientName.trim());
      // Open LemonSqueezy checkout in current tab
      window.location.href = checkout_url;
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create checkout");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md animate-fade-in">
        <div className="flex items-center justify-between px-6 pt-6 pb-4 border-b border-gray-100">
          <div>
            <h2 className="text-base font-semibold text-gray-900">Add client workspace</h2>
            <p className="text-sm text-gray-500 mt-0.5">One-time payment of $99 per client</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Client company name</label>
            <input
              type="text"
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              required
              autoFocus
              className="input"
              placeholder="Acme Inc."
            />
          </div>

          <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-3 text-xs text-indigo-700 leading-relaxed">
            After payment, a dedicated compliance workspace will be created for this client. You&apos;ll be able to manage their data and share a Trust Center link with them.
          </div>

          <div className="flex gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-secondary justify-center py-2.5"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !clientName.trim()}
              className="flex-1 btn-primary justify-center py-2.5"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Redirecting…
                </>
              ) : (
                <>
                  Pay $99 &amp; continue
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function TrustCenterCell({ clientId }: { clientId: string }) {
  const [info, setInfo] = useState<{ slug: string; public_url: string; is_enabled: boolean } | null>(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getClientTrustCenter(clientId)
      .then(setInfo)
      .catch(() => setInfo(null))
      .finally(() => setLoading(false));
  }, [clientId]);

  const handleCopy = async () => {
    if (!info?.public_url) return;
    await navigator.clipboard.writeText(info.public_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <span className="text-xs text-gray-400">Loading…</span>;
  if (!info) return <span className="text-xs text-gray-400">—</span>;

  return (
    <div className="flex items-center gap-2">
      {info.is_enabled ? (
        <>
          <a
            href={info.public_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1 truncate max-w-[180px]"
          >
            {info.public_url.replace("https://", "")}
            <ExternalLink className="w-3 h-3 shrink-0" />
          </a>
          <button
            onClick={handleCopy}
            className="text-gray-400 hover:text-gray-600 transition-colors shrink-0"
            title="Copy URL"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </>
      ) : (
        <span className="text-xs text-gray-400 italic">Not enabled</span>
      )}
    </div>
  );
}

export default function PartnerClientsPage() {
  const { user } = useAuth();
  const [clients, setClients] = useState<PartnerClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [switchingId, setSwitchingId] = useState<string | null>(null);
  const { switchToClient } = useAuth();

  const loadClients = async () => {
    try {
      const data = await api.getPartnerClients();
      setClients(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load clients");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClients();
  }, []);

  const handleSwitch = async (client: PartnerClient) => {
    setSwitchingId(client.id);
    try {
      const switchResponse = await api.switchToClient(client.id);
      await switchToClient(switchResponse);
      // switchToClient in auth-provider calls router.push("/dashboard")
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to switch to client");
      setSwitchingId(null);
    }
  };

  if (!user) return null;

  return (
    <>
      {showAdd && (
        <AddClientModal
          onClose={() => setShowAdd(false)}
          onSuccess={() => {
            setShowAdd(false);
            loadClients();
          }}
        />
      )}

      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
            <p className="text-sm text-gray-500 mt-0.5">
              {clients.length === 0
                ? "No clients yet — add your first one below"
                : `${clients.length} client workspace${clients.length !== 1 ? "s" : ""}`}
            </p>
          </div>
          <button onClick={() => setShowAdd(true)} className="btn-primary shrink-0">
            <Plus className="w-4 h-4" />
            Add client
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-xl px-4 py-3 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-sm text-gray-400">Loading clients…</p>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && clients.length === 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 p-12 text-center">
            <div className="w-14 h-14 bg-brand-50 rounded-2xl flex items-center justify-center mx-auto mb-4">
              <Building2 className="w-7 h-7 text-brand-500" />
            </div>
            <h3 className="text-base font-semibold text-gray-900 mb-1">No clients yet</h3>
            <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
              Each client workspace costs $99 one-time. You&apos;ll manage their compliance data and share a Trust Center link with them.
            </p>
            <button onClick={() => setShowAdd(true)} className="btn-primary mx-auto">
              <Plus className="w-4 h-4" />
              Add your first client
            </button>
          </div>
        )}

        {/* Client list */}
        {!loading && clients.length > 0 && (
          <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3">Client</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3 hidden sm:table-cell">Trust Center</th>
                  <th className="text-left text-xs font-semibold text-gray-500 uppercase tracking-wider px-6 py-3 hidden md:table-cell">Added</th>
                  <th className="px-6 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {clients.map((client) => (
                  <tr key={client.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
                          <Shield className="w-4 h-4 text-brand-500" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{client.name}</p>
                          <p className="text-xs text-gray-400 capitalize">{client.plan} plan</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      <TrustCenterCell clientId={client.id} />
                    </td>
                    <td className="px-6 py-4 hidden md:table-cell">
                      <div className="flex items-center gap-1.5 text-xs text-gray-400">
                        <Calendar className="w-3.5 h-3.5" />
                        {new Date(client.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleSwitch(client)}
                        disabled={switchingId === client.id}
                        className="btn-secondary text-xs py-1.5 px-3"
                      >
                        {switchingId === client.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <>
                            Manage
                            <ArrowRight className="w-3.5 h-3.5" />
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}
