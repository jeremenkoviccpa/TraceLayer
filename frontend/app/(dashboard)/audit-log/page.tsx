"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { AuditLog, Page } from "@/lib/types";
import { ScrollText, Search, ChevronLeft, ChevronRight } from "lucide-react";

const ACTION_OPTIONS = [
  { value: "", label: "All actions" },
  { value: "user.login", label: "Sign in" },
  { value: "user.password_changed", label: "Password changed" },
  { value: "user.email_verified", label: "Email verified" },
  { value: "integration.connected", label: "Integration connected" },
  { value: "integration.disconnected", label: "Integration disconnected" },
  { value: "integration.collect_triggered", label: "Collection triggered" },
  { value: "report.generated", label: "Report generated" },
  { value: "report.downloaded", label: "Report downloaded" },
  { value: "member.invited", label: "Member invited" },
  { value: "member.removed", label: "Member removed" },
  { value: "company.updated", label: "Company updated" },
  { value: "plan.upgraded", label: "Plan upgraded" },
  { value: "plan.downgraded", label: "Plan downgraded" },
];

const ACTION_COLORS: Record<string, string> = {
  "user.login": "bg-blue-50 text-blue-700",
  "user.logout": "bg-gray-100 text-gray-600",
  "user.password_changed": "bg-amber-50 text-amber-700",
  "user.email_verified": "bg-emerald-50 text-emerald-700",
  "integration.connected": "bg-emerald-50 text-emerald-700",
  "integration.disconnected": "bg-red-50 text-red-700",
  "integration.collect_triggered": "bg-blue-50 text-blue-700",
  "report.generated": "bg-violet-50 text-violet-700",
  "report.downloaded": "bg-violet-50 text-violet-700",
  "member.invited": "bg-teal-50 text-teal-700",
  "member.removed": "bg-red-50 text-red-700",
  "invite.revoked": "bg-amber-50 text-amber-700",
  "company.updated": "bg-gray-100 text-gray-700",
  "plan.upgraded": "bg-emerald-50 text-emerald-700",
  "plan.downgraded": "bg-amber-50 text-amber-700",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function AuditLogPage() {
  const [data, setData] = useState<Page<AuditLog> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [action, setAction] = useState("");
  const [emailSearch, setEmailSearch] = useState("");
  const [emailInput, setEmailInput] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await api.getAuditLog({
        page,
        page_size: 50,
        action: action || undefined,
        user_email: emailSearch || undefined,
      });
      setData(result);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [page, action, emailSearch]);

  useEffect(() => { load(); }, [load]);

  const handleEmailSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setEmailSearch(emailInput);
  };

  const handleActionChange = (val: string) => {
    setAction(val);
    setPage(1);
  };

  return (
    <div>
      <div className="flex items-center gap-2 mb-6">
        <ScrollText className="w-5 h-5 text-gray-400" />
        <h1 className="text-2xl font-bold text-gray-900">Audit Log</h1>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3 mb-5">
        <select
          value={action}
          onChange={(e) => handleActionChange(e.target.value)}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 bg-white"
        >
          {ACTION_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>

        <form onSubmit={handleEmailSearch} className="flex gap-2 flex-1">
          <input
            type="text"
            placeholder="Filter by email…"
            value={emailInput}
            onChange={(e) => setEmailInput(e.target.value)}
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
          <button
            type="submit"
            className="flex items-center gap-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium px-3 py-2 rounded-lg transition-colors"
          >
            <Search className="w-4 h-4" />
            Search
          </button>
        </form>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50 text-left">
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Time</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">User</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Action</th>
                <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Resource</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 8 }).map((_, i) => (
                  <tr key={i} className="border-b border-gray-100">
                    <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse w-32" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse w-40" /></td>
                    <td className="px-4 py-3"><div className="h-5 bg-gray-100 rounded-full animate-pulse w-28" /></td>
                    <td className="px-4 py-3"><div className="h-4 bg-gray-100 rounded animate-pulse w-24" /></td>
                  </tr>
                ))
              ) : data?.items.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-12 text-center text-sm text-gray-400">
                    No audit events found.
                  </td>
                </tr>
              ) : (
                data?.items.map((log) => (
                  <tr key={log.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {formatDate(log.created_at)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 truncate max-w-[180px]">
                      {log.user_email ?? <span className="text-gray-400 italic">system</span>}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center text-xs font-medium px-2.5 py-1 rounded-full ${ACTION_COLORS[log.action] ?? "bg-gray-100 text-gray-600"}`}>
                        {log.action_label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {log.resource_type ? (
                        <span className="capitalize">{log.resource_type}{log.resource_id ? ` · ${log.resource_id.slice(0, 8)}` : ""}</span>
                      ) : "—"}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-4 py-3 border-t border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              {data.total} events · page {data.page} of {data.pages}
            </span>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="p-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-40 transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
