"use client";

import { useEffect } from "react";
import type { CSSProperties } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/components/auth-provider";
import {
  ShieldCheck,
  Plug,
  FileText,
  Zap,
  ArrowRight,
  CheckCircle2,
  BarChart3,
  Lock,
} from "lucide-react";

const INTEGRATIONS = [
  "AWS", "GitHub", "Slack", "Google Workspace", "Jira", "Okta", "Azure AD",
];

const FRAMEWORKS = [
  { name: "SOC 2", desc: "Type II" },
  { name: "ISO 27001", desc: "2022" },
  { name: "HIPAA", desc: "Security Rule" },
];

const FEATURES = [
  {
    icon: Plug,
    title: "One-click integrations",
    desc: "Connect AWS, GitHub, Slack, Google Workspace, Okta, Jira and Azure AD in minutes. No agents, no code.",
  },
  {
    icon: Zap,
    title: "Automated evidence collection",
    desc: "Evidence is collected continuously every 24 hours — IAM users, audit logs, repositories, policies and more.",
  },
  {
    icon: BarChart3,
    title: "Real-time compliance score",
    desc: "See your SOC 2, ISO 27001 or HIPAA posture at a glance. Per-control breakdown shows exactly what to fix.",
  },
  {
    icon: FileText,
    title: "Audit-ready PDF reports",
    desc: "Generate a formatted evidence report in one click. Hand it directly to your auditor or security team.",
  },
  {
    icon: ShieldCheck,
    title: "Multi-framework coverage",
    desc: "Switch between frameworks without reconfiguring. Your integrations map evidence to all frameworks simultaneously.",
  },
  {
    icon: Lock,
    title: "Secure by default",
    desc: "Credentials encrypted at rest with Fernet. JWT auth with refresh token rotation. Role-based access control.",
  },
];

const HOW_IT_WORKS = [
  {
    step: "01",
    title: "Connect your tools",
    desc: "Link your cloud infrastructure and SaaS apps in under 5 minutes using API keys or service accounts.",
  },
  {
    step: "02",
    title: "Evidence collected automatically",
    desc: "TraceLayer pulls IAM users, audit logs, repositories, and access policies and maps them to compliance controls.",
  },
  {
    step: "03",
    title: "Score, report, repeat",
    desc: "See your compliance score instantly. Generate a PDF report for your auditor whenever you need it.",
  },
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
        <div className="absolute -top-32 right-0 h-80 w-80 rounded-full bg-[radial-gradient(circle,_rgba(15,118,110,0.25),_rgba(247,241,232,0))]" />
        <div className="absolute -bottom-40 -left-10 h-96 w-96 rounded-full bg-[radial-gradient(circle,_rgba(249,115,22,0.22),_rgba(247,241,232,0))]" />
        <div className="max-w-6xl mx-auto px-6 pt-20 pb-16 text-center relative">
          <div className="inline-flex items-center gap-2 bg-white/80 text-[var(--accent)] text-xs font-semibold px-3 py-1.5 rounded-full mb-6 border border-black/5 fade-up">
            <ShieldCheck className="w-3.5 h-3.5" />
          SOC 2 · ISO 27001 · HIPAA
          </div>
          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight mb-5 tracking-tight fade-up">
          Compliance evidence,<br />
          <span className="text-[var(--accent)]">collected automatically</span>
          </h1>
          <p className="text-lg text-[var(--muted)] max-w-xl mx-auto mb-8 fade-up delay-1">
          TraceLayer connects to your cloud tools and continuously collects the evidence
          your auditor needs — so you&apos;re always audit-ready.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap fade-up delay-2">
            <Link href="/register" className="inline-flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-strong)] text-white font-semibold px-6 py-3 rounded-xl transition-colors text-sm">
            Start for free <ArrowRight className="w-4 h-4" />
            </Link>
            <Link href="/login" className="inline-flex items-center gap-2 border border-black/10 hover:border-black/20 text-[var(--ink)] font-semibold px-6 py-3 rounded-xl transition-colors text-sm">
            Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Integration strip */}
      <section className="border-y border-black/5 bg-white/60 py-5">
        <div className="max-w-4xl mx-auto px-6 flex flex-wrap items-center justify-center gap-x-8 gap-y-3">
          <span className="text-xs text-[var(--muted)] font-medium uppercase tracking-wide mr-2">Integrates with</span>
          {INTEGRATIONS.map((name) => (
            <span key={name} className="text-sm font-semibold text-[var(--muted)]">{name}</span>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">How it works</p>
          <h2 className="text-3xl font-extrabold">Up and running in minutes</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {HOW_IT_WORKS.map((item) => (
            <div key={item.step}>
              <div className="text-5xl font-black text-[color:var(--accent)]/10 mb-3 leading-none">{item.step}</div>
              <h3 className="text-base font-bold mb-2">{item.title}</h3>
              <p className="text-sm text-[var(--muted)] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="bg-white/60 py-20">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-12">
            <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Features</p>
            <h2 className="text-3xl font-extrabold">Everything you need for continuous compliance</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="bg-[var(--card)] rounded-2xl border border-black/5 p-6 shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
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

      {/* Frameworks */}
      <section className="max-w-6xl mx-auto px-6 py-20">
        <div className="text-center mb-10">
          <p className="text-xs font-bold text-[var(--accent)] uppercase tracking-widest mb-2">Frameworks</p>
          <h2 className="text-3xl font-extrabold">One platform, multiple frameworks</h2>
          <p className="text-[var(--muted)] mt-3 text-sm max-w-lg mx-auto">
            Your integrations map evidence to all frameworks simultaneously. Switch without reconnecting anything.
          </p>
        </div>
        <div className="flex justify-center gap-6 flex-wrap">
          {FRAMEWORKS.map((f) => (
            <div key={f.name} className="bg-[var(--card)] border border-black/5 rounded-2xl px-10 py-8 text-center min-w-[160px] shadow-[0_8px_24px_rgba(15,23,42,0.05)]">
              <ShieldCheck className="w-8 h-8 text-[var(--accent)] mx-auto mb-3" />
              <p className="font-extrabold text-lg">{f.name}</p>
              <p className="text-xs text-[var(--muted)] mt-1">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-[var(--accent)] py-16">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-3xl font-extrabold text-white mb-3">Ready to get audit-ready?</h2>
          <p className="text-white/80 mb-8 text-sm">
            Create your account, connect your first integration, and see your compliance score in under 5 minutes.
          </p>
          <Link href="/register" className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-[var(--accent)] font-bold px-8 py-3 rounded-xl transition-colors text-sm">
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/5 py-6">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between text-xs text-[var(--muted)] flex-wrap gap-3">
          <span className="font-bold text-[var(--muted)]">TraceLayer</span>
          <div className="flex items-center gap-4">
            {["SOC 2", "ISO 27001", "HIPAA"].map((f) => (
              <span key={f} className="flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3 text-[var(--accent-warm)]" /> {f}
              </span>
            ))}
          </div>
          <span>© {new Date().getFullYear()} TraceLayer</span>
        </div>
      </footer>

      <style jsx global>{`
        @keyframes fadeUp {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .fade-up {
          animation: fadeUp 0.7s ease-out both;
        }
        .fade-up.delay-1 {
          animation-delay: 0.1s;
        }
        .fade-up.delay-2 {
          animation-delay: 0.2s;
        }
      `}</style>
    </div>
  );
}
