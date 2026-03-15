"use client";

import { useEffect, useRef, useState } from "react";
import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useAuth } from "@/components/auth-provider";
import {
  ShieldCheck, Plug, FileText, Zap, ArrowRight, CheckCircle2,
  BarChart3, Lock, Star, Clock, TrendingUp, Users, ChevronDown,
  Menu, X, AlertTriangle, BookOpen, GraduationCap, Target,
  Globe, ClipboardList, Building2, UserCheck, Shield,
} from "lucide-react";

// ── Integration logos ────────────────────────────────────────────────────────

function AwsLogo() {
  return (
    <svg width="48" height="30" viewBox="0 0 48 30" fill="none">
      <text x="0" y="21" fontSize="20" fontWeight="900" fill="#FF9900" fontFamily="Arial,sans-serif">aws</text>
      <path d="M2 26 Q24 32 46 26" stroke="#FF9900" strokeWidth="2" fill="none" strokeLinecap="round"/>
    </svg>
  );
}

function GithubLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="#1f2937">
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>
  );
}

function SlackLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M5.042 15.165a2.528 2.528 0 01-2.52 2.523A2.528 2.528 0 010 15.165a2.527 2.527 0 012.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 012.521-2.52 2.527 2.527 0 012.521 2.52v6.313A2.528 2.528 0 018.834 24a2.528 2.528 0 01-2.521-2.522v-6.313z" fill="#E01E5A"/>
      <path d="M8.834 5.042a2.528 2.528 0 01-2.521-2.52A2.528 2.528 0 018.834 0a2.528 2.528 0 012.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 012.521 2.521 2.528 2.528 0 01-2.521 2.521H2.522A2.528 2.528 0 010 8.834a2.528 2.528 0 012.522-2.521h6.312z" fill="#36C5F0"/>
      <path d="M18.956 8.834a2.528 2.528 0 012.522-2.521A2.528 2.528 0 0124 8.834a2.528 2.528 0 01-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 01-2.523 2.521 2.527 2.527 0 01-2.52-2.521V2.522A2.527 2.527 0 0115.165 0a2.528 2.528 0 012.523 2.522v6.312z" fill="#2EB67D"/>
      <path d="M15.165 18.956a2.528 2.528 0 012.523 2.522A2.528 2.528 0 0115.165 24a2.527 2.527 0 01-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 01-2.52-2.523 2.526 2.526 0 012.52-2.52h6.313A2.527 2.527 0 0124 15.165a2.528 2.528 0 01-2.522 2.523h-6.313z" fill="#ECB22E"/>
    </svg>
  );
}

function GoogleLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  );
}

function JiraLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <defs>
        <linearGradient id="jira-g1" x1="16.2" y1="6.11" x2="10.6" y2="0.89" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/><stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
        <linearGradient id="jira-g2" x1="7.5" y1="11.57" x2="13.9" y2="18.3" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0052CC"/><stop offset="1" stopColor="#2684FF"/>
        </linearGradient>
      </defs>
      <path d="M11.571 11.513H0a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0012.575 24V12.518a1.005 1.005 0 00-1.004-1.005z" fill="#2684FF"/>
      <path d="M6.107 6.108H17.678A5.218 5.218 0 0012.446.893h-2.13V-1.16A5.215 5.215 0 005.103 4.054v2.049h1.004z" fill="url(#jira-g1)"/>
      <path d="M17.679 6.107H6.108a5.218 5.218 0 005.232 5.215h2.13v2.057A5.215 5.215 0 0018.683 18.6V7.112a1.005 1.005 0 00-1.004-1.005z" fill="url(#jira-g2)"/>
    </svg>
  );
}

function OktaLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <circle cx="12" cy="12" r="11" fill="#007DC1"/>
      <circle cx="12" cy="12" r="4.5" fill="white"/>
    </svg>
  );
}

function AzureLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M13.05 4.24L6.56 19.03l14.96.01L13.05 4.24z" fill="#0078D4"/>
      <path d="M13.29 4.24L8.73 10.9l4.44 8.13H2.48L13.29 4.24z" fill="#0078D4" opacity=".7"/>
    </svg>
  );
}

function GitLabLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M23.955 13.587l-1.342-4.135-2.664-8.189a.455.455 0 00-.867 0L16.418 9.45H7.582L4.918 1.263a.455.455 0 00-.867 0L1.386 9.45.044 13.587a.924.924 0 00.331 1.023L12 23.054l11.625-8.443a.92.92 0 00.33-1.024" fill="#FC6D26"/>
      <path d="M12 23.054l4.418-13.605H7.582z" fill="#E24329"/>
      <path d="M12 23.054L7.582 9.449H1.386z" fill="#FC6D26"/>
      <path d="M1.386 9.45L.044 13.587a.924.924 0 00.331 1.023L12 23.054z" fill="#FCA326"/>
      <path d="M1.386 9.45h6.196L4.918 1.263a.456.456 0 00-.867 0z" fill="#E24329"/>
      <path d="M12 23.054l4.418-13.605h6.196z" fill="#FC6D26"/>
      <path d="M22.614 9.45l1.341 4.137a.924.924 0 01-.331 1.023L12 23.054z" fill="#FCA326"/>
      <path d="M22.614 9.45h-6.196l2.664-8.187a.455.455 0 01.867 0z" fill="#E24329"/>
    </svg>
  );
}

function GCPLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M12 6.5L14.5 4H9.5L12 6.5z" fill="#EA4335"/>
      <path d="M18 8.5l2.5-2.5h-5L18 8.5z" fill="#4285F4"/>
      <path d="M6 8.5l2.5-2.5h-5L6 8.5z" fill="#FBBC05"/>
      <rect x="4" y="9" width="16" height="8" rx="4" fill="#34A853"/>
      <circle cx="8" cy="13" r="1.5" fill="white"/>
      <circle cx="12" cy="13" r="1.5" fill="white"/>
      <circle cx="16" cy="13" r="1.5" fill="white"/>
    </svg>
  );
}

function LinearLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <defs>
        <linearGradient id="linear-g" x1="0" y1="0" x2="24" y2="24" gradientUnits="userSpaceOnUse">
          <stop stopColor="#5E6AD2"/><stop offset="1" stopColor="#8B8FF0"/>
        </linearGradient>
      </defs>
      <path d="M3.5 17.5L17.5 3.5M3.5 17.5l3.5 3.5M3.5 17.5l-3.5-3.5M17.5 3.5l3.5 3.5M17.5 3.5l-3.5-3.5" stroke="url(#linear-g)" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="12" cy="12" r="5" stroke="url(#linear-g)" strokeWidth="2"/>
    </svg>
  );
}

function DatadogLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#632CA6"/>
      <path d="M7 8h10M7 12h7M7 16h10" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <circle cx="17" cy="12" r="2" fill="#7241D0"/>
      <circle cx="17" cy="12" r="1" fill="white"/>
    </svg>
  );
}

function PagerDutyLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#06AC38"/>
      <rect x="10" y="5" width="4" height="10" rx="2" fill="white"/>
      <circle cx="12" cy="18" r="2" fill="white"/>
    </svg>
  );
}

function SentryLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <path d="M13.414 2.586a2 2 0 00-2.828 0L2.586 11.586a2 2 0 000 2.828l3.536 3.536h11.314l3.536-3.536a2 2 0 000-2.828L13.414 2.586z" fill="#362D59"/>
      <path d="M12 8v5M12 15v1" stroke="white" strokeWidth="2" strokeLinecap="round"/>
    </svg>
  );
}

function TeamsLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#5059C9"/>
      <circle cx="15" cy="8" r="3" fill="#7B83EB"/>
      <rect x="9" y="11" width="12" height="8" rx="2" fill="#5059C9"/>
      <circle cx="9" cy="9" r="2.5" fill="#7B83EB"/>
      <rect x="3" y="12" width="10" height="7" rx="2" fill="#7B83EB"/>
    </svg>
  );
}

function StripeLogo() {
  return (
    <svg width="36" height="18" viewBox="0 0 60 25" fill="none">
      <text x="0" y="20" fontSize="20" fontWeight="700" fill="#635BFF" fontFamily="Arial,sans-serif">stripe</text>
    </svg>
  );
}

function RipplingLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#F36C21"/>
      <path d="M7 12a5 5 0 005 5V7a5 5 0 00-5 5z" fill="white"/>
      <path d="M12 7a5 5 0 015 5 5 5 0 01-5 5" stroke="white" strokeWidth="1.5" fill="none"/>
    </svg>
  );
}

function BambooLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="6" fill="#73AC39"/>
      <path d="M9 20V8M9 8C9 5.8 10.8 4 13 4s4 1.8 4 4-1.8 4-4 4H9" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
      <path d="M9 13c0 2.2-1.8 4-4 4" stroke="white" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  );
}

function NotionLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none">
      <rect width="24" height="24" rx="4" fill="#191919"/>
      <path d="M6 5.5h8l4 4.5V19a.5.5 0 01-.5.5H6a.5.5 0 01-.5-.5V6a.5.5 0 01.5-.5z" fill="white"/>
      <path d="M14 5.5V10H18" stroke="#191919" strokeWidth="1"/>
      <path d="M9 13h6M9 16h4" stroke="#9B9B9B" strokeWidth="1.3" strokeLinecap="round"/>
    </svg>
  );
}

const INTEGRATION_LOGOS = [
  { name: "AWS",              logo: <AwsLogo />       },
  { name: "GitHub",           logo: <GithubLogo />    },
  { name: "Slack",            logo: <SlackLogo />     },
  { name: "Google Workspace", logo: <GoogleLogo />    },
  { name: "Okta",             logo: <OktaLogo />      },
  { name: "Azure AD",         logo: <AzureLogo />     },
  { name: "Jira",             logo: <JiraLogo />      },
  { name: "GitLab",           logo: <GitLabLogo />    },
  { name: "GCP",              logo: <GCPLogo />       },
  { name: "Linear",           logo: <LinearLogo />    },
  { name: "Datadog",          logo: <DatadogLogo />   },
  { name: "PagerDuty",        logo: <PagerDutyLogo /> },
  { name: "Sentry",           logo: <SentryLogo />    },
  { name: "Teams",            logo: <TeamsLogo />     },
  { name: "Stripe",           logo: <StripeLogo />    },
  { name: "Rippling",         logo: <RipplingLogo />  },
  { name: "BambooHR",         logo: <BambooLogo />    },
  { name: "Notion",           logo: <NotionLogo />    },
];

// ── Static data ───────────────────────────────────────────────────────────────

const STATS = [
  { value: "18+",  label: "Native integrations"    },
  { value: "7",    label: "Compliance frameworks"   },
  { value: "15+",  label: "Compliance modules"      },
  { value: "100%", label: "Automated evidence"      },
];

const FRAMEWORKS = [
  { name: "SOC 2",    desc: "Type I & II",       detail: "Trust Service Criteria — security, availability, confidentiality, and privacy", color: "from-teal-500 to-emerald-500" },
  { name: "ISO 27001",desc: "2022 Edition",      detail: "93 Annex A controls across 4 themes — organizational, people, physical, technological", color: "from-blue-500 to-cyan-500" },
  { name: "HIPAA",    desc: "Security Rule",     detail: "Administrative, physical, and technical safeguards for protected health information", color: "from-violet-500 to-purple-500" },
  { name: "GDPR",     desc: "EU Regulation",     detail: "Data protection by design, DPIA, consent management, DPO, and breach notification", color: "from-indigo-500 to-blue-500" },
  { name: "PCI DSS",  desc: "v4.0",              detail: "12 requirements for organizations that process, store, or transmit cardholder data", color: "from-amber-500 to-orange-500" },
  { name: "CCPA",     desc: "California Privacy", detail: "Consumer rights, data inventory, opt-out mechanisms, and service provider controls", color: "from-rose-500 to-pink-500" },
  { name: "NIST CSF", desc: "Framework 2.0",     detail: "Identify, protect, detect, respond, and recover — the cybersecurity lifecycle", color: "from-cyan-500 to-teal-500" },
];

const FEATURES = [
  {
    icon: Plug,
    title: "18+ native integrations",
    desc: "Connect AWS, GitHub, Okta, Slack, Google Workspace, Azure AD, GitLab, GCP, Datadog, PagerDuty, Stripe, and more in minutes. No agents. No code.",
  },
  {
    icon: Zap,
    title: "Automated evidence collection",
    desc: "Evidence runs every 24 hours without you lifting a finger — IAM users, audit logs, repositories, access policies, SaaS activity, and more.",
  },
  {
    icon: Target,
    title: "Readiness Timeline",
    desc: "See your exact readiness score and a week-by-week estimate to audit-ready — with stage-specific next steps to close the gap fast.",
  },
  {
    icon: AlertTriangle,
    title: "Risk Register",
    desc: "Log risks with likelihood × impact scoring. Assign owners, track treatment status, and satisfy risk assessment requirements across every framework.",
  },
  {
    icon: BookOpen,
    title: "Policy Templates",
    desc: "Pre-written policies for SOC 2, ISO 27001, HIPAA, GDPR, and more. Customize and adopt in one click — incident response, BCP, vendor risk, and more.",
  },
  {
    icon: GraduationCap,
    title: "Training Tracker",
    desc: "Assign security awareness training to employees by email. Track completion, flag overdue, and generate CC1.4 evidence automatically.",
  },
  {
    icon: Building2,
    title: "Vendor Due Diligence",
    desc: "Track all vendors with risk levels, SOC 2 / ISO / HIPAA certifications, review dates, and contact info. Satisfies CC9.2 out of the box.",
  },
  {
    icon: UserCheck,
    title: "Access Review Workflows",
    desc: "Run formal quarterly access reviews with reviewer sign-off, users reviewed count, and documented findings. Audit-ready CC6.3 evidence.",
  },
  {
    icon: Globe,
    title: "Public Trust Page",
    desc: "Share a live compliance posture page with customers and investors — verified by TraceLayer, updated continuously, no manual upkeep.",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Connect your tools",
    desc: "Link your cloud infrastructure and SaaS apps in under 5 minutes using API keys or service accounts. 18+ integrations, no OAuth dance.",
  },
  {
    step: "02",
    title: "Evidence collected automatically",
    desc: "TraceLayer pulls IAM users, audit logs, repositories, and access policies every 24 hours and maps them to all 7 compliance frameworks simultaneously.",
  },
  {
    step: "03",
    title: "Score, report, repeat",
    desc: "See your readiness score update in real time. Generate a formatted PDF report for your auditor whenever you need it — no prep, no consultants.",
  },
];

const TESTIMONIALS = [
  {
    quote: "We cut our SOC 2 prep from 3 months to 2 weeks. The automated evidence collection alone saved us hundreds of hours and eliminated the spreadsheet chaos entirely.",
    author: "Sarah Chen",
    role: "Head of Security, Series B SaaS",
    stars: 5,
  },
  {
    quote: "Our auditor was genuinely impressed. Everything was organized, timestamped, and mapped to controls. TraceLayer made us look like we had a 10-person compliance team.",
    author: "Marcus Webb",
    role: "CTO, Fintech Startup",
    stars: 5,
  },
  {
    quote: "We needed SOC 2 and GDPR simultaneously. TraceLayer mapped our AWS and GitHub evidence to both frameworks without any extra configuration. Saved weeks.",
    author: "Priya Nair",
    role: "VP Engineering, Healthcare Platform",
    stars: 5,
  },
];

const PAIN_POINTS = [
  { before: "Spreadsheets tracking evidence manually",         after: "Automated collection every 24 hours across 18+ tools" },
  { before: "No idea how close you are to audit-ready",        after: "Live readiness score with week-by-week estimate"       },
  { before: "Training completion tracked in email threads",    after: "Training tracker with automatic CC1.4 evidence"       },
  { before: "Vendor compliance buried in shared folders",      after: "Vendor hub with certs, risk levels, and review dates" },
  { before: "Quarterly access reviews done ad hoc",            after: "Formal review cycles with documented auditor sign-off" },
  { before: "Consultants charging $50k+ for the same thing",  after: "Full compliance program self-served at startup cost"   },
];

const PRICING = [
  {
    name: "Starter",
    price: "Free",
    period: "",
    desc: "Perfect for early-stage teams getting audit-ready.",
    features: [
      "Up to 3 integrations",
      "SOC 2, ISO 27001 & HIPAA frameworks",
      "Automated evidence collection",
      "Risk Register & Policy Templates",
      "Training tracker",
      "Vendor risk & pen test tracking",
      "Access review workflows",
      "JSON reports",
      "Up to 3 team members",
    ],
    cta: "Get started free",
    highlighted: false,
  },
  {
    name: "Growth",
    price: "$99",
    period: "/mo",
    desc: "For teams actively pursuing certification.",
    features: [
      "Unlimited integrations (18+)",
      "All 7 frameworks (incl. GDPR, PCI DSS, CCPA, NIST CSF)",
      "PDF & CSV reports",
      "AI Compliance Advisor",
      "AI Questionnaire Autofill",
      "AI Audit Package",
      "Trust Center (public page)",
      "Unlimited team members",
      "Priority support",
    ],
    cta: "Start free trial",
    highlighted: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "",
    desc: "For larger orgs with advanced compliance needs.",
    features: [
      "Everything in Growth",
      "Custom integrations",
      "SSO / SAML",
      "Dedicated CSM",
      "SLA guarantee",
      "Custom audit reports",
    ],
    cta: "Contact sales",
    highlighted: false,
  },
];

const FAQ = [
  {
    q: "How long does setup take?",
    a: "Under 5 minutes. Create an account, paste an API key for your first integration, and evidence collection starts immediately. No agents to deploy, no code to write.",
  },
  {
    q: "Which compliance frameworks do you support?",
    a: "SOC 2 Type I & II, ISO 27001 (2022 edition), HIPAA Security Rule, GDPR, PCI DSS v4.0, CCPA, and NIST CSF 2.0. Evidence collected from your integrations maps to all seven simultaneously — no duplicate work, no reconnecting anything.",
  },
  {
    q: "What is the Readiness Timeline?",
    a: "The Readiness Timeline calculates a blended score (70% automated controls, 30% manual controls) and estimates how many weeks you are from audit-ready at your current pace. It updates in real time and surfaces stage-specific next actions.",
  },
  {
    q: "What integrations are supported?",
    a: "AWS (IAM, CloudTrail), GitHub, Slack, Google Workspace, Okta, Azure AD, Jira, GitLab, GCP, Linear, Datadog, PagerDuty, Sentry, Microsoft Teams, Stripe, Rippling, BambooHR, and Notion — 18 integrations, each collecting multiple evidence types.",
  },
  {
    q: "Does TraceLayer cover training and vendor management?",
    a: "Yes. The Training Tracker lets you assign security awareness courses by email, track completion, flag overdue assignments, and produce CC1.4 evidence. The Vendor hub tracks all third-party vendors with risk levels, SOC 2 / ISO / HIPAA certifications, review dates, and contact info for CC9.2.",
  },
  {
    q: "What are Access Review Workflows?",
    a: "Access Reviews let you create formal quarterly review cycles, assign a reviewer, document scope, record how many users were reviewed and how many access changes were made, and capture findings — all with a completed-at timestamp for CC6.3 auditor evidence.",
  },
  {
    q: "Do you store my cloud credentials?",
    a: "All credentials are encrypted at rest using Fernet symmetric encryption before being written to the database. We never store or log plaintext secrets, and access is scoped to your company only.",
  },
  {
    q: "Can I use TraceLayer for a SOC 2 Type II audit?",
    a: "Yes. TraceLayer collects continuous evidence with timestamps across your entire observation period — exactly what auditors need for a Type II opinion. Generate a formatted PDF report on demand, and share a read-only auditor access link directly from Settings.",
  },
  {
    q: "Is there a free plan?",
    a: "Yes — TraceLayer is free to start with no credit card required. The free plan includes SOC 2, ISO 27001, and HIPAA frameworks, automated evidence collection, Risk Register, Policy Templates, Training Tracker, Vendor hub, Access Reviews, and JSON reports for up to 3 integrations and 3 team members. PDF reports, AI features, Trust Center, and unlimited integrations require the Growth plan at $99/mo.",
  },
  {
    q: "How is the compliance score calculated?",
    a: "Each control is scored on three factors: coverage (70% weight — evidence types present), recency (20% — how fresh the evidence is), and volume (10% — number of records). Scores are snapshotted up to once per hour.",
  },
];

const NAV_LINKS = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#features",     label: "Features"     },
  { href: "#pricing",      label: "Pricing"      },
  { href: "#faq",          label: "FAQ"          },
  { href: "/tools",        label: "Free Tools"   },
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

// ── Marquee ───────────────────────────────────────────────────────────────────

function LogoPill({ name, logo }: { name: string; logo: React.ReactNode }) {
  return (
    <div className="flex items-center gap-2.5 bg-white border border-black/6 rounded-2xl px-4 py-2.5 shadow-sm shrink-0">
      <span className="flex items-center justify-center w-6 h-6">{logo}</span>
      <span className="text-xs font-semibold text-gray-600 whitespace-nowrap">{name}</span>
    </div>
  );
}

function MarqueeRow({ reverse = false }: { reverse?: boolean }) {
  const items = [...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS, ...INTEGRATION_LOGOS];
  return (
    <div className="overflow-hidden" style={{ maskImage: "linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%)" }}>
      <div
        className="flex gap-3 w-max"
        style={{ animation: `${reverse ? "marqueeRight" : "marqueeLeft"} 40s linear infinite` }}
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
    <div className="space-y-2.5">
      {items.map((item, i) => (
        <div
          key={i}
          className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
            open === i
              ? "bg-white border-[color:var(--accent)]/25 shadow-[0_4px_20px_rgba(15,118,110,0.08)]"
              : "bg-white/70 border-black/5 hover:border-black/10 hover:bg-white/90"
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

// ── Page ──────────────────────────────────────────────────────────────────────

export default function LandingPage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [user, loading, router]);

  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled]     = useState(false);
  const [hidden, setHidden]         = useState(false);
  const [progress, setProgress]     = useState(0);
  const lastY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      const docH = document.documentElement.scrollHeight - window.innerHeight;
      setProgress(docH > 0 ? (y / docH) * 100 : 0);
      setScrolled(y > 20);
      setHidden(y > lastY.current && y > 120);
      lastY.current = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const smoothScroll = (e: React.MouseEvent<HTMLAnchorElement>, href: string) => {
    if (!href.startsWith("#")) return;
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth", block: "start" });
    setMobileOpen(false);
  };

  if (loading || user) return null;

  return (
    <div
      className="min-h-screen bg-[var(--bg)] text-[var(--ink)] font-[family:'Sora',_ui-sans-serif,_system-ui]"
      style={THEME}
    >
      {/* Scroll progress bar */}
      <div className="fixed top-0 left-0 right-0 h-[2px] z-[60] bg-transparent">
        <div className="h-full bg-[var(--accent)] transition-all duration-75" style={{ width: `${progress}%` }} />
      </div>

      {/* Nav */}
      <header
        className={`fixed top-[2px] left-0 right-0 z-50 transition-all duration-300 ${
          hidden ? "-translate-y-full" : "translate-y-0"
        } ${
          scrolled
            ? "bg-[#f7f1e8]/96 backdrop-blur-md shadow-sm border-b border-black/5"
            : "bg-[#f7f1e8]/70 backdrop-blur-sm"
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <a href="#" onClick={(e) => smoothScroll(e, "#")} className="flex items-center gap-2.5 shrink-0">
            <Image src="/logo-icon.png" alt="TraceLayer" width={30} height={30} className="rounded-lg" />
            <span className="font-extrabold text-base tracking-tight">TraceLayer</span>
          </a>

          <nav className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map((l) =>
              l.href.startsWith("#") ? (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={(e) => smoothScroll(e, l.href)}
                  className="text-sm text-[var(--muted)] hover:text-[var(--ink)] font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all"
                >
                  {l.label}
                </a>
              ) : (
                <Link
                  key={l.href}
                  href={l.href}
                  className="text-sm font-semibold text-[var(--accent)] bg-[color:var(--accent)]/8 border border-[color:var(--accent)]/15 px-3 py-1.5 rounded-lg hover:bg-[color:var(--accent)]/15 transition-all"
                >
                  {l.label}
                </Link>
              )
            )}
          </nav>

          <div className="hidden md:flex items-center gap-2">
            <Link href="/login" className="text-sm text-[var(--muted)] hover:text-[var(--ink)] font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all">
              Sign in
            </Link>
            <Link href="/register" className="text-sm bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-4 py-1.5 rounded-lg transition-colors shadow-sm">
              Get started free
            </Link>
          </div>

          <button
            className="md:hidden p-2 rounded-lg hover:bg-black/5 transition-colors text-[var(--ink)]"
            onClick={() => setMobileOpen((v) => !v)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {mobileOpen && (
          <div className="md:hidden bg-[color:var(--bg)]/98 backdrop-blur-md border-b border-black/5 px-6 py-4 space-y-1">
            {NAV_LINKS.map((l) =>
              l.href.startsWith("#") ? (
                <a
                  key={l.href}
                  href={l.href}
                  onClick={(e) => smoothScroll(e, l.href)}
                  className="block text-sm font-medium text-[var(--ink)] px-3 py-2.5 rounded-lg hover:bg-black/5 transition-colors"
                >
                  {l.label}
                </a>
              ) : (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setMobileOpen(false)}
                  className="block text-sm font-semibold text-[var(--accent)] px-3 py-2.5 rounded-lg hover:bg-black/5 transition-colors"
                >
                  {l.label}
                </Link>
              )
            )}
            <div className="pt-3 border-t border-black/5 space-y-2">
              <Link href="/login" onClick={() => setMobileOpen(false)} className="block text-sm font-medium text-center text-[var(--muted)] px-3 py-2.5 rounded-lg border border-black/10 hover:bg-black/5 transition-colors">
                Sign in
              </Link>
              <Link href="/register" onClick={() => setMobileOpen(false)} className="block text-sm font-semibold text-center bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white px-3 py-2.5 rounded-lg transition-colors">
                Get started free
              </Link>
            </div>
          </div>
        )}
      </header>

      <div className="h-14" />

      {/* ── Hero ─────────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-[radial-gradient(#0f766e14_1px,transparent_1px)] [background-size:28px_28px]" />
        {/* Glow orbs */}
        <div className="absolute -top-40 right-0 h-[500px] w-[500px] rounded-full bg-[radial-gradient(circle,_rgba(15,118,110,0.2),_transparent_65%)] pointer-events-none" />
        <div className="absolute -bottom-40 -left-20 h-[400px] w-[400px] rounded-full bg-[radial-gradient(circle,_rgba(249,115,22,0.12),_transparent_65%)] pointer-events-none" />

        <div className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center relative">
          {/* Announcement badge */}
          <div className="inline-flex items-center gap-2 bg-white/85 text-[var(--accent)] text-xs font-semibold px-3.5 py-1.5 rounded-full mb-6 border border-black/5 shadow-sm">
            <span className="relative flex h-2 w-2 shrink-0">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
            SOC 2 · ISO 27001 · HIPAA · GDPR · PCI DSS · CCPA · NIST CSF
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-[64px] font-extrabold leading-[1.1] mb-6 tracking-tight">
            Stop chasing compliance.<br />
            <span className="bg-gradient-to-r from-[var(--accent)] via-emerald-500 to-teal-400 bg-clip-text text-transparent">
              Let it run itself.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-[var(--muted)] max-w-2xl mx-auto mb-8 leading-relaxed">
            TraceLayer is your complete compliance program — automated evidence collection across 18+ integrations, risk register, policy templates, training tracker, vendor management, access reviews, and a live readiness score. Everything in one platform.
          </p>

          <div className="flex items-center justify-center gap-3 flex-wrap mb-12">
            <Link
              href="/register"
              className="relative inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-7 py-3.5 rounded-xl transition-colors text-sm overflow-hidden group shadow-[0_0_28px_rgba(15,118,110,0.35)] hover:shadow-[0_0_36px_rgba(15,118,110,0.55)]"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/15 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
              Start for free
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/login" className="inline-flex items-center gap-2 border border-black/12 hover:border-black/20 bg-white/60 hover:bg-white/90 text-[var(--ink)] font-semibold px-7 py-3.5 rounded-xl transition-all text-sm">
              Sign in
            </Link>
          </div>

          {/* Dashboard preview */}
          <div className="max-w-3xl mx-auto">
            <div className="bg-white rounded-2xl border border-black/8 shadow-[0_24px_80px_rgba(15,23,42,0.12)] overflow-hidden">
              {/* Browser chrome */}
              <div className="flex items-center gap-1.5 px-4 py-3 border-b border-gray-100 bg-gray-50/80">
                <div className="w-2.5 h-2.5 rounded-full bg-red-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-400" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-400" />
                <div className="flex-1 mx-4">
                  <div className="bg-white border border-gray-200 rounded-md px-3 py-1 text-[11px] text-gray-400 font-mono hidden sm:block max-w-[220px] mx-auto text-center">
                    app.tracelayer.io/readiness
                  </div>
                </div>
              </div>
              {/* Stats row */}
              <div className="p-3 sm:p-5 grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-3 bg-gray-50/50">
                {[
                  { label: "Readiness",  value: "82%",   color: "text-teal-600",    sub: "SOC 2" },
                  { label: "Evidence",   value: "3,241", color: "text-gray-900",    sub: "records" },
                  { label: "Training",   value: "11/14", color: "text-emerald-600", sub: "completed" },
                  { label: "Est. time",  value: "~4wk",  color: "text-amber-600",   sub: "to audit" },
                ].map((s) => (
                  <div key={s.label} className="bg-white rounded-xl border border-gray-100 p-3 text-left">
                    <p className="text-[10px] text-gray-400 uppercase tracking-widest mb-1">{s.label}</p>
                    <p className={`text-xl font-black ${s.color}`}>{s.value}</p>
                    <p className="text-[10px] text-gray-400 mt-0.5">{s.sub}</p>
                  </div>
                ))}
              </div>
              {/* Controls + next steps */}
              <div className="px-3 sm:px-5 pb-3 sm:pb-5 bg-gray-50/50 grid sm:grid-cols-2 gap-3">
                <div className="bg-white rounded-xl border border-gray-100 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xs font-semibold text-gray-700">SOC 2 Controls</span>
                    <span className="text-xs text-teal-600 font-bold">82%</span>
                  </div>
                  {[
                    { name: "Access Control",       score: 95 },
                    { name: "Logging & Monitoring",  score: 88 },
                    { name: "Change Management",     score: 72 },
                  ].map((c) => (
                    <div key={c.name} className="mb-2">
                      <div className="flex justify-between text-xs text-gray-500 mb-1">
                        <span>{c.name}</span><span className="font-semibold">{c.score}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${c.score}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
                <div className="bg-white rounded-xl border border-gray-100 p-4">
                  <p className="text-xs font-semibold text-gray-700 mb-3">Recommended next steps</p>
                  <div className="space-y-2">
                    {[
                      { label: "Schedule annual pen test",   done: false },
                      { label: "Complete Q1 vendor reviews", done: false },
                      { label: "Run Q1 access review",       done: true  },
                      { label: "Policy templates adopted",   done: true  },
                    ].map((item) => (
                      <div key={item.label} className="flex items-center gap-2">
                        <div className={`w-4 h-4 rounded-full flex items-center justify-center shrink-0 ${item.done ? "bg-emerald-100" : "bg-gray-100"}`}>
                          {item.done && <div className="w-2 h-2 rounded-full bg-emerald-500" />}
                        </div>
                        <span className={`text-[11px] ${item.done ? "text-gray-400 line-through" : "text-gray-700"}`}>{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            {/* Live sync pill */}
            <div className="flex justify-center mt-4">
              <div className="inline-flex items-center gap-2 bg-white/90 backdrop-blur rounded-full px-4 py-2 shadow-md border border-black/5 text-xs">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                <span className="text-gray-500">Evidence synced</span>
                <span className="font-semibold text-gray-900">3 minutes ago</span>
                <span className="text-gray-300">·</span>
                <span className="text-gray-500">Next run in <span className="font-semibold text-gray-900">21h</span></span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Integrations marquee ──────────────────────────────────────────────── */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/50">
        <p className="text-center text-[11px] text-[var(--muted)] font-bold uppercase tracking-widest mb-6">
          Integrates with the tools you already use
        </p>
        <MarqueeRow />
      </section>

      {/* ── Stats ─────────────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-12 border-b border-black/5">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
          {STATS.map((s) => (
            <div key={s.label} className="group">
              <p className="text-4xl md:text-5xl font-extrabold text-[var(--accent)] mb-1.5 group-hover:scale-105 transition-transform duration-200 leading-none">
                {s.value}
              </p>
              <p className="text-xs text-[var(--muted)] font-semibold">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────────── */}
      <section id="how-it-works" className="scroll-mt-16 max-w-6xl mx-auto px-6 py-14 md:py-22">
        <div className="text-center mb-12 md:mb-16">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">How it works</p>
          <h2 className="text-2xl md:text-4xl font-extrabold">Up and running in minutes</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
            No consultants. No long implementation projects. Connect your tools and compliance evidence starts flowing automatically.
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12 md:gap-8 relative">
          {/* Connector line on desktop */}
          <div className="hidden md:block absolute top-8 left-[16.67%] right-[16.67%] h-px bg-gradient-to-r from-transparent via-[color:var(--accent)]/20 to-transparent" />
          {HOW_IT_WORKS.map((item) => (
            <div key={item.step} className="text-center relative">
              <div className="w-16 h-16 rounded-2xl bg-white border border-black/5 shadow-[0_4px_20px_rgba(15,23,42,0.06)] flex items-center justify-center mx-auto mb-5">
                <span className="text-2xl font-black text-[var(--accent)]">{item.step}</span>
              </div>
              <h3 className="text-base font-bold mb-2.5">{item.title}</h3>
              <p className="text-sm text-[var(--muted)] leading-relaxed max-w-[260px] mx-auto">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Module grid ───────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-12 md:py-18 border-y border-black/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Complete platform</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Every tool your compliance program needs</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
              Not just evidence collection. A full compliance stack for startups chasing SOC 2, ISO 27001, HIPAA, GDPR, and more.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {[
              { icon: Zap,          label: "Evidence Collection",  desc: "Automated, 24h"      },
              { icon: BarChart3,    label: "Compliance Score",     desc: "Real-time"            },
              { icon: Target,       label: "Readiness Timeline",   desc: "Weeks to audit"       },
              { icon: AlertTriangle,label: "Risk Register",        desc: "CC3 & CC9"            },
              { icon: BookOpen,     label: "Policy Templates",     desc: "Pre-written"          },
              { icon: GraduationCap,label: "Training Tracker",     desc: "CC1.4 evidence"       },
              { icon: Shield,       label: "Pen Test Tracker",     desc: "Annual requirement"   },
              { icon: Building2,    label: "Vendor Diligence",     desc: "CC9.2"                },
              { icon: UserCheck,    label: "Access Reviews",       desc: "CC6.3 sign-off"       },
              { icon: ClipboardList,label: "Questionnaire Fill",   desc: "AI-assisted"          },
              { icon: Globe,        label: "Trust Page",           desc: "Live public page"     },
              { icon: FileText,     label: "Audit Reports",        desc: "PDF & JSON"           },
              { icon: Lock,         label: "Auditor Portal",       desc: "Read-only access"     },
              { icon: Users,        label: "Team RBAC",            desc: "Admin & member"       },
              { icon: Plug,         label: "18+ Integrations",     desc: "AWS, GitHub, Okta…"   },
            ].map(({ icon: Icon, label, desc }) => (
              <div key={label} className="bg-[var(--card)] rounded-2xl border border-black/5 p-4 hover:shadow-[0_8px_24px_rgba(15,23,42,0.08)] hover:-translate-y-0.5 transition-all duration-200 group">
                <div className="w-8 h-8 bg-[color:var(--accent)]/10 rounded-xl flex items-center justify-center mb-3 group-hover:bg-[color:var(--accent)]/18 transition-colors">
                  <Icon className="w-4 h-4 text-[var(--accent)]" />
                </div>
                <p className="text-xs font-bold text-[var(--ink)] leading-snug">{label}</p>
                <p className="text-[10px] text-[var(--muted)] mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Before / After ────────────────────────────────────────────────────── */}
      <section className="bg-slate-900 py-14 md:py-22">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-orange-400 uppercase tracking-widest mb-2">The old way vs TraceLayer</p>
            <h2 className="text-2xl md:text-4xl font-extrabold text-white">Compliance doesn&apos;t have to be painful</h2>
          </div>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="bg-white/5 rounded-2xl p-6 border border-white/8">
              <p className="text-xs font-bold text-red-400 uppercase tracking-widest mb-5">Before</p>
              <div className="space-y-3.5">
                {PAIN_POINTS.map((p) => (
                  <div key={p.before} className="flex items-start gap-3">
                    <div className="w-5 h-5 rounded-full bg-red-500/15 border border-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
                      <X className="w-2.5 h-2.5 text-red-400" />
                    </div>
                    <p className="text-sm text-white/55 leading-snug">{p.before}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-teal-500/10 rounded-2xl p-6 border border-teal-500/20">
              <p className="text-xs font-bold text-teal-400 uppercase tracking-widest mb-5">With TraceLayer</p>
              <div className="space-y-3.5">
                {PAIN_POINTS.map((p) => (
                  <div key={p.after} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-teal-400 shrink-0 mt-0.5" />
                    <p className="text-sm text-white/80 leading-snug">{p.after}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────────── */}
      <section id="features" className="scroll-mt-16 bg-white/60 py-14 md:py-22">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Features</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">A complete compliance program, not just a tool</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
              Built for startups who need to move fast without sacrificing security posture — from first integration to audit day.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[var(--card)] rounded-2xl border border-black/5 p-6 shadow-[0_4px_20px_rgba(15,23,42,0.04)] hover:shadow-[0_8px_32px_rgba(15,23,42,0.08)] hover:-translate-y-0.5 transition-all duration-200">
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

      {/* ── Second marquee ────────────────────────────────────────────────────── */}
      <section className="py-10 overflow-hidden border-y border-black/5 bg-white/40">
        <MarqueeRow reverse />
      </section>

      {/* ── Frameworks ────────────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-6 py-14 md:py-22">
        <div className="text-center mb-10 md:mb-14">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Frameworks</p>
          <h2 className="text-2xl md:text-4xl font-extrabold">Seven frameworks, one platform</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
            Your integrations map evidence to all frameworks simultaneously. Switch views without reconnecting anything or doing duplicate work.
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FRAMEWORKS.map((f) => (
            <div key={f.name} className="bg-[var(--card)] border border-black/5 rounded-2xl p-5 shadow-[0_4px_16px_rgba(15,23,42,0.05)] hover:shadow-[0_8px_28px_rgba(15,23,42,0.09)] hover:-translate-y-0.5 transition-all duration-200 group">
              <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} flex items-center justify-center mb-3 shadow-sm`}>
                <ShieldCheck className="w-5 h-5 text-white" />
              </div>
              <p className="font-extrabold text-base text-[var(--ink)]">{f.name}</p>
              <p className="text-[11px] text-[var(--muted)] font-semibold mt-0.5 mb-2">{f.desc}</p>
              <p className="text-xs text-[var(--muted)] leading-relaxed">{f.detail}</p>
            </div>
          ))}
          {/* "More coming" card */}
          <div className="bg-[var(--card)] border border-dashed border-black/10 rounded-2xl p-5 flex flex-col items-start justify-center">
            <div className="w-10 h-10 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
              <span className="text-lg font-black text-gray-400">+</span>
            </div>
            <p className="font-bold text-sm text-[var(--ink)]">More on the roadmap</p>
            <p className="text-xs text-[var(--muted)] mt-1 leading-relaxed">FedRAMP, SOX, and custom framework mapping coming soon.</p>
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────────────────── */}
      <section className="bg-white/60 py-14 md:py-22 border-y border-black/5">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">What teams say</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Trusted by security-conscious teams</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {TESTIMONIALS.map((t) => (
              <div key={t.author} className="bg-[var(--card)] rounded-2xl border border-black/5 p-6 shadow-[0_4px_20px_rgba(15,23,42,0.05)]">
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: t.stars }).map((_, i) => (
                    <Star key={i} className="w-3.5 h-3.5 fill-[var(--accent-warm)] text-[var(--accent-warm)]" />
                  ))}
                </div>
                <p className="text-sm text-[var(--ink)] leading-relaxed mb-5">&ldquo;{t.quote}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[color:var(--accent)]/12 flex items-center justify-center text-xs font-bold text-[var(--accent)] shrink-0">
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

      {/* ── Metrics strip ─────────────────────────────────────────────────────── */}
      <section className="border-b border-black/5 bg-[var(--bg)] py-12">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-1 sm:grid-cols-3 gap-10 text-center">
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <Clock className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">2 weeks</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Average time to first audit-ready report</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <TrendingUp className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">90%</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Reduction in manual evidence prep</p>
          </div>
          <div>
            <div className="flex items-center justify-center gap-2 mb-1.5">
              <Users className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-2xl font-extrabold text-[var(--ink)]">1 person</span>
            </div>
            <p className="text-xs text-[var(--muted)]">Can run your entire compliance program</p>
          </div>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────────────────── */}
      <section id="pricing" className="scroll-mt-16 bg-white/60 py-14 md:py-22">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12 md:mb-16">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Pricing</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Start free. Scale when you&apos;re ready.</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto leading-relaxed">
              No credit card required to get started. Upgrade to Growth for AI features, PDF reports, Trust Center, and unlimited integrations.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-2xl border p-7 ${
                  plan.highlighted
                    ? "bg-slate-900 border-slate-800 shadow-[0_24px_60px_rgba(15,23,42,0.3)]"
                    : "bg-[var(--card)] border-black/5 shadow-[0_4px_20px_rgba(15,23,42,0.05)]"
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-[var(--accent-warm)] text-white text-[10px] font-bold uppercase tracking-widest px-3 py-1.5 rounded-full shadow-sm">
                      Most popular
                    </span>
                  </div>
                )}
                <p className={`text-sm font-bold mb-1 ${plan.highlighted ? "text-white/50" : "text-[var(--muted)]"}`}>{plan.name}</p>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-4xl font-black ${plan.highlighted ? "text-white" : "text-[var(--ink)]"}`}>{plan.price}</span>
                  {plan.period && <span className={`text-sm ${plan.highlighted ? "text-white/40" : "text-[var(--muted)]"}`}>{plan.period}</span>}
                </div>
                <p className={`text-xs mb-6 leading-relaxed ${plan.highlighted ? "text-white/45" : "text-[var(--muted)]"}`}>{plan.desc}</p>
                <div className="space-y-2.5 mb-7">
                  {plan.features.map((f) => (
                    <div key={f} className="flex items-start gap-2.5">
                      <CheckCircle2 className={`w-4 h-4 shrink-0 mt-0.5 ${plan.highlighted ? "text-emerald-400" : "text-[var(--accent)]"}`} />
                      <span className={`text-xs leading-snug ${plan.highlighted ? "text-white/65" : "text-[var(--ink)]"}`}>{f}</span>
                    </div>
                  ))}
                </div>
                <Link
                  href="/register"
                  className={`block text-center text-sm font-semibold py-2.5 rounded-xl transition-colors ${
                    plan.highlighted
                      ? "bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white"
                      : "bg-[color:var(--ink)]/6 hover:bg-[color:var(--ink)]/10 text-[var(--ink)]"
                  }`}
                >
                  {plan.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────────────────────── */}
      <section id="faq" className="scroll-mt-16 py-14 md:py-22 bg-[var(--bg)]">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10 md:mb-14">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">FAQ</p>
            <h2 className="text-2xl md:text-4xl font-extrabold">Common questions</h2>
            <p className="text-[var(--muted)] mt-3 text-sm max-w-md mx-auto leading-relaxed">
              Everything you need to know before getting started.
            </p>
          </div>
          <FaqAccordion items={FAQ} />
          <p className="text-center text-sm text-[var(--muted)] mt-8">
            Still have questions?{" "}
            <a href="mailto:hello@tracelayer.io" className="text-[var(--accent)] font-semibold hover:underline">
              Drop us a line
            </a>
          </p>
        </div>
      </section>

      {/* ── Final CTA ─────────────────────────────────────────────────────────── */}
      <section className="bg-slate-900 py-16 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(15,118,110,0.3),_transparent_70%)] pointer-events-none" />
        <div className="absolute top-0 right-0 w-80 h-80 rounded-full bg-teal-500/10 blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        <div className="max-w-2xl mx-auto px-6 text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/10 text-teal-300 text-xs font-semibold px-3.5 py-1.5 rounded-full mb-6 border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Free to start · No credit card required
          </div>
          <h2 className="text-3xl md:text-5xl font-extrabold text-white mb-5 leading-tight">
            Your next audit<br />starts now.
          </h2>
          <p className="text-white/60 mb-8 text-sm leading-relaxed max-w-md mx-auto">
            Create your account and get your full compliance program running in minutes — evidence collection, risk register, policies, training, vendors, and a live readiness score.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-[0_0_32px_rgba(15,118,110,0.4)]"
          >
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/30 text-xs mt-4">Setup in 5 minutes · SOC 2 · ISO 27001 · HIPAA · GDPR · PCI DSS · CCPA · NIST CSF</p>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────────── */}
      <footer className="border-t border-black/5 pt-14 pb-8 bg-[var(--bg)]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-12">
            {/* Brand */}
            <div className="col-span-2 sm:col-span-1">
              <div className="flex items-center gap-2.5 mb-3">
                <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
                <span className="font-extrabold text-base text-[var(--ink)]">TraceLayer</span>
              </div>
              <p className="text-xs text-[var(--muted)] leading-relaxed max-w-[200px]">
                Continuous compliance automation for modern engineering teams.
              </p>
              <div className="flex flex-wrap gap-1.5 mt-4">
                {["SOC 2", "ISO 27001", "HIPAA", "GDPR", "PCI DSS"].map((f) => (
                  <span key={f} className="text-[10px] font-semibold text-[var(--accent)] bg-[color:var(--accent)]/8 px-2 py-0.5 rounded-full border border-[color:var(--accent)]/15">
                    {f}
                  </span>
                ))}
              </div>
            </div>

            {/* Product */}
            <div>
              <p className="text-xs font-bold text-[var(--ink)] uppercase tracking-wider mb-4">Product</p>
              <ul className="space-y-2.5">
                {[
                  { label: "How it works", href: "#how-it-works" },
                  { label: "Features",     href: "#features"     },
                  { label: "Pricing",      href: "#pricing"      },
                  { label: "FAQ",          href: "#faq"          },
                ].map((l) => (
                  <li key={l.label}>
                    <a
                      href={l.href}
                      onClick={(e) => smoothScroll(e, l.href)}
                      className="text-xs text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
                    >
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* Account */}
            <div>
              <p className="text-xs font-bold text-[var(--ink)] uppercase tracking-wider mb-4">Account</p>
              <ul className="space-y-2.5">
                {[
                  { label: "Sign in",     href: "/login"    },
                  { label: "Get started", href: "/register" },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="text-xs text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Legal */}
            <div>
              <p className="text-xs font-bold text-[var(--ink)] uppercase tracking-wider mb-4">Legal</p>
              <ul className="space-y-2.5">
                {[
                  { label: "Privacy Policy",   href: "/privacy" },
                  { label: "Terms of Service", href: "/terms"   },
                ].map((l) => (
                  <li key={l.label}>
                    <Link href={l.href} className="text-xs text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div className="border-t border-black/5 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-[var(--muted)]">© {new Date().getFullYear()} TraceLayer. All rights reserved.</p>
            <p className="text-xs text-[var(--muted)]">Built for startups chasing certification.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
