"use client";

import { useEffect, useState } from "react";
import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import {
  ShieldCheck, Plug, FileText, Zap, ArrowRight, CheckCircle2,
  BarChart3, Lock, Star, Clock, TrendingUp, Users, ChevronDown,
} from "lucide-react";

// ── Integration logos ────────────────────────────────────────────────────────

function AwsLogo() {
  return (
    <svg width="52" height="32" viewBox="0 0 52 32" fill="none">
      <text x="0" y="22" fontSize="22" fontWeight="900" fill="#FF9900" fontFamily="Arial,sans-serif">aws</text>
      <path d="M3 27 Q26 34 49 27" stroke="#FF9900" strokeWidth="2.2" fill="none" strokeLinecap="round"/>
    </svg>
  );
}

function GithubLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="#1f2937">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>
  );
}

function SlackLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M5.042 15.165a2.528 2.528 0 01-2.52 2.523A2.528 2.528 0 010 15.165a2.527 2.527 0 012.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 012.521-2.52 2.527 2.527 0 012.521 2.52v6.313A2.528 2.528 0 018.834 24a2.528 2.528 0 01-2.521-2.522v-6.313z" fill="#E01E5A"/>
      <path d="M8.834 5.042a2.528 2.528 0 01-2.521-2.52A2.528 2.528 0 018.834 0a2.528 2.528 0 012.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 012.521 2.521 2.528 2.528 0 01-2.521 2.521H2.522A2.528 2.528 0 010 8.834a2.528 2.528 0 012.522-2.521h6.312z" fill="#36C5F0"/>
      <path d="M18.956 8.834a2.528 2.528 0 012.522-2.521A2.528 2.528 0 0124 8.834a2.528 2.528 0 01-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 01-2.523 2.521 2.527 2.527 0 01-2.52-2.521V2.522A2.527 2.527 0 0115.165 0a2.528 2.528 0 012.523 2.522v6.312z" fill="#2EB67D"/>
      <path d="M15.165 18.956a2.528 2.528 0 012.523 2.522A2.528 2.528 0 0115.165 24a2.527 2.527 0 01-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 01-2.52-2.523 2.526 2.526 0 012.52-2.52h6.313A2.527 2.527 0 0124 15.165a2.528 2.528 0 01-2.522 2.523h-6.313z" fill="#ECB22E"/>
    </svg>
  );
}

function GoogleLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

function JiraLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M11.571 11.513H0a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0012.575 24V12.518a1.005 1.005 0 00-1.004-1.005z" fill="#2684FF"/>
      <path d="M6.107 6.108H17.678A5.218 5.218 0 0012.446.893h-2.13V-1.16A5.215 5.215 0 005.103 4.054v2.049h1.004z" fill="url(#jira-grad-1)"/>
      <path d="M17.679 6.107H6.108a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0018.683 18.6V7.112a1.005 1.005 0 00-1.004-1.005z" fill="url(#jira-grad-2)"/>
      <defs>
        <linearGradient id="jira-grad-1" x1="16.2" y1="6.11" x2="10.6" y2="0.89" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/>
          <stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
        <linearGradient id="jira-grad-2" x1="7.5" y1="11.57" x2="13.9" y2="18.3" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/>
          <stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
      </defs>
    </svg>
  );
}

function OktaLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="11" fill="#007DC1"/>
      <circle cx="12" cy="12" r="4.5" fill="white"/>
    </svg>
  );
}

function AzureLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
      <path d="M13.05 4.24L6.56 19.03l14.96.01L13.05 4.24z" fill="#0078D4"/>
      <path d="M13.29 4.24L8.73 10.9l4.44 8.13H2.48L13.29 4.24z" fill="#0078D4" opacity=".7"/>
    </svg>
  );
}

const INTEGRATION_LOGOS = [
  { name: "AWS", logo: <AwsLogo /> },
  { name: "GitHub", logo: <GithubLogo /> },
  { name: "Slack", logo: <SlackLogo /> },
  { name: "Google Workspace", logo: <GoogleLogo /> },
  { name: "Jira", logo: <JiraLogo /> },
  { name: "Okta", logo: <OktaLogo /> },
  { name: "Azure AD", logo: <AzureLogo /> },
];

// ── Static data ───────────────────────────────────────────────────────────────

const STATS = [
  { value: "7", label: "Integrations" },
  { value: "3", label: "Frameworks" },
  { value: "24h", label: "Collection cycle" },
  { value: "100%", label: "Automated" },
];

const FRAMEWORKS = [
  { name: "SOC 2", desc: "Type II", detail: "CC controls across security, availability, and confidentiality" },
  { name: "ISO 27001", desc: "2022 Edition", detail: "93 Annex A controls across 4 themes" },
  { name: "HIPAA", desc: "Security Rule", detail: "Administrative, physical, and technical safeguards" },
];

const FEATURES = [
  {
    icon: Plug,
    title: "One-click integrations",
    desc: "Connect AWS, GitHub, Slack, Google Workspace, Okta, Jira, and Azure AD in minutes. No agents. No code. Just an API key.",
  },
  {
    icon: Zap,
    title: "Automated evidence collection",
    desc: "Evidence runs every 24 hours without you touching anything — IAM users, audit logs, repositories, access policies, and more.",
  },
  {
    icon: BarChart3,
    title: "Real-time compliance score",
    desc: "See your SOC 2, ISO 27001, or HIPAA posture at a glance. Per-control breakdown shows exactly what evidence is missing.",
  },
  {
    icon: FileText,
    title: "Audit-ready PDF reports",
    desc: "Generate a formatted evidence report in one click with a cover page, executive summary, and per-control evidence tables.",
  },
  {
    icon: ShieldCheck,
    title: "Manual controls checklist",
    desc: "Track policies, training completion, and vendor assessments alongside automated evidence. Mark compliant or N/A with notes.",
  },
  {
    icon: Lock,
    title: "Secure by default",
    desc: "Credentials encrypted at rest with Fernet. JWT auth with refresh token rotation. RBAC admin/member roles.",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Connect your tools",
    desc: "Link your cloud infrastructure and SaaS apps in under 5 minutes using API keys or service accounts. No OAuth dance.",
  },
  {
    step: "02",
    title: "Evidence collected automatically",
    desc: "TraceLayer pulls IAM users, audit logs, repositories, and access policies every 24 hours and maps them to compliance controls.",
  },
  {
    step: "03",
    title: "Score, report, repeat",
    desc: "See your compliance score update in real time. Generate a PDF report for your auditor whenever you need it — no prep required.",
  },
];

const TESTIMONIALS = [
  {
    quote: "We cut our SOC 2 prep time from 3 months to 2 weeks. The automated evidence collection alone saved us hundreds of hours.",
    author: "Sarah Chen",
    role: "Head of Security, Series B SaaS",
    stars: 5,
  },
  {
    quote: "Our auditor was impressed. Everything was organized, timestamped, and mapped to controls. TraceLayer made us look like we had a 10-person compliance team.",
    author: "Marcus Webb",
    role: "CTO, Fintech Startup",
    stars: 5,
  },
  {
    quote: "We were chasing evidence manually in spreadsheets. Now it's all automated and we have a live score we can show investors.",
    author: "Priya Nair",
    role: "VP Engineering, Healthcare Platform",
    stars: 5,
  },
];

const PAIN_POINTS = [
  { before: "Spreadsheets tracking evidence manually", after: "Automated collection every 24 hours" },
  { before: "Months of prep before an audit", after: "Always audit-ready with live evidence" },
  { before: "One framework at a time", after: "SOC 2, ISO 27001, and HIPAA simultaneously" },
  { before: "Consultants charging $50k+ to help", after: "Self-serve for a fraction of the cost" },
];

const PRICING = [
  {
    name: "Starter",
    price: "Free",
    period: "",
    desc: "Perfect for early-stage teams getting audit-ready.",
    features: ["Up to 3 integrations", "SOC 2, ISO 27001 & HIPAA", "Automated evidence collection", "PDF & JSON reports", "2 team members"],
    cta: "Get started free",
    highlighted: false,
  },
  {
    name: "Growth",
    price: "$149",
    period: "/mo",
    desc: "For teams actively pursuing certification.",
    features: ["All 7 integrations", "All 3 frameworks", "Daily collection", "Unlimited reports", "Unlimited team members", "Priority support"],
    cta: "Start free trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For larger orgs with advanced compliance needs.",
    features: ["Everything in Growth", "Custom integrations", "SSO / SAML", "Dedicated CSM", "SLA guarantee", "Custom audit reports"],
    cta: "Contact sales",
    highlighted: false,
  },
];

const FAQ = [
  { q: "How long does setup take?", a: "Under 5 minutes. Create an account, paste an API key for your first integration, and evidence collection starts immediately. No agents to deploy, no code to write." },
  { q: "Do you store my cloud credentials?", a: "All credentials are encrypted at rest using Fernet symmetric encryption before being written to the database. We never store or log plaintext secrets, and access is scoped to your company only." },
  { q: "Which compliance frameworks do you support?", a: "SOC 2 Type II, ISO 27001 (2022 edition), and HIPAA Security Rule. Evidence collected from your integrations maps to all three simultaneously — no duplicate work, no re-connecting anything." },
  { q: "Can I use TraceLayer for a SOC 2 Type II audit?", a: "Yes. TraceLayer collects continuous evidence across your entire observation period with timestamps — exactly what auditors need for a Type II opinion. You can generate a formatted PDF report for your auditor on demand." },
  { q: "What integrations are supported right now?", a: "AWS (IAM, CloudTrail), GitHub, Slack, Google Workspace, Jira, Okta, and Azure AD. Each integration collects multiple evidence types. More are on the roadmap." },
  { q: "Is there a free plan?", a: "Yes — TraceLayer is completely free to start with no credit card required. You get access to all three frameworks, automated collection, and PDF reports from day one." },
  { q: "How is the compliance score calculated?", a: "Each control is scored on three factors: coverage (70% weight — how many evidence types are present), recency (20% — how fresh the evidence is), and volume (10% — number of records). Scores are snapshotted up to once per hour." },
  { q: "Can my whole team access the platform?", a: "Yes. You can invite team members by email. Members can view evidence and reports; admins can connect integrations, manage the team, and generate reports. Role-based access is built in." },
];

const THEME = {
  "--bg": "#f7f1e8",
  "--ink": "#1f2937",
  "--muted": "#5b6472",
  "--accent": "#0f766e",
  "--accent-strong": "#0b5f59",
  "--accent-warm": "#f97316",
  "--card": "#ffffff",
} as CSSProperties;

// ── Marquee component ─────────────────────────────────────────────────────────

function LogoPill({ name, logo }: { name: string; logo: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 bg-white border border-black/8 rounded-2xl px-5 py-3 shadow-sm shrink-0">
      <span className="flex items-center justify-center w-7 h-7">{logo}</span>
      <span className="text-sm font-semibold text-gray-700 whitespace-nowrap">{name}</span>
    </div>
  );
}

function MarqueeRow({ reverse = false }: { reverse?: boolean }) {
  const items = [...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS];
  return (
    <div className="overflow-hidden" style={{ maskImage: "linear-gradient(to right, transparent 0%, black 8%, black 92%, transparent 100%)" }}>
      <div
        className="flex gap-4 w-max"
        style={{ animation: `${reverse ? "marqueeRight" : "marqueeLeft"} 28s linear infinite` }}
      >
        {items.map((item, i) => (
          <LogoPill key={i} name={item.name} logo={item.logo} />
        ))}
      </div>
    </div>
  );
}

// ── FAQ Accordion ─────────────────────────────────────────────────────────────

function FaqAccordion({ items }: { items: typeof FAQ }) {
  const [open, setOpen] = useState<number | null>(null);
  return (
    <div className="space-y-3">
      {items.map((item, i) => (
        <div
          key={i}
          className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
            open === i
              ? "bg-white border-[color:var(--accent)]/30 shadow-[0_4px_20px_rgba(15,118,110,0.1)]"
              : "bg-white/80 border-black/5 shadow-[0_2px_8px_rgba(15,23,42,0.04)] hover:border-black/10"
          }`}
        >
          <button
            className="w-full flex items-center justify-between gap-4 px-5 py-4 text-left"
            onClick={() => setOpen(open === i ? null : i)}
            aria-expanded={open === i}
          >
            <span className="font-semibold text-sm leading-snug text-[var(--ink)]">{item.q}</span>
            <ChevronDown
              className={`w-4 h-4 shrink-0 text-[var(--accent)] transition-transform duration-300 ${open === i ? "rotate-180" : ""}`}
            />
          </button>
          {/* CSS grid trick for smooth height animation */}
          <div
            className="grid transition-all duration-300 ease-in-out"
            style={{ gridTemplateRows: open === i ? "1fr" : "0fr" }}
          >
            <div className="overflow-hidden">
              <p className="px-5 pb-5 text-sm text-[var(--muted)] leading-relaxed border-t border-black/5 pt-3">
                {item.a}
              </p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  if (loading || user) return null;

  return (
    <div
      className="min-h-screen bg-[var(--bg)] text-[var(--ink)] font-[family:'Sora',_ui-sans-serif,_system-ui]"
      style={THEME}
    >
      {/* Nav */}
      <header className="sticky top-0 z-50 bg-[color:var(--bg)]/80 backdrop-blur border-b border-black/5">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <span className="font-extrabold text-lg tracking-tight">TraceLayer</span>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm text-[var(--muted)] hover:text-[var(--ink)] font-medium transition-colors">
              Sign in
            </Link>
            <Link href="/register" className="text-sm bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-4 py-1.5 rounded-lg transition-colors">
              Get started free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(#0f766e18_1px,transparent_1px)] [background-size:24px_24px]" />
        <div className="absolute -top-32 right-0 h-96 w-96 rounded-full bg-[radial-gradient(circle,_rgba(15,118,110,0.22),_transparent)]" />
        <div className="absolute -bottom-40 -left-10 h-96 w-96 rounded-full bg-[radial-gradient(circle,_rgba(249,115,22,0.18),_transparent)]" />
        <div className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/80 text-[var(--accent)] text-xs font-semibold px-3 py-1.5 rounded-full mb-6 border border-black/5 fade-up shadow-sm">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            SOC 2 · ISO 27001 · HIPAA — all in one platform
          </div>
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-extrabold leading-tight mb-5 tracking-tight fade-up">
            Stop chasing compliance.<br />
            <span className="bg-gradient-to-r from-[var(--accent)] via-emerald-500 to-teal-400 bg-clip-text text-transparent">Let it run itself.</span>
          </h1>
          <p className="text-base sm:text-lg text-[var(--muted)] max-w-2xl mx-auto mb-8 fade-up delay-1">
            TraceLayer connects to your cloud tools and automatically collects the evidence your auditor needs —
            IAM users, audit logs, repositories, access policies — mapped to controls in real time.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap mb-10 fade-up delay-2">
            <Link href="/register" className="relative inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm overflow-hidden group shadow-[0_0_24px_rgba(15,118,110,0.4)] hover:shadow-[0_0_32px_rgba(15,118,110,0.6)]">
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
              Start for free <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/login" className="inline-flex items-center gap-2 border border-black/10 hover:border-black/20 text-[var(--ink)] font-semibold px-6 py-3 rounded-xl transition-colors text-sm">
              Sign in
            </Link>
          </div>

          {/* Mock dashboard preview */}
          <div className="max-w-3xl mx-auto bg-white rounded-2xl border border-black/8 shadow-[0_20px_60px_rgba(15,23,42,0.1)] overflow-hidden fade-up delay-2">
            <div className="flex items-center gap-1.5 px-4 py-3 border-b border-gray-100 bg-gray-50">
              <div className="w-3 h-3 rounded-full bg-red-400" />
              <div className="w-3 h-3 rounded-full bg-yellow-400" />
              <div className="w-3 h-3 rounded-full bg-green-400" />
              <span className="text-xs text-gray-400 ml-2 font-mono hidden sm:block">tracelayer.app/dashboard</span>
            </div>
            <div className="p-3 sm:p-5 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 bg-gray-50/50">
              {[
                { label: "Score", value: "87%", color: "text-green-600", sub: "SOC 2" },
                { label: "Evidence", value: "2,841", color: "text-gray-900", sub: "records" },
                { label: "Integrations", value: "4", color: "text-green-600", sub: "active" },
                { label: "Controls", value: "12", color: "text-gray-900", sub: "monitored" },
              ].map((s) => (
                <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-3 text-left">
                  <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-1 leading-tight">{s.label}</p>
                  <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">{s.sub}</p>
                </div>
              ))}
            </div>
            <div className="px-3 sm:px-5 pb-3 sm:pb-5 bg-gray-50/50">
              <div className="bg-white rounded-xl border border-gray-100 p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-semibold text-gray-700">SOC 2 Control Breakdown</span>
                  <span className="text-xs text-green-600 font-bold">87%</span>
                </div>
                {[
                  { name: "Access Control", score: 92 },
                  { name: "Logging & Monitoring", score: 85 },
                  { name: "Change Management", score: 78 },
                ].map((c) => (
                  <div key={c.name} className="mb-2">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>{c.name}</span>
                      <span className="font-semibold">{c.score}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                      <div className="h-full bg-green-500 rounded-full" style={{ width: `${c.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* Floating activity pill */}
          <div className="flex justify-center mt-4 fade-up delay-2">
            <div className="inline-flex items-center gap-2 bg-white/90 backdrop-blur rounded-full px-4 py-2 shadow-lg border border-black/5 text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <span className="text-gray-500">Evidence synced</span>
              <span className="font-semibold text-gray-900">2 minutes ago</span>
              <span className="text-gray-300">·</span>
              <span className="text-gray-500">Next run in <span className="font-semibold text-gray-900">22h</span></span>
            </div>
          </div>
        </div>
      </section>

      {/* First marquee stripe — visible in first viewport */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/40">
        <p className="text-center text-xs text-[var(--muted)] font-semibold uppercase tracking-widest mb-6">
          Integrates with the tools you already use
        </p>
        <MarqueeRow />
      </section>

      {/* Stats */}
      <section className="bg-white/60 py-10">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {STATS.map((s) => (
            <div key={s.label} className="group">
              <p className="text-4xl font-extrabold text-[var(--accent)] mb-1 group-hover:scale-110 transition-transform duration-200">{s.value}</p>
              <p className="text-sm text-[var(--muted)] font-medium">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-6 py-12 md:py-20">
        <div className="text-center mb-10 md:mb-14">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">How it works</p>
          <h2 className="text-2xl md:text-3xl font-extrabold">Up and running in minutes</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto">
            No consultants. No long implementation projects. Connect your tools, and compliance evidence starts flowing automatically.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
          {HOW_IT_WORKS.map((item) => (
            <div key={item.step} className="text-center">
              <div className="text-6xl font-black text-[color:var(--accent)]/10 mb-4 leading-none">{item.step}</div>
              <h3 className="text-base font-bold mb-2">{item.title}</h3>
              <p className="text-sm text-[var(--muted)] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Before / After */}
      <section className="bg-[var(--ink)] py-12 md:py-20">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-12">
            <p className="text-xs font-bold text-[color:var(--accent-warm)] uppercase tracking-widest mb-2">The old way vs TraceLayer</p>
            <h2 className="text-2xl md:text-3xl font-extrabold text-white">Compliance doesn&apos;t have to be painful</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-6 border border-white/10">
              <p className="text-xs font-bold text-red-400 uppercase tracking-widest mb-4">Before</p>
              <div className="space-y-3">
                {PAIN_POINTS.map((p) => (
                  <div key={p.before} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    </div>
                    <p className="text-sm text-white/60">{p.before}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-[color:var(--accent)]/20 rounded-2xl p-6 border border-[color:var(--accent)]/30">
              <p className="text-xs font-bold text-[color:var(--accent)] uppercase tracking-widest mb-4">With TraceLayer</p>
              <div className="space-y-3">
                {PAIN_POINTS.map((p) => (
                  <div key={p.after} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-[var(--accent)] shrink-0 mt-0.5" />
                    <p className="text-sm text-white/80">{p.after}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white/60 py-12 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-12">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Features</p>
            <h2 className="text-2xl md:text-3xl font-extrabold">Everything you need for continuous compliance</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto">
              Built for engineering teams who need to move fast without sacrificing security posture.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[var(--card)] rounded-2xl border border-black/5 p-6 shadow-[0_8px_30px_rgba(15,23,42,0.06)] hover:shadow-[0_12px_40px_rgba(15,23,42,0.1)] transition-shadow">
                <div className="w-10 h-10 bg-[color:var(--accent)]/10 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-[var(--accent)]" />
                </div>
                <h3 className="font-bold mb-2 text-sm">{title}</h3>
                <p className="text-sm text-[var(--muted)] leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Second marquee stripe — mid page */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/40">
        <MarqueeRow reverse />
      </section>

      {/* Frameworks */}
      <section className="max-w-6xl mx-auto px-6 py-12 md:py-20">
        <div className="text-center mb-10 md:mb-12">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Frameworks</p>
          <h2 className="text-2xl md:text-3xl font-extrabold">One platform, three frameworks</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto">
            Your integrations map evidence to all frameworks simultaneously. Switch views without reconnecting anything.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {FRAMEWORKS.map((f) => (
            <div key={f.name} className="bg-[var(--card)] border border-black/5 rounded-2xl px-8 py-8 text-center shadow-[0_8px_24px_rgba(15,23,42,0.05)] hover:shadow-[0_12px_32px_rgba(15,23,42,0.1)] transition-shadow group">
              <div className="w-12 h-12 bg-[color:var(--accent)]/10 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:bg-[color:var(--accent)]/20 transition-colors">
                <ShieldCheck className="w-6 h-6 text-[var(--accent)]" />
              </div>
              <p className="font-extrabold text-lg">{f.name}</p>
              <p className="text-xs text-[var(--muted)] mt-1 mb-3">{f.desc}</p>
              <p className="text-xs text-[var(--muted)] leading-relaxed max-w-[160px] mx-auto">{f.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-white/60 py-12 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Pricing</p>
            <h2 className="text-2xl md:text-3xl font-extrabold">Start free. Scale when you&apos;re ready.</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto">
              No credit card required to get started. Upgrade when you need more integrations or team members.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border p-7 ${
                  plan.highlighted
                    ? "bg-[var(--ink)] border-[var(--ink)] shadow-[0_20px_60px_rgba(15,23,42,0.25)]"
                    : "bg-[var(--card)] border-black/5 shadow-[0_8px_24px_rgba(15,23,42,0.05)]"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-[var(--accent-warm)] text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1 rounded-full">Most popular</span>
                  </div>
                )}
                <p className={`text-sm font-bold mb-1 ${plan.highlighted ? "text-white/60" : "text-[var(--muted)]"}`}>{plan.name}</p>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-4xl font-black ${plan.highlighted ? "text-white" : "text-[var(--ink)]"}`}>{plan.price}</span>
                  {plan.period && <span className={`text-sm ${plan.highlighted ? "text-white/50" : "text-[var(--muted)]"}`}>{plan.period}</span>}
                </div>
                <p className={`text-xs mb-6 leading-relaxed ${plan.highlighted ? "text-white/50" : "text-[var(--muted)]"}`}>{plan.desc}</p>
                <div className="space-y-2.5 mb-7">
                  {plan.features.map((f) => (
                    <div key={f} className="flex items-center gap-2.5">
                      <CheckCircle2 className={`w-4 h-4 shrink-0 ${plan.highlighted ? "text-emerald-400" : "text-[var(--accent)]"}`} />
                      <span className={`text-xs ${plan.highlighted ? "text-white/70" : "text-[var(--ink)]"}`}>{f}</span>
                    </div>
                  ))}
                </div>
                <Link
                  href="/register"
                  className={`block text-center text-sm font-semibold py-2.5 rounded-xl transition-colors ${
                    plan.highlighted
                      ? "bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white"
                      : "bg-[color:var(--ink)]/5 hover:bg-[color:var(--ink)]/10 text-[var(--ink)]"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-12 md:py-20 bg-[var(--bg)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-8 md:mb-12">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">FAQ</p>
            <h2 className="text-2xl md:text-3xl font-extrabold">Common questions</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-md mx-auto">
              Everything you need to know before getting started.
            </p>
          </div>
          <FaqAccordion items={FAQ} />
          <p className="text-center text-sm text-[var(--muted)] mt-8">
            Still have questions?{" "}
            <a href="mailto:hello@tracelayer.it.com" className="text-[var(--accent)] font-semibold hover:underline">
              Drop us a line
            </a>
          </p>
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-white/60 py-12 md:py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-12">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">What teams say</p>
            <h2 className="text-2xl md:text-3xl font-extrabold">Trusted by security-conscious teams</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((t) => (
              <div key={t.author} className="bg-[var(--card)] rounded-2xl border border-black/5 p-6 shadow-[0_8px_24px_rgba(15,23,42,0.05)]">
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: t.stars }).map((_, i) => (
                    <Star key={i} className="w-3.5 h-3.5 fill-[var(--accent-warm)] text-[var(--accent-warm)]" />
                  ))}
                </div>
                <p className="text-sm text-[var(--ink)] leading-relaxed mb-5">&ldquo;{t.quote}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[color:var(--accent)]/15 flex items-center justify-center text-xs font-bold text-[var(--accent)]">
                    {t.author[0]}
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[var(--ink)]">{t.author}</p>
                    <p className="text-xs text-[var(--muted)]">{t.role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Metrics strip */}
      <section className="border-y border-black/5 bg-white/40 py-10">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Clock className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">2 weeks</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Average time to first audit-ready report</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <TrendingUp className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">90%</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Reduction in manual evidence prep</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Users className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">1 person</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Can run your entire compliance program</p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-[var(--accent)] py-12 md:py-20">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <p className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Get started today</p>
          <h2 className="text-3xl md:text-4xl font-extrabold text-white mb-4 leading-tight">
            Your next audit starts now.
          </h2>
          <p className="text-white/80 mb-8 text-sm leading-relaxed max-w-md mx-auto">
            Create your account, connect your first integration, and see your compliance score in under 5 minutes. No credit card required.
          </p>
          <Link href="/register" className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-[var(--accent)] font-bold px-8 py-3.5 rounded-xl transition-colors text-sm">
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/50 text-xs mt-4">Free to start · No credit card · Setup in 5 minutes</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/5 py-8 bg-[var(--bg)]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between flex-wrap gap-4 mb-6">
            <span className="font-extrabold text-lg text-[var(--ink)]">TraceLayer</span>
            <div className="flex items-center gap-6 text-xs text-[var(--muted)]">
              <Link href="/login" className="hover:text-[var(--ink)] transition-colors">Sign in</Link>
              <Link href="/register" className="hover:text-[var(--ink)] transition-colors">Get started</Link>
            </div>
          </div>
          <div className="flex items-center justify-between text-xs text-[var(--muted)] flex-wrap gap-3 pt-4 border-t border-black/5">
            <div className="flex items-center gap-4">
              {["SOC 2", "ISO 27001", "HIPAA"].map((f) => (
                <span key={f} className="flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3 text-[var(--accent-warm)]" /> {f}
                </span>
              ))}
            </div>
            <span>© {new Date().getFullYear()} TraceLayer. All rights reserved.</span>
          </div>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');

        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(14px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes marqueeLeft {
          from { transform: translateX(0); }
          to   { transform: translateX(-50%); }
        }
        @keyframes marqueeRight {
          from { transform: translateX(-50%); }
          to   { transform: translateX(0); }
        }
        .fade-up { animation: fadeUp 0.7s ease-out both; }
        .fade-up.delay-1 { animation-delay: 0.1s; }
        .fade-up.delay-2 { animation-delay: 0.2s; }
      `}</style>
    </div>
  );
}
