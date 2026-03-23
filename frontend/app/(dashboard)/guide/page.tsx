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
  MessageCircle,
  Bot,
  Monitor,
  Users,
  Bell,
  Layers,
  Flag,
  Rocket,
  CheckCircle2,
  Clock,
  Zap,
} from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

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

// ── Phase definitions ──────────────────────────────────────────────────────

const PHASES: Phase[] = [
  {
    number: 1,
    label: "Foundation",
    title: "Connect your stack",
    subtitle: "Wire up the tools your team already uses. TraceLayer pulls evidence continuously — no manual uploads, no spreadsheets.",
    timeline: "Day 1–2",
    accent: "border-blue-300",
    markerBg: "bg-blue-600",
    markerText: "text-white",
    cardBg: "bg-blue-50/50 border-blue-100",
    milestone: "First evidence auto-collected",
    features: [
      { href: "/integrations", label: "Integrations", icon: Plug, description: "Connect 50+ tools — GitHub, AWS, Okta, Google Workspace, Slack, and more" },
      { href: "/data-flows",   label: "Data Flow Map", icon: Workflow, description: "Visual map of where your data goes, which tools process it, and which regulations apply" },
      { href: "/devices",      label: "Devices",      icon: Monitor,  description: "Enroll and track employee devices for MDM and endpoint compliance", badge: "New" },
    ],
  },
  {
    number: 2,
    label: "Posture",
    title: "Review your compliance posture",
    subtitle: "Check which controls are passing, failing, or missing evidence. Your score updates in real time as evidence flows in.",
    timeline: "Day 2–3",
    accent: "border-brand-300",
    markerBg: "bg-brand-600",
    markerText: "text-white",
    cardBg: "bg-brand-50/50 border-brand-100",
    milestone: "Readiness score above 60%",
    features: [
      { href: "/dashboard",   label: "Dashboard",   icon: Target,      description: "Overall readiness score and top gaps at a glance" },
      { href: "/compliance",  label: "Controls",    icon: ShieldCheck, description: "All controls mapped to SOC 2, ISO 27001, HIPAA, GDPR, and more" },
      { href: "/evidence",    label: "Evidence",    icon: Database,    description: "Browse and search every auto-collected evidence record" },
      { href: "/readiness",   label: "Readiness",   icon: Layers,      description: "Framework-by-framework gap analysis with remediation steps" },
    ],
  },
  {
    number: 3,
    label: "Gaps",
    title: "Close the gaps",
    subtitle: "Everything not covered by integrations gets handled here — risks, incidents, policies, vendors, and assets.",
    timeline: "Week 1–2",
    accent: "border-amber-300",
    markerBg: "bg-amber-500",
    markerText: "text-white",
    cardBg: "bg-amber-50/50 border-amber-100",
    milestone: "Risk register complete, policies published",
    features: [
      { href: "/policies",        label: "Policies",        icon: BookOpen,      description: "Create, version, and publish your security policy library" },
      { href: "/risks",           label: "Risk Register",   icon: AlertTriangle, description: "Log risks with severity, likelihood, owner, and mitigations" },
      { href: "/vendors",         label: "Vendor Risk",     icon: Building2,     description: "Assess and continuously monitor third-party vendors" },
      { href: "/assets",          label: "Asset Inventory", icon: Server,        description: "Maintain your infrastructure and software asset register" },
      { href: "/incidents",       label: "Incidents",       icon: Siren,         description: "Record and respond to security incidents" },
      { href: "/vulnerabilities", label: "Vulnerabilities", icon: Bug,           description: "Track CVEs and remediation status from your scanners" },
      { href: "/pen-tests",       label: "Pen Tests",       icon: ShieldAlert,   description: "Upload pen test reports and track findings by severity" },
      { href: "/access-reviews",  label: "Access Reviews",  icon: UserCheck,     description: "Run periodic user access reviews against each system" },
    ],
  },
  {
    number: 4,
    label: "People",
    title: "Get your team compliant",
    subtitle: "Compliance is a team sport. Training must be done, policies must be signed, and leavers must be tracked.",
    timeline: "Week 2",
    accent: "border-purple-300",
    markerBg: "bg-purple-600",
    markerText: "text-white",
    cardBg: "bg-purple-50/50 border-purple-100",
    milestone: "All employees trained and policies signed",
    features: [
      { href: "/portal",            label: "Employee Portal",   icon: Users,         description: "Self-service hub where employees sign policies, attest devices, and complete tasks", badge: "New" },
      { href: "/training",          label: "Training",          icon: GraduationCap, description: "Track security awareness training completion across your team" },
      { href: "/background-checks", label: "Background Checks", icon: BadgeCheck,    description: "Log pre-employment screening and verification records" },
      { href: "/offboarding",       label: "Offboarding",       icon: UserMinus,     description: "Ensure access is fully revoked when staff leave" },
      { href: "/team",              label: "Team",              icon: UserCheck,     description: "Manage users, roles, and permissions in TraceLayer" },
    ],
  },
  {
    number: 5,
    label: "Privacy",
    title: "Handle privacy obligations",
    subtitle: "If you process personal data you need these. GDPR and CCPA auditors check every one of them.",
    timeline: "Week 2–3",
    accent: "border-teal-300",
    markerBg: "bg-teal-600",
    markerText: "text-white",
    cardBg: "bg-teal-50/50 border-teal-100",
    milestone: "RoPA complete, DSARs tracked",
    features: [
      { href: "/ropa",             label: "Data Processing (RoPA)", icon: Archive,    description: "Record of Processing Activities for GDPR Art. 30 compliance" },
      { href: "/soa",              label: "Statement of Applicability", icon: BookCheck, description: "Document which controls apply to your organisation and why" },
      { href: "/data-breaches",    label: "Breach Register",        icon: ShieldX,    description: "Log and manage personal data breaches with 72-hour reporting" },
      { href: "/subject-requests", label: "Subject Requests",       icon: UserSearch, description: "Track DSARs, right-to-erasure, and data portability requests" },
      { href: "/business-continuity", label: "Business Continuity", icon: RefreshCw,  description: "BCP documentation, RTO/RPO targets, and disaster recovery plans" },
    ],
  },
  {
    number: 6,
    label: "Collaboration",
    title: "Collaborate in real time",
    subtitle: "Connect your auditor directly and keep your team in sync with automated Slack reminders.",
    timeline: "Ongoing",
    accent: "border-indigo-300",
    markerBg: "bg-indigo-600",
    markerText: "text-white",
    cardBg: "bg-indigo-50/50 border-indigo-100",
    milestone: "Auditor has live access, team receiving alerts",
    features: [
      { href: "/compliance",    label: "Auditor Access + Chat", icon: MessageCircle, description: "Invite your auditor for read-only access and exchange comments directly on evidence", badge: "New" },
      { href: "/questionnaire", label: "Questionnaire",         icon: ClipboardList, description: "Pre-fill security questionnaire answers and collaborate with comments" },
      { href: "/ai-agents",     label: "AI Agents",             icon: Bot,           description: "Autonomous agents that monitor your posture and flag issues 24/7", badge: "New" },
      { href: "/settings",      label: "Slack Bot",             icon: Bell,          description: "Send automated compliance reminders to your team via Slack webhook", badge: "New" },
    ],
  },
  {
    number: 7,
    label: "Audit",
    title: "Get audit-ready",
    subtitle: "When the auditor arrives, everything needs to be in one place fast. These tools get you across the line.",
    timeline: "2 weeks before audit",
    accent: "border-emerald-300",
    markerBg: "bg-emerald-600",
    markerText: "text-white",
    cardBg: "bg-emerald-50/50 border-emerald-100",
    milestone: "Audit package generated, auditor signed off",
    features: [
      { href: "/audit-package",      label: "AI Audit Package",    icon: Sparkles,       description: "One-click AI-generated PDF with narrative, evidence index, and gap analysis" },
      { href: "/reports",            label: "Reports",             icon: FileText,       description: "Export compliance reports by framework for any stakeholder" },
      { href: "/management-reviews", label: "Management Reviews",  icon: ClipboardCheck, description: "Document leadership sign-off and periodic security review records" },
      { href: "/audit-log",          label: "Audit Log",           icon: Database,       description: "Immutable activity trail — every action by every user, timestamped" },
    ],
  },
];

// ── Page ───────────────────────────────────────────────────────────────────

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
          Follow these 7 phases in order. Most teams are audit-ready in 2–3 weeks. Each phase builds on the last.
        </p>
      </div>

      {/* Progress bar */}
      <div className="bg-white rounded-2xl border border-gray-100 p-4 mb-10 flex items-center gap-5 shadow-sm">
        <div className="flex items-center gap-1.5 shrink-0">
          <Rocket className="w-4 h-4 text-brand-600" />
          <span className="text-xs font-semibold text-gray-700">7-phase roadmap</span>
        </div>
        <div className="flex-1 flex items-center gap-1">
          {PHASES.map((p, i) => (
            <div key={p.number} className="flex items-center gap-1 flex-1">
              <div className={`h-1.5 rounded-full flex-1 ${i < 2 ? "bg-brand-500" : "bg-gray-100"}`} />
            </div>
          ))}
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-400 shrink-0">
          <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> 2–3 weeks</span>
          <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> Audit-ready</span>
        </div>
      </div>

      {/* Roadmap */}
      <div className="relative">
        {/* Vertical spine */}
        <div className="absolute left-[19px] top-5 bottom-5 w-px bg-gradient-to-b from-blue-300 via-purple-300 to-emerald-300 opacity-40" />

        <div className="space-y-0">
          {PHASES.map((phase, i) => (
            <div key={phase.number} className="relative flex gap-6 pb-8">
              {/* Phase marker */}
              <div className="relative z-10 shrink-0">
                <div className={`w-10 h-10 rounded-full ${phase.markerBg} flex items-center justify-center shadow-md`}>
                  <span className={`text-xs font-extrabold ${phase.markerText}`}>{phase.number}</span>
                </div>
              </div>

              {/* Phase card */}
              <div className="flex-1 min-w-0">
                {/* Phase header */}
                <div className="flex items-center gap-2.5 mb-3 mt-2">
                  <span className={`text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full ${phase.markerBg} ${phase.markerText} opacity-90`}>
                    {phase.label}
                  </span>
                  <span className="text-[10px] text-gray-400 font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3" />{phase.timeline}
                  </span>
                </div>

                <div className={`rounded-2xl border p-5 ${phase.cardBg}`}>
                  <h2 className="text-base font-bold text-gray-900 mb-1">{phase.title}</h2>
                  <p className="text-sm text-gray-500 mb-5 leading-relaxed">{phase.subtitle}</p>

                  {/* Feature grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-4">
                    {phase.features.map(({ href, label, icon: Icon, description, badge }) => (
                      <Link
                        key={href}
                        href={href}
                        className="group flex items-start gap-3 bg-white hover:bg-white rounded-xl px-3.5 py-3 border border-white/80 hover:border-gray-200 shadow-sm hover:shadow transition-all"
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

      {/* Done state */}
      <div className="bg-gradient-to-br from-emerald-600 to-teal-600 rounded-2xl p-6 text-center shadow-lg shadow-emerald-500/20 mb-10">
        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center mx-auto mb-3">
          <CheckCircle2 className="w-5 h-5 text-white" />
        </div>
        <p className="text-white font-bold text-base mb-1">You're audit-ready</p>
        <p className="text-white/70 text-xs leading-relaxed max-w-sm mx-auto">
          All 7 phases complete. Generate your AI Audit Package and share your auditor access link. Your evidence is continuously updated.
        </p>
        <div className="flex items-center justify-center gap-3 mt-4">
          <Link href="/audit-package" className="inline-flex items-center gap-1.5 bg-white hover:bg-white/90 text-emerald-700 font-semibold px-4 py-2 rounded-xl text-xs transition-colors">
            <Sparkles className="w-3.5 h-3.5" /> Generate audit package
          </Link>
          <Link href="/compliance" className="inline-flex items-center gap-1.5 bg-white/10 hover:bg-white/20 text-white font-semibold px-4 py-2 rounded-xl text-xs transition-colors">
            <MessageCircle className="w-3.5 h-3.5" /> Invite auditor
          </Link>
        </div>
      </div>

      {/* Footer */}
      <p className="text-center text-xs text-gray-400">
        Questions? Email{" "}
        <a href="mailto:support@tracelayer.it.com" className="text-brand-600 hover:underline">
          support@tracelayer.it.com
        </a>
      </p>
    </div>
  );
}
