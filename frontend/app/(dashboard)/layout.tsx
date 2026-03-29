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
  ChevronDown,
  Sparkles,
  Zap,
  ArrowLeftCircle,
  LifeBuoy,
  Siren,
  Bug,
  Server,
  RefreshCw,
  UserMinus,
  BookCheck,
  ShieldX,
  UserSearch,
  ClipboardCheck,
  BadgeCheck,
  Archive,
  ShieldHalf,
  Workflow,
  Compass,
  Bot,
  Monitor,
} from "lucide-react";
import { usePlan } from "@/hooks/usePlan";
import { api } from "@/lib/api";
import AppTour from "@/components/AppTour";
import Toaster from "@/components/ui/Toaster";
import GlobalChat from "@/components/global-chat";

type NavItem = { href: string; label: string; icon: React.ElementType; tourId?: string };
type NavSection = {
  id: string;
  type: "flat" | "collapsible";
  number?: string;
  title?: string;
  tourNavId?: string;
  items: NavItem[];
};

const NAV_SECTIONS: NavSection[] = [
  {
    id: "top",
    type: "flat",
    items: [
      { href: "/dashboard", label: "Dashboard",       icon: LayoutDashboard },
      { href: "/guide",     label: "Getting Started", icon: Compass         },
    ],
  },
  {
    id: "scope",
    type: "collapsible",
    number: "1",
    title: "Scope & Setup",
    tourNavId: "tour-nav-compliance",
    items: [
      { href: "/integrations", label: "Integrations",  icon: Plug,      tourId: "tour-integrations" },
      { href: "/soa",          label: "Applicability", icon: BookCheck  },
    ],
  },
  {
    id: "policies",
    type: "collapsible",
    number: "2",
    title: "Policies",
    items: [
      { href: "/policies", label: "Policy Library", icon: BookOpen },
    ],
  },
  {
    id: "controls",
    type: "collapsible",
    number: "3",
    title: "Controls & Evidence",
    items: [
      { href: "/compliance", label: "Controls",  icon: ShieldCheck },
      { href: "/evidence",   label: "Evidence",  icon: Database    },
      { href: "/readiness",  label: "Readiness", icon: Target      },
    ],
  },
  {
    id: "risk",
    type: "collapsible",
    number: "4",
    title: "Risk & Security",
    tourNavId: "tour-nav-risk",
    items: [
      { href: "/risks",           label: "Risk Register",   icon: AlertTriangle },
      { href: "/incidents",       label: "Incidents",       icon: Siren         },
      { href: "/vulnerabilities", label: "Vulnerabilities", icon: Bug           },
      { href: "/pen-tests",       label: "Pen Tests",       icon: ShieldAlert   },
    ],
  },
  {
    id: "operations",
    type: "collapsible",
    number: "5",
    title: "Operations",
    items: [
      { href: "/assets",              label: "Asset Inventory",     icon: Server    },
      { href: "/devices",             label: "Device Monitoring",   icon: Monitor   },
      { href: "/access-reviews",      label: "Access Reviews",      icon: UserCheck },
      { href: "/vendors",             label: "Vendor Risk",         icon: Building2 },
      { href: "/business-continuity", label: "Business Continuity", icon: RefreshCw },
    ],
  },
  {
    id: "people",
    type: "collapsible",
    number: "6",
    title: "People",
    items: [
      { href: "/training",          label: "Training",          icon: GraduationCap },
      { href: "/background-checks", label: "Background Checks", icon: BadgeCheck    },
      { href: "/offboarding",       label: "Offboarding",       icon: UserMinus     },
    ],
  },
  {
    id: "privacy",
    type: "collapsible",
    number: "7",
    title: "Privacy",
    items: [
      { href: "/data-flows",       label: "Data Flow Map",    icon: Workflow   },
      { href: "/ropa",             label: "RoPA",             icon: Archive    },
      { href: "/data-breaches",    label: "Breach Register",  icon: ShieldX    },
      { href: "/subject-requests", label: "Subject Requests", icon: UserSearch },
    ],
  },
  {
    id: "ai",
    type: "collapsible",
    number: "8",
    title: "AI Governance",
    items: [
      { href: "/questionnaire", label: "AI Questionnaire", icon: ClipboardList },
      { href: "/audit-package", label: "AI Audit Package", icon: Sparkles      },
      { href: "/ai-agents",     label: "Agent Monitor",    icon: Bot            },
    ],
  },
  {
    id: "reports",
    type: "collapsible",
    title: "Audit & Reports",
    tourNavId: "tour-nav-reporting",
    items: [
      { href: "/reports",            label: "Reports",         icon: FileText       },
      { href: "/management-reviews", label: "Mgmt Reviews",    icon: ClipboardCheck },
      { href: "/portal",             label: "Auditor Portal",  icon: UserCheck      },
    ],
  },
  {
    id: "account",
    type: "collapsible",
    title: "Account",
    items: [
      { href: "/team",      label: "Team",      icon: Users      },
      { href: "/audit-log", label: "Audit Log", icon: ScrollText },
      { href: "/settings",  label: "Settings",  icon: Settings   },
    ],
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout, exitClientContext } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [openSections, setOpenSections] = useState<Set<string>>(new Set());
  const [resendSent, setResendSent] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [onboardingChecked, setOnboardingChecked] = useState(false);
  const [clientName, setClientName] = useState<string | null>(null);
  const { isPro } = usePlan();

  useEffect(() => {
    setClientName(api.isInClientContext() ? api.getActiveClientName() : null);
  }, []);

  // Persist collapse state
  useEffect(() => {
    const stored = localStorage.getItem("sidebar-collapsed");
    if (stored === "true") setCollapsed(true);
  }, []);

  // Load persisted open sections + auto-open the section containing the active route
  useEffect(() => {
    const stored = localStorage.getItem("nav-open-sections");
    const initial: Set<string> = stored ? new Set(JSON.parse(stored)) : new Set();
    for (const s of NAV_SECTIONS) {
      if (s.items.some((item) => item.href === pathname)) {
        initial.add(s.id);
        break;
      }
    }
    setOpenSections(initial);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-open section when navigating to a new route
  useEffect(() => {
    setOpenSections((prev) => {
      for (const s of NAV_SECTIONS) {
        if (s.items.some((item) => item.href === pathname) && !prev.has(s.id)) {
          const next = new Set(prev);
          next.add(s.id);
          localStorage.setItem("nav-open-sections", JSON.stringify([...next]));
          return next;
        }
      }
      return prev;
    });
  }, [pathname]);

  const toggleCollapsed = () => {
    setCollapsed((c) => {
      localStorage.setItem("sidebar-collapsed", String(!c));
      return !c;
    });
  };

  const toggleSection = (id: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      localStorage.setItem("nav-open-sections", JSON.stringify([...next]));
      return next;
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
        className={`fixed inset-y-0 left-0 z-40 bg-slate-900 border-r border-white/5 flex flex-col
          transition-all duration-200 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0
          ${collapsed ? "md:w-16" : "md:w-60"}
          w-60`}
      >
        {/* Logo */}
        <div className={`h-16 border-b border-white/5 flex items-center shrink-0 transition-all duration-200 ${collapsed ? "justify-center px-0" : "justify-between px-4"}`}>
          {collapsed ? (
            <Link href="/dashboard" className="flex items-center justify-center">
              <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
            </Link>
          ) : (
            <>
              <Link href="/dashboard" className="flex items-center gap-2.5">
                <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
                <span className="text-base font-bold text-white tracking-tight">TraceLayer</span>
              </Link>
              <button
                onClick={() => setMobileOpen(false)}
                className="md:hidden text-white/40 hover:text-white/70 p-1 rounded-lg hover:bg-white/5 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 py-3 overflow-y-auto overflow-x-hidden">
          <div className={collapsed ? "px-2" : "px-3"}>
            {NAV_SECTIONS.map((section, si) => {
              const hasActive = section.items.some((item) => pathname === item.href);

              // ── Icon-only (collapsed sidebar) mode ──
              if (collapsed) {
                return (
                  <div key={section.id}>
                    {si > 0 && <div className="border-t border-white/5 my-1" />}
                    <div className="space-y-0.5">
                      {section.items.map(({ href, label, icon: Icon, tourId }) => {
                        const active = pathname === href;
                        return (
                          <div key={href} className="relative group/item">
                            <Link href={href} id={tourId}
                              className={`flex items-center justify-center w-10 h-10 mx-auto rounded-xl transition-all duration-150
                                ${active ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
                            >
                              <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-slate-500"}`} />
                            </Link>
                            <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50
                              opacity-0 group-hover/item:opacity-100 transition-opacity duration-150">
                              <div className="bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-lg">
                                {label}
                                <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              }

              // ── Flat (always-visible) section ──
              if (section.type === "flat") {
                return (
                  <div key={section.id} className="space-y-0.5 mb-2">
                    {section.items.map(({ href, label, icon: Icon, tourId }) => {
                      const active = pathname === href;
                      return (
                        <Link key={href} href={href} id={tourId}
                          className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150
                            ${active ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
                        >
                          <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-slate-500"}`} />
                          {label}
                        </Link>
                      );
                    })}
                  </div>
                );
              }

              // ── Collapsible section ──
              const isOpen = openSections.has(section.id);
              return (
                <div key={section.id} className="mb-0.5">
                  <button
                    id={section.tourNavId}
                    onClick={() => toggleSection(section.id)}
                    className="w-full flex items-center gap-2 px-3 py-1.5 rounded-xl transition-colors hover:bg-white/5 group/sec"
                  >
                    {section.number && (
                      <span className={`text-[10px] font-bold w-5 h-5 rounded-md flex items-center justify-center shrink-0 leading-none transition-colors
                        ${hasActive ? "bg-brand-600 text-white" : "bg-white/10 text-slate-500 group-hover/sec:bg-white/15"}`}>
                        {section.number}
                      </span>
                    )}
                    <span className={`text-[13px] font-semibold flex-1 text-left transition-colors
                      ${hasActive ? "text-slate-200" : "text-slate-400 group-hover/sec:text-slate-300"}`}>
                      {section.title}
                    </span>
                    <ChevronDown className={`w-3 h-3 shrink-0 transition-transform duration-200
                      ${isOpen ? "rotate-180" : ""} ${hasActive ? "text-slate-400" : "text-slate-600"}`} />
                  </button>
                  <div className={`overflow-hidden transition-all duration-200 ease-in-out ${isOpen ? "max-h-[400px]" : "max-h-0"}`}>
                    <div className="space-y-0.5 mt-0.5 pb-1 pl-2">
                      {section.items.map(({ href, label, icon: Icon, tourId }) => {
                        const active = pathname === href;
                        return (
                          <Link key={href} href={href} id={tourId}
                            className={`flex items-center gap-3 px-3 py-1.5 rounded-xl text-[12px] font-medium transition-all duration-150
                              ${active ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
                          >
                            <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-slate-500"}`} />
                            {label}
                          </Link>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Super-admin link — only visible to internal admins */}
          {user && (process.env.NEXT_PUBLIC_SUPER_ADMIN_EMAILS ?? "").split(",").map(e => e.trim()).filter(Boolean).includes(user.email) && (
            <div className={`mt-4 pt-4 border-t border-white/5 ${collapsed ? "px-2" : "px-3"}`}>
              <div className="relative group/item">
                <Link
                  href="/superadmin"
                  className={`flex items-center rounded-xl text-sm font-medium transition-all duration-150
                    ${collapsed ? "justify-center w-10 h-10 mx-auto" : "gap-3 px-3 py-2"}
                    ${pathname === "/superadmin"
                      ? "bg-purple-600 text-white shadow-sm"
                      : "text-purple-400 hover:bg-purple-500/10 hover:text-purple-300"
                    }`}
                >
                  <ShieldHalf className={`w-4 h-4 shrink-0 ${pathname === "/superadmin" ? "text-white" : "text-purple-400"}`} />
                  {!collapsed && <span>Super Admin</span>}
                </Link>
                {collapsed && (
                  <div className="pointer-events-none absolute left-full top-1/2 -translate-y-1/2 ml-3 z-50 opacity-0 group-hover/item:opacity-100 transition-opacity duration-150">
                    <div className="bg-gray-900 text-white text-xs font-medium px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-lg">
                      Super Admin
                      <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </nav>

        {/* Free plan upgrade CTA — shown only to admins on free plan */}
        {!isPro && !collapsed && user?.role === "admin" && (
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
              <p className="text-[10px] text-white/70 leading-snug mb-2.5">Unlock AI features, PDF reports, all 9 frameworks &amp; more.</p>
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/90">$149 / mo</span>
                <span className="text-[10px] font-semibold text-brand-200 group-hover:text-white transition-colors">Upgrade →</span>
              </div>
            </Link>
          </div>
        )}

        {/* Help & Support */}
        <div className={`border-t border-white/5 pt-2 pb-1 shrink-0 ${collapsed ? "px-2" : "px-3"}`}>
          <div className="relative group/help">
            <a
              href="mailto:support@tracelayer.it.com"
              className={`flex items-center rounded-xl text-sm text-slate-500 hover:bg-white/5 hover:text-slate-300 transition-all duration-150
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
        <div className={`hidden md:flex border-t border-white/5 py-2 shrink-0 ${collapsed ? "justify-center px-2" : "px-3"}`}>
          <button
            onClick={toggleCollapsed}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
            className={`flex items-center gap-2 text-xs text-slate-500 hover:text-white hover:bg-white/5 rounded-xl transition-all duration-150
              ${collapsed ? "w-10 h-8 justify-center" : "px-3 py-2 w-full"}`}
          >
            {collapsed
              ? <ChevronRight className="w-3.5 h-3.5 shrink-0" />
              : <><ChevronLeft className="w-3.5 h-3.5 shrink-0" /><span>Collapse</span></>
            }
          </button>
        </div>

        {/* User */}
        <div className={`border-t border-white/5 py-3 shrink-0 space-y-0.5 ${collapsed ? "px-2" : "px-3"}`}>
          {/* Avatar row */}
          <div className={`flex items-center rounded-xl py-2 ${collapsed ? "justify-center" : "gap-3 px-3"}`}>
            <div className="w-7 h-7 rounded-lg bg-white/10 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-white/80">{initials}</span>
            </div>
            {!collapsed && (
              <span className="text-xs text-slate-500 truncate flex-1">{user.email}</span>
            )}
          </div>
          {/* Sign out */}
          <div className="relative group/logout">
            <button
              onClick={handleLogout}
              className={`flex items-center rounded-xl text-sm text-slate-400 hover:bg-white/5 hover:text-white w-full transition-all duration-150
                ${collapsed ? "justify-center w-10 h-10 mx-auto" : "gap-3 px-3 py-2"}`}
            >
              <LogOut className="w-4 h-4 text-slate-500 shrink-0" />
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
      <Toaster />
      <GlobalChat />

    </div>
  );
}
