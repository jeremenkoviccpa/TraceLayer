import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Data Processing Agreement – TraceLayer",
  description: "TraceLayer Data Processing Agreement (DPA) for enterprise customers under GDPR Article 28.",
};

function Section({ id, title, children }: { id: string; title: string; children: React.ReactNode }) {
  return (
    <section id={id} className="mb-10 scroll-mt-24">
      <h2 className="text-lg font-bold text-gray-900 mb-3">{title}</h2>
      <div className="text-sm text-gray-600 leading-relaxed space-y-3">{children}</div>
    </section>
  );
}

export default function DpaPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 px-6 py-4 flex items-center justify-between max-w-4xl mx-auto">
        <Link href="/" className="font-bold text-gray-900 text-lg">TraceLayer</Link>
        <Link href="/login" className="text-sm text-brand-600 hover:underline">Sign in</Link>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <div className="mb-10">
          <p className="text-xs font-semibold uppercase tracking-widest text-brand-600 mb-2">Legal</p>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Data Processing Agreement</h1>
          <p className="text-sm text-gray-400">Last updated: March 16, 2026 · Effective for all Growth and Partner plan customers</p>
        </div>

        <div className="bg-brand-50 border border-brand-100 rounded-xl px-5 py-4 mb-10 text-sm text-brand-800 leading-relaxed">
          This Data Processing Agreement (&quot;DPA&quot;) forms part of the TraceLayer Terms of Service between
          TraceLayer (&quot;Processor&quot;) and the customer entity that has accepted those terms (&quot;Controller&quot;).
          It satisfies the requirements of <strong>GDPR Article 28</strong> and applies where TraceLayer
          processes personal data on your behalf.
        </div>

        {/* TOC */}
        <nav className="bg-gray-50 border border-gray-100 rounded-xl p-5 mb-10">
          <p className="text-xs font-bold uppercase tracking-widest text-gray-500 mb-3">Contents</p>
          <ol className="space-y-1.5 text-sm">
            {[
              ["1", "Definitions", "#definitions"],
              ["2", "Subject Matter and Duration", "#subject-matter"],
              ["3", "Nature and Purpose of Processing", "#nature"],
              ["4", "Controller Obligations", "#controller"],
              ["5", "Processor Obligations (TraceLayer)", "#processor"],
              ["6", "Sub-processors", "#sub-processors"],
              ["7", "Security Measures", "#security"],
              ["8", "Data Subject Rights", "#data-subject-rights"],
              ["9", "International Transfers", "#transfers"],
              ["10", "Data Retention and Return", "#retention"],
              ["11", "Liability and Indemnification", "#liability"],
              ["12", "Governing Law", "#governing-law"],
            ].map(([num, label, href]) => (
              <li key={num}>
                <a href={href as string} className="text-brand-600 hover:underline">
                  {num}. {label}
                </a>
              </li>
            ))}
          </ol>
        </nav>

        <Section id="definitions" title="1. Definitions">
          <p>
            <strong>&quot;Controller&quot;</strong> means the entity that determines the purposes and means of processing personal data — i.e., the TraceLayer customer.
          </p>
          <p>
            <strong>&quot;Processor&quot;</strong> means TraceLayer, which processes personal data on behalf of the Controller.
          </p>
          <p>
            <strong>&quot;Personal Data&quot;</strong> means any information relating to an identified or identifiable natural person, as defined by GDPR Article 4(1).
          </p>
          <p>
            <strong>&quot;Processing&quot;</strong> has the meaning given in GDPR Article 4(2) and includes collection, storage, retrieval, use, disclosure, and deletion.
          </p>
          <p>
            <strong>&quot;Sub-processor&quot;</strong> means any third party engaged by TraceLayer to process personal data on behalf of the Controller.
          </p>
          <p>
            <strong>&quot;Standard Contractual Clauses&quot; (SCCs)</strong> means the European Commission&apos;s standard contractual clauses for international data transfers (Commission Decision 2021/914).
          </p>
        </Section>

        <Section id="subject-matter" title="2. Subject Matter and Duration">
          <p>
            TraceLayer processes personal data to provide the compliance evidence collection and monitoring
            services described in the Terms of Service. Processing begins when the Controller connects an
            integration or creates an account and continues for the duration of the subscription, including
            any trial period.
          </p>
          <p>
            Upon termination of the agreement, TraceLayer will delete or return all personal data in
            accordance with Section 10 (Data Retention and Return).
          </p>
        </Section>

        <Section id="nature" title="3. Nature and Purpose of Processing">
          <p>TraceLayer processes personal data for the following purposes:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Providing the platform and its features (authentication, dashboard, evidence collection)</li>
            <li>Collecting compliance evidence from integrated third-party services on behalf of the Controller</li>
            <li>Generating compliance scores, reports, and audit packages</li>
            <li>Sending transactional emails (onboarding, alerts, weekly reports)</li>
            <li>Supporting users and resolving technical issues</li>
          </ul>
          <p>
            <strong>Categories of data subjects:</strong> The Controller&apos;s employees, contractors, and
            system users whose data is surfaced via connected integrations (e.g., GitHub, AWS IAM, Slack,
            Google Workspace).
          </p>
          <p>
            <strong>Categories of personal data:</strong> Email addresses, names, user identifiers, role
            and permission data, login events, IP addresses, and integration-specific metadata (e.g.,
            GitHub commit authors, AWS IAM user records). TraceLayer does not collect sensitive categories
            of data (GDPR Article 9) by design.
          </p>
        </Section>

        <Section id="controller" title="4. Controller Obligations">
          <p>The Controller warrants and represents that it:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Has a lawful basis for processing personal data and for instructing TraceLayer to process on its behalf</li>
            <li>Has provided appropriate notices to data subjects and, where required, obtained valid consent</li>
            <li>Will only provide TraceLayer with the personal data necessary for the stated purposes</li>
            <li>Will inform TraceLayer promptly of any changes to applicable laws or regulatory requirements affecting the processing</li>
            <li>Is responsible for ensuring its instructions to TraceLayer comply with applicable data protection law</li>
          </ul>
        </Section>

        <Section id="processor" title="5. Processor Obligations (TraceLayer)">
          <p>TraceLayer shall:</p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li>Process personal data only on documented instructions from the Controller (including via product configuration), unless required to do so by EU or Member State law</li>
            <li>Ensure that persons authorised to process personal data are subject to appropriate confidentiality obligations</li>
            <li>Implement appropriate technical and organisational security measures as described in Section 7</li>
            <li>Assist the Controller in responding to data subject rights requests (Section 8)</li>
            <li>Notify the Controller without undue delay (and no later than 72 hours) upon becoming aware of a personal data breach affecting Controller data</li>
            <li>Provide all information necessary to demonstrate compliance with this DPA and cooperate with reasonable audits upon 30 days&apos; written notice</li>
            <li>Delete or return all personal data upon termination of the agreement (Section 10)</li>
          </ul>
        </Section>

        <Section id="sub-processors" title="6. Sub-processors">
          <p>
            TraceLayer uses the following approved sub-processors. We will provide at least 30 days&apos;
            notice before adding or replacing any sub-processor. If the Controller objects, it may terminate
            the affected services with a pro-rata refund.
          </p>
          <div className="overflow-x-auto mt-3">
            <table className="w-full text-xs border-collapse">
              <thead>
                <tr className="bg-gray-50 border-y border-gray-200">
                  <th className="text-left px-3 py-2 font-semibold text-gray-700">Sub-processor</th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-700">Purpose</th>
                  <th className="text-left px-3 py-2 font-semibold text-gray-700">Location</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {[
                  ["Supabase / PostgreSQL", "Database hosting and storage", "AWS us-east-1 (USA)"],
                  ["Railway", "Application hosting (API servers)", "AWS us-west (USA)"],
                  ["Vercel", "Frontend hosting and CDN", "Global edge network"],
                  ["Resend", "Transactional email delivery", "USA"],
                  ["Sentry", "Error monitoring (no PII in payloads)", "USA"],
                  ["Groq", "AI report generation (anonymised inputs)", "USA"],
                  ["LemonSqueezy", "Payment processing (billing data only)", "USA"],
                ].map(([name, purpose, location]) => (
                  <tr key={name} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium text-gray-800">{name}</td>
                    <td className="px-3 py-2 text-gray-600">{purpose}</td>
                    <td className="px-3 py-2 text-gray-500">{location}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>

        <Section id="security" title="7. Security Measures">
          <p>
            TraceLayer has implemented the following technical and organisational measures in accordance
            with GDPR Article 32:
          </p>
          <ul className="list-disc pl-5 space-y-1.5">
            <li><strong>Encryption in transit:</strong> All data transmitted between clients and servers uses TLS 1.2 or higher</li>
            <li><strong>Encryption at rest:</strong> Database volumes and object storage are encrypted at rest using AES-256</li>
            <li><strong>Credential security:</strong> Integration credentials are encrypted with Fernet symmetric encryption before storage; password hashes use bcrypt</li>
            <li><strong>Access control:</strong> Production systems require multi-factor authentication; access is granted on a least-privilege basis</li>
            <li><strong>Network security:</strong> API servers run behind firewalls with restricted inbound rules; security headers applied to all responses</li>
            <li><strong>Audit logging:</strong> Material actions (logins, data exports, integration changes) are logged to an append-only audit log</li>
            <li><strong>Vulnerability management:</strong> Dependencies are monitored for CVEs; critical patches applied within 24 hours</li>
          </ul>
          <p>
            For a full description of our security posture, see our{" "}
            <Link href="/security" className="text-brand-600 hover:underline">Security page</Link>.
          </p>
        </Section>

        <Section id="data-subject-rights" title="8. Data Subject Rights">
          <p>
            TraceLayer will, to the extent technically feasible, assist the Controller in fulfilling
            data subject requests under GDPR Articles 15–22 (access, rectification, erasure, restriction,
            portability, objection). The Controller remains responsible for responding to data subjects;
            TraceLayer provides tooling and cooperation at the Controller&apos;s written request.
          </p>
          <p>
            Controllers may request deletion of all personal data associated with their account by
            contacting <a href="mailto:privacy@tracelayer.it.com" className="text-brand-600 hover:underline">privacy@tracelayer.it.com</a>.
            TraceLayer will complete deletion within 30 days.
          </p>
        </Section>

        <Section id="transfers" title="9. International Data Transfers">
          <p>
            TraceLayer&apos;s infrastructure is primarily located in the United States. Transfers of personal
            data from the European Economic Area (EEA) to the United States are made under the{" "}
            <strong>EU Standard Contractual Clauses</strong> (Commission Decision 2021/914, Module 2:
            Controller to Processor). By entering into this DPA, both parties are deemed to have executed
            the SCCs.
          </p>
          <p>
            The SCCs are supplemented by the technical and organisational measures described in Section 7,
            which we assess as providing an essentially equivalent level of protection to that in the EEA.
          </p>
        </Section>

        <Section id="retention" title="10. Data Retention and Return">
          <p>
            TraceLayer retains personal data for the duration of the active subscription plus a 30-day
            grace period to allow data export. After this period, or upon written request from the
            Controller, TraceLayer will permanently delete all personal data from production systems
            within 30 days and from backups within 90 days.
          </p>
          <p>
            Upon request, TraceLayer will provide written confirmation of deletion. The Controller may
            export their data at any time via the platform&apos;s export functionality.
          </p>
        </Section>

        <Section id="liability" title="11. Liability and Indemnification">
          <p>
            Each party shall be liable for damages caused by processing that infringes applicable data
            protection law. TraceLayer&apos;s aggregate liability under this DPA shall not exceed the amounts
            paid by the Controller in the 12 months preceding the claim. The Controller indemnifies
            TraceLayer against third-party claims arising from the Controller&apos;s unlawful instructions or
            failure to comply with applicable law.
          </p>
        </Section>

        <Section id="governing-law" title="12. Governing Law">
          <p>
            This DPA is governed by the law of the jurisdiction specified in the applicable Terms of
            Service. For EU/EEA customers, the applicable EU data protection law shall also apply
            with respect to processing covered by this DPA.
          </p>
          <p>
            For questions about this DPA or to execute a countersigned copy for enterprise contracts,
            contact{" "}
            <a href="mailto:legal@tracelayer.it.com" className="text-brand-600 hover:underline">
              legal@tracelayer.it.com
            </a>.
          </p>
        </Section>
      </main>

      <footer className="border-t border-gray-100 py-8 px-6 text-center">
        <div className="flex flex-wrap items-center justify-center gap-4 text-xs text-gray-400">
          <Link href="/" className="hover:text-gray-600">TraceLayer</Link>
          <Link href="/privacy" className="hover:text-gray-600">Privacy Policy</Link>
          <Link href="/terms" className="hover:text-gray-600">Terms of Service</Link>
          <Link href="/security" className="hover:text-gray-600">Security</Link>
          <a href="mailto:legal@tracelayer.it.com" className="hover:text-gray-600">legal@tracelayer.it.com</a>
        </div>
      </footer>
    </div>
  );
}
