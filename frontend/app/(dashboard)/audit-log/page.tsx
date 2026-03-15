"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { AuditLog, Page } from "@/lib/types";
import { ScrollText, Search, ChevronLeft, ChevronRight, CalendarDays, Clock } from "lucide-react";

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

// Dot color for timeline entries (based on action type)
const ACTION_DOT: Record<string, string> = {
  "user.login": "bg-blue-400",
  "user.logout": "bg-gray-400",
  "user.password_changed": "bg-amber-400",
  "user.email_verified": "bg-emerald-400",
  "integration.connected": "bg-emerald-400",
  "integration.disconnected": "bg-red-400",
  "integration.collect_triggered": "bg-blue-400",
  "report.generated": "bg-violet-400",
  "report.downloaded": "bg-violet-400",
  "member.invited": "bg-teal-400",
  "member.removed": "bg-red-400",
  "invite.revoked": "bg-amber-400",
  "company.updated": "bg-gray-400",
  "plan.upgraded": "bg-emerald-400",
  "plan.downgraded": "bg-amber-400",
};

const ACTION_BADGE: Record<string, string> = {
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

function formatTimeOnly(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function isToday(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate();
}

function isThisWeek(iso: string) {
  const d = new Date(iso);
  const now = new Date();
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
  return d >= weekAgo;
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

  // Compute stats from loaded page (approximation for display)
  const todayCount = data?.items.filter((l) => isToday(l.created_at)).length ?? 0;
  const weekCount = data?.items.filter((l) => isThisWeek(l.created_at)).length ?? 0;
  const totalEvents = data?.total ?? 0;

  return (
    <div className="space-y-6">
      {/* Dark Hero Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-6 shadow-xl">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div className="w-11 h-11 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "rgba(100,116,139,0.25)" }}>
            <ScrollText className="w-5 h-5" style={{ color: "#94a3b8" }} />
          </div>
          {/* Title + stats */}
          <div className="flex-1">
            <h1 className="text-xl font-bold text-white">Audit Log</h1>
            <p className="text-sm text-slate-400 mt-0.5">Immutable record of all actions taken in your compliance workspace.</p>
            <div className="flex items-center gap-6 mt-4">
              <div>
                <p className="text-2xl font-bold text-slate-300">
                  {loading ? "—" : todayCount}
                </p>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                  <Clock className="w-3 h-3" /> Today
                </p>
              </div>
              <div className="w-px h-8 bg-slate-700" />
              <div>
                <p className="text-2xl font-bold text-slate-300">
                  {loading ? "—" : weekCount}
                </p>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-1">
                  <CalendarDays className="w-3 h-3" /> This week
                </p>
              </div>
              <div className="w-px h-8 bg-slate-700" />
              <div>
                <p className="text-2xl font-bold text-slate-300">
                  {loading ? "—" : totalEvents.toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">Total events</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <select
            value={action}
            onChange={(e) => handleActionChange(e.target.value)}
            className="border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400/30 focus:border-slate-400 bg-white text-gray-700"
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
              className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400/30 focus:border-slate-400"
            />
            <button
              type="submit"
              className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white text-sm font-medium px-4 py-2 rounded-xl transition-colors"
            >
              <Search className="w-3.5 h-3.5" />
              Search
            </button>
          </form>
        </div>
      </div>

      {/* Timeline List */}
      <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
        {loading ? (
          <div className="divide-y divide-gray-50">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4 px-5 py-4">
                <div className="w-2.5 h-2.5 rounded-full bg-gray-100 animate-pulse shrink-0" />
                <div className="flex-1 flex gap-4">
                  <div className="h-4 bg-gray-100 rounded animate-pulse w-32" />
                  <div className="h-4 bg-gray-100 rounded animate-pulse w-40" />
                  <div className="h-5 bg-gray-100 rounded-full animate-pulse w-28 ml-auto" />
                </div>
              </div>
            ))}
          </div>
        ) : data?.items.length === 0 ? (
          <div className="px-5 py-16 text-center">
            <ScrollText className="w-8 h-8 text-gray-200 mx-auto mb-3" />
            <p className="text-sm text-gray-400">No audit events found.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {data?.items.map((log) => (
              <div
                key={log.id}
                className="flex items-start gap-4 px-5 py-4 hover:bg-slate-50/60 transition-colors group"
              >
                {/* Timeline dot */}
                <div className="flex flex-col items-center shrink-0 mt-1.5">
                  <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${ACTION_DOT[log.action] ?? "bg-gray-300"}`} />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4">
                  {/* User */}
                  <p className="text-sm font-medium text-gray-800 truncate min-w-0 sm:w-48">
                    {log.user_email ?? <span className="text-gray-400 italic font-normal">system</span>}
                  </p>

                  {/* Action badge */}
                  <span className={`inline-flex items-center text-xs font-semibold px-2.5 py-1 rounded-full shrink-0 ${ACTION_BADGE[log.action] ?? "bg-gray-100 text-gray-600"}`}>
                    {log.action_label}
                  </span>

                  {/* Resource */}
                  {log.resource_type && (
                    <span className="text-xs text-gray-400 shrink-0 capitalize">
                      {log.resource_type}{log.resource_id ? ` · ${log.resource_id.slice(0, 8)}` : ""}
                    </span>
                  )}
                </div>

                {/* Timestamp */}
                <div className="shrink-0 text-right">
                  <p className="text-xs font-medium text-gray-500 whitespace-nowrap">{formatTimeOnly(log.created_at)}</p>
                  <p className="text-[10px] text-gray-300 mt-0.5 whitespace-nowrap">{formatDate(log.created_at).split(",")[0]}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {data && data.pages > 1 && (
          <div className="px-5 py-3.5 border-t border-gray-100 flex items-center justify-between bg-gray-50/50">
            <span className="text-xs text-gray-400">
              {data.total.toLocaleString()} events &middot; page {data.page} of {data.pages}
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-gray-600 rounded-lg hover:bg-white hover:border hover:border-gray-200 disabled:opacity-40 transition-all"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(data.pages, p + 1))}
                disabled={page === data.pages}
                className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-gray-600 rounded-lg hover:bg-white hover:border hover:border-gray-200 disabled:opacity-40 transition-all"
              >
                Next
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
