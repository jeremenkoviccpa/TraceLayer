"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SuperAdminCompany, SuperAdminUser } from "@/lib/types";
import {
  ChevronDown, ChevronRight, Shield, Users, Building2, Crown,
  Trash2, CheckCircle, RotateCcw, MoreHorizontal, X,
} from "lucide-react";

const PLAN_COLORS: Record<string, string> = {
  growth: "bg-emerald-100 text-emerald-800 border border-emerald-200",
  free: "bg-slate-100 text-slate-600 border border-slate-200",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  member: "bg-blue-100 text-blue-700",
  viewer: "bg-slate-100 text-slate-600",
};

function ConfirmModal({
  message,
  onConfirm,
  onCancel,
  danger = false,
}: {
  message: string;
  onConfirm: () => void;
  onCancel: () => void;
  danger?: boolean;
}) {
  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6">
        <div className="flex items-start gap-3 mb-4">
          {danger && <Trash2 className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />}
          <p className="text-sm text-slate-700 leading-relaxed">{message}</p>
        </div>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className={`px-4 py-2 text-sm rounded-lg font-medium text-white ${danger ? "bg-red-500 hover:bg-red-600" : "bg-[#0f766e] hover:bg-[#0d6460]"}`}
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

export default function SuperAdminPage() {
  const [companies, setCompanies] = useState<SuperAdminCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [users, setUsers] = useState<Record<string, SuperAdminUser[]>>({});
  const [loadingUsers, setLoadingUsers] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ message: string; action: () => Promise<void>; danger?: boolean } | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState<string | null>(null);

  useEffect(() => {
    api.superAdminListCompanies()
      .then(setCompanies)
      .catch(() => setError("Access denied or unable to load companies."))
      .finally(() => setLoading(false));
  }, []);

  async function toggleExpand(id: string) {
    if (expanded === id) { setExpanded(null); return; }
    setExpanded(id);
    if (!users[id]) {
      setLoadingUsers(id);
      try {
        const u = await api.superAdminListUsers(id);
        setUsers((prev) => ({ ...prev, [id]: u }));
      } finally {
        setLoadingUsers(null);
      }
    }
  }

  async function setPlan(company: SuperAdminCompany, plan: string) {
    setSaving(company.id + ":plan");
    try {
      const updated = await api.superAdminPatchCompany(company.id, { plan });
      setCompanies((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } finally { setSaving(null); }
  }

  async function setPartner(company: SuperAdminCompany, val: boolean) {
    setSaving(company.id + ":partner");
    try {
      const updated = await api.superAdminPatchCompany(company.id, { is_partner_account: val });
      setCompanies((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } finally { setSaving(null); }
  }

  async function resetSubscription(company: SuperAdminCompany) {
    setSaving(company.id + ":reset");
    try {
      const updated = await api.superAdminPatchCompany(company.id, { reset_subscription: true });
      setCompanies((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } finally { setSaving(null); }
  }

  async function deleteCompany(company: SuperAdminCompany) {
    setSaving(company.id + ":delete");
    try {
      await api.superAdminDeleteCompany(company.id);
      setCompanies((prev) => prev.filter((c) => c.id !== company.id));
      if (expanded === company.id) setExpanded(null);
    } finally { setSaving(null); }
  }

  async function setUserRole(companyId: string, user: SuperAdminUser, role: string) {
    setSaving(user.id + ":role");
    try {
      const updated = await api.superAdminPatchUser(companyId, user.id, { role });
      setUsers((prev) => ({ ...prev, [companyId]: prev[companyId].map((u) => (u.id === updated.id ? updated : u)) }));
    } finally { setSaving(null); }
  }

  async function forceVerifyUser(companyId: string, user: SuperAdminUser) {
    setSaving(user.id + ":verify");
    try {
      const updated = await api.superAdminPatchUser(companyId, user.id, { email_verified: true });
      setUsers((prev) => ({ ...prev, [companyId]: prev[companyId].map((u) => (u.id === updated.id ? updated : u)) }));
    } finally { setSaving(null); }
  }

  async function deleteUser(companyId: string, user: SuperAdminUser) {
    setSaving(user.id + ":delete");
    try {
      await api.superAdminDeleteUser(companyId, user.id);
      setUsers((prev) => ({ ...prev, [companyId]: prev[companyId].filter((u) => u.id !== user.id) }));
      // decrement user_count on company
      setCompanies((prev) => prev.map((c) => c.id === companyId ? { ...c, user_count: c.user_count - 1 } : c));
    } finally { setSaving(null); }
  }

  function ask(message: string, action: () => Promise<void>, danger = false) {
    setConfirm({ message, action, danger });
  }

  async function runConfirm() {
    if (!confirm) return;
    const action = confirm.action;
    setConfirm(null);
    await action();
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#0f766e]" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Shield className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <p className="text-slate-600 font-medium">{error}</p>
          <p className="text-slate-400 text-sm mt-1">This page is only accessible to internal admins.</p>
        </div>
      </div>
    );
  }

  const totalCompanies = companies.length;
  const growthCount = companies.filter((c) => c.plan === "growth").length;
  const totalUsers = companies.reduce((sum, c) => sum + c.user_count, 0);

  return (
    <div className="max-w-6xl mx-auto space-y-5" onClick={() => setUserMenuOpen(null)}>
      {confirm && (
        <ConfirmModal
          message={confirm.message}
          danger={confirm.danger}
          onConfirm={runConfirm}
          onCancel={() => setConfirm(null)}
        />
      )}

      {/* Header */}
      <div className="flex items-center gap-2.5">
        <div className="p-1.5 bg-purple-100 rounded-lg shrink-0">
          <Shield className="w-5 h-5 text-purple-600" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg sm:text-2xl font-bold text-slate-900 leading-tight">Super Admin</h1>
          <p className="text-slate-500 text-xs sm:text-sm hidden sm:block">Manage companies and user access</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-2 sm:gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-1.5 text-slate-500 text-xs sm:text-sm mb-1">
            <Building2 className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Companies</span>
            <span className="sm:hidden">Cos</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-slate-900">{totalCompanies}</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-1.5 text-slate-500 text-xs sm:text-sm mb-1">
            <Crown className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-emerald-600" />
            <span className="hidden sm:inline">Growth plans</span>
            <span className="sm:hidden">Growth</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-slate-900">{growthCount}</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-3 sm:p-4">
          <div className="flex items-center gap-1.5 text-slate-500 text-xs sm:text-sm mb-1">
            <Users className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Total users</span>
            <span className="sm:hidden">Users</span>
          </div>
          <div className="text-xl sm:text-2xl font-bold text-slate-900">{totalUsers}</div>
        </div>
      </div>

      {/* Companies table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-4 py-3 text-slate-500 font-medium w-6"></th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Company</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium hidden md:table-cell">Admins</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium hidden sm:table-cell">Users</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Plan</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium hidden lg:table-cell">Partner</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium hidden lg:table-cell">Created</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {companies.map((company) => (
              <>
                <tr
                  key={company.id}
                  className="hover:bg-slate-50 cursor-pointer"
                  onClick={() => toggleExpand(company.id)}
                >
                  <td className="px-4 py-3 text-slate-400">
                    {expanded === company.id
                      ? <ChevronDown className="w-4 h-4" />
                      : <ChevronRight className="w-4 h-4" />}
                  </td>
                  <td className="px-4 py-3 font-medium text-slate-900 max-w-[140px] sm:max-w-none truncate">{company.name}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs hidden md:table-cell">
                    {company.admin_emails.join(", ") || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600 hidden sm:table-cell">{company.user_count}</td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <select
                      value={company.plan}
                      onChange={(e) => setPlan(company, e.target.value)}
                      disabled={saving === company.id + ":plan"}
                      className={`text-xs font-medium px-2 py-1 rounded-full border-0 cursor-pointer focus:ring-2 focus:ring-[#0f766e] ${PLAN_COLORS[company.plan] ?? "bg-slate-100 text-slate-600"}`}
                    >
                      <option value="free">Free</option>
                      <option value="growth">Growth</option>
                    </select>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setPartner(company, !company.is_partner_account)}
                      disabled={saving === company.id + ":partner"}
                      className={`text-xs font-medium px-2 py-1 rounded-full transition-colors ${
                        company.is_partner_account
                          ? "bg-indigo-100 text-indigo-700 hover:bg-indigo-200"
                          : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                      }`}
                    >
                      {company.is_partner_account ? "Yes" : "No"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-slate-400 text-xs hidden lg:table-cell">
                    {new Date(company.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-1">
                      {/* Reset subscription */}
                      <button
                        title="Reset subscription to Free"
                        onClick={() => ask(
                          `Reset subscription for "${company.name}"? This will set plan to Free and clear billing data.`,
                          () => resetSubscription(company),
                        )}
                        disabled={saving === company.id + ":reset"}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                      {/* Delete company */}
                      <button
                        title="Delete company"
                        onClick={() => ask(
                          `Permanently delete "${company.name}" and all its data? This cannot be undone.`,
                          () => deleteCompany(company),
                          true,
                        )}
                        disabled={saving === company.id + ":delete"}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>

                {/* Expanded user rows */}
                {expanded === company.id && (
                  <tr key={company.id + "-users"}>
                    <td colSpan={8} className="bg-slate-50 px-4 sm:px-8 py-4">
                      {loadingUsers === company.id ? (
                        <p className="text-slate-400 text-sm">Loading users…</p>
                      ) : (users[company.id] ?? []).length === 0 ? (
                        <p className="text-slate-400 text-sm italic">No users in this company.</p>
                      ) : (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 text-xs">
                              <th className="text-left pb-2 pr-4">Email</th>
                              <th className="text-left pb-2 pr-4">Name</th>
                              <th className="text-left pb-2 pr-4">Role</th>
                              <th className="text-left pb-2 pr-4">Verified</th>
                              <th className="text-left pb-2">Actions</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100">
                            {(users[company.id] ?? []).map((user) => (
                              <tr key={user.id}>
                                <td className="py-1.5 pr-4 text-slate-700">{user.email}</td>
                                <td className="py-1.5 pr-4 text-slate-500">{user.full_name ?? "—"}</td>
                                <td className="py-1.5 pr-4">
                                  <select
                                    value={user.role}
                                    onChange={(e) => setUserRole(company.id, user, e.target.value)}
                                    disabled={saving === user.id + ":role"}
                                    className={`text-xs font-medium px-2 py-0.5 rounded-full border-0 cursor-pointer focus:ring-2 focus:ring-[#0f766e] ${ROLE_COLORS[user.role] ?? "bg-slate-100 text-slate-600"}`}
                                  >
                                    <option value="admin">Admin</option>
                                    <option value="member">Member</option>
                                    <option value="viewer">Viewer</option>
                                  </select>
                                </td>
                                <td className="py-1.5 pr-4">
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${user.email_verified ? "text-emerald-600" : "text-amber-600"}`}>
                                    {user.email_verified ? "Verified" : "Unverified"}
                                  </span>
                                </td>
                                <td className="py-1.5">
                                  <div className="flex items-center gap-1">
                                    {!user.email_verified && (
                                      <button
                                        title="Force-verify email"
                                        onClick={() => forceVerifyUser(company.id, user)}
                                        disabled={saving === user.id + ":verify"}
                                        className="p-1 rounded text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-colors"
                                      >
                                        <CheckCircle className="w-3.5 h-3.5" />
                                      </button>
                                    )}
                                    <button
                                      title="Delete user"
                                      onClick={() => ask(
                                        `Delete user "${user.email}" from this company?`,
                                        () => deleteUser(company.id, user),
                                        true,
                                      )}
                                      disabled={saving === user.id + ":delete"}
                                      className="p-1 rounded text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                                    >
                                      <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
