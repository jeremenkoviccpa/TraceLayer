import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import {
  ArrowRight, CheckCircle2, Users, ShieldCheck, Microscope,
  FileSearch, Building2, ExternalLink,
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
      <header className="border-b border-gray-100 px-6 py-4 sticky top-0 z-10 bg-white/80 backdrop-blur">
        <div className="max-w-5xl mx-auto flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-bold text-gray-900">TraceLayer</span>
          </Link>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
            <Link href="/partner-login" className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 bg-white text-gray-700 font-semibold px-4 py-2.5 text-sm hover:border-gray-300 transition-colors">
              Consultant sign in
            </Link>
            <Link href="/register?type=partner" className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-500 text-white font-semibold px-5 py-2.5 text-sm shadow-lg shadow-brand-950/30 hover:bg-brand-400 transition-colors">
              Join as a consultant <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-brand-500/20 border border-brand-400/30 text-brand-300 text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
            <Users className="w-3.5 h-3.5" />
            TraceLayer Partner Program
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold text-white mb-5 leading-tight">
            One platform.<br className="hidden sm:block" /> Three ways to partner.
          </h1>
          <p className="text-white/60 text-lg max-w-2xl mx-auto leading-relaxed mb-12">
            Whether you manage compliance for clients, audit SOC 2 reports, or run penetration tests —
            TraceLayer integrates into your workflow and sends you the right customers at the right time.
          </p>

          {/* 3 Track Cards */}
          <div className="grid sm:grid-cols-3 gap-4 text-left">
            {[
              {
                icon: Users,
                badge: "Consultants",
                color: "bg-brand-500/20 border-brand-400/30 text-brand-300",
                title: "Manage client compliance at scale",
                desc: "One login. Every client. Switch between client workspaces, share Trust Center links, track compliance across your entire book.",
                cta: "Join as a consultant →",
                href: "/register?type=partner",
                primary: true,
              },
              {
                icon: FileSearch,
                badge: "Auditors",
                color: "bg-violet-500/20 border-violet-400/30 text-violet-300",
                title: "Receive audit-ready customers",
                desc: "When a customer hits 75%+ readiness, TraceLayer surfaces auditor partners. You receive warm leads who arrive organized — reducing your fieldwork time.",
                cta: "Apply to list your firm →",
                href: "mailto:partners@tracelayer.it.com?subject=Auditor partner inquiry",
                primary: false,
              },
              {
                icon: Microscope,
                badge: "Pen Testers",
                color: "bg-orange-500/20 border-orange-400/30 text-orange-300",
                title: "Get qualified pen test referrals",
                desc: "SOC 2 requires an annual pen test. TraceLayer shows your firm when a customer's pen test section is empty or overdue — warm, qualified leads.",
                cta: "Apply to list your firm →",
                href: "mailto:partners@tracelayer.it.com?subject=Pen test partner inquiry",
                primary: false,
              },
            ].map(({ icon: Icon, badge, color, title, desc, cta, href, primary }) => (
              <div key={badge} className={`bg-white/5 border border-white/10 rounded-2xl p-6 flex flex-col gap-4 hover:bg-white/8 transition-colors ${primary ? "ring-1 ring-brand-400/40" : ""}`}>
                <div className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border w-fit ${color}`}>
                  <Icon className="w-3 h-3" />
                  {badge}
                </div>
                <div className="flex-1">
                  <h3 className="text-white font-semibold mb-2 leading-snug">{title}</h3>
                  <p className="text-white/50 text-sm leading-relaxed">{desc}</p>
                </div>
                <a href={href} className="text-sm font-semibold text-white/70 hover:text-white transition-colors flex items-center gap-1">
                  {cta}
                </a>
              </div>
            ))}
          </div>

          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 mt-10 text-xs text-white/40">
            {["$99/client for consultants", "Free listing for auditors & pen testers", "In-product referrals", "No platform fee"].map((f) => (
              <span key={f} className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" /> {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── Track A: Consultants ─────────────────────────────────────────────── */}
      <section className="px-6 py-20 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-brand-50 rounded-xl flex items-center justify-center">
            <Users className="w-4 h-4 text-brand-600" />
          </div>
          <span className="text-xs font-bold uppercase tracking-widest text-brand-600">Track 1 — Consultants & vCISOs</span>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-3">Manage every client from one dashboard</h2>
        <p className="text-gray-500 max-w-2xl mb-10 leading-relaxed">
          The TraceLayer partner portal lets you provision dedicated compliance workspaces for each client,
          switch between them with one click, and share a branded Trust Center with their auditors.
        </p>

        <div className="grid sm:grid-cols-2 gap-5 mb-10">
          {[
            { title: "One login, all clients", body: "Add a workspace for each client ($99 one-time, first 3 free). Switch into any client context in one click." },
            { title: "Branded Trust Center per client", body: "Each client gets a public Trust Center URL showing live compliance status. Share it with auditors or boards." },
            { title: "Full compliance stack", body: "SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS — all frameworks, 120+ integrations, AI Audit Package PDF." },
            { title: "Bill your way", body: "Pay $99 per client workspace — once, not monthly. Bill your clients however you like and keep the margin." },
          ].map(({ title, body }) => (
            <div key={title} className="bg-gray-50 rounded-2xl border border-gray-100 p-6">
              <ShieldCheck className="w-5 h-5 text-brand-500 mb-3" />
              <h3 className="font-semibold text-gray-900 mb-1.5">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <Link href="/register?type=partner" className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-500 text-white font-semibold px-6 py-3 text-sm shadow-lg shadow-brand-950/30 hover:bg-brand-400 transition-colors">
            Start your partner account <ArrowRight className="w-4 h-4" />
          </Link>
          <Link href="/partner-login" className="inline-flex items-center justify-center gap-2 rounded-xl border border-gray-200 text-gray-700 font-semibold px-5 py-3 text-sm hover:border-gray-300 transition-colors">
            Already a partner? Sign in
          </Link>
        </div>
      </section>

      {/* ── Track B: Auditors ────────────────────────────────────────────────── */}
      <section className="bg-slate-950 px-6 py-20">
        <div className="max-w-5xl mx-auto">
          <div className="flex items-center gap-3 mb-3">
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

          <div className="grid sm:grid-cols-3 gap-4 mb-12">
            {[
              { title: "In-product referrals", body: "Your firm appears in our auditor directory when customers reach audit-readiness. They reach out to you directly." },
              { title: "Read-only audit access", body: "Customers can grant you a secure link to their compliance evidence. Review the full control set before engagement starts." },
              { title: "Higher audit margin", body: "Customers arrive organized. Less fieldwork chasing evidence = more audits per month at the same cost." },
            ].map(({ title, body }) => (
              <div key={title} className="bg-white/5 border border-white/10 rounded-2xl p-5">
                <h3 className="font-semibold text-white mb-2">{title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>

          {/* Auditor directory */}
          <h3 className="text-sm font-bold uppercase tracking-widest text-white/40 mb-4">Current auditor partners</h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mb-8">
            {AUDITORS.map(({ name, note, frameworks, featured }) => (
              <div key={name} className={`bg-white/5 border rounded-2xl p-4 ${featured ? "border-violet-400/30" : "border-white/10"}`}>
                <div className="flex items-start justify-between mb-2">
                  <p className="font-semibold text-white text-sm">{name}</p>
                  {featured && (
                    <span className="text-[10px] font-bold uppercase tracking-wider text-violet-400 bg-violet-400/10 px-1.5 py-0.5 rounded-full">Featured</span>
                  )}
                </div>
                <p className="text-xs text-white/40 mb-3">{note}</p>
                <div className="flex flex-wrap gap-1">
                  {frameworks.map((f) => (
                    <span key={f} className="text-[10px] font-medium text-white/50 bg-white/5 border border-white/10 px-1.5 py-0.5 rounded-md">{f}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <a
            href="mailto:partners@tracelayer.it.com?subject=Auditor partner inquiry"
            className="inline-flex items-center gap-2 rounded-xl bg-violet-500 text-white font-semibold px-6 py-3 text-sm hover:bg-violet-400 transition-colors"
          >
            Apply to list your firm <ArrowRight className="w-4 h-4" />
          </a>
        </div>
      </section>

      {/* ── Track C: Pen Testers ─────────────────────────────────────────────── */}
      <section className="px-6 py-20 max-w-5xl mx-auto">
        <div className="flex items-center gap-3 mb-3">
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
            { title: "Remediation visibility", body: "After the test, your findings are tracked in TraceLayer as evidence. Customers return for annual tests because you're embedded in their workflow." },
            { title: "Simple referral model", body: "Flat referral fee per engaged lead, or rev-share. Your Cobalt partner URL is all it takes to get started." },
          ].map(({ title, body }) => (
            <div key={title} className="bg-orange-50 border border-orange-100 rounded-2xl p-5">
              <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
            </div>
          ))}
        </div>

        {/* Pen test directory */}
        <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-4">Current pen test partners</h3>
        <div className="grid sm:grid-cols-2 gap-3 mb-8">
          {PEN_TESTERS.map(({ name, note, specialties, href, featured }) => (
            <div key={name} className={`bg-white border rounded-2xl p-4 hover:border-orange-200 transition-colors ${featured ? "border-orange-200 bg-orange-50/30" : "border-gray-100"}`}>
              <div className="flex items-start justify-between mb-2">
                <div>
                  <p className="font-semibold text-gray-900 text-sm">{name}</p>
                  <p className="text-xs text-gray-400">{note}</p>
                </div>
                {featured && (
                  <span className="text-[10px] font-bold uppercase tracking-wider text-orange-500 bg-orange-50 border border-orange-100 px-1.5 py-0.5 rounded-full">Featured</span>
                )}
              </div>
              <div className="flex items-center justify-between mt-3">
                <div className="flex flex-wrap gap-1">
                  {specialties.map((s) => (
                    <span key={s} className="text-[10px] font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded-md">{s}</span>
                  ))}
                </div>
                <a href={href} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-xs font-semibold text-brand-600 hover:text-brand-700 transition-colors shrink-0 ml-2">
                  Visit <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>

        <a
          href="mailto:partners@tracelayer.it.com?subject=Pen test partner inquiry"
          className="inline-flex items-center gap-2 rounded-xl bg-orange-500 text-white font-semibold px-6 py-3 text-sm hover:bg-orange-400 transition-colors"
        >
          Apply to list your firm <ArrowRight className="w-4 h-4" />
        </a>
      </section>

      {/* Revenue potential callout */}
      <section className="px-6 py-16 bg-brand-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">The partner flywheel</h2>
          <p className="text-white/70 max-w-2xl mx-auto mb-10 leading-relaxed">
            Once the ecosystem is running, partners refer customers, customers get audited, auditors refer the next batch.
            Each relationship compounds. The first 5 partners are the hardest.
          </p>
          <div className="grid sm:grid-cols-3 gap-4 text-left">
            {[
              { n: "$4,500–7,500", label: "per month", note: "Auditor referrals (3–5 audits/mo × $1,500 avg)" },
              { n: "$1,500–3,000", label: "per month", note: "Pen test referrals (2–4 engagements/mo × $750 avg)" },
              { n: "$1,500–3,000", label: "per month", note: "Policy consultant referrals (3–6 × $500 avg)" },
            ].map(({ n, label, note }) => (
              <div key={n} className="bg-white/10 rounded-2xl p-5 border border-white/10">
                <p className="text-3xl font-black text-white">{n}</p>
                <p className="text-sm text-white/60 mb-1">{label}</p>
                <p className="text-xs text-white/40 leading-relaxed">{note}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 py-8 px-6 text-center">
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-400">
          <Link href="/" className="hover:text-gray-600">TraceLayer</Link>
          <Link href="/register" className="hover:text-gray-600">Sign up</Link>
          <Link href="/partner-login" className="hover:text-gray-600">Partner login</Link>
          <Link href="/security" className="hover:text-gray-600">Security</Link>
          <a href="mailto:partners@tracelayer.it.com" className="hover:text-gray-600">partners@tracelayer.it.com</a>
        </div>
      </footer>
    </div>
  );
}
