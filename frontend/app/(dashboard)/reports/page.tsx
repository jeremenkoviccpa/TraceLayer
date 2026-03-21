"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { openPaddleCheckout } from "@/lib/paddle";
import type { Report } from "@/lib/types";
import {
  FileText,
  Download,
  Clock,
  CheckCircle2,
  AlertCircle,
  Plus,
  BarChart2,
  CalendarDays,
  Lock,
} from "lucide-react";
import { usePlan } from "@/hooks/usePlan";

// ── Status helpers ──────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (status === "complete") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3.5 h-3.5" />
        Complete
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-600 border border-red-200">
        <AlertCircle className="w-3.5 h-3.5" />
        Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
      <Clock className="w-3.5 h-3.5 animate-pulse" />
      Generating…
    </span>
  );
}

const FRAMEWORKS = [
  { value: "soc2", label: "SOC 2" },
  { value: "iso27001", label: "ISO 27001" },
  { value: "hipaa", label: "HIPAA" },
];

// Per-framework accent colours for report cards
const FRAMEWORK_ACCENT: Record<string, { bar: string; icon: string; badge: string }> = {
  soc2: {
    bar: "bg-emerald-500",
    icon: "text-emerald-500 bg-emerald-50",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  iso27001: {
    bar: "bg-blue-500",
    icon: "text-blue-500 bg-blue-50",
    badge: "bg-blue-50 text-blue-700 border-blue-200",
  },
  hipaa: {
    bar: "bg-violet-500",
    icon: "text-violet-500 bg-violet-50",
    badge: "bg-violet-50 text-violet-700 border-violet-200",
  },
};

function defaultAccent() {
  return {
    bar: "bg-emerald-500",
    icon: "text-emerald-500 bg-emerald-50",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
  };
}

// ── Report card ─────────────────────────────────────────────────

function ReportCard({
  report,
  downloading,
  onDownload,
}: {
  report: Report;
  downloading: boolean;
  onDownload: (r: Report) => void;
}) {
  const accent = FRAMEWORK_ACCENT[report.framework.toLowerCase()] ?? defaultAccent();

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex hover:shadow-md transition-shadow duration-200">
      {/* Left accent bar */}
      <div className={`w-1.5 shrink-0 ${accent.bar}`} />

      <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between px-5 py-5">
        {/* Icon + meta */}
        <div className="flex items-start gap-4">
          <div
            className={`shrink-0 w-11 h-11 rounded-xl flex items-center justify-center ${accent.icon} border border-current/10`}
          >
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`inline-block px-2 py-0.5 rounded-md text-xs font-bold uppercase border ${accent.badge}`}
              >
                {report.framework}
              </span>
              <span className="text-gray-700 font-semibold text-sm capitalize">
                {report.report_type} report
              </span>
              <span className="text-gray-300 text-xs">·</span>
              <span className="text-gray-400 text-xs font-mono uppercase">{report.fmt}</span>
              <StatusBadge status={report.status} />
            </div>
            <div className="flex flex-wrap gap-x-4 gap-y-0.5 mt-2 text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <CalendarDays className="w-3.5 h-3.5 shrink-0" />
                Created {new Date(report.created_at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  year: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </span>
              {report.generated_at && (
                <span className="flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-400" />
                  Generated {new Date(report.generated_at).toLocaleString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Download button */}
        {report.status === "complete" && (
          <button
            onClick={() => onDownload(report)}
            disabled={downloading}
            className="shrink-0 self-start sm:self-auto flex items-center gap-2 px-4 py-2 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100 text-sm font-semibold transition-colors disabled:opacity-40"
          >
            <Download className="w-4 h-4" />
            {downloading ? "Downloading…" : `Download ${report.fmt.toUpperCase()}`}
          </button>
        )}
      </div>
    </div>
  );
}

// ── Hero stat ────────────────────────────────────────────────────

function HeroStat({
  label,
  value,
  colorClass,
}: {
  label: string;
  value: string | number;
  colorClass: string;
}) {
  return (
    <div className="flex flex-col">
      <span className={`text-2xl font-bold tabular-nums ${colorClass}`}>{value}</span>
      <span className="text-slate-400 text-xs mt-0.5 whitespace-nowrap">{label}</span>
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────

export default function ReportsPage() {
  const { isPro } = usePlan();
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [upgradingPdf, setUpgradingPdf] = useState(false);
  const [toast, setToast] = useState("");
  const [framework, setFramework] = useState("soc2");
  const [format, setFormat] = useState("json");

  const handlePdfUpgrade = useCallback(async () => {
    setUpgradingPdf(true);
    try {
      const { checkout_url } = await api.createCheckout();
      await openPaddleCheckout(checkout_url);
    } catch {
      router.push("/settings#billing");
    } finally {
      setUpgradingPdf(false);
    }
  }, [router]);

  const load = () =>
    api
      .getReports()
      .then((p) => setReports(p.items))
      .catch(console.error)
      .finally(() => setLoading(false));

  useEffect(() => {
    load();
  }, []);

  // Poll every 3 s while any report is pending
  useEffect(() => {
    const hasPending = reports.some((r) => r.status === "pending");
    if (!hasPending) return;
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [reports]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(""), 5000);
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await api.generateReport(framework, "full", format);
      await load();
      showToast("Report generation started");
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Failed to generate report");
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (report: Report) => {
    if (report.status !== "complete") return;
    setDownloading(report.id);
    try {
      const { url, file_name } = await api.downloadReport(report.id, report.fmt);
      const fileName = file_name ?? `tracelayer-report-${report.id.slice(0, 8)}.${report.fmt}`;

      // Fetch as blob so the download attribute works on mobile (cross-origin URLs
      // are ignored by mobile browsers — a local object URL always triggers save).
      try {
        const res = await fetch(url);
        const blob = await res.blob();
        const objectUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = objectUrl;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(objectUrl);
      } catch {
        // Fallback: open in new tab (iOS Safari PDF viewer lets user save from there)
        window.open(url, "_blank", "noopener,noreferrer");
      }
    } catch (err: unknown) {
      showToast(err instanceof Error ? err.message : "Download failed");
    } finally {
      setDownloading(null);
    }
  };

  // Derived stats
  const totalReports = reports.length;
  const latestReport = reports.reduce<Report | null>((latest, r) => {
    if (!latest) return r;
    return new Date(r.created_at) > new Date(latest.created_at) ? r : latest;
  }, null);
  const latestDate = latestReport
    ? new Date(latestReport.created_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : "—";

  return (
    <div className="space-y-6 overflow-x-hidden">
      {/* ── Toast ── */}
      {toast && (
        <div className="fixed top-4 right-4 bg-slate-900 text-white text-sm px-4 py-2.5 rounded-xl shadow-xl z-50 border border-slate-700 animate-in fade-in slide-in-from-top-2 duration-200">
          {toast}
        </div>
      )}

      {/* ── Dark Hero Card ── */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 shadow-xl">
        {/* Subtle grid texture */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        {/* Emerald glow blob */}
        <div className="pointer-events-none absolute -top-16 -left-16 w-72 h-72 rounded-full bg-emerald-500/10 blur-3xl" />

        <div className="relative px-4 sm:px-7 py-5 sm:py-7 flex flex-col gap-4 sm:gap-6 sm:flex-row sm:items-center sm:justify-between">
          {/* Left — icon + copy + stats */}
          <div className="flex items-start gap-3 sm:gap-5">
            <div className="shrink-0 flex items-center justify-center w-10 h-10 sm:w-14 sm:h-14 rounded-2xl bg-emerald-500/15 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
              <FileText className="w-5 h-5 sm:w-7 sm:h-7 text-emerald-400" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-2xl font-bold text-white tracking-tight">Reports</h1>
              <p className="text-slate-400 text-xs sm:text-sm mt-0.5 sm:mt-1 max-w-md leading-relaxed hidden sm:block">
                Generate audit-ready compliance reports for your auditors and stakeholders.
              </p>
              {/* Stats row */}
              <div className="flex flex-wrap gap-3 sm:gap-6 mt-2 sm:mt-4">
                <HeroStat
                  label="Total reports"
                  value={totalReports}
                  colorClass="text-emerald-400"
                />
                <div className="hidden sm:block w-px bg-slate-700 self-stretch" />
                <HeroStat
                  label="Latest report"
                  value={latestDate}
                  colorClass="text-slate-200"
                />
              </div>
            </div>
          </div>

          {/* Right — generate controls */}
          <div className="shrink-0 flex flex-col gap-3 sm:items-end">
            <div className="flex items-center gap-2 flex-wrap">
              {/* Framework picker */}
              <select
                value={framework}
                onChange={(e) => setFramework(e.target.value)}
                className="border border-slate-600 bg-slate-800 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-colors"
              >
                {FRAMEWORKS.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>

              {/* Format toggle */}
              <div className="flex rounded-lg border border-slate-600 overflow-hidden text-sm">
                <button
                  onClick={() => setFormat("json")}
                  className={`px-3 py-2 font-semibold transition-colors ${
                    format === "json"
                      ? "bg-emerald-600 text-white"
                      : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                  }`}
                >
                  JSON
                </button>
                {isPro ? (
                  <button
                    onClick={() => setFormat("pdf")}
                    className={`px-3 py-2 font-semibold transition-colors ${
                      format === "pdf"
                        ? "bg-emerald-600 text-white"
                        : "text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                    }`}
                  >
                    PDF
                  </button>
                ) : (
                  <button
                    onClick={handlePdfUpgrade}
                    disabled={upgradingPdf}
                    title="PDF reports require the Growth plan"
                    className="relative flex items-center gap-1.5 px-3 py-2 font-semibold text-slate-500 hover:text-slate-300 disabled:opacity-50 transition-colors border-l border-slate-700 group"
                  >
                    {upgradingPdf
                      ? <span className="w-3 h-3 border border-amber-400 border-t-transparent rounded-full animate-spin" />
                      : <Lock className="w-3 h-3 text-amber-500/80 group-hover:text-amber-400 transition-colors" />
                    }
                    <span className="group-hover:text-slate-300 transition-colors">PDF</span>
                    <span className="absolute -top-2 -right-1 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-[8px] font-black uppercase rounded px-1 py-0.5 leading-none shadow-sm">
                      Pro
                    </span>
                  </button>
                )}
              </div>

              {/* Generate */}
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors shadow-md shadow-emerald-900/40"
              >
                <Plus className="w-4 h-4" />
                {generating ? "Generating…" : "Generate report"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── Report List ── */}
      {loading ? (
        <div className="flex flex-col items-center justify-center h-48 gap-3">
          <div className="w-7 h-7 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-400">Loading reports…</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-14 flex flex-col items-center text-center">
          <div className="w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center mb-4">
            <BarChart2 className="w-7 h-7 text-emerald-300" />
          </div>
          <p className="text-gray-700 font-semibold">No reports generated yet</p>
          <p className="text-gray-400 text-sm mt-1 max-w-xs">
            Reports are the deliverable you hand to auditors or enterprise security teams. Once you have evidence collected, use the controls above to generate a SOC 2, ISO 27001, or GDPR readiness report as a PDF.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports.map((r) => (
            <ReportCard
              key={r.id}
              report={r}
              downloading={downloading === r.id}
              onDownload={handleDownload}
            />
          ))}
        </div>
      )}
    </div>
  );
}
