"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import { Users, LogOut, Menu, X, LayoutDashboard, CreditCard, Globe } from "lucide-react";

const NAV = [
  { href: "/partner/clients", label: "Clients", icon: Users },
  { href: "/partner/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/partner/payments", label: "Payments", icon: CreditCard },
  { href: "/partners", label: "Partner directory", icon: Globe, external: true },
];

export default function PartnerLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isPartner, setIsPartner] = useState<boolean | null>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
      return;
    }
    if (!loading && user) {
      (async () => {
        try {
          const { api } = await import("@/lib/api");
          const company = await api.getCompany();
          if (!company.is_partner_account) {
            router.replace("/dashboard");
          } else {
            setIsPartner(true);
          }
        } catch {
          router.replace("/dashboard");
        }
      })();
    }
  }, [user, loading, router]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (loading || !user || isPartner === null) {
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
        className={`fixed inset-y-0 left-0 z-40 w-60 bg-white border-r border-gray-100 flex flex-col
          transition-transform duration-200 ease-in-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"} md:translate-x-0`}
      >
        {/* Logo */}
        <div className="h-16 border-b border-gray-100 flex items-center justify-between px-4 shrink-0">
          <Link href="/partner/clients" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
            <div>
              <span className="text-base font-bold text-gray-900 tracking-tight block leading-none">TraceLayer</span>
              <span className="text-[10px] font-medium text-brand-600 leading-none">Partner</span>
            </div>
          </Link>
          <button
            onClick={() => setMobileOpen(false)}
            className="md:hidden text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 py-4 px-3 overflow-y-auto">
          <div className="space-y-0.5">
            {NAV.map(({ href, label, icon: Icon, external }) => {
              const active = !external && (pathname === href || pathname.startsWith(href + "/"));
              if (external) {
                return (
                  <a
                    key={href}
                    href={href}
                    className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-900 transition-all duration-150"
                  >
                    <Icon className="w-4 h-4 shrink-0 text-gray-400" />
                    {label}
                  </a>
                );
              }
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-3 px-3 py-2 rounded-xl text-sm font-medium transition-all duration-150
                    ${active
                      ? "bg-brand-600 text-white shadow-sm shadow-brand-600/20"
                      : "text-gray-500 hover:bg-gray-50 hover:text-gray-900"
                    }`}
                >
                  <Icon className={`w-4 h-4 shrink-0 ${active ? "text-white" : "text-gray-400"}`} />
                  {label}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* User */}
        <div className="border-t border-gray-100 py-3 px-3 shrink-0 space-y-0.5">
          <div className="flex items-center gap-3 px-3 py-2 rounded-xl">
            <div className="w-7 h-7 rounded-lg bg-brand-100 flex items-center justify-center shrink-0">
              <span className="text-xs font-bold text-brand-700">{initials}</span>
            </div>
            <span className="text-xs text-gray-500 truncate flex-1">{user.email}</span>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2 rounded-xl text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-900 w-full transition-all duration-150"
          >
            <LogOut className="w-4 h-4 text-gray-400 shrink-0" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-h-screen md:ml-60 overflow-x-hidden">
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
            <span className="font-bold text-gray-900 text-sm">TraceLayer Partner</span>
          </div>
        </header>

        <main className="flex-1 p-5 md:p-8 max-w-7xl mx-auto w-full">{children}</main>
      </div>
    </div>
  );
}
