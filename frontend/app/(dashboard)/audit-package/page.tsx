"use client";

import { useEffect, useState, useRef } from "react";
import { api } from "@/lib/api";
import type { Report } from "@/lib/types";
import { PlanGate } from "@/components/plan-gate";
import {
  Sparkles,
  Download,
  Clock,
  CheckCircle2,
  AlertCircle,
  Shield,
  FileText,
  BarChart2,
  AlertTriangle,
  Users,
  BookOpen,
  ShieldAlert,
  Building2,
  UserCheck,
  GraduationCap,
  ChevronDown,
  Loader2,
  CalendarDays,
  TrendingUp,
} from "lucide-react";

// ── Types ────────────────────────────────────────────────────────────────────

const FRAMEWORKS = [
  { value: "soc2",     label: "SOC 2 Type II",  desc: "Trust service criteria for security, availability & confidentiality" },
  { value: "iso27001", label: "ISO/IEC 27001",   desc: "International information security management standard" },
  { value: "hipaa",    label: "HIPAA",            desc: "Health Insurance Portability and Accountability Act" },
  { value: "gdpr",     label: "GDPR",             desc: "General Data Protection Regulation" },
  { value: "pci_dss",  label: "PCI DSS",          desc: "Payment Card Industry Data Security Standard" },
  { value: "ccpa",     label: "CCPA",             desc: "California Consumer Privacy Act" },
  { value: "nist_csf", label: "NIST CSF",         desc: "NIST Cybersecurity Framework" },
  { value: "dpdp",     label: "DPDP Act",         desc: "India Digital Personal Data Protection Act 2023" },
  { value: "cert_in",  label: "CERT-In",          desc: "India Cybersecurity Directions 2022" },
];

const WHAT_IS_INCLUDED = [
  { icon: Sparkles,     label: "AI Executive Summary",       desc: "Board-ready narrative of your compliance posture" },
  { icon: BarChart2,    label: "Compliance Score Overview",  desc: "Overall score with passing/failing control breakdown" },
  { icon: TrendingUp,   label: "AI Gap Analysis",            desc: "Specific gaps and 5 prioritised remediation actions" },
  { icon: Shield,       label: "Evidence Records",           desc: "All automated evidence per control" },
  { icon: FileText,     label: "Manual Controls",            desc: "Attested compliance controls and their status" },
  { icon: BookOpen,     label: "Policy Library",             desc: "Adopted security and compliance policies" },
  { icon: AlertTriangle,label: "Risk Register",              desc: "Risks with severity, likelihood and impact scores" },
  { icon: ShieldAlert,  label: "Penetration Testing",        desc: "Security testing history and findings by severity" },
  { icon: GraduationCap,label: "Security Training",          desc: "Employee training completion rates" },
  { icon: Building2,    label: "Vendor Risk Management",     desc: "Third-party vendors with risk levels and certifications" },
  { icon: UserCheck,    label: "Access Reviews",             desc: "Periodic access control review records" },
];

const GENERATION_STEPS = [
  "Gathering compliance evidence…",
  "Analysing control scores…",
  "Collecting risk register…",
  "Reviewing vendor assessments…",
  "Checking training records…",
  "Consulting access reviews…",
  "Generating AI executive summary…",
  "Writing gap analysis…",
  "Compiling prioritised recommendations…",
  "Building PDF document…",
  "Finalising audit package…",
];

// ── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  if (status === "complete") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
        <CheckCircle2 className="w-3.5 h-3.5" /> Complete
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-red-50 text-red-600 border border-red-200">
        <AlertCircle className="w-3.5 h-3.5" /> Failed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
      <Clock className="w-3.5 h-3.5 animate-pulse" /> Generating…
    </span>
  );
}

const FW_LABELS: Record<string, string> = {
  soc2:     "SOC 2",
  iso27001: "ISO 27001",
  hipaa:    "HIPAA",
  gdpr:     "GDPR",
  pci_dss:  "PCI DSS",
  nist_csf: "NIST CSF",
};

// ── Package card ─────────────────────────────────────────────────────────────

function PackageCard({
  report,
  downloading,
  onDownload,
}: {
  report: Report;
  downloading: boolean;
  onDownload: (r: Report) => void;
}) {
  const fw = FW_LABELS[report.framework.toLowerCase()] ?? report.framework.toUpperCase();
  const isReady = report.status === "complete";

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden flex hover:shadow-md transition-shadow duration-200">
      <div className="w-1.5 shrink-0 bg-gradient-to-b from-indigo-500 to-teal-500" />
      <div className="flex flex-1 flex-col gap-4 sm:flex-row sm:items-center sm:justify-between px-5 py-5">
        <div className="flex items-start gap-4">
          <div className="shrink-0 w-11 h-11 rounded-xl bg-indigo-50 flex items-center justify-center border border-indigo-100">
            <Sparkles className="w-5 h-5 text-indigo-500" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-semibold text-gray-900">AI Audit Package</span>
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100">
                {fw}
              </span>
              <StatusBadge status={report.status} />
            </div>
            <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400 flex-wrap">
              <span className="flex items-center gap-1">
                <CalendarDays className="w-3.5 h-3.5" />
                {report.generated_at
                  ? new Date(report.generated_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })
                  : new Date(report.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
              </span>
              {report.file_size && (
                <span>{(report.file_size / 1024).toFixed(0)} KB PDF</span>
              )}
            </div>
          </div>
        </div>
        <div className="shrink-0">
          {isReady ? (
            <button
              onClick={() => onDownload(report)}
              disabled={downloading}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 active:scale-95 transition-all duration-150 disabled:opacity-60"
            >
              {downloading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Download className="w-4 h-4" />
              )}
              Download PDF
            </button>
          ) : report.status === "error" ? (
            <span className="text-xs text-red-500 font-medium">Generation failed</span>
          ) : (
            <div className="flex items-center gap-2 text-xs text-amber-600 font-medium">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Building package…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

export default function AuditPackagePage() {
  const [framework, setFramework] = useState("soc2");
  const [fwOpen, setFwOpen]       = useState(false);
  const [generating, setGenerating] = useState(false);
  const [stepIdx, setStepIdx]       = useState(0);
  const [packages, setPackages]     = useState<Report[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError]           = useState<string | null>(null);

  const pollingRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepRef     = useRef<ReturnType<typeof setInterval> | null>(null);
  const fwDropRef   = useRef<HTMLDivElement>(null);

  const selectedFw = FRAMEWORKS.find(f => f.value === framework) ?? FRAMEWORKS[0];

  // ── Load previous packages ────────────────────────────────────────────────
  const loadPackages = async () => {
    try {
      const data = await api.getReports();
      const pkgs = (data.items ?? []).filter(r => r.report_type === "audit_package");
      setPackages(pkgs);
    } catch {
      // silent
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    loadPackages();
  }, []);

  // ── Poll while any package is generating ─────────────────────────────────
  useEffect(() => {
    const hasPending = packages.some(p => p.status === "pending");
    if (hasPending && !pollingRef.current) {
      pollingRef.current = setInterval(loadPackages, 3000);
    }
    if (!hasPending && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setGenerating(false);
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [packages]);

  // ── Step cycle during generation ──────────────────────────────────────────
  useEffect(() => {
    if (generating) {
      setStepIdx(0);
      stepRef.current = setInterval(() => {
        setStepIdx(i => (i + 1) % GENERATION_STEPS.length);
      }, 2200);
    } else {
      if (stepRef.current) clearInterval(stepRef.current);
    }
    return () => {
      if (stepRef.current) clearInterval(stepRef.current);
    };
  }, [generating]);

  // ── Close FW dropdown on outside click ───────────────────────────────────
  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (fwDropRef.current && !fwDropRef.current.contains(e.target as Node)) {
        setFwOpen(false);
      }
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  // ── Generate ──────────────────────────────────────────────────────────────
  const handleGenerate = async () => {
    setError(null);
    setGenerating(true);
    try {
      await api.generateAuditPackage(framework);
      await loadPackages();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start generation. Please try again.");
      setGenerating(false);
    }
  };

  // ── Download ──────────────────────────────────────────────────────────────
  const handleDownload = async (report: Report) => {
    setDownloading(report.id);
    try {
      const { url } = await api.downloadReport(report.id, "pdf");
      window.open(url, "_blank");
    } catch {
      // silent
    } finally {
      setDownloading(null);
    }
  };

  const pendingPackages  = packages.filter(p => p.status === "pending");
  const completePackages = packages.filter(p => p.status !== "pending");

  return (
    <div className="space-y-8 overflow-x-hidden">

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-900 via-indigo-800 to-teal-800 p-8 md:p-10 text-white shadow-xl">
        {/* Background decoration */}
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="absolute -top-20 -right-20 w-72 h-72 rounded-full bg-white/5 blur-3xl" />
          <div className="absolute -bottom-20 -left-20 w-72 h-72 rounded-full bg-teal-500/10 blur-3xl" />
        </div>

        <div className="relative flex flex-col md:flex-row md:items-start md:justify-between gap-8">
          {/* Left: title + description */}
          <div className="max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-xs font-semibold text-teal-300 mb-5">
              <Sparkles className="w-3.5 h-3.5" />
              AI-Powered · Groq llama-3.3-70b
            </div>
            <h1 className="text-3xl md:text-4xl font-bold leading-tight tracking-tight mb-3">
              AI Audit Package
            </h1>
            <p className="text-indigo-200 text-base leading-relaxed">
              One-click PDF that compiles your entire compliance programme — evidence, controls, risks, vendors, training, pen tests and access reviews — with an AI-written executive narrative and gap analysis your auditor will actually read.
            </p>
          </div>

          {/* Right: generator card */}
          <PlanGate feature="AI Audit Package" mode="hide">
          <div className="shrink-0 w-full md:w-72 bg-white/10 backdrop-blur border border-white/20 rounded-2xl p-5 space-y-4">

            {/* Framework picker */}
            <div>
              <label className="text-xs font-semibold text-indigo-200 uppercase tracking-wider mb-2 block">
                Framework
              </label>
              <div ref={fwDropRef} className="relative">
                <button
                  onClick={() => setFwOpen(o => !o)}
                  className="w-full flex items-center justify-between gap-2 px-4 py-2.5 bg-white/10 border border-white/20 rounded-xl text-sm font-semibold text-white hover:bg-white/20 transition-colors"
                >
                  {selectedFw.label}
                  <ChevronDown className={`w-4 h-4 text-indigo-300 transition-transform ${fwOpen ? "rotate-180" : ""}`} />
                </button>
                {fwOpen && (
                  <div className="absolute z-20 top-full mt-1.5 left-0 right-0 bg-white rounded-xl shadow-xl border border-gray-100 py-1 overflow-hidden">
                    {FRAMEWORKS.map(fw => (
                      <button
                        key={fw.value}
                        onClick={() => { setFramework(fw.value); setFwOpen(false); }}
                        className={`w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 transition-colors ${framework === fw.value ? "font-semibold text-indigo-600 bg-indigo-50" : "text-gray-700"}`}
                      >
                        {fw.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <p className="mt-1.5 text-xs text-indigo-300">{selectedFw.desc}</p>
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={generating || pendingPackages.length > 0}
              className="w-full flex items-center justify-center gap-2.5 px-4 py-3 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-500 text-white font-bold text-sm shadow-lg hover:from-teal-400 hover:to-indigo-400 active:scale-95 transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {generating || pendingPackages.length > 0 ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating…
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Generate AI Audit Package
                </>
              )}
            </button>

            {error && (
              <p className="text-xs text-red-300 text-center">{error}</p>
            )}
          </div>
          </PlanGate>
        </div>
      </div>

      {/* ── Generation progress ───────────────────────────────────────── */}
      {(generating || pendingPackages.length > 0) && (
        <div className="bg-gradient-to-r from-indigo-50 to-teal-50 rounded-2xl border border-indigo-100 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-600 animate-pulse" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-900">Building your AI Audit Package</p>
              <p className="text-xs text-indigo-600 mt-0.5 transition-all duration-500">
                {GENERATION_STEPS[stepIdx]}
              </p>
            </div>
          </div>
          {/* Progress bar */}
          <div className="h-1.5 bg-indigo-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-indigo-500 to-teal-500 rounded-full transition-all duration-[2200ms]"
              style={{ width: `${((stepIdx + 1) / GENERATION_STEPS.length) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">This takes 20–60 seconds. You can leave this page — we'll keep it ready for download.</p>
        </div>
      )}

      {/* ── What's included ───────────────────────────────────────────── */}
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-1">What's included</h2>
        <p className="text-sm text-gray-500 mb-4">Every AI Audit Package compiles all 11 data sections into a single professionally formatted PDF.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {WHAT_IS_INCLUDED.map(({ icon: Icon, label, desc }) => (
            <div
              key={label}
              className="flex items-start gap-3 bg-white rounded-xl border border-gray-100 px-4 py-3.5 hover:border-indigo-200 hover:shadow-sm transition-all duration-150"
            >
              <div className="shrink-0 w-8 h-8 rounded-lg bg-indigo-50 flex items-center justify-center mt-0.5">
                <Icon className="w-4 h-4 text-indigo-500" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{label}</p>
                <p className="text-xs text-gray-500 leading-relaxed mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Previous packages ─────────────────────────────────────────── */}
      <PlanGate feature="AI Audit Package — Generated reports" mode="hide">
      <div>
        <h2 className="text-lg font-bold text-gray-900 mb-4">Generated Packages</h2>

        {loadingList ? (
          <div className="flex items-center gap-2 text-sm text-gray-400 py-8">
            <Loader2 className="w-4 h-4 animate-spin" /> Loading…
          </div>
        ) : packages.length === 0 ? (
          <div className="bg-white rounded-2xl border border-dashed border-gray-200 py-16 flex flex-col items-center gap-3 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-indigo-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-700">No packages yet</p>
              <p className="text-xs text-gray-400 mt-0.5">Generate your first AI Audit Package above.</p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Pending at top */}
            {pendingPackages.map(p => (
              <PackageCard
                key={p.id}
                report={p}
                downloading={downloading === p.id}
                onDownload={handleDownload}
              />
            ))}
            {/* Completed */}
            {completePackages.map(p => (
              <PackageCard
                key={p.id}
                report={p}
                downloading={downloading === p.id}
                onDownload={handleDownload}
              />
            ))}
          </div>
        )}
      </div>
      </PlanGate>

    </div>
  );
}
