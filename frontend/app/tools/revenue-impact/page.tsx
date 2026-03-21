"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight, DollarSign, TrendingDown, AlertTriangle,
  Clock, CheckCircle2, ChevronRight, BarChart3, Shield,
  ArrowLeft, Sparkles, Users, Lock,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

type Step = 1 | 2 | 3 | "results";

interface Inputs {
  arr: number;
  employees: number;
  frameworks: string[];
  pipelineDeals: number;
  avgDealSize: number;
  complianceStatus: "none" | "inprogress" | "certified";
}

// ── Constants ─────────────────────────────────────────────────────────────────

const ARR_OPTIONS = [
  { label: "< $500K",        value: 300_000   },
  { label: "$500K – $1M",    value: 750_000   },
  { label: "$1M – $3M",      value: 2_000_000 },
  { label: "$3M – $10M",     value: 6_500_000 },
  { label: "$10M – $30M",    value: 20_000_000 },
  { label: "$30M+",          value: 50_000_000 },
];

const EMP_OPTIONS = [
  { label: "1 – 10",    value: 5   },
  { label: "11 – 25",   value: 18  },
  { label: "26 – 50",   value: 38  },
  { label: "51 – 100",  value: 75  },
  { label: "101 – 250", value: 175 },
  { label: "250+",      value: 300 },
];

const DEAL_SIZES = [
  { label: "< $5K",          value: 2_500  },
  { label: "$5K – $25K",     value: 15_000 },
  { label: "$25K – $100K",   value: 60_000 },
  { label: "$100K – $500K",  value: 250_000 },
  { label: "$500K+",         value: 750_000 },
];

const PIPELINE_OPTIONS = [
  { label: "0 – 2",   value: 1  },
  { label: "3 – 5",   value: 4  },
  { label: "6 – 10",  value: 8  },
  { label: "11 – 20", value: 15 },
  { label: "20+",     value: 25 },
];

const FRAMEWORKS = [
  { id: "soc2",      label: "SOC 2",       desc: "Required by 78% of enterprise buyers" },
  { id: "iso27001",  label: "ISO 27001",   desc: "EMEA procurement standard"             },
  { id: "gdpr",      label: "GDPR",        desc: "EU/UK data protection law"             },
  { id: "hipaa",     label: "HIPAA",       desc: "US healthcare data law"                },
];

// ── Calculation engine ────────────────────────────────────────────────────────

function calcRisk(inputs: Inputs) {
  const { arr, employees, frameworks, pipelineDeals, avgDealSize, complianceStatus } = inputs;

  // ── 1. Revenue blocked in pipeline ──────────────────────────────────────
  // 72% of enterprise deals require at least SOC 2 / ISO 27001
  // Block rate by status: none=65%, inprogress=30%, certified=5%
  const blockRate = complianceStatus === "none" ? 0.65
    : complianceStatus === "inprogress" ? 0.30
    : 0.05;
  const enterpriseFraction = 0.72;
  const pipelineBlocked = pipelineDeals * avgDealSize * enterpriseFraction * blockRate;

  // ── 2. Annual churn from compliance pressure ─────────────────────────────
  // Customers renewing will ask for certs; block rate is lower (30% of blockRate)
  const churnRisk = complianceStatus === "certified" ? 0
    : arr * (blockRate * 0.30);

  // ── 3. Regulatory fines exposure ────────────────────────────────────────
  let finesExposure = 0;
  if (frameworks.includes("gdpr")) {
    // 4% of global annual turnover, but for modeling we use 2% ARR (expected value)
    finesExposure += arr * 0.02;
  }
  if (frameworks.includes("hipaa")) {
    // $100–$50K per violation; assume 5 potential violations at $10K avg expected
    finesExposure += 50_000;
  }
  if (frameworks.includes("soc2") && complianceStatus === "none") {
    // Data breach cost average for non-certified companies: ~$200K for SMBs
    finesExposure += 200_000;
  }

  // ── 4. Internal staff cost ───────────────────────────────────────────────
  // Without automation: compliance takes ~12% of eng/ops time
  // Avg fully-loaded cost: $120/hr, 2080 hrs/yr
  const annualStaffCost = 120 * 2080 * employees * 0.12;
  // Scale down by team size (not everyone does compliance)
  const complianceHeadcount = Math.max(0.5, employees * 0.12);
  const staffCost = 120 * 2080 * complianceHeadcount;

  // External audit prep (consultant fees)
  const auditPrepCost = complianceStatus === "certified"
    ? 0
    : Math.min(150_000, 50_000 + arr * 0.005);

  const totalStaffCost = staffCost + auditPrepCost;

  // ── 5. Opportunity cost of delayed deals (time-to-close) ────────────────
  // Average 4-6 months delay to close a deal without cert; time value of money
  const delayCost = pipelineDeals * avgDealSize * 0.08; // 8% time-value per year

  // ── Totals ───────────────────────────────────────────────────────────────
  const totalExposure = pipelineBlocked + churnRisk + finesExposure + totalStaffCost + delayCost;

  // TraceLayer savings: automates 80% of staff work, closes 70% of deal blocks
  const tlSavings = staffCost * 0.80 + pipelineBlocked * 0.70;

  // ROI
  const tlAnnualCost = 149 * 12; // Growth plan
  const roiMultiple = tlAnnualCost > 0 ? Math.round(tlSavings / tlAnnualCost) : 0;

  return {
    pipelineBlocked,
    churnRisk,
    finesExposure,
    totalStaffCost,
    delayCost,
    totalExposure,
    tlSavings,
    roiMultiple,
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function fmt(n: number, compact = false) {
  if (compact && n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  if (compact && n >= 1_000) return `$${Math.round(n / 1_000)}K`;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

function RiskBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = Math.min(100, (value / max) * 100);
  return (
    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

// ── Option button ─────────────────────────────────────────────────────────────

function OptionBtn({
  selected,
  onClick,
  children,
}: {
  selected: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2.5 rounded-xl border text-sm font-semibold transition-all ${
        selected
          ? "bg-teal-600 border-teal-600 text-white shadow-md shadow-teal-600/20"
          : "border-gray-200 text-gray-600 hover:border-teal-300 hover:text-teal-700 hover:bg-teal-50/50"
      }`}
    >
      {children}
    </button>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function RevenueImpactPage() {
  const [step, setStep] = useState<Step>(1);
  const [inputs, setInputs] = useState<Inputs>({
    arr: 0,
    employees: 0,
    frameworks: ["soc2"],
    pipelineDeals: 0,
    avgDealSize: 0,
    complianceStatus: "none",
  });

  const set = <K extends keyof Inputs>(key: K, val: Inputs[K]) =>
    setInputs((p) => ({ ...p, [key]: val }));

  const toggleFramework = (id: string) => {
    setInputs((p) => ({
      ...p,
      frameworks: p.frameworks.includes(id)
        ? p.frameworks.filter((f) => f !== id)
        : [...p.frameworks, id],
    }));
  };

  const step1Valid = inputs.arr > 0 && inputs.employees > 0 && inputs.frameworks.length > 0;
  const step2Valid = inputs.pipelineDeals > 0 && inputs.avgDealSize > 0;
  const step3Valid = !!inputs.complianceStatus;

  const results = step === "results" ? calcRisk(inputs) : null;

  const progressPct = step === "results" ? 100 : ((step as number) / 3) * 100;

  return (
    <div className="min-h-screen bg-[#f7f1e8] font-[family:'Sora',_ui-sans-serif,_system-ui]">

      {/* Nav */}
      <header className="sticky top-0 z-50 bg-[#f7f1e8]/95 backdrop-blur-md border-b border-black/5">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-extrabold text-base tracking-tight text-gray-900">TraceLayer</span>
          </Link>
          <Link href="/tools" className="hidden md:flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
            <ArrowLeft className="w-3.5 h-3.5" /> Free Tools
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login" className="hidden md:block text-sm text-gray-500 hover:text-gray-900 font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
              Sign in
            </Link>
            <Link href="/register" className="text-sm bg-teal-600 hover:bg-teal-700 text-white font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-sm">
              Get started free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="max-w-3xl mx-auto px-6 pt-14 pb-8 text-center">
        <div className="inline-flex items-center gap-2 bg-white/80 text-orange-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5 border border-black/5 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-orange-500" />
          Free · 2 minutes · No signup
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight tracking-tight">
          How much is non-compliance<br />
          <span className="bg-gradient-to-r from-orange-500 to-rose-500 bg-clip-text text-transparent">costing your business?</span>
        </h1>
        <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed">
          3 quick questions. See the real dollar impact — blocked deals, regulatory fines, and staff time — plus exactly how much you could recover.
        </p>
      </section>

      {/* Calculator */}
      <section className="max-w-2xl mx-auto px-6 pb-20">

        {/* Progress bar */}
        {step !== "results" && (
          <div className="mb-8">
            <div className="flex items-center justify-between text-xs text-gray-400 font-semibold mb-2">
              <span>Step {step as number} of 3</span>
              <span>{Math.round(progressPct)}% complete</span>
            </div>
            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-orange-500 to-rose-500 rounded-full transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {/* ── Step 1: Business basics ── */}
        {step === 1 && (
          <div className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-7 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center shrink-0">
                <BarChart3 className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h2 className="font-extrabold text-gray-900 text-lg leading-tight">Your business</h2>
                <p className="text-xs text-gray-400">Revenue, team size &amp; target frameworks</p>
              </div>
            </div>

            <div className="space-y-6">
              {/* ARR */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2.5">
                  Annual recurring revenue (ARR)
                </label>
                <div className="flex flex-wrap gap-2">
                  {ARR_OPTIONS.map((o) => (
                    <OptionBtn key={o.value} selected={inputs.arr === o.value} onClick={() => set("arr", o.value)}>
                      {o.label}
                    </OptionBtn>
                  ))}
                </div>
              </div>

              {/* Employees */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2.5">
                  Team size
                </label>
                <div className="flex flex-wrap gap-2">
                  {EMP_OPTIONS.map((o) => (
                    <OptionBtn key={o.value} selected={inputs.employees === o.value} onClick={() => set("employees", o.value)}>
                      {o.label}
                    </OptionBtn>
                  ))}
                </div>
              </div>

              {/* Frameworks */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2.5">
                  Which frameworks matter to your customers? <span className="text-gray-400 font-normal">(pick all that apply)</span>
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {FRAMEWORKS.map((f) => {
                    const selected = inputs.frameworks.includes(f.id);
                    return (
                      <button
                        key={f.id}
                        onClick={() => toggleFramework(f.id)}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-left transition-all ${
                          selected
                            ? "border-teal-500 bg-teal-50"
                            : "border-gray-200 hover:border-teal-200 hover:bg-teal-50/30"
                        }`}
                      >
                        <div className={`w-4 h-4 rounded-md border-2 flex items-center justify-center shrink-0 transition-colors ${
                          selected ? "border-teal-500 bg-teal-500" : "border-gray-300"
                        }`}>
                          {selected && <CheckCircle2 className="w-3 h-3 text-white" />}
                        </div>
                        <div>
                          <p className="text-sm font-bold text-gray-800">{f.label}</p>
                          <p className="text-xs text-gray-400">{f.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={!step1Valid}
              className="mt-8 w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3.5 rounded-xl transition-colors"
            >
              Continue <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* ── Step 2: Pipeline ── */}
        {step === 2 && (
          <div className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-7 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center shrink-0">
                <TrendingDown className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h2 className="font-extrabold text-gray-900 text-lg leading-tight">Your sales pipeline</h2>
                <p className="text-xs text-gray-400">We&apos;ll calculate how many deals compliance is blocking</p>
              </div>
            </div>

            <div className="space-y-6">
              {/* Pipeline deals */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2.5">
                  Enterprise deals currently in pipeline
                  <span className="block text-xs font-normal text-gray-400 mt-0.5">Deals where the buyer asks about security or compliance</span>
                </label>
                <div className="flex flex-wrap gap-2">
                  {PIPELINE_OPTIONS.map((o) => (
                    <OptionBtn key={o.value} selected={inputs.pipelineDeals === o.value} onClick={() => set("pipelineDeals", o.value)}>
                      {o.label}
                    </OptionBtn>
                  ))}
                </div>
              </div>

              {/* Avg deal size */}
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2.5">
                  Average deal size
                </label>
                <div className="flex flex-wrap gap-2">
                  {DEAL_SIZES.map((o) => (
                    <OptionBtn key={o.value} selected={inputs.avgDealSize === o.value} onClick={() => set("avgDealSize", o.value)}>
                      {o.label}
                    </OptionBtn>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button
                onClick={() => setStep(1)}
                className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-200 text-gray-600 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => setStep(3)}
                disabled={!step2Valid}
                className="flex-1 flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-colors"
              >
                Continue <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Compliance status ── */}
        {step === 3 && (
          <div className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-7 md:p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-9 h-9 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center shrink-0">
                <Shield className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <h2 className="font-extrabold text-gray-900 text-lg leading-tight">Current compliance status</h2>
                <p className="text-xs text-gray-400">Where are you right now?</p>
              </div>
            </div>

            <div className="space-y-3">
              {[
                {
                  id: "none" as const,
                  label: "No active compliance program",
                  desc: "We handle it ad hoc — no dedicated process or tooling",
                  risk: "Highest risk",
                  riskColor: "text-red-600 bg-red-50",
                },
                {
                  id: "inprogress" as const,
                  label: "Working on it",
                  desc: "We've started but haven't achieved any certifications yet",
                  risk: "Medium risk",
                  riskColor: "text-orange-600 bg-orange-50",
                },
                {
                  id: "certified" as const,
                  label: "Certified / audit complete",
                  desc: "We hold SOC 2, ISO 27001, or another active certification",
                  risk: "Lower risk",
                  riskColor: "text-teal-700 bg-teal-50",
                },
              ].map((opt) => {
                const selected = inputs.complianceStatus === opt.id;
                return (
                  <button
                    key={opt.id}
                    onClick={() => set("complianceStatus", opt.id)}
                    className={`w-full flex items-center gap-4 px-4 py-4 rounded-xl border text-left transition-all ${
                      selected
                        ? "border-teal-500 bg-teal-50"
                        : "border-gray-200 hover:border-teal-200 hover:bg-gray-50"
                    }`}
                  >
                    <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 transition-colors ${
                      selected ? "border-teal-500 bg-teal-500" : "border-gray-300"
                    }`}>
                      {selected && <div className="w-2 h-2 bg-white rounded-full" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-sm text-gray-900">{opt.label}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{opt.desc}</p>
                    </div>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0 ${opt.riskColor}`}>
                      {opt.risk}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="flex gap-3 mt-8">
              <button
                onClick={() => setStep(2)}
                className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-200 text-gray-600 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> Back
              </button>
              <button
                onClick={() => setStep("results")}
                disabled={!step3Valid}
                className="flex-1 flex items-center justify-center gap-2 bg-gradient-to-r from-orange-500 to-rose-500 hover:from-orange-600 hover:to-rose-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold py-3 rounded-xl transition-all shadow-md shadow-orange-500/20"
              >
                Calculate my risk <Sparkles className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* ── Results ── */}
        {step === "results" && results && (
          <div className="space-y-5">

            {/* Header card */}
            <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-7 md:p-8 text-white relative overflow-hidden">
              <div className="absolute -top-10 -right-10 w-48 h-48 rounded-full bg-[radial-gradient(circle,rgba(249,115,22,0.15),transparent)]" />
              <div className="absolute -bottom-8 -left-8 w-40 h-40 rounded-full bg-[radial-gradient(circle,rgba(244,63,94,0.10),transparent)]" />
              <p className="text-xs font-bold text-white/50 uppercase tracking-widest mb-2">Total estimated risk exposure</p>
              <p className="text-4xl md:text-5xl font-extrabold bg-gradient-to-r from-orange-400 to-rose-400 bg-clip-text text-transparent mb-1">
                {fmt(results.totalExposure)}
              </p>
              <p className="text-white/60 text-sm">per year · based on your inputs</p>

              <div className="mt-6 grid grid-cols-3 gap-4 pt-5 border-t border-white/10">
                <div>
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-wider mb-1">With TraceLayer</p>
                  <p className="text-lg font-extrabold text-teal-400">{fmt(results.tlSavings)}</p>
                  <p className="text-[10px] text-white/40">recovered / yr</p>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-wider mb-1">ROI</p>
                  <p className="text-lg font-extrabold text-teal-400">{results.roiMultiple}×</p>
                  <p className="text-[10px] text-white/40">return on cost</p>
                </div>
                <div>
                  <p className="text-[10px] font-bold text-white/40 uppercase tracking-wider mb-1">Payback</p>
                  <p className="text-lg font-extrabold text-teal-400">
                    {results.roiMultiple >= 10 ? "< 2 weeks" : results.roiMultiple >= 4 ? "< 45 days" : "< 90 days"}
                  </p>
                  <p className="text-[10px] text-white/40">to break even</p>
                </div>
              </div>
            </div>

            {/* Breakdown */}
            <div className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-6">
              <h3 className="font-extrabold text-gray-900 mb-5">Risk breakdown</h3>
              <div className="space-y-4">
                {[
                  {
                    label: "Revenue blocked in sales pipeline",
                    icon: TrendingDown,
                    value: results.pipelineBlocked,
                    color: "bg-rose-500",
                    iconColor: "text-rose-500",
                    bg: "bg-rose-50",
                    desc: `${Math.round(inputs.pipelineDeals * 0.72 * (inputs.complianceStatus === "none" ? 0.65 : inputs.complianceStatus === "inprogress" ? 0.30 : 0.05))} deals likely stalled without a compliance cert`,
                  },
                  {
                    label: "Annual churn risk from compliance pressure",
                    icon: Users,
                    value: results.churnRisk,
                    color: "bg-orange-400",
                    iconColor: "text-orange-500",
                    bg: "bg-orange-50",
                    desc: "Existing customers who will ask for certs at renewal",
                  },
                  {
                    label: "Regulatory fines exposure",
                    icon: AlertTriangle,
                    value: results.finesExposure,
                    color: "bg-amber-400",
                    iconColor: "text-amber-500",
                    bg: "bg-amber-50",
                    desc: `Based on ${inputs.frameworks.map(f => f.toUpperCase()).join(", ")} obligations and expected breach probability`,
                  },
                  {
                    label: "Internal staff cost (manual compliance work)",
                    icon: Clock,
                    value: results.totalStaffCost,
                    color: "bg-violet-400",
                    iconColor: "text-violet-500",
                    bg: "bg-violet-50",
                    desc: "Team hours + external audit prep — fully-loaded cost",
                  },
                  {
                    label: "Deal delay opportunity cost",
                    icon: DollarSign,
                    value: results.delayCost,
                    color: "bg-sky-400",
                    iconColor: "text-sky-500",
                    bg: "bg-sky-50",
                    desc: "Time-value of 4–6 month compliance-related sales delays",
                  },
                ].map((row) => {
                  const Icon = row.icon;
                  return (
                    <div key={row.label}>
                      <div className="flex items-start gap-3 mb-1.5">
                        <div className={`w-7 h-7 rounded-lg ${row.bg} flex items-center justify-center shrink-0 mt-0.5`}>
                          <Icon className={`w-3.5 h-3.5 ${row.iconColor}`} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-1">
                            <span className="text-sm font-semibold text-gray-800 leading-snug">{row.label}</span>
                            <span className="text-sm font-extrabold text-gray-900 shrink-0">{fmt(row.value, true)}</span>
                          </div>
                          <RiskBar value={row.value} max={results.totalExposure * 0.6} color={row.color} />
                          <p className="text-xs text-gray-400 mt-1">{row.desc}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* What TraceLayer recovers */}
            <div className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-6">
              <h3 className="font-extrabold text-gray-900 mb-4">What TraceLayer fixes</h3>
              <div className="space-y-2.5">
                {[
                  {
                    text: "Automates 80%+ of evidence collection — your team stops doing compliance manually",
                    icon: CheckCircle2,
                  },
                  {
                    text: "Continuous readiness dashboard — walk into any enterprise deal with proof, not promises",
                    icon: CheckCircle2,
                  },
                  {
                    text: "SOC 2 audit in weeks, not months — auditors get a live evidence room, not a spreadsheet",
                    icon: CheckCircle2,
                  },
                  {
                    text: "GDPR/HIPAA data flow maps auto-generated from your integrations",
                    icon: CheckCircle2,
                  },
                  {
                    text: "AI agent monitoring — track what your AI tools do with customer data in real-time",
                    icon: CheckCircle2,
                  },
                ].map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.text} className="flex items-start gap-3">
                      <Icon className="w-4 h-4 text-teal-500 shrink-0 mt-0.5" />
                      <p className="text-sm text-gray-600 leading-snug">{item.text}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* CTA */}
            <div className="bg-teal-600 rounded-2xl p-7 text-center">
              <div className="inline-flex items-center gap-2 bg-white/20 text-white/80 text-xs font-semibold px-3 py-1.5 rounded-full mb-4">
                <Lock className="w-3 h-3" /> Free to start · No credit card
              </div>
              <h3 className="text-2xl font-extrabold text-white mb-2 leading-tight">
                Recover {fmt(results.tlSavings, true)} this year
              </h3>
              <p className="text-white/75 text-sm mb-6 max-w-md mx-auto leading-relaxed">
                Get SOC 2-ready in weeks, unblock enterprise deals, and put your team back on product — not spreadsheets.
              </p>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm"
              >
                Start for free — see it in 5 minutes <ArrowRight className="w-4 h-4" />
              </Link>
              <p className="text-white/50 text-xs mt-3">
                {results.roiMultiple}× ROI · Pays back in {results.roiMultiple >= 10 ? "under 2 weeks" : results.roiMultiple >= 4 ? "under 45 days" : "under 90 days"}
              </p>
            </div>

            {/* Start over */}
            <div className="text-center">
              <button
                onClick={() => {
                  setStep(1);
                  setInputs({ arr: 0, employees: 0, frameworks: ["soc2"], pipelineDeals: 0, avgDealSize: 0, complianceStatus: "none" });
                }}
                className="text-sm text-gray-400 hover:text-gray-700 underline underline-offset-2 transition-colors"
              >
                Start over with different inputs
              </button>
            </div>
          </div>
        )}

      </section>

      {/* Social proof strip */}
      {step !== "results" && (
        <div className="border-t border-black/5 py-8 bg-white/50">
          <div className="max-w-3xl mx-auto px-6">
            <p className="text-center text-xs font-semibold text-gray-400 uppercase tracking-wider mb-6">
              Trusted by startup CTOs closing enterprise deals
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
              {[
                { stat: "78%", desc: "of enterprise buyers require SOC 2 before signing" },
                { stat: "$4.5M", desc: "average cost of a data breach for a mid-market company" },
                { stat: "4–6 mo", desc: "average sales delay when compliance is missing" },
              ].map((item) => (
                <div key={item.stat} className="text-center">
                  <p className="text-2xl font-extrabold text-gray-900 mb-1">{item.stat}</p>
                  <p className="text-xs text-gray-500 leading-snug">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-black/5 py-8 bg-[#f7f1e8]">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={24} height={24} className="rounded-md" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
          <p className="text-xs text-gray-400">Estimates are based on industry benchmarks. Actual figures vary by company.</p>
          <Link href="/register" className="text-sm font-semibold text-teal-600 hover:text-teal-700 transition-colors">
            Get started free →
          </Link>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
        html { scroll-behavior: smooth; }
      `}</style>
    </div>
  );
}
