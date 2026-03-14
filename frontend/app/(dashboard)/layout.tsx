"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import {
  LayoutDashboard,
  Plug,
  ShieldCheck,
  FileText,
  Database,
  Users,
  Settings,
  LogOut,
  Menu,
  X,
  MailWarning,
  ScrollText,
} from "lucide-react";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/integrations", label: "Integrations", icon: Plug },
  { href: "/compliance", label: "Compliance", icon: ShieldCheck },
  { href: "/evidence", label: "Evidence", icon: Database },
  { href: "/reports", label: "Reports", icon: FileText },
  { href: "/team", label: "Team", icon: Users },
  { href: "/audit-log", label: "Audit Log", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [resendSent, setResendSent] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);

  const handleResend = async () => {
    setResendLoading(true);
    try {
      await (await import("@/lib/api")).api.resendVerification();
      setResendSent(true);
    } catch {
      // silent
    } finally {
      setResendLoading(false);
    }
  };

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [user, loading, router]);

  // Close sidebar on navigation
  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-64 md:w-56 bg-white border-r border-gray-200 flex flex-col
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        <div className="px-5 py-5 border-b border-gray-200 flex items-center justify-between">
          <span className="text-lg font-bold text-gray-900">TraceLayer</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden text-gray-400 hover:text-gray-600 p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`}
              >
                <Icon className="w-4 h-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="px-3 py-4 border-t border-gray-200">
          <div className="px-3 py-2 text-xs text-gray-500 truncate">{user.email}</div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 hover:text-gray-900 w-full transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 md:ml-56 flex flex-col min-h-screen">
        {/* Mobile top bar */}
        <header className="md:hidden sticky top-0 z-20 bg-white border-b border-gray-200 px-4 h-14 flex items-center gap-3 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-600 hover:text-gray-900 p-1 -ml-1"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="font-bold text-gray-900">TraceLayer</span>
        </header>

        {/* Email verification banner */}
        {user && !user.email_verified && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
            <div className="flex items-center gap-2 text-sm text-amber-800 flex-1">
              <MailWarning className="w-4 h-4 shrink-0 text-amber-600" />
              <span>Please verify your email address to ensure uninterrupted access.</span>
            </div>
            {resendSent ? (
              <span className="text-xs text-amber-700 font-medium shrink-0">Email sent!</span>
            ) : (
              <button
                onClick={handleResend}
                disabled={resendLoading}
                className="text-xs font-semibold text-amber-800 underline underline-offset-2 hover:text-amber-900 disabled:opacity-60 shrink-0 text-left sm:text-right"
              >
                {resendLoading ? "Sending…" : "Resend verification email"}
              </button>
            )}
          </div>
        )}

        <main className="flex-1 p-4 md:p-8">{children}</main>
      </div>
    </div>
  );
}
