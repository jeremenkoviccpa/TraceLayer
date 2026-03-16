import Link from "next/link";
import Image from "next/image";
import type { Metadata } from "next";
import { Users, CheckCircle2, ArrowRight, Building2, Globe, Shield } from "lucide-react";

export const metadata: Metadata = {
  title: "Partner Program – TraceLayer",
  description: "Join the TraceLayer Partner Program. Manage SOC 2 and ISO 27001 compliance for your clients as an agency, consultancy, or MSP.",
};

const BENEFITS = [
  {
    icon: Building2,
    title: "Your own partner dashboard",
    body: "Manage all your clients from one place. Add a new workspace, switch into any client's environment, and manage their compliance — all in a single login.",
  },
  {
    icon: Globe,
    title: "Branded Trust Center per client",
    body: "Each client gets a public Trust Center URL showing their live compliance status. Share it with their auditors, prospects, or board — it updates in real-time.",
  },
  {
    icon: Shield,
    title: "Full compliance stack included",
    body: "SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS — every framework, AI Audit Package PDF generation, evidence collection from 18+ integrations.",
  },
  {
    icon: Users,
    title: "Simple per-client pricing",
    body: "Flat $99 per client workspace, billed once. No monthly subscriptions for client seats. You control the billing relationship with your clients.",
  },
];

const HOW_IT_WORKS = [
  { step: "1", title: "Create your partner account", body: "Register as a Partner / Agency. You get a dedicated partner dashboard immediately." },
  { step: "2", title: "Add a client workspace", body: "Click 'Add client', enter the company name, and pay $99. The workspace is provisioned instantly." },
  { step: "3", title: "Connect their tools", body: "Switch into the client's dashboard and connect AWS, GitHub, Slack, and other integrations in minutes." },
  { step: "4", title: "Share the Trust Center", body: "Hand over a branded Trust Center link. TraceLayer keeps their compliance score current automatically." },
];

export default function PartnersPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Nav */}
      <header className="border-b border-gray-100 px-6 py-4 sticky top-0 z-10 bg-white/80 backdrop-blur">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <Image src="/logo-icon.png" alt="TraceLayer" width={28} height={28} className="rounded-lg" />
            <span className="font-bold text-gray-900">TraceLayer</span>
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/partner-login" className="text-sm text-gray-500 hover:text-gray-700">Partner sign in</Link>
            <Link href="/register?type=partner" className="text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 px-4 py-2 rounded-lg transition-colors">
              Become a partner
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
            Compliance automation<br className="hidden sm:block" /> for your whole client roster
          </h1>
          <p className="text-white/60 text-lg max-w-2xl mx-auto leading-relaxed mb-10">
            Add TraceLayer to your service offering. Manage SOC 2, ISO 27001, GDPR, and HIPAA
            compliance for every client from a single partner dashboard.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register?type=partner"
              className="flex items-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-semibold px-7 py-3.5 rounded-xl text-base transition-colors shadow-lg shadow-brand-950/50"
            >
              Join the partner program <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              href="/partner-login"
              className="text-sm text-white/60 hover:text-white/80 transition-colors"
            >
              Already a partner? Sign in →
            </Link>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 mt-10 text-xs text-white/40">
            {["$99 per client workspace", "No monthly seat fees", "All frameworks included", "Cancel any time"].map((f) => (
              <span key={f} className="flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-brand-400" /> {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Who it's for */}
      <section className="px-6 py-16 max-w-5xl mx-auto">
        <p className="text-center text-xs font-bold uppercase tracking-widest text-gray-400 mb-10">Built for</p>
        <div className="grid sm:grid-cols-3 gap-6 text-center">
          {[
            { label: "Security consultancies", desc: "Add ongoing compliance monitoring to your retainer. Reduce manual evidence work by 80%." },
            { label: "MSPs & IT providers", desc: "Bundle compliance as a premium service tier. Differentiate from commodity IT support." },
            { label: "Accounting & audit firms", desc: "Pre-audit evidence collection included. Walk into engagements with evidence already gathered." },
          ].map(({ label, desc }) => (
            <div key={label} className="bg-gray-50 rounded-2xl p-6 border border-gray-100">
              <p className="font-semibold text-gray-900 mb-2">{label}</p>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Benefits */}
      <section className="px-6 py-16 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">Everything in the partner dashboard</h2>
          <div className="grid sm:grid-cols-2 gap-6">
            {BENEFITS.map(({ icon: Icon, title, body }) => (
              <div key={title} className="bg-white rounded-2xl border border-gray-100 p-6 shadow-sm">
                <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="w-5 h-5 text-brand-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="px-6 py-16 max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">How it works</h2>
        <div className="space-y-6">
          {HOW_IT_WORKS.map(({ step, title, body }) => (
            <div key={step} className="flex gap-5">
              <div className="w-9 h-9 bg-brand-600 text-white rounded-xl flex items-center justify-center font-bold text-sm shrink-0 mt-0.5">
                {step}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing */}
      <section className="px-6 py-16 bg-slate-900">
        <div className="max-w-lg mx-auto text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">Pricing</p>
          <h2 className="text-3xl font-bold text-white mb-4">Simple, transparent pricing</h2>
          <p className="text-white/60 text-sm leading-relaxed mb-8">
            Your partner account is free. You pay $99 per client workspace you provision — once, not monthly.
            Bill your clients however you like.
          </p>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-8 text-left mb-6">
            <div className="flex items-baseline gap-2 mb-1">
              <span className="text-4xl font-black text-white">$99</span>
              <span className="text-white/40 text-sm">per client workspace</span>
            </div>
            <p className="text-white/40 text-xs mb-6">One-time. Includes everything.</p>
            <ul className="space-y-2.5">
              {[
                "All compliance frameworks (SOC 2, ISO 27001, GDPR, HIPAA, PCI DSS)",
                "18+ integrations (AWS, GitHub, Slack, Google Workspace…)",
                "AI Audit Package PDF generation",
                "Branded Trust Center link",
                "Weekly compliance briefing emails to client admins",
                "Unlimited team members per workspace",
              ].map((f) => (
                <li key={f} className="flex items-start gap-2.5 text-sm text-white/70">
                  <CheckCircle2 className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
                  {f}
                </li>
              ))}
            </ul>
          </div>
          <Link
            href="/register?type=partner"
            className="w-full flex items-center justify-center gap-2 bg-brand-500 hover:bg-brand-400 text-white font-bold py-3.5 rounded-xl transition-colors text-base"
          >
            Get started free <ArrowRight className="w-4 h-4" />
          </Link>
          <p className="text-white/30 text-xs mt-4">Partner account is free · No credit card until you add a client</p>
        </div>
      </section>

      {/* Directory placeholder */}
      <section className="px-6 py-16 max-w-5xl mx-auto">
        <div className="bg-brand-50 border border-brand-100 rounded-2xl p-8 text-center">
          <Users className="w-10 h-10 text-brand-400 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Partner directory — coming soon</h2>
          <p className="text-sm text-gray-500 max-w-md mx-auto leading-relaxed mb-6">
            We&apos;re building a public directory of certified TraceLayer partners. Verified partners will
            get a profile page and referrals from companies looking for compliance help.
          </p>
          <a
            href="mailto:partners@tracelayer.it.com"
            className="inline-flex items-center gap-2 text-sm font-semibold text-brand-600 hover:text-brand-700"
          >
            Email us to reserve your spot <ArrowRight className="w-3.5 h-3.5" />
          </a>
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
