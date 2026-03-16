import Link from "next/link";
import type { Metadata } from "next";
import { Shield, Lock, Server, Eye, AlertTriangle, Users, Mail, CheckCircle2 } from "lucide-react";

export const metadata: Metadata = {
  title: "Security – TraceLayer",
  description: "How TraceLayer protects your data: infrastructure, encryption, access control, incident response, and vulnerability disclosure.",
};

function Pill({ label, color = "gray" }: { label: string; color?: "green" | "amber" | "gray" | "brand" }) {
  const cls = {
    green: "bg-emerald-50 text-emerald-700 border-emerald-200",
    amber: "bg-amber-50 text-amber-700 border-amber-200",
    gray: "bg-gray-50 text-gray-600 border-gray-200",
    brand: "bg-brand-50 text-brand-700 border-brand-200",
  }[color];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full border ${cls}`}>
      <CheckCircle2 className="w-3 h-3" />
      {label}
    </span>
  );
}

function Card({ icon: Icon, iconColor, iconBg, title, children }: {
  icon: React.ElementType; iconColor: string; iconBg: string;
  title: string; children: React.ReactNode;
}) {
  return (
    <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-[0_2px_8px_rgba(15,23,42,0.06)]">
      <div className="flex items-start gap-4">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconBg}`}>
          <Icon className={`w-5 h-5 ${iconColor}`} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
          <div className="text-sm text-gray-600 leading-relaxed space-y-2">{children}</div>
        </div>
      </div>
    </div>
  );
}

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <Link href="/" className="font-bold text-gray-900 text-lg">TraceLayer</Link>
          <div className="flex items-center gap-4">
            <Link href="/dpa" className="text-sm text-gray-500 hover:text-gray-700">DPA</Link>
            <Link href="/login" className="text-sm text-brand-600 hover:underline font-semibold">Sign in</Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <div className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 px-6 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <div className="w-16 h-16 bg-brand-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6 ring-1 ring-brand-400/30">
            <Shield className="w-8 h-8 text-brand-400" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">Security at TraceLayer</h1>
          <p className="text-white/60 text-base sm:text-lg max-w-2xl mx-auto leading-relaxed">
            We help you prove your security posture to auditors — so ours needs to be rock-solid too.
            Here&apos;s exactly how we protect your data.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-2 mt-8">
            <Pill label="TLS 1.2+ in transit" color="green" />
            <Pill label="AES-256 at rest" color="green" />
            <Pill label="MFA enforced" color="green" />
            <Pill label="SOC 2 Type II (in progress)" color="brand" />
            <Pill label="GDPR compliant" color="brand" />
          </div>
        </div>
      </div>

      <main className="max-w-5xl mx-auto px-6 py-14 space-y-4">

        {/* Quick summary bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: "Uptime SLA", value: "99.9%", sub: "Monthly" },
            { label: "Breach notification", value: "72 h", sub: "GDPR requirement" },
            { label: "Patch SLA (critical)", value: "24 h", sub: "CVE response" },
            { label: "Audit log retention", value: "2 years", sub: "Append-only" },
          ].map((s) => (
            <div key={s.label} className="bg-white border border-gray-100 rounded-2xl p-4 text-center shadow-sm">
              <p className="text-2xl font-bold text-gray-900">{s.value}</p>
              <p className="text-xs font-semibold text-gray-700 mt-0.5">{s.label}</p>
              <p className="text-[11px] text-gray-400 mt-0.5">{s.sub}</p>
            </div>
          ))}
        </div>

        <Card icon={Server} iconColor="text-brand-600" iconBg="bg-brand-50" title="Infrastructure & Hosting">
          <p>
            TraceLayer runs on <strong>Railway</strong> (API) and <strong>Vercel</strong> (frontend),
            both hosted on AWS infrastructure. Data is stored in <strong>Supabase PostgreSQL</strong>
            (AWS us-east-1) with automated daily backups retained for 30 days.
          </p>
          <p>
            All servers are protected by network-level firewalls. Inbound access to the API is
            restricted to HTTPS on port 443. There is no direct database access from the public internet.
          </p>
          <p>
            Application deployments are automated via CI/CD pipelines with mandatory security checks.
            Each production deployment is immutable; rollbacks are available within minutes.
          </p>
        </Card>

        <Card icon={Lock} iconColor="text-emerald-600" iconBg="bg-emerald-50" title="Encryption">
          <p>
            <strong>In transit:</strong> All traffic between clients and TraceLayer servers is encrypted
            using <strong>TLS 1.2 or higher</strong>. HTTP connections are automatically redirected to
            HTTPS. HSTS is enforced in production.
          </p>
          <p>
            <strong>At rest:</strong> Database volumes and object storage (evidence files, reports) are
            encrypted at rest using <strong>AES-256</strong> via the underlying cloud provider.
          </p>
          <p>
            <strong>Credentials:</strong> Integration credentials (API keys, tokens) are encrypted
            with <strong>Fernet symmetric encryption</strong> before being stored. The encryption key
            is stored separately from the database and rotated periodically. User passwords are hashed
            with <strong>bcrypt</strong> and never stored in plaintext.
          </p>
        </Card>

        <Card icon={Users} iconColor="text-purple-600" iconBg="bg-purple-50" title="Access Control">
          <p>
            <strong>Multi-factor authentication</strong> is enforced for all TraceLayer production systems.
            Access is granted on a <strong>least-privilege basis</strong> — engineers only access
            the systems required for their role.
          </p>
          <p>
            Customer data is strictly isolated by company. Our multi-tenant architecture ensures one
            customer&apos;s data can never be accessed by another, enforced at both the application layer
            (JWT claims + row-level checks) and the database layer.
          </p>
          <p>
            Access to production databases requires VPN and is limited to a small team of senior engineers.
            All access is logged and reviewed quarterly.
          </p>
        </Card>

        <Card icon={Eye} iconColor="text-blue-600" iconBg="bg-blue-50" title="Audit Logging & Monitoring">
          <p>
            All material user actions — logins, integration connections, data exports, permission changes,
            and admin operations — are written to an <strong>append-only audit log</strong> retained for
            2 years. Customers can access their own audit log from the TraceLayer dashboard.
          </p>
          <p>
            Infrastructure metrics and API errors are monitored 24/7 via <strong>Sentry</strong> and
            Railway&apos;s observability tooling. Anomaly alerts are routed to our on-call rotation.
            Error events are scrubbed of PII before being sent to monitoring providers.
          </p>
        </Card>

        <Card icon={AlertTriangle} iconColor="text-amber-600" iconBg="bg-amber-50" title="Incident Response">
          <p>
            In the event of a confirmed personal data breach, TraceLayer will:
          </p>
          <ul className="list-disc pl-5 space-y-1">
            <li>Notify affected customers <strong>within 72 hours</strong> of becoming aware of the breach, meeting GDPR Article 33 requirements</li>
            <li>Provide a written incident report detailing the nature of the breach, data affected, likely consequences, and remediation steps taken</li>
            <li>Cooperate with supervisory authorities and customers during any investigation</li>
          </ul>
          <p>
            All incidents are tracked in a private incident register with root-cause analysis and
            follow-up actions documented.
          </p>
        </Card>

        <Card icon={Shield} iconColor="text-red-600" iconBg="bg-red-50" title="Vulnerability Management">
          <p>
            <strong>Dependency scanning:</strong> All backend and frontend dependencies are monitored
            for known CVEs using automated tooling. Critical vulnerabilities are patched within 24 hours;
            high-severity within 7 days.
          </p>
          <p>
            <strong>Penetration testing:</strong> TraceLayer conducts annual third-party penetration tests.
            Findings are triaged by severity and remediated according to our patch SLAs.
          </p>
          <p>
            <strong>OWASP Top 10:</strong> Code reviews include security checks for injection, broken
            authentication, XSS, insecure deserialization, and other OWASP Top 10 risks.
          </p>
        </Card>

        <Card icon={Users} iconColor="text-slate-600" iconBg="bg-slate-50" title="Employee & Organisational Security">
          <p>
            All employees and contractors with access to production systems undergo background checks
            and sign confidentiality agreements before their first day. Security awareness training
            is conducted annually and upon onboarding.
          </p>
          <p>
            Access is revoked immediately upon offboarding. We maintain a clear acceptable-use policy
            and enforce device management (screen lock, disk encryption) on all devices used to access
            production systems.
          </p>
        </Card>

        {/* Compliance roadmap */}
        <div className="bg-white border border-gray-100 rounded-2xl p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Compliance Roadmap</h3>
          <div className="space-y-3">
            {[
              { label: "GDPR — Data Processing Agreement available", status: "done" },
              { label: "SOC 2 Type I audit — Q3 2026", status: "in-progress" },
              { label: "SOC 2 Type II audit — Q1 2027", status: "planned" },
              { label: "ISO 27001 certification — 2027", status: "planned" },
            ].map(({ label, status }) => (
              <div key={label} className="flex items-center gap-3">
                <div className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                  status === "done" ? "bg-emerald-500" :
                  status === "in-progress" ? "bg-amber-400" : "bg-gray-200"
                }`} />
                <span className="text-sm text-gray-700">{label}</span>
                {status === "in-progress" && (
                  <span className="text-[10px] font-bold uppercase tracking-wide text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-md ml-auto">
                    In progress
                  </span>
                )}
                {status === "done" && (
                  <span className="text-[10px] font-bold uppercase tracking-wide text-emerald-600 bg-emerald-50 px-1.5 py-0.5 rounded-md ml-auto">
                    Available
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Contact */}
        <div className="bg-gradient-to-br from-brand-600 to-brand-700 rounded-2xl p-8 text-white text-center">
          <Mail className="w-8 h-8 text-white/60 mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Security questions or vulnerability reports?</h3>
          <p className="text-white/70 text-sm mb-6 max-w-md mx-auto">
            If you&apos;ve found a security issue or have questions about our security posture,
            please contact our security team directly. We respond to all reports within 48 hours.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <a
              href="mailto:security@tracelayer.it.com"
              className="bg-white text-brand-700 font-semibold text-sm px-5 py-2.5 rounded-xl hover:bg-white/90 transition-colors"
            >
              security@tracelayer.it.com
            </a>
            <Link
              href="/dpa"
              className="text-white/80 hover:text-white text-sm font-medium border border-white/20 px-5 py-2.5 rounded-xl hover:border-white/40 transition-colors"
            >
              View DPA →
            </Link>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-200 bg-white py-8 px-6 text-center mt-8">
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-400">
          <Link href="/" className="hover:text-gray-600">TraceLayer</Link>
          <Link href="/privacy" className="hover:text-gray-600">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-gray-600">Terms of Service</Link>
          <Link href="/dpa" className="hover:text-gray-600">DPA</Link>
          <a href="mailto:security@tracelayer.it.com" className="hover:text-gray-600">security@tracelayer.it.com</a>
        </div>
      </footer>
    </div>
  );
}
