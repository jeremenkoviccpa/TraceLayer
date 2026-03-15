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
  AlertTriangle,
  BookOpen,
  ClipboardList,
  GraduationCap,
  ShieldAlert,
  Building2,
  UserCheck,
  Target,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Zap,
} from "lucide-react";
import { usePlan } from "@/hooks/usePlan";

type NavItem = { href: string; label: string; icon: React.ElementType };
type NavGroup = { title?: string; items: NavItem[] };

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { href: "/dashboard",  label: "Dashboard",  icon: LayoutDashboard },
      { href: "/readiness",  label: "Readiness",  icon: Target },
    ],
  },
  {
    title: "Evidence",
    items: [
      { href: "/compliance",   label: "Controls",      icon: ShieldCheck },
      { href: "/evidence",     label: "Evidence",      icon: Database },
      { href: "/integrations", label: "Integrations",  icon: Plug },
    ],
  },
  {
    title: "Security",
    items: [
      { href: "/risks",          label: "Risk Register",  icon: AlertTriangle },
      { href: "/pen-tests",      label: "Pen Tests",      icon: ShieldAlert },
      { href: "/vendors",        label: "Vendor Risk",    icon: Building2 },
      { href: "/access-reviews", label: "Access Reviews", icon: UserCheck },
    ],
  },
  {
    title: "People",
    items: [
      { href: "/training", label: "Training", icon: GraduationCap },
      { href: "/policies", label: "Policies",  icon: BookOpen },
    ],
  },
  {
    title: "Reporting",
    items: [
      { href: "/reports",        label: "Reports",        icon: FileText },
      { href: "/questionnaire",  label: "Questionnaire",  icon: ClipboardList },
      { href: "/audit-package",  label: "Audit Package",  icon: Sparkles },
    ],
  },
  {
    items: [
      { href: "/team",      label: "Team",      icon: Users },
      { href: "/audit-log", label: "Audit Log", icon: ScrollText },
      { href: "/settings",  label: "Settings",  icon: Settings },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [resendSent, setResendSent] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const { isPro } = usePlan();

  // Persist collapse state
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored === "true") setCollapsed(true);
  }, []);

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      localStorage.setItem("sidebar-collapsed", String(!c));
      return !c;
    });
  };

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

  // Redirect new users to onboarding (checked once per session)
  useEffect(() => {
    if (loading || !user || onboardingChecked) return;
    if (sessionStorage.getItem("onboarding_done") === "true") {
      setOnboardingChecked(true);
      return;
    }
    (async () => {
      try {
        const { api: apiClient } = await import("@/lib/api");
        const company = await apiClient.getCompany();
        if (!company.onboarding_completed) {
          router.replace("/onboarding");
          return;
        }
        sessionStorage.setItem("onboarding_done", "true");
      } catch {
        // non-fatal
      } finally {
        setOnboardingChecked(true);
      }
    })();
  }, [user, loading, router, onboardingChecked]);

  useEffect(() => {
    setMobileOpen(false);
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
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-30 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-40 bg-white border-r border-gray-100 flex flex-col
          transition-all duration-200 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0
          ${collapsed ? "md:w-16" : "md:w-60"}
          w-60`}
      >
        {/* Logo */}
        <div className={`h-16 border-b border-gray-100 flex items-center shrink-0 transition-all duration-200 ${collapsed ? "justify-center px-0" : "justify-between px-4"}`}>
          {collapsed ? (
            <Link href="/dashboard" className="flex items-center justify-center">
              <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
            </Link>
          ) : (
            <>
              <Link href="/dashboard" className="flex items-center gap-2.5">
                <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
                <span className="text-base font-bold text-gray-900 tracking-tight">TraceLayer</span>
              </Link>
              <button
                onClick={() => setMobileOpen(false)}
                className="md:hidden text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 overflow-y-auto overflow-x-hidden">
          <div className={`space-y-5 ${collapsed ? "px-2" : "px-3"}`}>
            {NAV_GROUPS.map((group, gi) => (
              <div key={gi}>
                {/* Section label — hidden when collapsed */}
                {group.title && !collapsed && (
                  <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-widest text-gray-400">
                    {group.title}
                  </p>
                )}
                {/* Thin divider for collapsed groups that have a title */}
                {group.title && collapsed && gi > 0 && (
                  <div className="border-t border-gray-100 mb-1" />
                )}
                <div className="space-y-0.5">
                  {group.items.map(({ href, label, icon: Icon }) => {
                    const active = pathname === href;
                    return (
                      <div key={href} className="relative group/item">
                        <Link
                          href={href}
                          className={`flex items-center rounded-xl text-sm font-medium transition-all duration-150
                            ${collapsed ? "justify-center w-10 h-10 mx-auto" : "gap-3 px-3 py-2"}
                            ${active
                              ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20"
                              : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                            }`}
                        >
                          <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-gray-400"}`} />
                          {!collapsed && label}
                        </Link>
                        {/* Tooltip for collapsed mode */}
                        {collapsed && (
                          <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50
                            opacity-0 group-hover/item:opacity-100 transition-opacity duration-150">
                            <div className="bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-lg">
                              {label}
                              <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </nav>

        {/* Free plan upgrade nudge — shown only when sidebar is expanded */}
        {!isPro && !collapsed && (
          <div className="px-3 pb-2 shrink-0">
            <Link
              href="/settings#billing"
              className="flex items-center gap-2.5 border border-gray-200 hover:border-brand-200 hover:bg-brand-50/40 rounded-xl px-3 py-2 transition-all group"
            >
              <div className="w-5 h-5 rounded-md bg-amber-50 border border-amber-200/80 flex items-center justify-center shrink-0">
                <Zap className="w-3 h-3 text-amber-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-gray-600 group-hover:text-brand-700 leading-none truncate">Upgrade to Growth</p>
                <p className="text-[10px] text-gray-400 mt-0.5 truncate">AI · PDF reports · $99/mo</p>
              </div>
            </Link>
          </div>
        )}

        {/* Collapse toggle — desktop only */}
        <div className={`hidden md:flex border-t border-gray-100 py-2 shrink-0 ${collapsed ? "justify-center px-2" : "px-3"}`}>
          <button
            onClick={toggleCollapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`flex items-center gap-2 text-xs text-gray-400 hover:text-gray-700 hover:bg-gray-50 rounded-xl transition-all duration-150
              ${collapsed ? "w-10 h-8 justify-center" : "px-3 py-2 w-full"}`}
          >
            {collapsed
              ? <ChevronRight className="w-3.5 h-3.5 shrink-0" />
              : <><ChevronLeft className="w-3.5 h-3.5 shrink-0" /><span>Collapse</span></>
            }
          </button>
        </div>

        {/* User */}
        <div className={`border-t border-gray-100 py-3 shrink-0 space-y-0.5 ${collapsed ? "px-2" : "px-3"}`}>
          {/* Avatar row */}
          <div className={`flex items-center rounded-xl py-2 ${collapsed ? "justify-center" : "gap-3 px-3"}`}>
            <div className="w-7 h-7 rounded-lg bg-brand-100 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-brand-700">{initials}</span>
            </div>
            {!collapsed && (
              <span className="text-xs text-gray-500 truncate flex-1">{user.email}</span>
            )}
          </div>
          {/* Sign out */}
          <div className="relative group/logout">
            <button
              onClick={handleLogout}
              className={`flex items-center rounded-xl text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-900 w-full transition-all duration-150
                ${collapsed ? "justify-center w-10 h-10 mx-auto" : "gap-3 px-3 py-2"}`}
            >
              <LogOut className="w-4 h-4 text-gray-400 shrink-0" />
              {!collapsed && "Sign out"}
            </button>
            {collapsed && (
              <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50
                opacity-0 group-hover/logout:opacity-100 transition-opacity duration-150">
                <div className="bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-lg">
                  Sign out
                  <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main area — margin tracks sidebar width */}
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-200 ${collapsed ? "md:ml-16" : "md:ml-60"}`}>
        {/* Mobile top bar */}
        <header className="md:hidden sticky top-0 z-20 bg-white/80 backdrop-blur border-b border-gray-100 px-4 h-14 flex items-center gap-3 shrink-0">
          <button
            onClick={() => setMobileOpen(true)}
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
