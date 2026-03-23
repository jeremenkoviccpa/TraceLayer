import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import {
  ArrowRight, CheckCircle2, Users, ShieldCheck, Microscope,
  FileSearch, ExternalLink, Zap,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Partner Program — TraceLayer",
  description:
    "Three ways to partner with TraceLayer: manage client compliance as a consultant, receive audit-ready referrals as a certified auditor, or get qualified pen test leads as a security testing firm.",
  openGraph: {
    title: "TraceLayer Partner Program",
    description:
      "Consultants, auditors, and pen test firms — build a compliance ecosystem that sends customers to you.",
  },
  alternates: { canonical: "https://www.tracelayer.it.com/partners" },
};

const AUDITORS = [
  { name: "Prescient Assurance", note: "Startup-friendly, fast timelines", frameworks: ["SOC 2", "ISO 27001", "HIPAA"], featured: true },
  { name: "Johanson Group", note: "Leading SMB & startup auditor", frameworks: ["SOC 2", "HIPAA", "PCI DSS"], featured: true },
  { name: "A-LIGN", note: "Enterprise-grade, all frameworks", frameworks: ["SOC 2", "ISO 27001", "FedRAMP"], featured: false },
  { name: "BARR Advisory", note: "Boutique CPA, tech-focused", frameworks: ["SOC 2", "ISO 27001", "HIPAA"], featured: false },
  { name: "Schellman", note: "Premium upmarket audits", frameworks: ["SOC 2", "ISO 27001", "FedRAMP"], featured: false },
];

const PEN_TESTERS = [
  { name: "Cobalt", note: "PtaaS — results in days", specialties: ["SOC 2", "Cloud Security", "API"], href: "https://cobalt.io", featured: true },
  { name: "NetSPI", note: "Enterprise-grade methodology", specialties: ["SOC 2", "ISO 27001", "PCI DSS"], href: "https://netspi.com", featured: false },
  { name: "Synack", note: "Crowdsourced red team", specialties: ["SOC 2", "HIPAA", "Cloud Security"], href: "https://synack.com", featured: false },
  { name: "Rapid7", note: "Full-service + vuln mgmt", specialties: ["SOC 2", "ISO 27001", "PCI DSS"], href: "https://rapid7.com", featured: false },
];

export default function PartnersPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="border-b border-gray-100 px-6 py-4 sticky top-0 z-10 bg-white/90 backdrop-blur-md">
        <div className="max-w-5xl mx-auto flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-bold text-gray-900">TraceLayer</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/partner-login" className="text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors hidden sm:block">
              Sign in
            </Link>
            <Link
              href="/register?type=partner"
              className="inline-flex items-center gap-1.5 rounded-xl bg-brand-600 text-white font-semibold px-4 py-2 text-sm shadow-sm shadow-brand-700/20 hover:bg-brand-500 transition-colors"
            >
              Join as a consultant <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-6 pt-20 pb-24 overflow-hidden">
        {/* Decorative glows */}
        <div className="absolute top-1/3 left-1/4 w-[600px] h-[600px] bg-brand-600/12 rounded-full blur-[140px] pointer-events-none" />
        <div className="absolute top-0 right-1/4 w-72 h-72 bg-violet-600/18 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-1/3 w-52 h-52 bg-orange-500/12 rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-4xl mx-auto text-center relative">
          <div className="inline-flex items-center gap-2 bg-brand-500/15 border border-brand-400/25 text-brand-300 text-xs font-semibold px-3.5 py-1.5 rounded-full mb-8">
            <Users className="w-3.5 h-3.5" />
            TraceLayer Partner Program
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white mb-5 leading-[1.1] tracking-tight">
            One platform.<br />
            <span className="text-brand-400">Three ways to partner.</span>
          </h1>
          <p className="text-white/55 text-lg max-w-2xl mx-auto leading-relaxed mb-14">
            Whether you manage compliance for clients, audit SOC 2 reports, or run penetration tests —
            TraceLayer integrates into your workflow and sends you customers at exactly the right moment.
          </p>

          {/* 3 Track Cards */}
          <div className="grid sm:grid-cols-3 gap-4 text-left mb-12">
            {[
              {
                icon: Users,
                badge: "Consultants",
                badgeClass: "bg-brand-500/20 border-brand-400/30 text-brand-300",
                title: "Manage client compliance at scale",
                desc: "One login. Every client. Switch between workspaces, share Trust Centers, track compliance across your entire book.",
                cta: "Join as a consultant →",
                href: "/register?type=partner",
                ring: "ring-1 ring-brand-400/30",
              },
              {
                icon: FileSearch,
                badge: "Auditors",
                badgeClass: "bg-violet-500/20 border-violet-400/30 text-violet-300",
                title: "Receive audit-ready customers",
                desc: "When a customer hits 75%+ readiness, TraceLayer surfaces your firm. They arrive organized — less fieldwork, more audits.",
                cta: "Apply to list your firm →",
                href: "mailto:hello@tracelayer.it.com?subject=Auditor partner inquiry",
                ring: "",
              },
              {
                icon: Microscope,
                badge: "Pen Testers",
                badgeClass: "bg-orange-500/20 border-orange-400/30 text-orange-300",
                title: "Get qualified pen test referrals",
                desc: "SOC 2 requires an annual pen test. TraceLayer shows your firm when a customer's section is empty or overdue.",
                cta: "Apply to list your firm →",
                href: "mailto:hello@tracelayer.it.com?subject=Pen test partner inquiry",
                ring: "",
              },
            ].map(({ icon: Icon, badge, badgeClass, title, desc, cta, href, ring }) => (
              <div
                key={badge}
                className={`group bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col gap-4 hover:bg-white/8 hover:border-white/20 transition-all duration-200 ${ring}`}
              >
                <div className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border w-fit ${badgeClass}`}>
                  <Icon className="w-3 h-3" />
                  {badge}
                </div>
                <div className="flex-1">
                  <h3 className="text-white font-semibold mb-2 leading-snug">{title}</h3>
                  <p className="text-white/50 text-sm leading-relaxed">{desc}</p>
                </div>
                <a
                  href={href}
                  className="text-sm font-semibold text-white/55 group-hover:text-white/90 transition-colors flex items-center gap-1"
                >
                  {cta}
                </a>
              </div>
            ))}
          </div>

          {/* Stats strip */}
          <div className="flex flex-wrap items-center justify-center gap-x-8 gap-y-3 text-xs text-white/35 pt-6 border-t border-white/10">
            {[
              "$99/client for consultants",
              "Free listing for auditors & pen testers",
              "In-product referrals",
              "No platform fee",
            ].map((text) => (
              <span key={text} className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" /> {text}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Track A: Consultants ─────────────────────────────────────────────── */}
      <section id="consultant" className="scroll-mt-16 px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-brand-50 rounded-xl flex items-center justify-center">
              <Users className="w-4 h-4 text-brand-600" />
            </div>
            <span className="text-xs font-bold uppercase tracking-widest text-brand-600">Track 1 — Consultants & vCISOs</span>
          </div>

          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-3">Manage every client from one dashboard</h2>
              <p className="text-gray-500 mb-8 leading-relaxed">
                The TraceLayer partner portal lets you provision dedicated compliance workspaces for each client,
                switch between them with one click, and share a branded Trust Center with their auditors.
              </p>

              <div className="space-y-5 mb-8">
                {[
                  { title: "One login, all clients", body: "Add a workspace per client ($99 once, first 3 free). Switch into any client context in a single click." },
                  { title: "Branded Trust Center per client", body: "Each client gets a public URL showing live compliance status. Share with auditors or boards directly." },
                  { title: "Full compliance stack", body: "SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS — all frameworks, 120+ integrations, AI Audit Package PDF." },
                  { title: "Bill your way", body: "Pay $99 per workspace — once, not monthly. Bill your clients however you like and keep the margin." },
                ].map(({ title, body }) => (
                  <div key={title} className="flex gap-4">
                    <div className="mt-0.5 w-5 h-5 rounded-full bg-brand-50 border border-brand-100 flex items-center justify-center shrink-0">
                      <CheckCircle2 className="w-3 h-3 text-brand-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 text-sm">{title}</p>
                      <p className="text-sm text-gray-500 leading-relaxed mt-0.5">{body}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  href="/register?type=partner"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 text-white font-semibold px-6 py-3 text-sm shadow-lg shadow-brand-700/25 hover:bg-brand-500 transition-colors"
                >
                  Start your partner account <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/partner-login"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 text-gray-600 font-semibold px-5 py-3 text-sm hover:border-gray-300 hover:text-gray-900 transition-colors"
                >
                  Already a partner? Sign in
                </Link>
              </div>
            </div>

            {/* Product preview mockup */}
            <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-100">
                <div>
                  <p className="text-xs font-bold text-gray-900">Partner dashboard</p>
                  <p className="text-[10px] text-gray-400 mt-0.5">3 active client workspaces</p>
                </div>
                <div className="w-7 h-7 rounded-lg bg-brand-100 flex items-center justify-center">
                  <Users className="w-3.5 h-3.5 text-brand-600" />
                </div>
              </div>
              <div className="space-y-2">
                {[
                  { name: "Acme Corp", score: 89, framework: "SOC 2", good: true },
                  { name: "TechFlow Inc", score: 71, framework: "ISO 27001", good: false },
                  { name: "SafeGuard LLC", score: 96, framework: "HIPAA", good: true },
                ].map(({ name, score, framework, good }) => (
                  <div key={name} className="bg-white rounded-xl border border-gray-100 px-4 py-3 flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center text-xs font-bold text-brand-700 shrink-0">
                      {name[0]}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-900 truncate">{name}</p>
                      <p className="text-[10px] text-gray-400">{framework}</p>
                    </div>
                    <span className={`text-sm font-bold ${good ? "text-emerald-600" : "text-amber-600"}`}>{score}%</span>
                    <div className={`w-2 h-2 rounded-full shrink-0 ${good ? "bg-emerald-400" : "bg-amber-400"}`} />
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
                <span className="text-xs text-gray-400">Free workspace usage</span>
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <div className="h-full bg-brand-500 rounded-full" style={{ width: "100%" }} />
                  </div>
                  <span className="text-xs font-semibold text-gray-700">3 / 3</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Track B: Auditors ────────────────────────────────────────────────── */}
      <section className="bg-slate-950 px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-violet-500/20 rounded-xl flex items-center justify-center">
              <FileSearch className="w-4 h-4 text-violet-400" />
            </div>
            <span className="text-xs font-bold uppercase tracking-widest text-violet-400">Track 2 — Auditors</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-3">Customers arrive pre-organized</h2>
          <p className="text-white/50 max-w-2xl mb-10 leading-relaxed">
            When a TraceLayer customer hits 75%+ readiness, we surface our certified auditor directory.
            You receive warm leads who have evidence already collected, controls already mapped — reducing your fieldwork by 30–40%.
          </p>

          {/* How it works mini-flow */}
          <div className="grid sm:grid-cols-3 gap-px bg-white/5 rounded-2xl overflow-hidden mb-12">
            {[
              { step: "01", title: "Customer reaches 75%", body: "TraceLayer shows the auditor directory directly inside the compliance dashboard." },
              { step: "02", title: "Read-only link sent", body: "Customer generates a secure access link — no account needed on your end. Evidence, controls, gaps — all visible." },
              { step: "03", title: "You start organized", body: "Fieldwork begins with controls already mapped. Less chasing evidence, more auditing." },
            ].map(({ step, title, body }) => (
              <div key={step} className="bg-slate-900 p-6">
                <p className="text-4xl font-black text-white/8 mb-3 font-mono">{step}</p>
                <p className="font-semibold text-white text-sm mb-1.5">{title}</p>
                <p className="text-xs text-white/40 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          {/* Auditor directory */}
          <h3 className="text-xs font-bold uppercase tracking-widest text-white/35 mb-4">Current auditor partners</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
            {AUDITORS.map(({ name, note, frameworks, featured }) => (
              <div
                key={name}
                className={`relative rounded-2xl p-4 border transition-colors hover:bg-white/8 ${
                  featured ? "bg-violet-500/5 border-violet-400/30" : "bg-white/5 border-white/10"
                }`}
              >
                {featured && (
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-500 to-violet-400 rounded-t-2xl" />
                )}
                <div className="flex items-start justify-between mb-2">
                  <p className="font-semibold text-white text-sm">{name}</p>
                  {featured && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-violet-300 bg-violet-400/15 px-1.5 py-0.5 rounded-full">
                      Featured
                    </span>
                  )}
                </div>
                <p className="text-xs text-white/40 mb-3">{note}</p>
                <div className="flex flex-wrap gap-1">
                  {frameworks.map((f) => (
                    <span key={f} className="text-[10px] font-medium text-white/50 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded-md">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <a
            href="mailto:hello@tracelayer.it.com?subject=Auditor partner inquiry"
            className="inline-flex items-center gap-2 rounded-xl bg-violet-600 text-white font-semibold px-6 py-3 text-sm hover:bg-violet-500 transition-colors"
          >
            Apply to list your firm <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      {/* ── Track C: Pen Testers ─────────────────────────────────────────────── */}
      <section id="pen-testers" className="scroll-mt-16 px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 bg-orange-50 rounded-xl flex items-center justify-center">
              <Microscope className="w-4 h-4 text-orange-500" />
            </div>
            <span className="text-xs font-bold uppercase tracking-widest text-orange-500">Track 3 — Pen Test Firms</span>
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Get qualified pen test referrals</h2>
          <p className="text-gray-500 max-w-2xl mb-10 leading-relaxed">
            SOC 2 and ISO 27001 require an annual penetration test. When a TraceLayer customer has no pen test on file
            or their last test is approaching 12 months old, we surface our recommended pen test partners.
          </p>

          <div className="grid sm:grid-cols-3 gap-4 mb-12">
            {[
              { title: "Demand-qualified leads", body: "Leads come to you mid-compliance journey — they have a deadline and a reason. No cold outreach needed on your end." },
              { title: "Embedded in their workflow", body: "After the test, your findings are tracked in TraceLayer as evidence. Customers return annually because you're embedded." },
              { title: "Simple referral model", body: "Flat referral fee per engaged lead, or rev-share. Your partner URL is all it takes to get started." },
            ].map(({ title, body }) => (
              <div key={title} className="bg-orange-50 border border-orange-100 rounded-2xl p-5">
                <div className="w-7 h-7 bg-orange-100 rounded-lg flex items-center justify-center mb-3">
                  <Zap className="w-3.5 h-3.5 text-orange-500" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-1.5 text-sm">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          {/* Pen test directory */}
          <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">Current pen test partners</h3>
          <div className="grid sm:grid-cols-2 gap-3 mb-8">
            {PEN_TESTERS.map(({ name, note, specialties, href, featured }) => (
              <div
                key={name}
                className={`group bg-white border rounded-2xl p-4 hover:shadow-md transition-all ${
                  featured ? "border-orange-200 bg-gradient-to-br from-orange-50/60 to-white" : "border-gray-100"
                }`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">{name}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{note}</p>
                  </div>
                  {featured && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-orange-500 bg-orange-50 border border-orange-100 px-1.5 py-0.5 rounded-full">
                      Featured
                    </span>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex flex-wrap gap-1">
                    {specialties.map((s) => (
                      <span key={s} className="text-[10px] font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md">{s}</span>
                    ))}
                  </div>
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors shrink-0 ml-3"
                  >
                    Visit <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>

          <a
            href="mailto:hello@tracelayer.it.com?subject=Pen test partner inquiry"
            className="inline-flex items-center gap-2 rounded-xl bg-orange-500 text-white font-semibold px-6 py-3 text-sm hover:bg-orange-400 transition-colors"
          >
            Apply to list your firm <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      {/* Revenue flywheel */}
      <section className="px-6 py-16 bg-gradient-to-br from-brand-700 to-brand-900">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-brand-200 text-xs font-bold uppercase tracking-widest mb-2">The partner flywheel</p>
          <h2 className="text-3xl font-bold text-white mb-3">Ecosystem revenue potential</h2>
          <p className="text-brand-200/60 max-w-xl mx-auto mb-10 leading-relaxed text-sm">
            Once the ecosystem runs, partners refer customers, customers get audited, auditors refer the next batch.
            Each relationship compounds.
          </p>
          <div className="grid sm:grid-cols-3 gap-4 text-left">
            {[
              { n: "$4,500–7,500", label: "/ month", note: "Auditor referrals (3–5 audits/mo × $1,500 avg)", accent: "bg-violet-500/20 border-violet-400/20" },
              { n: "$1,500–3,000", label: "/ month", note: "Pen test referrals (2–4 engagements/mo × $750 avg)", accent: "bg-orange-500/20 border-orange-400/20" },
              { n: "$1,500–3,000", label: "/ month", note: "Consultant referrals (3–6 engagements × $500 avg)", accent: "bg-brand-400/20 border-brand-300/20" },
            ].map(({ n, label, note, accent }) => (
              <div key={n} className={`${accent} border rounded-2xl p-5`}>
                <p className="text-3xl font-black text-white">{n}</p>
                <p className="text-sm text-white/50 mb-2">{label}</p>
                <p className="text-xs text-white/40 leading-relaxed">{note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Consultant registration CTA */}
      <section className="px-6 py-16 bg-gray-50 border-t border-gray-100">
        <div className="max-w-lg mx-auto text-center">
          <div className="w-12 h-12 bg-brand-50 border border-brand-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
            <ShieldCheck className="w-6 h-6 text-brand-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">Ready to start managing clients?</h2>
          <p className="text-gray-500 text-sm mb-8 leading-relaxed">
            Create your partner account in minutes. Your first 3 client workspaces are free.
            No monthly fees, no platform commissions.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/register?type=partner"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 text-white font-semibold px-6 py-3 text-sm shadow-lg shadow-brand-700/20 hover:bg-brand-500 transition-colors"
            >
              Create your partner account <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/partner-login"
              className="inline-flex items-center justify-center rounded-xl border border-gray-200 text-gray-600 font-semibold px-5 py-3 text-sm hover:border-gray-300 hover:text-gray-900 transition-colors"
            >
              Sign in to existing account
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2">
            <Image src="/logo-icon.png" alt="TraceLayer" width={20} height={20} className="rounded-md" />
            <span className="text-sm font-semibold text-gray-500">TraceLayer</span>
          </Link>
          <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-gray-400">
            <Link href="/" className="hover:text-gray-600 transition-colors">Home</Link>
            <Link href="/register" className="hover:text-gray-600 transition-colors">Sign up</Link>
            <Link href="/partner-login" className="hover:text-gray-600 transition-colors">Partner login</Link>
            <Link href="/security" className="hover:text-gray-600 transition-colors">Security</Link>
            <a href="mailto:hello@tracelayer.it.com" className="hover:text-gray-600 transition-colors">
              hello@tracelayer.it.com
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
