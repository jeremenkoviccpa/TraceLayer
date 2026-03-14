"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";
import type { Invitation, Member } from "@/lib/types";
import { Users, Mail, Trash2, Plus, Copy, Check } from "lucide-react";

export default function TeamPage() {
  const { user } = useAuth();
  const [members, setMembers] = useState<Member[]>([]);
  const [invites, setInvites] = useState<Invitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"member" | "admin">("member");
  const [sending, setSending] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
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
      await load();
      // Auto-copy invite URL
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

  const isAdmin = user?.role === "admin";

  return (
    <div>
      {toast && (
        <div className="fixed top-4 right-4 bg-gray-900 text-white text-sm px-4 py-2 rounded-lg shadow-lg z-50">
          {toast}
        </div>
      )}

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Team</h1>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Members */}
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Users className="w-4 h-4 text-gray-400" />
            <h2 className="font-semibold text-gray-800">Members ({members.length})</h2>
          </div>

          {loading ? (
            <div className="flex justify-center py-8">
              <div className="w-5 h-5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : (
            <div className="space-y-2">
              {members.map((m) => (
                <div key={m.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{m.email}</p>
                    <p className="text-xs text-gray-400 capitalize">{m.role}</p>
                  </div>
                  {isAdmin && m.id !== user?.id && (
                    <button
                      onClick={() => handleRemove(m.id)}
                      className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
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

        {/* Invite */}
        {isAdmin && (
          <div className="space-y-4">
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <Plus className="w-4 h-4 text-gray-400" />
                <h2 className="font-semibold text-gray-800">Invite someone</h2>
              </div>

              <form onSubmit={handleInvite} className="space-y-3">
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  required
                  placeholder="colleague@company.com"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value as "member" | "admin")}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
                <button
                  type="submit"
                  disabled={sending}
                  className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-60 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  {sending ? "Sending…" : "Send invite"}
                </button>
              </form>
            </div>

            {/* Pending invites */}
            {invites.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Mail className="w-4 h-4 text-gray-400" />
                  <h2 className="font-semibold text-gray-800">Pending invites</h2>
                </div>
                <div className="space-y-2">
                  {invites.map((inv) => (
                    <div key={inv.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
                      <div>
                        <p className="text-sm text-gray-900">{inv.email}</p>
                        <p className="text-xs text-gray-400 capitalize">{inv.role}</p>
                      </div>
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleCopy(inv.invite_url, inv.id)}
                          className="p-1.5 text-gray-400 hover:text-brand-600 hover:bg-brand-50 rounded transition-colors"
                          title="Copy invite link"
                        >
                          {copied === inv.id ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>
                        <button
                          onClick={() => handleRevoke(inv.id)}
                          className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition-colors"
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
        )}
      </div>
    </div>
  );
}
