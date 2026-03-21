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
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Zap,
  ArrowLeftCircle,
  LifeBuoy,
  Siren,
  Bug,
  Server,
  RefreshCw,
  UserMinus,
  Bell,
  BookCheck,
  ShieldX,
  UserSearch,
  ClipboardCheck,
  BadgeCheck,
  Archive,
} from "lucide-react";
import type { AppNotification } from "@/lib/types";
import { usePlan } from "@/hooks/usePlan";
import { api } from "@/lib/api";
import AppTour from "@/components/AppTour";

type NavItem = { href: string; label: string; icon: React.ElementType; tourId?: string };
type NavGroup = { title?: string; items: NavItem[] };

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/readiness", label: "Readiness", icon: Target },
    ],
  },
  {
    title: "Compliance",
    items: [
      { href: "/compliance",   label: "Controls",     icon: ShieldCheck },
      { href: "/evidence",     label: "Evidence",     icon: Database    },
      { href: "/integrations", label: "Integrations", icon: Plug,       tourId: "tour-integrations" },
    ],
  },
  {
    title: "Risk & Security",
    items: [
      { href: "/risks",           label: "Risk Register",  icon: AlertTriangle },
      { href: "/incidents",       label: "Incidents",      icon: Siren         },
      { href: "/vulnerabilities", label: "Vulnerabilities", icon: Bug          },
      { href: "/pen-tests",       label: "Pen Tests",      icon: ShieldAlert   },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/assets",              label: "Asset Inventory",     icon: Server    },
      { href: "/business-continuity", label: "Business Continuity", icon: RefreshCw },
      { href: "/vendors",             label: "Vendor Risk",         icon: Building2 },
      { href: "/access-reviews",      label: "Access Reviews",      icon: UserCheck },
    ],
  },
  {
    title: "People",
    items: [
      { href: "/training",          label: "Training",          icon: GraduationCap },
      { href: "/policies",          label: "Policies",          icon: BookOpen      },
      { href: "/background-checks", label: "Background Checks", icon: BadgeCheck    },
      { href: "/offboarding",       label: "Offboarding",       icon: UserMinus     },
    ],
  },
  {
    title: "Privacy",
    items: [
      { href: "/soa",              label: "Statement of Applicability", icon: BookCheck  },
      { href: "/ropa",             label: "Data Processing (RoPA)",     icon: Archive    },
      { href: "/data-breaches",    label: "Breach Register",            icon: ShieldX    },
      { href: "/subject-requests", label: "Subject Requests",           icon: UserSearch },
    ],
  },
  {
    title: "Reporting",
    items: [
      { href: "/reports",            label: "Reports",           icon: FileText       },
      { href: "/questionnaire",      label: "Questionnaire",     icon: ClipboardList  },
      { href: "/audit-package",      label: "Audit Package",     icon: Sparkles       },
      { href: "/management-reviews", label: "Management Reviews", icon: ClipboardCheck },
    ],
  },
  {
    items: [
      { href: "/team",      label: "Team",      icon: Users     },
      { href: "/audit-log", label: "Audit Log", icon: ScrollText },
      { href: "/settings",  label: "Settings",  icon: Settings  },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout, exitClientContext } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());
  const [resendSent, setResendSent] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [clientName, setClientName] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [notifOpen, setNotifOpen] = useState(false);
  const unreadCount = notifications.filter((n) => !n.read).length;
  const { isPro } = usePlan();

  useEffect(() => {
    setClientName(api.isInClientContext() ? api.getActiveClientName() : null);
  }, []);

  // Notification polling
  useEffect(() => {
    if (!user) return;
    const load = () => api.getNotifications().then(setNotifications).catch(() => {});
    load();
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, [user]);

  const markNotifRead = (id: string) => {
    api.markNotificationRead(id).catch(() => {});
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllNotifRead = () => {
    api.markAllNotificationsRead().catch(() => {});
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  // Persist collapse state
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored === "true") setCollapsed(true);
  }, []);

  // Load open groups from localStorage + auto-expand current active group on mount
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-open-groups");
    const initial: Set<string> = stored ? new Set(JSON.parse(stored)) : new Set();
    const activeGroup = NAV_GROUPS.find(
      (g) => g.title && g.items.some((i) => i.href === pathname)
    );
    if (activeGroup?.title) initial.add(activeGroup.title);
    setOpenGroups(initial);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-expand group when navigating to a page inside a collapsed group
  useEffect(() => {
    const activeGroup = NAV_GROUPS.find(
      (g) => g.title && g.items.some((i) => i.href === pathname)
    );
    if (!activeGroup?.title) return;
    setOpenGroups((prev) => {
      if (prev.has(activeGroup.title!)) return prev;
      const next = new Set(prev);
      next.add(activeGroup.title!);
      localStorage.setItem("sidebar-open-groups", JSON.stringify([...next]));
      return next;
    });
  }, [pathname]);

  const toggleGroup = (title: string) => {
    setOpenGroups((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      localStorage.setItem("sidebar-open-groups", JSON.stringify([...next]));
      return next;
    });
  };

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
        if (company.is_partner_account) {
          router.replace("/partner/clients");
          return;
        }
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
            {NAV_GROUPS.map((group, gi) => {
              const isOpen = !group.title || collapsed || openGroups.has(group.title);
              return (
                <div key={gi}>
                  {/* Section label — clickable toggle when expanded, divider when collapsed */}
                  {group.title && !collapsed && (
                    <button
                      id={
                        group.title === "Compliance" ? "tour-nav-compliance" :
                        group.title === "Risk & Security" ? "tour-nav-risk" :
                        group.title === "Reporting" ? "tour-nav-reporting" :
                        undefined
                      }
                      onClick={() => toggleGroup(group.title!)}
                      className="w-full flex items-center justify-between px-3 mb-1 rounded-lg py-0.5 group/section hover:bg-gray-50 transition-colors"
                    >
                      <p className="text-[10px] font-semibold uppercase tracking-widest text-gray-400 group-hover/section:text-gray-600 transition-colors">
                        {group.title}
                      </p>
                      <ChevronDown
                        className={`w-3 h-3 text-gray-300 group-hover/section:text-gray-500 transition-all duration-200 ${isOpen ? "" : "-rotate-90"}`}
                      />
                    </button>
                  )}
                  {group.title && collapsed && gi > 0 && (
                    <div className="border-t border-gray-100 mb-1" />
                  )}
                  {isOpen && (
                    <div className="space-y-0.5">
                      {group.items.map(({ href, label, icon: Icon, tourId }) => {
                        const active = pathname === href;
                        return (
                          <div key={href} className="relative group/item">
                            <Link
                              href={href}
                              id={tourId}
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
                  )}
                </div>
              );
            })}
          </div>
        </nav>

        {/* Free plan upgrade CTA — shown only when sidebar is expanded */}
        {!isPro && !collapsed && (
          <div className="px-3 pb-3 shrink-0">
            <Link
              href="/settings#billing"
              className="block rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 px-3.5 py-3 shadow-sm shadow-brand-600/30 hover:shadow-brand-600/50 hover:from-brand-500 hover:to-brand-600 transition-all group"
            >
              <div className="flex items-center gap-2 mb-2">
                <div className="w-5 h-5 rounded-md bg-white/20 flex items-center justify-center shrink-0">
                  <Zap className="w-3 h-3 text-white" />
                </div>
                <p className="text-xs font-bold text-white leading-none">Upgrade to Growth</p>
              </div>
              <p className="text-[10px] text-white/70 leading-snug mb-2.5">Unlock AI features, PDF reports, all 7 frameworks &amp; more.</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/90">$149 / mo</span>
                <span className="text-[10px] font-semibold text-brand-200 group-hover:text-white transition-colors">Upgrade →</span>
              </div>
            </Link>
          </div>
        )}

        {/* Help & Support */}
        <div className={`border-t border-gray-100 pt-2 pb-1 shrink-0 ${collapsed ? "px-2" : "px-3"}`}>
          <div className="relative group/help">
            <a
              href="mailto:support@tracelayer.it.com"
              className={`flex items-center rounded-xl text-sm text-gray-400 hover:bg-gray-50 hover:text-gray-700 transition-all duration-150
                ${collapsed ? "justify-center w-10 h-10 mx-auto" : "gap-3 px-3 py-2 w-full"}`}
            >
              <LifeBuoy className="w-4 h-4 shrink-0" />
              {!collapsed && <span className="text-xs">Help & Support</span>}
            </a>
            {collapsed && (
              <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50
                opacity-0 group-hover/help:opacity-100 transition-opacity duration-150">
                <div className="bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-lg">
                  Help & Support
                  <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                </div>
              </div>
            )}
          </div>
        </div>

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
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-200 overflow-x-hidden ${collapsed ? "md:ml-16" : "md:ml-60"}`}>
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
          <button
            onClick={() => setNotifOpen((o) => !o)}
            className="relative ml-auto text-gray-500 hover:text-gray-900 p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-0.5 right-0.5 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>
        </header>

        {/* Partner client context banner */}
        {clientName && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-sm text-amber-800 flex-1 min-w-0">
              <Building2 className="w-4 h-4 shrink-0 text-amber-600" />
              <span className="truncate">
                Viewing client: <span className="font-semibold">{clientName}</span>
              </span>
            </div>
            <button
              onClick={async () => {
                await exitClientContext();
                setClientName(null);
              }}
              className="flex items-center gap-1.5 text-xs font-semibold text-amber-800 hover:text-amber-900 shrink-0 underline underline-offset-2"
            >
              <ArrowLeftCircle className="w-3.5 h-3.5" />
              Exit client view
            </button>
          </div>
        )}

        {/* Email verification banner */}
        {user && !user.email_verified && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2.5 flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
            <div className="flex items-center gap-2 text-sm text-amber-800 flex-1 min-w-0">
              <MailWarning className="w-4 h-4 shrink-0 text-amber-600" />
              <span className="min-w-0 truncate">Please verify your email to ensure uninterrupted access.</span>
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

      <AppTour />

      {/* Desktop notification bell — fixed top-right */}
      <div className="hidden md:block fixed top-4 right-4 z-50">
        <button
          onClick={() => setNotifOpen((o) => !o)}
          className="relative bg-white border border-gray-100 text-gray-500 hover:text-gray-900 p-2 rounded-xl hover:bg-gray-50 transition-colors shadow-sm"
        >
          <Bell className="w-5 h-5" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[1.1rem] h-[1.1rem] bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center px-0.5">
              {unreadCount > 9 ? "9+" : unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* Notification panel */}
      {notifOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setNotifOpen(false)} />
          <div className="fixed top-14 right-4 md:top-14 z-50 w-80 bg-white rounded-2xl border border-gray-100 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
              <h3 className="font-semibold text-sm text-gray-900">Notifications</h3>
              {unreadCount > 0 && (
                <button onClick={markAllNotifRead} className="text-xs text-brand-600 hover:text-brand-700 font-medium">
                  Mark all read
                </button>
              )}
            </div>
            <div className="max-h-96 overflow-y-auto divide-y divide-gray-50">
              {notifications.length === 0 ? (
                <p className="text-center py-10 text-sm text-gray-400">No notifications</p>
              ) : (
                notifications.slice(0, 20).map((n) => (
                  <button
                    key={n.id}
                    onClick={() => markNotifRead(n.id)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${!n.read ? "bg-brand-50/40" : ""}`}
                  >
                    <p className={`text-sm ${!n.read ? "font-semibold text-gray-900" : "text-gray-700"}`}>{n.title}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                  </button>
                ))
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
