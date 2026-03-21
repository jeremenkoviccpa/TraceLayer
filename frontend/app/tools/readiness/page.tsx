"use client";

import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, ArrowRight, Zap, CheckCircle2 } from "lucide-react";
import { ComplianceQuiz } from "@/components/compliance-quiz";

export default function ReadinessPage() {
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
        <div className="inline-flex items-center gap-2 bg-violet-100 text-violet-700 text-xs font-semibold px-3 py-1.5 rounded-full mb-5 border border-violet-200">
          <Zap className="w-3.5 h-3.5" />
          Automation · 5 questions · 60 seconds
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-gray-900 mb-4 leading-tight tracking-tight">
          Compliance Readiness Check
        </h1>
        <p className="text-gray-500 text-base max-w-xl mx-auto leading-relaxed mb-6">
          Answer 5 quick questions about your stack. See exactly how much compliance work you can automate today — and what to tackle first.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-500">
          {["No signup required", "Instant results", "Personalised to your stack"].map((t) => (
            <span key={t} className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-500" /> {t}
            </span>
          ))}
        </div>
      </section>

      {/* Tool */}
      <section className="bg-slate-900 py-14 md:py-20 overflow-hidden relative">
        <div className="absolute -top-32 right-0 w-96 h-96 rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.15),transparent)] pointer-events-none" />
        <div className="absolute -bottom-20 -left-10 w-80 h-80 rounded-full bg-[radial-gradient(circle,rgba(16,185,129,0.10),transparent)] pointer-events-none" />
        <div className="max-w-3xl mx-auto px-4 sm:px-6 relative">
          <ComplianceQuiz />
        </div>
      </section>

      {/* What you'll learn strip */}
      <section className="border-y border-black/5 py-10 bg-white/50">
        <div className="max-w-4xl mx-auto px-6">
          <p className="text-center text-xs font-bold text-gray-400 uppercase tracking-widest mb-7">What this check reveals</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {[
              {
                title: "Your automation score",
                desc: "How much of your compliance evidence can be collected automatically based on the tools you already use.",
              },
              {
                title: "Hours you're wasting",
                desc: "An estimate of how many engineering hours per week you're burning on manual compliance tasks.",
              },
              {
                title: "What to tackle first",
                desc: "Prioritised recommendations based on your timeline, framework, and current evidence process.",
              },
            ].map((item) => (
              <div key={item.title} className="flex flex-col gap-2">
                <p className="font-bold text-gray-900 text-sm">{item.title}</p>
                <p className="text-xs text-gray-500 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Other tools */}
      <section className="py-10 bg-[#f7f1e8]">
        <div className="max-w-4xl mx-auto px-6">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-5">Also free</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {[
              { href: "/tools/gap-scanner", label: "SOC 2 Gap Scanner", desc: "10 controls · 2 minutes — see which gaps your auditor would flag", badge: "Audit Risk", badgeColor: "bg-teal-100 text-teal-700" },
              { href: "/tools/revenue-impact", label: "Revenue Impact Calculator", desc: "3 questions · 2 minutes — see the dollar cost of non-compliance", badge: "Revenue", badgeColor: "bg-orange-100 text-orange-700" },
            ].map((t) => (
              <Link key={t.href} href={t.href} className="group flex items-center justify-between bg-white rounded-xl border border-black/5 px-5 py-4 hover:border-teal-200 hover:shadow-sm transition-all">
                <div>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${t.badgeColor}`}>{t.badge}</span>
                  <p className="font-bold text-gray-900 text-sm mt-1">{t.label}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{t.desc}</p>
                </div>
                <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-teal-500 transition-colors shrink-0 ml-4" />
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-teal-600 py-12">
        <div className="max-w-2xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-extrabold text-white mb-3">Ready to automate it?</h2>
          <p className="text-white/75 text-sm mb-6 max-w-md mx-auto leading-relaxed">
            Connect your tools and TraceLayer starts collecting evidence automatically — no spreadsheets, no manual work.
          </p>
          <Link href="/register" className="inline-flex items-center gap-2 bg-white hover:bg-white/90 text-teal-700 font-bold px-8 py-3.5 rounded-xl transition-colors text-sm">
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
            <Link href="/tools" className="hover:text-gray-700 transition-colors">All free tools</Link>
            <Link href="/#pricing" className="hover:text-gray-700 transition-colors">Pricing</Link>
            <Link href="/login" className="hover:text-gray-700 transition-colors">Sign in</Link>
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
