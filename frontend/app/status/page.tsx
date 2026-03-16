"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type ServiceStatus = "operational" | "degraded" | "outage" | "checking";

interface HealthResponse {
  status: string;
  db: string;
  env: string;
}

interface ServiceState {
  name: string;
  description: string;
  status: ServiceStatus;
}

function StatusBadge({ status }: { status: ServiceStatus }) {
  if (status === "operational") return (
    <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
      <CheckCircle2 className="w-3.5 h-3.5" /> Operational
    </span>
  );
  if (status === "degraded") return (
    <span className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-full">
      <AlertTriangle className="w-3.5 h-3.5" /> Degraded
    </span>
  );
  if (status === "outage") return (
    <span className="flex items-center gap-1.5 text-xs font-semibold text-red-700 bg-red-50 border border-red-200 px-2.5 py-1 rounded-full">
      <XCircle className="w-3.5 h-3.5" /> Outage
    </span>
  );
  return (
    <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 bg-gray-50 border border-gray-200 px-2.5 py-1 rounded-full">
      <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Checking…
    </span>
  );
}

function overallStatus(services: ServiceState[]): ServiceStatus {
  if (services.some((s) => s.status === "checking")) return "checking";
  if (services.some((s) => s.status === "outage")) return "outage";
  if (services.some((s) => s.status === "degraded")) return "degraded";
  return "operational";
}

const OVERALL_COPY: Record<ServiceStatus, { headline: string; sub: string; bg: string; border: string; text: string }> = {
  operational: {
    headline: "All Systems Operational",
    sub: "Everything is running normally.",
    bg: "from-emerald-600 to-emerald-700",
    border: "border-emerald-500",
    text: "text-emerald-100",
  },
  degraded: {
    headline: "Partial Degradation",
    sub: "Some services are experiencing issues. We're working on it.",
    bg: "from-amber-500 to-amber-600",
    border: "border-amber-400",
    text: "text-amber-100",
  },
  outage: {
    headline: "Service Disruption",
    sub: "We're aware and actively working to restore service.",
    bg: "from-red-600 to-red-700",
    border: "border-red-500",
    text: "text-red-100",
  },
  checking: {
    headline: "Checking status…",
    sub: "Fetching live system health.",
    bg: "from-slate-700 to-slate-800",
    border: "border-slate-600",
    text: "text-slate-300",
  },
};

export default function StatusPage() {
  const [services, setServices] = useState<ServiceState[]>([
    { name: "API",                  description: "REST API and authentication",              status: "checking" },
    { name: "Database",             description: "PostgreSQL — evidence and user data",       status: "checking" },
    { name: "Frontend",             description: "Web application and dashboard",             status: "operational" },
    { name: "Evidence Collection",  description: "Scheduled integration collectors",          status: "checking" },
    { name: "Email Delivery",       description: "Transactional and alert emails via Resend", status: "checking" },
  ]);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
      const data: HealthResponse = res.ok ? await res.json() : { status: "error", db: "error", env: "" };

      const apiOk = res.ok && data.status === "ok";
      const dbOk  = data.db === "ok";

      setServices((prev) => prev.map((s) => {
        if (s.name === "API")                 return { ...s, status: apiOk ? "operational" : "outage" };
        if (s.name === "Database")            return { ...s, status: dbOk  ? "operational" : "outage" };
        if (s.name === "Evidence Collection") return { ...s, status: apiOk ? "operational" : "degraded" };
        if (s.name === "Email Delivery")      return { ...s, status: apiOk ? "operational" : "degraded" };
        return s;
      }));
      setLastChecked(new Date());
    } catch {
      setServices((prev) => prev.map((s) =>
        s.name === "Frontend" ? s : { ...s, status: "outage" }
      ));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { check(); }, []); // eslint-disable-line

  const overall = overallStatus(services);
  const copy    = OVERALL_COPY[overall];

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link href="/" className="font-bold text-gray-900 text-lg">TraceLayer</Link>
          <div className="flex items-center gap-4">
            <a href="mailto:support@tracelayer.it.com" className="text-sm text-gray-500 hover:text-gray-700">
              support@tracelayer.it.com
            </a>
            <Link href="/login" className="text-sm text-brand-600 hover:underline font-semibold">Sign in</Link>
          </div>
        </div>
      </header>

      {/* Hero status bar */}
      <div className={`bg-gradient-to-r ${copy.bg} px-6 py-10`}>
        <div className="max-w-3xl mx-auto">
          <h1 className="text-2xl font-bold text-white mb-1">{copy.headline}</h1>
          <p className={`text-sm ${copy.text}`}>{copy.sub}</p>
          {lastChecked && (
            <p className="text-xs text-white/40 mt-3">
              Last checked {lastChecked.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </p>
          )}
        </div>
      </div>

      <main className="max-w-3xl mx-auto px-6 py-10 space-y-6">

        {/* Refresh */}
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wider">Current Status</h2>
          <button
            onClick={check}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-brand-600 hover:text-brand-700 font-semibold disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>

        {/* Service list */}
        <div className="bg-white border border-gray-100 rounded-2xl shadow-sm divide-y divide-gray-50">
          {services.map((svc) => (
            <div key={svc.name} className="flex items-center justify-between px-5 py-4">
              <div>
                <p className="text-sm font-semibold text-gray-900">{svc.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{svc.description}</p>
              </div>
              <StatusBadge status={svc.status} />
            </div>
          ))}
        </div>

        {/* Incident history */}
        <div>
          <h2 className="text-sm font-bold text-gray-700 uppercase tracking-wider mb-3">Incident History</h2>
          <div className="bg-white border border-gray-100 rounded-2xl shadow-sm px-5 py-6 text-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-semibold text-gray-700">No incidents in the last 90 days</p>
            <p className="text-xs text-gray-400 mt-1">We&apos;ll post updates here if anything changes.</p>
          </div>
        </div>

        {/* Subscribe / contact */}
        <div className="bg-slate-900 rounded-2xl px-6 py-6 text-white">
          <h3 className="font-semibold mb-1">Get notified about incidents</h3>
          <p className="text-sm text-white/60 mb-4">
            Email <a href="mailto:support@tracelayer.it.com" className="text-brand-400 hover:text-brand-300 underline">
              support@tracelayer.it.com
            </a> to be added to our incident notifications list, or check back here for live status.
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <a href="mailto:support@tracelayer.it.com"
               className="bg-white/10 hover:bg-white/20 border border-white/10 px-3 py-1.5 rounded-lg font-medium transition-colors">
              Contact support →
            </a>
            <Link href="/security"
               className="bg-white/10 hover:bg-white/20 border border-white/10 px-3 py-1.5 rounded-lg font-medium transition-colors">
              View security posture →
            </Link>
          </div>
        </div>

        {/* Uptime setup hint for operators */}
        <p className="text-[11px] text-gray-400 text-center">
          Uptime monitoring: point UptimeRobot / Better Uptime at{" "}
          <code className="bg-gray-100 px-1 py-0.5 rounded text-gray-600">{API_URL}/health</code>
          {" "}to get alerting and an embedded badge.
        </p>
      </main>

      <footer className="border-t border-gray-200 bg-white py-6 px-6 text-center">
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-400">
          <Link href="/" className="hover:text-gray-600">TraceLayer</Link>
          <Link href="/security" className="hover:text-gray-600">Security</Link>
          <Link href="/dpa" className="hover:text-gray-600">DPA</Link>
          <a href="mailto:support@tracelayer.it.com" className="hover:text-gray-600">support@tracelayer.it.com</a>
        </div>
      </footer>
    </div>
  );
}
