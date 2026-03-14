"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import Image from "next/image";
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
  { href: "/dashboard",   label: "Dashboard",   icon: LayoutDashboard },
  { href: "/integrations",label: "Integrations", icon: Plug },
  { href: "/compliance",  label: "Compliance",   icon: ShieldCheck },
  { href: "/evidence",    label: "Evidence",     icon: Database },
  { href: "/reports",     label: "Reports",      icon: FileText },
  { href: "/team",        label: "Team",         icon: Users },
  { href: "/audit-log",   label: "Audit Log",    icon: ScrollText },
  { href: "/settings",    label: "Settings",     icon: Settings },
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

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-warm-100">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-400">Loading…</p>
        </div>
      </div>
    );
  }

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  const initials = user.email.slice(0, 2).toUpperCase();

  return (
    <div className="flex min-h-screen bg-warm-100">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 w-60 bg-white border-r border-gray-100 flex flex-col
          transform transition-transform duration-200 ease-in-out
          ${sidebarOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        {/* Logo */}
        <div className="px-4 h-16 border-b border-gray-100 flex items-center justify-between shrink-0">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={32} height={32} className="rounded-lg" />
            <span className="text-base font-bold text-gray-900 tracking-tight">TraceLayer</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="md:hidden text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                  active
                    ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20"
                    : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-gray-400"}`} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* User */}
        <div className="px-3 py-4 border-t border-gray-100 space-y-1 shrink-0">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl">
            <div className="w-7 h-7 rounded-lg bg-brand-100 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-brand-700">{initials}</span>
            </div>
            <span className="text-xs text-gray-500 truncate flex-1">{user.email}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-900 w-full transition-all duration-150"
          >
            <LogOut className="w-4 h-4 text-gray-400" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex-1 md:ml-60 flex flex-col min-h-screen">
        {/* Mobile top bar */}
        <header className="md:hidden sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-gray-100 px-4 h-14 flex items-center gap-3 shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="text-gray-500 hover:text-gray-900 p-1.5 rounded-lg hover:bg-gray-100 transition-colors -ml-1"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Image src="/logo-icon.png" alt="TraceLayer" width={24} height={24} className="rounded-md" />
            <span className="font-bold text-gray-900 text-sm">TraceLayer</span>
          </div>
        </header>

        {/* Email verification banner */}
        {user && !user.email_verified && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
            <div className="flex items-center gap-2 text-sm text-amber-800 flex-1">
              <MailWarning className="w-4 h-4 shrink-0 text-amber-600" />
              <span>Please verify your email to ensure uninterrupted access.</span>
            </div>
            {resendSent ? (
              <span className="text-xs text-amber-700 font-semibold shrink-0">✓ Email sent!</span>
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

        <main className="flex-1 p-5 md:p-8 max-w-7xl mx-auto w-full">{children}</main>
      </div>
    </div>
  );
}
