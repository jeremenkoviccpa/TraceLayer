"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import type { Invitation, Member } from "@/lib/types";
import { Users, Mail, Trash2, Plus, Copy, Check, Shield, UserCheck, Lock, Zap } from "lucide-react";
import { usePlan } from "@/hooks/usePlan";
import { useUpgrade } from "@/components/plan-gate";

const FREE_MEMBER_LIMIT = 3;

function getInitials(email: string) {
  return email.slice(0, 2).toUpperCase();
}

function getRoleColor(role: string) {
  if (role === "admin") return "bg-violet-500";
  return "bg-indigo-400";
}

function RoleBadge({ role }: { role: string }) {
  if (role === "admin") {
    return (
      <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-violet-100 text-violet-700">
        <Shield className="w-2.5 h-2.5" />
        Admin
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">
      <UserCheck className="w-2.5 h-2.5" />
      Member
    </span>
  );
}

export default function TeamPage() {
  const { user } = useAuth();
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "admin">("member");
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [showInviteForm, setShowInviteForm] = useState(false);
  const [toast, setToast] = useState("");

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 3000);
  };

  const load = async () => {
    try {
      const [m, i] = await Promise.all([api.getMembers(), api.getInvites()]);
      setMembers(m);
      setInvites(i);
    } catch {
      // non-admins can't see invites — just load members
      try {
        setMembers(await api.getMembers());
      } catch { /* ignore */ }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    setSending(true);
    try {
      const inv = await api.createInvite(inviteEmail, inviteRole);
      setInviteEmail("");
      setShowInviteForm(false);
      await load();
      await navigator.clipboard.writeText(inv.invite_url).catch(() => {});
      showToast("Invite created — link copied to clipboard");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to send invite");
    } finally {
      setSending(false);
    }
  };

  const handleCopy = async (url: string, id: string) => {
    await navigator.clipboard.writeText(url).catch(() => {});
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const handleRevoke = async (id: string) => {
    try {
      await api.revokeInvite(id);
      await load();
      showToast("Invite revoked");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to revoke invite");
    }
  };

  const handleRemove = async (memberId: string) => {
    if (!confirm("Remove this member from the organization?")) return;
    try {
      await api.removeMember(memberId);
      await load();
      showToast("Member removed");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to remove member");
    }
  };

  const { isPro } = usePlan();
  const { trigger: triggerUpgrade } = useUpgrade();
  const isAdmin = user?.role === "admin";
  const adminCount = members.filter((m) => m.role === "admin").length;
  const memberCount = members.filter((m) => m.role !== "admin").length;
  const atMemberLimit = !isPro && members.length >= FREE_MEMBER_LIMIT;

  return (
    <div className="space-y-6 overflow-x-hidden">
      {/* Toast */}
      {toast && (
        <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-lg z-50 flex items-center gap-2">
          <Check className="w-3.5 h-3.5 text-green-400" />
          {toast}
        </div>
      )}

      {/* Dark Hero Card */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-2xl p-5 sm:p-6 shadow-xl">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4 flex-1 min-w-0">
            {/* Icon */}
            <div className="w-10 h-10 sm:w-11 sm:h-11 rounded-xl flex items-center justify-center shrink-0" style={{ backgroundColor: "rgba(99,102,241,0.2)" }}>
              <Users className="w-5 h-5" style={{ color: "#6366F1" }} />
            </div>
            {/* Title + Stats */}
            <div className="flex-1 min-w-0">
              <h1 className="text-xl font-bold text-white">Team</h1>
              <p className="text-sm text-slate-400 mt-0.5">Manage your team members and their roles.</p>
              {/* Stats */}
              <div className="flex flex-wrap gap-4 sm:gap-6 mt-4">
                <div>
                  <p className="text-2xl font-bold" style={{ color: "#6366F1" }}>
                    {loading ? "—" : members.length}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">Total members</p>
                </div>
                <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
                <div>
                  <p className="text-2xl font-bold text-violet-400">
                    {loading ? "—" : adminCount}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">Admins</p>
                </div>
                <div className="hidden sm:block w-px h-8 bg-slate-700 self-center" />
                <div>
                  <p className="text-2xl font-bold text-slate-300">
                    {loading ? "—" : memberCount}
                  </p>
                  <p className="text-xs text-slate-400 mt-0.5">Members</p>
                </div>
              </div>
              {/* Free plan seat usage — admins only */}
              {!isPro && !loading && isAdmin && (
                <div className="mt-4 max-w-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[11px] text-slate-400">
                      {members.length} / {FREE_MEMBER_LIMIT} seats used
                    </span>
                    {atMemberLimit && (
                      <button onClick={triggerUpgrade} className="flex items-center gap-1 text-[10px] font-semibold text-amber-300 hover:text-amber-200 transition-colors">
                        <Zap className="w-2.5 h-2.5" /> Upgrade for unlimited
                      </button>
                    )}
                  </div>
                  <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${atMemberLimit ? "bg-amber-400" : "bg-violet-500"}`}
                      style={{ width: `${Math.min((members.length / FREE_MEMBER_LIMIT) * 100, 100)}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
          {/* Action Button */}
          {isAdmin && (
            atMemberLimit ? (
              <button
                onClick={triggerUpgrade}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 shadow-sm shrink-0 transition-colors self-start sm:self-auto"
              >
                <Lock className="w-4 h-4 text-amber-500" />
                Upgrade to invite more
              </button>
            ) : (
              <button
                onClick={() => setShowInviteForm(true)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white shadow-lg shrink-0 transition-opacity hover:opacity-90 self-start sm:self-auto"
                style={{ backgroundColor: "#6366F1" }}
              >
                <Plus className="w-4 h-4" />
                Invite member
              </button>
            )
          )}
        </div>
      </div>

      {/* Invite Form Modal */}
      {showInviteForm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-gray-100 shadow-2xl p-6 w-full max-w-sm">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ backgroundColor: "rgba(99,102,241,0.1)" }}>
                <Plus className="w-4 h-4" style={{ color: "#6366F1" }} />
              </div>
              <h2 className="font-semibold text-gray-900">Invite someone</h2>
            </div>
            <form onSubmit={handleInvite} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Email address</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                  placeholder="colleague@company.com"
                  className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5">Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as "member" | "admin")}
                  className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-400"
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2 pt-1">
                <button
                  type="button"
                  onClick={() => setShowInviteForm(false)}
                  className="flex-1 border border-gray-200 text-gray-600 text-sm font-medium px-4 py-2.5 rounded-xl hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={sending}
                  className="flex-1 text-white text-sm font-semibold px-4 py-2.5 rounded-xl transition-opacity disabled:opacity-60"
                  style={{ backgroundColor: "#6366F1" }}
                >
                  {sending ? "Sending…" : "Send invite"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Members Grid */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <div className="flex items-center gap-2 mb-5">
          <Users className="w-4 h-4 text-gray-400" />
          <h2 className="font-semibold text-gray-800">Members</h2>
          <span className="ml-auto text-xs text-gray-400 font-medium">{members.length} total</span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-20 bg-gray-50 rounded-xl animate-pulse" />
            ))}
          </div>
        ) : members.length === 0 ? (
          <div className="text-center py-12 text-sm text-gray-400">No members yet.</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {members.map((m) => (
              <div
                key={m.id}
                className="flex items-center gap-3 p-4 rounded-xl border border-gray-100 hover:border-indigo-100 hover:bg-indigo-50/30 transition-all group"
              >
                {/* Avatar */}
                <div className={`w-9 h-9 rounded-xl ${getRoleColor(m.role)} flex items-center justify-center shrink-0`}>
                  <span className="text-white text-xs font-bold">{getInitials(m.email)}</span>
                </div>
                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{m.email}</p>
                  <div className="mt-1">
                    <RoleBadge role={m.role} />
                  </div>
                </div>
                {/* Remove */}
                {isAdmin && m.id !== user?.id && (
                  <button
                    onClick={() => handleRemove(m.id)}
                    className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    title="Remove member"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pending Invites */}
      {isAdmin && invites.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-100 p-6">
          <div className="flex items-center gap-2 mb-5">
            <Mail className="w-4 h-4 text-gray-400" />
            <h2 className="font-semibold text-gray-800">Pending invites</h2>
            <span className="ml-1 inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-700">
              {invites.length}
            </span>
          </div>
          <div className="space-y-2">
            {invites.map((inv) => (
              <div
                key={inv.id}
                className="flex items-center justify-between p-3 rounded-xl border border-dashed border-gray-200 hover:border-indigo-200 hover:bg-indigo-50/20 transition-all group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                    <Mail className="w-3.5 h-3.5 text-gray-400" />
                  </div>
                  <div>
                    <p className="text-sm text-gray-900 font-medium">{inv.email}</p>
                    <RoleBadge role={inv.role} />
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleCopy(inv.invite_url, inv.id)}
                    className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
                    title="Copy invite link"
                  >
                    {copied === inv.id ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    onClick={() => handleRevoke(inv.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Revoke invite"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
