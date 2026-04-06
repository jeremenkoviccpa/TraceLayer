"use client";

import Link from "next/link";
import {
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
  Target,
  Bot,
  Monitor,
  Flag,
  Rocket,
  CheckCircle2,
  Clock,
  Zap,
} from "lucide-react";

type FeatureLink = {
  href: string;
  label: string;
  icon: React.ElementType;
  description: string;
  badge?: string;
};

type Phase = {
  number: number;
  label: string;
  title: string;
  subtitle: string;
  timeline: string;
  accent: string;
  markerBg: string;
  markerText: string;
  cardBg: string;
  features: FeatureLink[];
  milestone: string;
};

const PHASES: Phase[] = [
  {
    number: 1,
    label: "Scope & Setup",
    title: "Connect your stack and define scope",
    subtitle: "Wire up the tools your team already uses and document what you're protecting. TraceLayer pulls evidence automatically from day one.",
    timeline: "Day 1",
    accent: "border-blue-300",
    markerBg: "bg-blue-600",
    markerText: "text-white",
    cardBg: "bg-blue-50/50 border-blue-100",
    milestone: "First integration connected, scope documented",
    features: [
      {
        href: "/integrations",
        label: "Integrations",
        icon: Plug,
        description: "Connect 100+ tools — GitHub, AWS, Okta, Google Workspace, Slack, OpenAI, Anthropic, and more. Evidence flows in automatically.",
      },
      {
        href: "/soa",
        label: "Applicability",
        icon: BookCheck,
        description: "Document which controls apply to your organisation and why. Required for ISO 27001 and SOC 2.",
      },
    ],
  },
  {
    number: 2,
    label: "Policies",
    title: "Write and publish your security policies",
    subtitle: "Auditors need written policies before they look at anything else. Use AI to generate compliant drafts tailored to your tech stack.",
    timeline: "Day 1–2",
    accent: "border-violet-300",
    markerBg: "bg-violet-600",
    markerText: "text-white",
    cardBg: "bg-violet-50/50 border-violet-100",
    milestone: "Core policies drafted and published",
    features: [
      {
        href: "/policies",
        label: "Policy Library",
        icon: BookOpen,
        description: "Pre-built templates for InfoSec, Acceptable Use, Incident Response, and more. AI generates full drafts in seconds.",
      },
    ],
  },
  {
    number: 3,
    label: "Controls & Evidence",
    title: "Monitor controls and collect evidence",
    subtitle: "Your compliance score updates in real time as evidence flows in from your integrations. See exactly what's passing, failing, or missing.",
    timeline: "Day 2–3",
    accent: "border-brand-300",
    markerBg: "bg-brand-600",
    markerText: "text-white",
    cardBg: "bg-brand-50/50 border-brand-100",
    milestone: "Readiness score above 60%, all controls mapped",
    features: [
      {
        href: "/compliance",
        label: "Controls",
        icon: ShieldCheck,
        description: "250+ controls mapped to 12 frameworks — SOC 2, ISO 27001, ISO 42001, HIPAA, GDPR, NIS2, LPDP, and more. Pass/fail at a glance.",
      },
      {
        href: "/evidence",
        label: "Evidence",
        icon: Database,
        description: "Browse, search, and download every auto-collected evidence record. Organised by control and framework.",
      },
      {
        href: "/readiness",
        label: "Readiness",
        icon: Target,
        description: "Framework-by-framework gap analysis with a prioritised remediation list and estimated weeks to audit-ready.",
      },
    ],
  },
  {
    number: 4,
    label: "Risk & Security",
    title: "Manage risks and security operations",
    subtitle: "Identify, score, and remediate your biggest risks. Document incidents, track vulnerabilities, and log pen test findings.",
    timeline: "Week 1",
    accent: "border-red-300",
    markerBg: "bg-red-600",
    markerText: "text-white",
    cardBg: "bg-red-50/50 border-red-100",
    milestone: "Risk register complete, no critical open incidents",
    features: [
      {
        href: "/risks",
        label: "Risk Register",
        icon: AlertTriangle,
        description: "Log risks with severity, likelihood, owner, and mitigations. Auditors expect a formal, reviewed risk register.",
      },
      {
        href: "/incidents",
        label: "Incidents",
        icon: Siren,
        description: "Record and manage security incidents with triage → investigate → remediate → close workflow.",
      },
      {
        href: "/vulnerabilities",
        label: "Vulnerabilities",
        icon: Bug,
        description: "Track CVEs and remediation status. Import from Qualys, Nessus, or any scanner. SLA tracking built in.",
      },
      {
        href: "/pen-tests",
        label: "Pen Tests",
        icon: ShieldAlert,
        description: "Upload pen test reports and track finding remediation. Re-test verification included.",
      },
      {
        href: "/change-management",
        label: "Change Management",
        icon: RefreshCw,
        description: "RFC lifecycle from draft → approval → deployment. Required for SOC 2 CC8.1 and ISO 27001 A.8.32.",
        badge: "New",
      },
    ],
  },
  {
    number: 5,
    label: "Operations",
    title: "Secure your assets and operations",
    subtitle: "Auditors check that you know what you have, who has access, and that third parties meet your standards.",
    timeline: "Week 1–2",
    accent: "border-amber-300",
    markerBg: "bg-amber-500",
    markerText: "text-white",
    cardBg: "bg-amber-50/50 border-amber-100",
    milestone: "Asset register complete, access reviews run, vendors assessed",
    features: [
      {
        href: "/assets",
        label: "Asset Inventory",
        icon: Server,
        description: "Maintain your infrastructure and software asset register. Auto-discover assets from integrations.",
      },
      {
        href: "/devices",
        label: "Device Monitoring",
        icon: Monitor,
        description: "Track endpoint compliance — encryption, patches, antivirus, and MDM enrolment status.",
        badge: "New",
      },
      {
        href: "/access-reviews",
        label: "Access Reviews",
        icon: UserCheck,
        description: "Run periodic user access reviews with an approve/revoke workflow. Orphaned accounts flagged automatically.",
      },
      {
        href: "/vendors",
        label: "Vendor Risk",
        icon: Building2,
        description: "Assess and continuously monitor third-party vendors. Track contracts, SLAs, and subprocessors.",
      },
      {
        href: "/business-continuity",
        label: "Business Continuity",
        icon: RefreshCw,
        description: "BCP documentation, RTO/RPO targets, DR plans, and recovery testing records.",
      },
    ],
  },
  {
    number: 6,
    label: "People",
    title: "Get your team compliant",
    subtitle: "Training must be completed, background checks logged, and leavers fully offboarded. These are non-negotiable for SOC 2 and ISO 27001.",
    timeline: "Week 2",
    accent: "border-purple-300",
    markerBg: "bg-purple-600",
    markerText: "text-white",
    cardBg: "bg-purple-50/50 border-purple-100",
    milestone: "All employees trained, background checks complete",
    features: [
      {
        href: "/training",
        label: "Training",
        icon: GraduationCap,
        description: "Track security awareness training completion across your team. Auto-reminders keep completion rates high.",
      },
      {
        href: "/background-checks",
        label: "Background Checks",
        icon: BadgeCheck,
        description: "Log pre-employment screening and periodic re-verification records securely.",
      },
      {
        href: "/offboarding",
        label: "Offboarding",
        icon: UserMinus,
        description: "Automated offboarding checklists — access revocation, equipment return, and exit documentation.",
      },
    ],
  },
  {
    number: 7,
    label: "Privacy",
    title: "Handle privacy obligations",
    subtitle: "Required if you process personal data. GDPR and CCPA auditors check every one of these items.",
    timeline: "Week 2–3",
    accent: "border-teal-300",
    markerBg: "bg-teal-600",
    markerText: "text-white",
    cardBg: "bg-teal-50/50 border-teal-100",
    milestone: "RoPA complete, DSARs tracked, breach register live",
    features: [
      {
        href: "/data-flows",
        label: "Data Flow Map",
        icon: Workflow,
        description: "Visual map of where data goes — source → processing → storage → third parties. Export for auditors.",
      },
      {
        href: "/ropa",
        label: "RoPA",
        icon: Archive,
        description: "Record of Processing Activities for GDPR Art. 30. Auto-populate from your integrations.",
      },
      {
        href: "/data-breaches",
        label: "Breach Register",
        icon: ShieldX,
        description: "Log personal data breaches and manage the 72-hour regulatory notification workflow.",
      },
      {
        href: "/subject-requests",
        label: "Subject Requests",
        icon: UserSearch,
        description: "Track DSARs, right-to-erasure, and portability requests. 30-day SLA tracking built in.",
      },
    ],
  },
  {
    number: 8,
    label: "AI Governance",
    title: "Govern your AI systems — ISO 42001",
    subtitle: "If your organisation develops or uses AI, ISO/IEC 42001:2023 is the global standard for AI Management Systems. Connect OpenAI, Anthropic, or Gemini to collect evidence automatically across all 15 control areas.",
    timeline: "Week 3",
    accent: "border-violet-300",
    markerBg: "bg-violet-600",
    markerText: "text-white",
    cardBg: "bg-violet-50/50 border-violet-100",
    milestone: "ISO 42001 framework selected, AI providers connected, impact assessments documented",
    features: [
      {
        href: "/compliance",
        label: "ISO 42001 Framework",
        icon: ShieldCheck,
        description: "15 controls covering AI governance (Cl. 4–5), risk assessment, human oversight, bias detection, transparency, and AI supply chain (A.10.1).",
        badge: "New",
      },
      {
        href: "/integrations",
        label: "AI Provider Integrations",
        icon: Plug,
        description: "Connect OpenAI, Anthropic, and Google Gemini. Model inventory, API key audit, and workspace config count as A.10.1 supply chain evidence.",
        badge: "New",
      },
      {
        href: "/custom-frameworks",
        label: "Custom Frameworks",
        icon: Database,
        description: "Build internal control frameworks with your own controls and evidence types. Scores in the dashboard alongside built-in frameworks.",
        badge: "New",
      },
      {
        href: "/questionnaire",
        label: "AI Questionnaire",
        icon: ClipboardList,
        description: "Answer vendor security questionnaires with AI assistance. Pre-fills from your live compliance data automatically.",
      },
      {
        href: "/audit-package",
        label: "AI Audit Package",
        icon: Sparkles,
        description: "One-click AI-generated PDF with executive narrative, evidence index, and gap analysis — ready for your auditor.",
        badge: "AI",
      },
      {
        href: "/ai-agents",
        label: "Agent Monitor",
        icon: Bot,
        description: "Autonomous agents monitor your compliance posture 24/7 and flag issues before auditors find them.",
      },
    ],
  },
];

export default function GuidePage() {
  return (
    <div className="max-w-4xl pb-16">

      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] font-bold uppercase tracking-widest text-brand-600 bg-brand-50 px-2.5 py-1 rounded-full">Getting started</span>
        </div>
        <h1 className="text-2xl font-extrabold text-gray-900 mb-2">Your path to audit-ready</h1>
        <p className="text-sm text-gray-500 max-w-xl leading-relaxed">
          Follow these 8 steps in order — they match the navigation on the left. Most teams are audit-ready in 2–3 weeks. Supports 12 frameworks including SOC 2, ISO 27001, ISO 42001, HIPAA, GDPR, and NIS2.
        </p>
      </div>

      {/* Progress bar */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-10 shadow-sm">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex items-center gap-1.5">
            <Rocket className="w-4 h-4 text-brand-600" />
            <span className="text-xs font-semibold text-gray-700">8-step roadmap</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-gray-400 ml-auto">
            <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> 2–3 weeks</span>
            <span className="hidden sm:flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> Audit-ready</span>
          </div>
        </div>
        <div className="flex items-center gap-1">
          {PHASES.map((p, i) => (
            <div key={p.number} className="flex items-center gap-1 flex-1">
              <div className={`h-1.5 rounded-full flex-1 ${i < 3 ? "bg-brand-500" : "bg-gray-100"}`} />
            </div>
          ))}
        </div>
      </div>

      {/* Roadmap */}
      <div className="relative">
        {/* Vertical spine */}
        <div className="absolute left-[19px] top-5 bottom-5 w-px bg-gradient-to-b from-blue-300 via-purple-300 to-emerald-300 opacity-40" />

        <div className="space-y-0">
          {PHASES.map((phase) => (
            <div key={phase.number} className="relative flex gap-3 sm:gap-6 pb-8">
              {/* Phase marker */}
              <div className="relative z-10 shrink-0">
                <div className={`w-10 h-10 rounded-full ${phase.markerBg} flex items-center justify-center shadow-md`}>
                  <span className={`text-xs font-extrabold ${phase.markerText}`}>{phase.number}</span>
                </div>
              </div>

              {/* Phase card */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2.5 mb-3 mt-2">
                  <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${phase.markerBg} ${phase.markerText} opacity-90`}>
                    {phase.label}
                  </span>
                  <span className="text-[10px] text-gray-400 font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" />{phase.timeline}
                  </span>
                </div>

                <div className={`rounded-2xl border p-4 sm:p-5 ${phase.cardBg}`}>
                  <h2 className="text-base font-bold text-gray-900 mb-1">{phase.title}</h2>
                  <p className="text-sm text-gray-500 mb-5 leading-relaxed">{phase.subtitle}</p>

                  {/* Feature grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
                    {phase.features.map(({ href, label, icon: Icon, description, badge }) => (
                      <Link
                        key={href}
                        href={href}
                        className="group flex items-start gap-2.5 bg-white hover:bg-white rounded-xl px-3 sm:px-3.5 py-3 border border-white/80 hover:border-gray-200 shadow-sm hover:shadow transition-all"
                      >
                        <div className="w-7 h-7 rounded-lg bg-gray-50 group-hover:bg-brand-50 border border-gray-100 flex items-center justify-center shrink-0 mt-0.5 transition-colors">
                          <Icon className="w-3.5 h-3.5 text-gray-400 group-hover:text-brand-600 transition-colors" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 transition-colors leading-tight">{label}</p>
                            {badge && (
                              <span className="text-[9px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded-full bg-brand-100 text-brand-700">{badge}</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-400 mt-0.5 leading-snug">{description}</p>
                        </div>
                        <ArrowRight className="w-3.5 h-3.5 text-gray-200 group-hover:text-brand-400 shrink-0 mt-1 ml-auto transition-colors" />
                      </Link>
                    ))}
                  </div>

                  {/* Milestone */}
                  <div className="flex items-center gap-2 bg-white/70 rounded-xl px-3.5 py-2.5">
                    <Flag className="w-3.5 h-3.5 text-brand-500 shrink-0" />
                    <p className="text-xs text-gray-600">
                      <span className="font-semibold text-gray-700">Milestone: </span>
                      {phase.milestone}
                    </p>
                    <CheckCircle2 className="w-3.5 h-3.5 text-gray-200 ml-auto shrink-0" />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit & Reports final step */}
      <div className="relative flex gap-3 sm:gap-6 pb-8">
        <div className="relative z-10 shrink-0">
          <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center shadow-md">
            <CheckCircle2 className="w-5 h-5 text-white" />
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2.5 mb-3 mt-2">
            <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full bg-emerald-600 text-white opacity-90">
              Audit & Reports
            </span>
            <span className="text-[10px] text-gray-400 font-medium flex items-center gap-1">
              <Clock className="w-3 h-3" />2 weeks before audit
            </span>
          </div>
          <div className="rounded-2xl border p-4 sm:p-5 bg-emerald-50/50 border-emerald-100">
            <h2 className="text-base font-bold text-gray-900 mb-1">Generate your audit package</h2>
            <p className="text-sm text-gray-500 mb-5 leading-relaxed">
              When the auditor arrives, generate everything in one click and share secure read-only access. Reports are always up to date.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
              {[
                { href: "/reports",            label: "Reports",          icon: FileText,       description: "Export compliance reports by framework — PDF or shareable link." },
                { href: "/management-reviews", label: "Management Reviews", icon: ClipboardCheck, description: "Document leadership sign-off and periodic security review records." },
                { href: "/portal",             label: "Auditor Portal",   icon: UserCheck,      description: "Secure read-only portal for your external auditor with time-limited access." },
              ].map(({ href, label, icon: Icon, description }) => (
                <Link key={href} href={href}
                  className="group flex items-start gap-2.5 bg-white hover:bg-white rounded-xl px-3 sm:px-3.5 py-3 border border-white/80 hover:border-gray-200 shadow-sm hover:shadow transition-all"
                >
                  <div className="w-7 h-7 rounded-lg bg-gray-50 group-hover:bg-brand-50 border border-gray-100 flex items-center justify-center shrink-0 mt-0.5 transition-colors">
                    <Icon className="w-3.5 h-3.5 text-gray-400 group-hover:text-brand-600 transition-colors" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 group-hover:text-brand-700 transition-colors leading-tight">{label}</p>
                    <p className="text-xs text-gray-400 mt-0.5 leading-snug">{description}</p>
                  </div>
                  <ArrowRight className="w-3.5 h-3.5 text-gray-200 group-hover:text-brand-400 shrink-0 mt-1 ml-auto transition-colors" />
                </Link>
              ))}
            </div>
            <div className="flex items-center gap-2 bg-white/70 rounded-xl px-3.5 py-2.5">
              <Flag className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
              <p className="text-xs text-gray-600">
                <span className="font-semibold text-gray-700">Milestone: </span>
                Audit package generated, auditor signed off
              </p>
              <CheckCircle2 className="w-3.5 h-3.5 text-gray-200 ml-auto shrink-0" />
            </div>
          </div>
        </div>
      </div>

      {/* Done card */}
      <div className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-6 text-center shadow-lg shadow-emerald-500/20 mb-10">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-3">
          <CheckCircle2 className="w-5 h-5 text-white" />
        </div>
        <p className="text-white font-bold text-base mb-1">You're audit-ready</p>
        <p className="text-white/70 text-xs leading-relaxed max-w-sm mx-auto">
          All 8 steps complete. Generate your AI Audit Package and share your auditor access link. Your evidence updates continuously.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-2 sm:gap-3 mt-4">
          <Link href="/audit-package"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-white hover:bg-white/90 text-emerald-700 font-semibold px-4 py-2 rounded-xl text-xs transition-colors">
            <Sparkles className="w-3.5 h-3.5" /> Generate audit package
          </Link>
          <Link href="/portal"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 bg-white/10 hover:bg-white/20 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-colors">
            <UserCheck className="w-3.5 h-3.5" /> Open auditor portal
          </Link>
        </div>
      </div>

      <p className="text-center text-xs text-gray-400">
        Questions? Email{" "}
        <a href="mailto:support@tracelayer.it.com" className="text-brand-600 hover:underline">
          support@tracelayer.it.com
        </a>
      </p>
    </div>
  );
}
