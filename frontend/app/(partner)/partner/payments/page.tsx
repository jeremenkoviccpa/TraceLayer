"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { CreditCard, CheckCircle2, Clock, AlertCircle, Calendar, Loader2 } from "lucide-react";

interface Payment {
  id: string;
  client_name: string;
  status: string;
  amount_cents: number;
  created_at: string | null;
  paid_at: string | null;
  client_company_id: string | null;
}

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: typeof CheckCircle2 }> = {
  paid:    { label: "Paid",    color: "text-emerald-600", bg: "bg-emerald-50", icon: CheckCircle2 },
  free:    { label: "Free",    color: "text-brand-600",   bg: "bg-brand-50",   icon: CheckCircle2 },
  manual:  { label: "Manual",  color: "text-violet-600",  bg: "bg-violet-50",  icon: CheckCircle2 },
  pending: { label: "Pending", color: "text-amber-600",   bg: "bg-amber-50",   icon: Clock },
};

export default function PartnerPaymentsPage() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getPartnerPayments()
      .then(setPayments)
      .catch(() => setError("Failed to load payments"))
      .finally(() => setLoading(false));
  }, []);

  const totalRevenue = payments.filter((p) => p.status === "paid").reduce((s, p) => s + p.amount_cents, 0);
  const freeSlots = payments.filter((p) => p.status === "free").length;
  const paidSlots = payments.filter((p) => p.status === "paid").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Payments</h1>
        <p className="text-sm text-gray-500 mt-0.5">Client workspace billing history</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center">
              <CreditCard className="w-4.5 h-4.5 text-emerald-500" />
            </div>
            <span className="text-sm font-medium text-gray-500">Revenue</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-2">${(totalRevenue / 100).toFixed(0)}</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-brand-50 flex items-center justify-center">
              <CheckCircle2 className="w-4.5 h-4.5 text-brand-500" />
            </div>
            <span className="text-sm font-medium text-gray-500">Free slots used</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-2">{freeSlots} <span className="text-base font-normal text-gray-400">/ 3</span></p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-100 p-5">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center">
              <CreditCard className="w-4.5 h-4.5 text-violet-500" />
            </div>
            <span className="text-sm font-medium text-gray-500">Paid workspaces</span>
          </div>
          <p className="text-3xl font-bold text-gray-900 mt-2">{paidSlots}</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-900">Payment history</h2>
        </div>
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-6 h-6 animate-spin text-brand-500" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 px-6 py-4 text-sm text-red-600">
            <AlertCircle className="w-4 h-4 shrink-0" /> {error}
          </div>
        ) : payments.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-sm text-gray-400">No payments yet. Add a client to get started.</p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-50">
                <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-6 py-3">Client</th>
                <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-6 py-3">Status</th>
                <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-6 py-3 hidden sm:table-cell">Amount</th>
                <th className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-6 py-3 hidden md:table-cell">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {payments.map((p) => {
                const cfg = STATUS_CONFIG[p.status] ?? STATUS_CONFIG.pending;
                const Icon = cfg.icon;
                return (
                  <tr key={p.id} className="hover:bg-gray-50/50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{p.client_name}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full ${cfg.bg} ${cfg.color}`}>
                        <Icon className="w-3 h-3" />
                        {cfg.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600 hidden sm:table-cell">
                      {p.status === "free" ? <span className="text-brand-600 font-medium">Free</span> : `$${(p.amount_cents / 100).toFixed(2)}`}
                    </td>
                    <td className="px-6 py-4 hidden md:table-cell">
                      <div className="flex items-center gap-1.5 text-xs text-gray-400">
                        <Calendar className="w-3.5 h-3.5" />
                        {p.paid_at
                          ? new Date(p.paid_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                          : p.created_at
                          ? new Date(p.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                          : "—"}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
