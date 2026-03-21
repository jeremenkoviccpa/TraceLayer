"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { SuperAdminCompany, SuperAdminUser } from "@/lib/types";
import { ChevronDown, ChevronRight, Shield, Users, Building2, Crown } from "lucide-react";

const PLAN_COLORS: Record<string, string> = {
  growth: "bg-emerald-100 text-emerald-800 border border-emerald-200",
  free: "bg-slate-100 text-slate-600 border border-slate-200",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-purple-100 text-purple-700",
  member: "bg-blue-100 text-blue-700",
  viewer: "bg-slate-100 text-slate-600",
};

export default function SuperAdminPage() {
  const [companies, setCompanies] = useState<SuperAdminCompany[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [users, setUsers] = useState<Record<string, SuperAdminUser[]>>({});
  const [loadingUsers, setLoadingUsers] = useState<string | null>(null);
  const [saving, setSaving] = useState<string | null>(null);

  useEffect(() => {
    api.superAdminListCompanies()
      .then(setCompanies)
      .catch(() => setError("Access denied or unable to load companies."))
      .finally(() => setLoading(false));
  }, []);

  async function toggleExpand(id: string) {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
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
    } finally {
      setSaving(null);
    }
  }

  async function setPartner(company: SuperAdminCompany, val: boolean) {
    setSaving(company.id + ":partner");
    try {
      const updated = await api.superAdminPatchCompany(company.id, { is_partner_account: val });
      setCompanies((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } finally {
      setSaving(null);
    }
  }

  async function setUserRole(companyId: string, user: SuperAdminUser, role: string) {
    setSaving(user.id + ":role");
    try {
      const updated = await api.superAdminPatchUser(companyId, user.id, { role });
      setUsers((prev) => ({
        ...prev,
        [companyId]: prev[companyId].map((u) => (u.id === updated.id ? updated : u)),
      }));
    } finally {
      setSaving(null);
    }
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
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-purple-100 rounded-lg">
          <Shield className="w-6 h-6 text-purple-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Super Admin</h1>
          <p className="text-slate-500 text-sm">Manage companies and user access</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Building2 className="w-4 h-4" /> Companies
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalCompanies}</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Crown className="w-4 h-4 text-emerald-600" /> Growth plans
          </div>
          <div className="text-2xl font-bold text-slate-900">{growthCount}</div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Users className="w-4 h-4" /> Total users
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalUsers}</div>
        </div>
      </div>

      {/* Companies table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="text-left px-4 py-3 text-slate-500 font-medium w-6"></th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Company</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Admins</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Users</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Plan</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Partner</th>
              <th className="text-left px-4 py-3 text-slate-500 font-medium">Created</th>
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
                  <td className="px-4 py-3 font-medium text-slate-900">{company.name}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs">
                    {company.admin_emails.join(", ") || "—"}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{company.user_count}</td>
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
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
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
                  <td className="px-4 py-3 text-slate-400 text-xs">
                    {new Date(company.created_at).toLocaleDateString()}
                  </td>
                </tr>

                {/* Expanded user rows */}
                {expanded === company.id && (
                  <tr key={company.id + "-users"}>
                    <td colSpan={7} className="bg-slate-50 px-8 py-4">
                      {loadingUsers === company.id ? (
                        <p className="text-slate-400 text-sm">Loading users…</p>
                      ) : (
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-slate-400 text-xs">
                              <th className="text-left pb-2 pr-4">Email</th>
                              <th className="text-left pb-2 pr-4">Name</th>
                              <th className="text-left pb-2 pr-4">Role</th>
                              <th className="text-left pb-2">Verified</th>
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
                                <td className="py-1.5">
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${user.email_verified ? "text-emerald-600" : "text-amber-600"}`}>
                                    {user.email_verified ? "Verified" : "Unverified"}
                                  </span>
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
