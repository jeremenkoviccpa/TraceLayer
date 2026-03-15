"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowRight, Zap, Shield, CheckCircle2 } from "lucide-react";
import { ComplianceQuiz } from "@/components/compliance-quiz";
import { GapScanner } from "@/components/gap-scanner";

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS = [
  {
    id: "readiness",
    anchor: "#readiness",
    badge: "Automation",
    icon: Zap,
    iconBg: "bg-violet-50 border-violet-100",
    iconColor: "text-violet-600",
    badgeBg: "bg-violet-100 text-violet-700",
    name: "Compliance Readiness Check",
    tagline: "5 questions · 60 seconds",
    desc: "Find out how much of your compliance work can be automated today based on your existing tech stack. Get a personalized score with specific recommendations.",
    pills: ["Stack-based analysis", "Instant results", "No signup"],
  },
  {
    id: "gap-scanner",
    anchor: "#gap-scanner",
    badge: "Audit Risk",
    icon: Shield,
    iconBg: "bg-teal-50 border-teal-100",
    iconColor: "text-teal-600",
    badgeBg: "bg-teal-100 text-teal-700",
    name: "SOC 2 Gap Scanner",
    tagline: "10 controls · 2 minutes",
    desc: "Walk through 10 critical SOC 2 controls and see exactly which gaps would be flagged in a real audit — with the exact language your auditor would use.",
    pills: ["Real audit criteria", "Per-control breakdown", "No signup"],
  },
];

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ToolsPage() {
  return (
    <div className="min-h-screen bg-[#f7f1e8] font-[family:'Sora',_ui-sans-serif,_system-ui]">

      {/* Nav */}
      <header className="sticky top-0 z-50 bg-[#f7f1e8]/95 backdrop-blur-md border-b border-black/5">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 shrink-0">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-extrabold text-base tracking-tight text-gray-900">TraceLayer</span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {[
              { href: "/#how-it-works", label: "How it works" },
              { href: "/#features",     label: "Features"     },
              { href: "/#pricing",      label: "Pricing"      },
            ].map((l) => (
              <Link
                key={l.href}
                href={l.href}
                className="text-sm text-gray-500 hover:text-gray-900 font-medium px-3 py-1.5 rounded-lg hover:bg-black/5 transition-all"
              >
                {l.label}
              </Link>
            ))}
            <span className="text-sm font-semibold text-teal-700 bg-teal-50 border border-teal-100 px-3 py-1.5 rounded-lg">
              Free Tools
            </span>
          </nav>

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
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-10 text-center">
        <div className="inline-flex items-center gap-2 bg-white/80 text-teal-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5 border border-black/5 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
          Free — no account required
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight tracking-tight">
          Free compliance tools<br />
          <span className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-transparent">built for engineering teams</span>
        </h1>
        <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed">
          Know where you stand before spending a dollar on compliance. Run both tools in under 5 minutes — no email, no signup.
        </p>
      </section>

      {/* Tool cards */}
      <section className="max-w-4xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            return (
              <div key={tool.id} className="bg-white rounded-2xl border border-black/5 shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-6 flex flex-col">
                <div className="flex items-start gap-4 mb-4">
                  <div className={`w-12 h-12 rounded-2xl border flex items-center justify-center shrink-0 ${tool.iconBg}`}>
                    <Icon className={`w-6 h-6 ${tool.iconColor}`} />
                  </div>
                  <div>
                    <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${tool.badgeBg}`}>
                      {tool.badge}
                    </span>
                    <h2 className="font-extrabold text-gray-900 mt-1 leading-snug">{tool.name}</h2>
                    <p className="text-xs text-gray-400 font-medium">{tool.tagline}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500 leading-relaxed mb-5 flex-1">{tool.desc}</p>
                <div className="flex flex-wrap gap-2 mb-5">
                  {tool.pills.map((p) => (
                    <span key={p} className="inline-flex items-center gap-1 text-[10px] font-semibold text-gray-500 bg-gray-50 border border-gray-100 px-2.5 py-1 rounded-full">
                      <CheckCircle2 className="w-3 h-3 text-teal-500" /> {p}
                    </span>
                  ))}
                </div>
                <a
                  href={tool.anchor}
                  className="inline-flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 text-white font-semibold py-2.5 rounded-xl transition-colors text-sm"
                >
                  Try it now <ArrowRight className="w-4 h-4" />
                </a>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Tool 1: Compliance Readiness Check ─────────────────────────────────── */}
      <section id="readiness" className="scroll-mt-16 bg-slate-900 py-14 md:py-20 overflow-hidden relative">
        <div className="absolute -top-32 right-0 w-96 h-96 rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.15),transparent)]" />
        <div className="absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-[radial-gradient(circle,rgba(16,185,129,0.10),transparent)]" />

        <div className="max-w-6xl mx-auto px-6 mb-12 relative">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-violet-500/20 rounded-xl flex items-center justify-center border border-violet-500/30">
              <Zap className="w-4 h-4 text-violet-400" />
            </div>
            <span className="text-xs font-bold text-violet-400 uppercase tracking-widest">Tool 1</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-2">Compliance Readiness Check</h2>
          <p className="text-white/60 text-sm max-w-lg">
            5 questions about your stack. See exactly how much of your compliance work TraceLayer can automate — and what to tackle first.
          </p>
        </div>

        <div className="max-w-3xl mx-auto px-4 sm:px-6 relative">
          <ComplianceQuiz />
        </div>
      </section>

      {/* Divider between tools */}
      <div className="bg-slate-800 border-y border-white/10 py-6">
        <div className="max-w-4xl mx-auto px-6 flex items-center justify-between flex-wrap gap-4">
          <p className="text-sm font-semibold text-white/70">Done with Tool 1? Run the Gap Scanner next.</p>
          <a
            href="#gap-scanner"
            className="inline-flex items-center gap-2 text-sm font-semibold text-teal-300 bg-teal-500/10 border border-teal-500/20 px-4 py-2 rounded-lg hover:bg-teal-500/20 transition-colors"
          >
            Go to SOC 2 Gap Scanner <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </div>

      {/* ── Tool 2: SOC 2 Gap Scanner ──────────────────────────────────────────── */}
      <section id="gap-scanner" className="scroll-mt-16 bg-slate-900 py-14 md:py-20 overflow-hidden relative">
        <div className="absolute -top-32 left-0 w-96 h-96 rounded-full bg-[radial-gradient(circle,rgba(20,184,166,0.15),transparent)]" />
        <div className="absolute -bottom-20 right-0 w-80 h-80 rounded-full bg-[radial-gradient(circle,rgba(16,185,129,0.10),transparent)]" />

        <div className="max-w-6xl mx-auto px-6 mb-12 relative">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-teal-500/20 rounded-xl flex items-center justify-center border border-teal-500/30">
              <Shield className="w-4 h-4 text-teal-400" />
            </div>
            <span className="text-xs font-bold text-teal-400 uppercase tracking-widest">Tool 2</span>
          </div>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-2">SOC 2 Gap Scanner</h2>
          <p className="text-white/60 text-sm max-w-lg">
            Walk through 10 critical SOC 2 controls. See which ones you&apos;d fail in a real audit — with the exact language your auditor will use.
          </p>
        </div>

        <div className="max-w-3xl mx-auto px-4 sm:px-6 relative">
          <GapScanner />
        </div>
      </section>

      {/* CTA */}
      <section className="bg-teal-600 py-12 md:py-16">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <p className="text-xs font-bold text-white/60 uppercase tracking-widest mb-3">Ready to fix what you found?</p>
          <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-3 leading-tight">
            Let TraceLayer collect the evidence automatically.
          </h2>
          <p className="text-white/75 text-sm mb-7 max-w-md mx-auto leading-relaxed">
            Connect your tools and TraceLayer starts mapping evidence to your compliance controls within minutes — no manual work, no spreadsheets.
          </p>
          <Link
            href="/register"
            className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm"
          >
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/50 text-xs mt-3">Free to start · No credit card · Setup in 5 minutes</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/5 py-8 bg-[#f7f1e8]">
        <div className="max-w-6xl mx-auto px-6 flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={24} height={24} className="rounded-md" />
            <span className="font-extrabold text-sm text-gray-900">TraceLayer</span>
          </div>
          <div className="flex items-center gap-6 text-xs text-gray-400">
            <Link href="/" className="hover:text-gray-700 transition-colors">Home</Link>
            <Link href="/#pricing" className="hover:text-gray-700 transition-colors">Pricing</Link>
            <Link href="/login" className="hover:text-gray-700 transition-colors">Sign in</Link>
            <Link href="/register" className="hover:text-gray-700 transition-colors">Get started</Link>
          </div>
          <span className="text-xs text-gray-400">© {new Date().getFullYear()} TraceLayer</span>
        </div>
      </footer>

      <style jsx global>{`
        @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&display=swap');
        html { scroll-behavior: smooth; }
      `}</style>
    </div>
  );
}
