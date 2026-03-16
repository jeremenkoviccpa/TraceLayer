"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PartnerClient } from "@/lib/types";
import { Building2, Users, ArrowRight, Plus, Loader2 } from "lucide-react";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";

export default function PartnerDashboardPage() {
  const { user } = useAuth();
  const [clients, setClients] = useState<PartnerClient[]>([]);
  const [loading, setLoading] = useState(true);
  const { switchToClient } = useAuth();
  const [switchingId, setSwitchingId] = useState<string | null>(null);

  useEffect(() => {
    api.getPartnerClients()
      .then(setClients)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSwitch = async (client: PartnerClient) => {
    setSwitchingId(client.id);
    try {
      const switchResponse = await api.switchToClient(client.id);
      await switchToClient(switchResponse);
    } catch {
      setSwitchingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Partner overview</h1>
        <p className="text-sm text-gray-500 mt-0.5">Welcome back, {user?.email}</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center">
              <Users className="w-4.5 h-4.5 text-brand-500" />
            </div>
            <span className="text-sm font-medium text-gray-500">Total clients</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {loading ? "—" : clients.length}
          </p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-green-50 flex items-center justify-center">
              <Building2 className="w-4.5 h-4.5 text-green-500" />
            </div>
            <span className="text-sm font-medium text-gray-500">Active workspaces</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-2">
            {loading ? "—" : clients.length}
          </p>
        </div>
      </div>

      {/* Client list */}
      <div className="bg-white rounded-2xl border border-gray-100">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-900">Client workspaces</h2>
          <Link href="/partner/clients" className="btn-secondary text-xs py-1.5 px-3">
            <Plus className="w-3.5 h-3.5" />
            Add client
          </Link>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
          </div>
        ) : clients.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-sm text-gray-400 mb-3">No clients yet</p>
            <Link href="/partner/clients" className="btn-primary mx-auto text-sm">
              <Plus className="w-4 h-4" />
              Add your first client
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {clients.map((client) => (
              <div key={client.id} className="flex items-center justify-between px-6 py-3.5 hover:bg-gray-50/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-brand-50 flex items-center justify-center shrink-0">
                    <Building2 className="w-4 h-4 text-brand-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{client.name}</p>
                    <p className="text-xs text-gray-400 capitalize">{client.plan}</p>
                  </div>
                </div>
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
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
