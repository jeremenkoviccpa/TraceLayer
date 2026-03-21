"use client";

import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight, Zap, Shield, CheckCircle2, TrendingDown,
  Clock, DollarSign, AlertTriangle, Target, Users, BarChart3,
} from "lucide-react";

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS = [
  {
    id: "readiness",
    href: "/tools/readiness",
    badge: "Automation",
    icon: Zap,
    iconBg: "bg-violet-50 border-violet-100",
    iconColor: "text-violet-600",
    badgeBg: "bg-violet-100 text-violet-700",
    accentColor: "from-violet-500 to-violet-600",
    name: "Compliance Readiness Check",
    tagline: "5 questions · 60 seconds",
    desc: "Find out how much of your compliance work can be automated today based on your existing tech stack. Get a personalized score with specific recommendations.",
    pills: ["Stack-based analysis", "Instant results", "No signup"],
    cta: "Check my readiness",
  },
  {
    id: "gap-scanner",
    href: "/tools/gap-scanner",
    badge: "Audit Risk",
    icon: Shield,
    iconBg: "bg-teal-50 border-teal-100",
    iconColor: "text-teal-600",
    badgeBg: "bg-teal-100 text-teal-700",
    accentColor: "from-teal-500 to-teal-600",
    name: "SOC 2 Gap Scanner",
    tagline: "10 controls · 2 minutes",
    desc: "Walk through 10 critical SOC 2 controls and see exactly which gaps would be flagged in a real audit — with the exact language your auditor would use.",
    pills: ["Real audit criteria", "Per-control breakdown", "No signup"],
    cta: "Scan for gaps",
  },
  {
    id: "revenue-impact",
    href: "/tools/revenue-impact",
    badge: "Revenue",
    icon: TrendingDown,
    iconBg: "bg-orange-50 border-orange-100",
    iconColor: "text-orange-500",
    badgeBg: "bg-orange-100 text-orange-700",
    accentColor: "from-orange-500 to-rose-500",
    name: "Revenue Impact Calculator",
    tagline: "3 questions · 2 minutes",
    desc: "See the exact dollar value of deals you're losing, fines you're exposed to, and staff time you're burning — with a clear ROI on fixing it.",
    pills: ["Personalised to your ARR", "Pipeline analysis", "No signup"],
    cta: "Calculate my risk",
    highlight: true,
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
      <section className="max-w-3xl mx-auto px-6 pt-16 pb-12 text-center">
        <div className="inline-flex items-center gap-2 bg-white/80 text-teal-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5 border border-black/5 shadow-sm">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500" />
          3 free tools · No account required · Takes under 5 minutes
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight tracking-tight">
          Know exactly where you stand<br />
          <span className="bg-gradient-to-r from-teal-600 to-emerald-500 bg-clip-text text-transparent">before spending a dollar on compliance</span>
        </h1>
        <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed">
          Three tools built for startup CTOs and engineering leaders. Run them in under 5 minutes — no email, no signup, no sales call.
        </p>
      </section>

      {/* Stats strip */}
      <section className="border-y border-black/5 py-8 bg-white/60">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 sm:grid-cols-4 gap-6">
          {[
            { stat: "78%",    desc: "of enterprise deals require SOC 2 before signing" },
            { stat: "$4.5M",  desc: "average cost of a data breach for SMBs"           },
            { stat: "12%",    desc: "of eng team time lost to manual compliance"        },
            { stat: "6 mo",   desc: "average deal delay when compliance is missing"     },
          ].map((item) => (
            <div key={item.stat} className="text-center">
              <p className="text-2xl font-extrabold text-gray-900 mb-1">{item.stat}</p>
              <p className="text-xs text-gray-500 leading-snug">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Tool cards */}
      <section className="max-w-5xl mx-auto px-6 py-14">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            return (
              <div
                key={tool.id}
                className={`bg-white rounded-2xl border shadow-[0_8px_30px_rgba(15,23,42,0.07)] p-6 flex flex-col ${
                  tool.highlight ? "border-orange-100 ring-1 ring-orange-100" : "border-black/5"
                }`}
              >
                {tool.highlight && (
                  <div className="inline-flex items-center gap-1.5 text-[10px] font-bold text-orange-600 bg-orange-50 border border-orange-100 px-2.5 py-1 rounded-full self-start mb-3">
                    <span className="w-1.5 h-1.5 rounded-full bg-orange-500 animate-pulse" />
                    Most popular
                  </div>
                )}
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
                <Link
                  href={tool.href}
                  className={`inline-flex items-center justify-center gap-2 font-semibold py-2.5 rounded-xl transition-all text-sm ${
                    tool.highlight
                      ? "bg-gradient-to-r from-orange-500 to-rose-500 hover:from-orange-600 hover:to-rose-600 text-white shadow-md shadow-orange-500/20"
                      : "bg-gray-900 hover:bg-gray-800 text-white"
                  }`}
                >
                  {tool.cta} <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            );
          })}
        </div>
      </section>

      {/* Why free? */}
      <section className="bg-slate-900 py-14 md:py-20">
        <div className="max-w-5xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-xs font-bold text-teal-400 uppercase tracking-widest mb-3">Why we built these</p>
              <h2 className="text-2xl md:text-3xl font-extrabold text-white mb-5 leading-tight">
                Most compliance tools hide the problem behind a sales demo.
              </h2>
              <p className="text-white/60 text-sm leading-relaxed mb-6">
                We built these tools because startup CTOs deserve to understand their compliance risk before committing to any vendor — including us.
              </p>
              <p className="text-white/60 text-sm leading-relaxed mb-8">
                Run all three tools. If the numbers are painful, TraceLayer fixes them. If they&apos;re not, you learned something useful for free.
              </p>
              <Link
                href="/register"
                className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-500 text-white font-bold px-6 py-3 rounded-xl transition-colors text-sm"
              >
                See TraceLayer in action <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
            <div className="space-y-4">
              {[
                {
                  icon: Target,
                  title: "Specific to your business",
                  desc: "Each tool uses your actual ARR, stack, and pipeline — not generic industry averages — so the output is actionable.",
                },
                {
                  icon: Clock,
                  title: "Under 5 minutes total",
                  desc: "All three tools combined take less time than a single sales call. Run them now, decide later.",
                },
                {
                  icon: DollarSign,
                  title: "Zero commercial pressure",
                  desc: "No email required, no sales follow-up unless you ask for it. The tools stand alone.",
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex items-start gap-4 bg-white/5 rounded-xl p-4 border border-white/10">
                    <div className="w-8 h-8 rounded-lg bg-teal-500/20 border border-teal-500/30 flex items-center justify-center shrink-0">
                      <Icon className="w-4 h-4 text-teal-400" />
                    </div>
                    <div>
                      <p className="font-bold text-white text-sm mb-1">{item.title}</p>
                      <p className="text-xs text-white/50 leading-relaxed">{item.desc}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* Who this is for */}
      <section className="py-14 bg-[#f7f1e8]">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Who uses these tools</p>
            <h2 className="text-2xl font-extrabold text-gray-900">Built for people who ask the right questions early</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            {[
              {
                role: "CTO closing enterprise deals",
                icon: Users,
                bg: "bg-violet-50 border-violet-100",
                iconColor: "text-violet-600",
                items: [
                  "Buyer just asked for a SOC 2 report",
                  "Deal is stalled at the security questionnaire stage",
                  "Want to know the actual cost of not having a cert",
                ],
              },
              {
                role: "Engineering lead starting compliance",
                icon: BarChart3,
                bg: "bg-teal-50 border-teal-100",
                iconColor: "text-teal-600",
                items: [
                  "Never done a SOC 2 audit before",
                  "Not sure which controls you'd actually fail",
                  "Want to understand automation potential before picking a tool",
                ],
              },
              {
                role: "Founder preparing for due diligence",
                icon: AlertTriangle,
                bg: "bg-orange-50 border-orange-100",
                iconColor: "text-orange-500",
                items: [
                  "Series A investor asking about security posture",
                  "Acquirer running technical due diligence",
                  "Board wants a compliance risk assessment",
                ],
              },
            ].map((card) => {
              const Icon = card.icon;
              return (
                <div key={card.role} className={`rounded-2xl border p-6 ${card.bg}`}>
                  <div className="flex items-center gap-3 mb-4">
                    <Icon className={`w-5 h-5 ${card.iconColor}`} />
                    <p className="font-extrabold text-gray-900 text-sm leading-snug">{card.role}</p>
                  </div>
                  <ul className="space-y-2">
                    {card.items.map((item) => (
                      <li key={item} className="flex items-start gap-2 text-xs text-gray-600 leading-snug">
                        <CheckCircle2 className="w-3.5 h-3.5 text-teal-500 shrink-0 mt-0.5" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* What happens next */}
      <section className="border-t border-black/5 py-14 bg-white/50">
        <div className="max-w-4xl mx-auto px-6">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">After the tools</p>
            <h2 className="text-2xl font-extrabold text-gray-900">From score to cert — in weeks, not months</h2>
            <p className="text-gray-500 text-sm mt-2 max-w-lg mx-auto">
              TraceLayer takes every gap these tools surface and automates the fix — continuous evidence collection, policy generation, and a live readiness score.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
            {[
              { step: "01", title: "Connect your tools", desc: "Link AWS, GitHub, Slack, Okta and 97+ more in minutes." },
              { step: "02", title: "Evidence flows in", desc: "TraceLayer collects and maps evidence to your controls automatically — every 24h." },
              { step: "03", title: "Close gaps fast", desc: "The dashboard shows exactly which controls need work. Generate policies in one click." },
              { step: "04", title: "Walk into the audit", desc: "Share a live evidence room with your auditor. Most customers finish in under 8 weeks." },
            ].map((item) => (
              <div key={item.step} className="relative">
                <div className="bg-white rounded-2xl border border-black/5 p-5 h-full">
                  <p className="text-2xl font-black text-gray-100 mb-2">{item.step}</p>
                  <p className="font-bold text-gray-900 text-sm mb-1.5">{item.title}</p>
                  <p className="text-xs text-gray-500 leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link
              href="/register"
              className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-bold px-8 py-3.5 rounded-xl transition-colors text-sm shadow-sm"
            >
              Start for free <ArrowRight className="w-4 h-4" />
            </Link>
            <p className="text-xs text-gray-400 mt-3">Free plan · No credit card · Setup in 5 minutes</p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-14 bg-[#f7f1e8]">
        <div className="max-w-2xl mx-auto px-6">
          <h2 className="text-xl font-extrabold text-gray-900 text-center mb-8">Quick answers</h2>
          <div className="space-y-4">
            {[
              {
                q: "Do I need to create an account?",
                a: "No. All three tools run entirely in your browser with no signup, no email, and no credit card.",
              },
              {
                q: "How accurate is the Revenue Impact Calculator?",
                a: "The numbers are based on industry benchmarks from Vanta, Drata, and Ponemon Institute research, then scaled to your specific ARR, pipeline, and compliance status. They're directionally accurate — the goal is to surface the order of magnitude, not provide an auditor-level figure.",
              },
              {
                q: "Is the SOC 2 Gap Scanner the same as a real audit?",
                a: "No — it covers the 10 most commonly failed SOC 2 controls and uses real auditor language, but a formal audit is far more comprehensive. Think of this as a quick triage: know which fires are burning before you call a firefighter.",
              },
              {
                q: "What does TraceLayer do that these tools don't?",
                a: "These tools diagnose. TraceLayer fixes. It connects to your infrastructure and SaaS tools, collects evidence continuously, maps it to SOC 2 / ISO 27001 / GDPR controls, and generates the audit-ready documentation your auditor needs.",
              },
            ].map((item) => (
              <div key={item.q} className="bg-white rounded-xl border border-black/5 p-5">
                <p className="font-bold text-gray-900 text-sm mb-2">{item.q}</p>
                <p className="text-xs text-gray-500 leading-relaxed">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
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
