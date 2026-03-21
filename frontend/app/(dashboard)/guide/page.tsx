"use client";

import Link from "next/link";
import {
  Compass,
  Plug,
  ShieldCheck,
  Database,
  AlertTriangle,
  Siren,
  Bug,
  ShieldAlert,
  Server,
  RefreshCw,
  Building2,
  UserCheck,
  GraduationCap,
  BookOpen,
  BadgeCheck,
  UserMinus,
  Workflow,
  BookCheck,
  Archive,
  ShieldX,
  UserSearch,
  FileText,
  ClipboardList,
  Sparkles,
  ClipboardCheck,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  Target,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

type StepLink = {
  href: string;
  label: string;
  icon: React.ElementType;
  description: string;
};

type Step = {
  number: number;
  title: string;
  subtitle: string;
  tip: string;
  color: string;
  iconBg: string;
  links: StepLink[];
};

// ── Step definitions ───────────────────────────────────────────────────────

const STEPS: Step[] = [
  {
    number: 1,
    title: "Connect your stack",
    subtitle: "Wire up the tools your team already uses. TraceLayer pulls evidence automatically — no manual uploads.",
    tip: "Start with GitHub, AWS, and your identity provider. Each integration auto-populates controls.",
    color: "border-blue-200 bg-blue-50/40",
    iconBg: "bg-blue-100 text-blue-600",
    links: [
      { href: "/integrations", label: "Integrations", icon: Plug, description: "Connect 50+ tools — GitHub, AWS, Okta, Slack, and more" },
      { href: "/data-flows",   label: "Data Flow Map", icon: Workflow, description: "See where your data flows and which regulations apply" },
    ],
  },
  {
    number: 2,
    title: "Review your compliance posture",
    subtitle: "Check which controls are passing, failing, or missing evidence. Your dashboard updates in real time.",
    tip: "Focus on your target framework first (SOC 2 / ISO 27001). Red controls need evidence or a manual note.",
    color: "border-brand-200 bg-brand-50/40",
    iconBg: "bg-brand-100 text-brand-600",
    links: [
      { href: "/dashboard",   label: "Dashboard",   icon: Target,      description: "Overall readiness score and top gaps" },
      { href: "/compliance",  label: "Controls",    icon: ShieldCheck, description: "All controls mapped to your frameworks" },
      { href: "/evidence",    label: "Evidence",    icon: Database,    description: "Browse and search auto-collected evidence" },
      { href: "/readiness",   label: "Readiness",   icon: Target,      description: "Framework-by-framework gap analysis" },
    ],
  },
  {
    number: 3,
    title: "Close the gaps",
    subtitle: "Anything not covered by integrations gets handled here — risks, incidents, policies, vendors, people.",
    tip: "Assign owners to each item. Auditors look for accountability, not just documentation.",
    color: "border-amber-200 bg-amber-50/40",
    iconBg: "bg-amber-100 text-amber-700",
    links: [
      { href: "/risks",           label: "Risk Register",   icon: AlertTriangle, description: "Log and track business risks with mitigations" },
      { href: "/incidents",       label: "Incidents",       icon: Siren,         description: "Record security incidents and response actions" },
      { href: "/vulnerabilities", label: "Vulnerabilities", icon: Bug,           description: "Track CVEs and remediation status" },
      { href: "/pen-tests",       label: "Pen Tests",       icon: ShieldAlert,   description: "Upload pen test reports and findings" },
      { href: "/policies",        label: "Policies",        icon: BookOpen,      description: "Create and version your security policies" },
      { href: "/vendors",         label: "Vendor Risk",     icon: Building2,     description: "Assess and track third-party vendors" },
      { href: "/assets",          label: "Asset Inventory", icon: Server,        description: "Maintain your infrastructure asset register" },
      { href: "/access-reviews",  label: "Access Reviews",  icon: UserCheck,     description: "Periodic user access review records" },
    ],
  },
  {
    number: 4,
    title: "Manage your people",
    subtitle: "Compliance is a team sport. Make sure training is done, policies are signed, and leavers are tracked.",
    tip: "KnowBe4 and 360Learning integrations auto-pull training completion — connect them to save hours.",
    color: "border-purple-200 bg-purple-50/40",
    iconBg: "bg-purple-100 text-purple-600",
    links: [
      { href: "/training",          label: "Training",          icon: GraduationCap, description: "Track security awareness training completion" },
      { href: "/background-checks", label: "Background Checks", icon: BadgeCheck,    description: "Log pre-employment screening records" },
      { href: "/offboarding",       label: "Offboarding",       icon: UserMinus,     description: "Ensure access is revoked when staff leave" },
      { href: "/team",              label: "Team",              icon: UserCheck,     description: "Manage users and roles in TraceLayer" },
    ],
  },
  {
    number: 5,
    title: "Handle privacy obligations",
    subtitle: "If you process personal data (you do), you need these. GDPR/CCPA auditors check all of them.",
    tip: "The Data Flow Map auto-populates most of your RoPA — edit and export it directly.",
    color: "border-teal-200 bg-teal-50/40",
    iconBg: "bg-teal-100 text-teal-700",
    links: [
      { href: "/data-flows",       label: "Data Flow Map",              icon: Workflow,   description: "Visual map of data → tool → region → regulation" },
      { href: "/ropa",             label: "Data Processing (RoPA)",     icon: Archive,    description: "Record of Processing Activities for GDPR Art. 30" },
      { href: "/soa",              label: "Statement of Applicability", icon: BookCheck,  description: "Which controls apply and why" },
      { href: "/data-breaches",    label: "Breach Register",            icon: ShieldX,    description: "Log and manage personal data breaches" },
      { href: "/subject-requests", label: "Subject Requests",           icon: UserSearch, description: "Track DSARs, erasure, and portability requests" },
    ],
  },
  {
    number: 6,
    title: "Prepare for audit",
    subtitle: "When the auditor arrives, you need everything in one place, fast. These tools get you there.",
    tip: "Run the AI Audit Package at least 2 weeks before your audit date — it flags what's still missing.",
    color: "border-emerald-200 bg-emerald-50/40",
    iconBg: "bg-emerald-100 text-emerald-700",
    links: [
      { href: "/audit-package",      label: "Audit Package",     icon: Sparkles,       description: "AI-generated audit evidence bundle with narrative" },
      { href: "/reports",            label: "Reports",           icon: FileText,       description: "Export compliance reports by framework" },
      { href: "/management-reviews", label: "Management Reviews", icon: ClipboardCheck, description: "Document leadership sign-off for auditors" },
      { href: "/questionnaire",      label: "Questionnaire",     icon: ClipboardList,  description: "Pre-filled security questionnaire answers" },
      { href: "/audit-log",          label: "Audit Log",         icon: Database,       description: "Full activity trail — who did what and when" },
    ],
  },
];

// ── Quick reference table ──────────────────────────────────────────────────

const QUICK_LINKS = [
  { href: "/integrations",     label: "Integrations",    icon: Plug         },
  { href: "/compliance",       label: "Controls",         icon: ShieldCheck  },
  { href: "/evidence",         label: "Evidence",         icon: Database     },
  { href: "/risks",            label: "Risk Register",    icon: AlertTriangle},
  { href: "/policies",         label: "Policies",         icon: BookOpen     },
  { href: "/vendors",          label: "Vendors",          icon: Building2    },
  { href: "/data-flows",       label: "Data Flows",       icon: Workflow     },
  { href: "/ropa",             label: "RoPA",             icon: Archive      },
  { href: "/training",         label: "Training",         icon: GraduationCap},
  { href: "/audit-package",    label: "Audit Package",    icon: Sparkles     },
  { href: "/reports",          label: "Reports",          icon: FileText     },
  { href: "/business-continuity", label: "BCP",          icon: RefreshCw    },
];

// ── Components ─────────────────────────────────────────────────────────────

function StepCard({ step }: { step: Step }) {
  return (
    <div className={`rounded-2xl border p-6 ${step.color}`}>
      <div className="flex items-start gap-4 mb-5">
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 font-bold text-sm ${step.iconBg}`}>
          {step.number}
        </div>
        <div>
          <h2 className="text-base font-bold text-gray-900">{step.title}</h2>
          <p className="text-sm text-gray-500 mt-0.5">{step.subtitle}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
        {step.links.map(({ href, label, icon: Icon, description }) => (
          <Link
            key={href}
            href={href}
            className="flex items-start gap-3 bg-white/80 hover:bg-white rounded-xl px-3.5 py-3 border border-white/60 hover:border-gray-200 transition-all group shadow-sm hover:shadow"
          >
            <div className="w-7 h-7 rounded-lg bg-gray-100 group-hover:bg-brand-50 flex items-center justify-center shrink-0 mt-0.5 transition-colors">
              <Icon className="w-3.5 h-3.5 text-gray-500 group-hover:text-brand-600 transition-colors" />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 transition-colors leading-tight">{label}</p>
              <p className="text-xs text-gray-400 mt-0.5 leading-snug">{description}</p>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-gray-300 group-hover:text-brand-500 shrink-0 mt-1 ml-auto transition-colors" />
          </Link>
        ))}
      </div>

      <div className="flex items-start gap-2 bg-white/60 rounded-xl px-3.5 py-2.5">
        <CheckCircle2 className="w-3.5 h-3.5 text-brand-500 mt-0.5 shrink-0" />
        <p className="text-xs text-gray-600"><span className="font-semibold text-gray-700">Pro tip: </span>{step.tip}</p>
      </div>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────

export default function GuidePage() {
  return (
    <div className="max-w-4xl">
      {/* Header */}
      <div className="flex items-center gap-3 mb-8">
        <div className="w-9 h-9 rounded-xl bg-brand-100 flex items-center justify-center shrink-0">
          <Compass className="w-5 h-5 text-brand-600" />
        </div>
        <div className="min-w-0">
          <h1 className="text-lg sm:text-xl font-bold text-gray-900 leading-tight">How to use TraceLayer</h1>
          <p className="text-xs sm:text-sm text-gray-500 mt-0.5 hidden sm:block">
            A recommended workflow from first integration to audit-ready. Follow the steps in order.
          </p>
        </div>
      </div>

      {/* Steps with connectors */}
      <div className="mb-10">
        {STEPS.map((step, i) => (
          <div key={step.number}>
            <StepCard step={step} />
            {i < STEPS.length - 1 && (
              <div className="flex justify-center py-2">
                <div className="flex flex-col items-center gap-0.5">
                  <div className="w-px h-3 bg-gray-300" />
                  <ChevronDown className="w-4 h-4 text-gray-400" />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Quick reference */}
      <div className="bg-white rounded-2xl border border-gray-100 p-6">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Quick reference</h2>
        <p className="text-xs text-gray-400 mb-4">Jump directly to any section of the app.</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {QUICK_LINKS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-2 px-3 py-2.5 rounded-xl border border-gray-100 hover:border-brand-200 hover:bg-brand-50/40 transition-all group"
            >
              <Icon className="w-3.5 h-3.5 text-gray-400 group-hover:text-brand-600 shrink-0 transition-colors" />
              <span className="text-xs font-medium text-gray-600 group-hover:text-brand-700 transition-colors">{label}</span>
            </Link>
          ))}
        </div>
      </div>

      {/* Footer note */}
      <p className="text-center text-xs text-gray-400 mt-6">
        Need help? Email us at{" "}
        <a href="mailto:support@tracelayer.it.com" className="text-brand-600 hover:text-brand-700 underline underline-offset-2">
          support@tracelayer.it.com
        </a>
      </p>
    </div>
  );
}
