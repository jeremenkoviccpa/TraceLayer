import Link from "next/link";

export const metadata = { title: "Terms of Service – TraceLayer" };

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 px-6 py-4 flex items-center justify-between max-w-4xl mx-auto">
        <Link href="/" className="font-bold text-gray-900 text-lg">TraceLayer</Link>
        <Link href="/login" className="text-sm text-brand-600 hover:underline">Sign in</Link>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12 prose prose-gray">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
        <p className="text-sm text-gray-400 mb-10">Last updated: March 14, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Acceptance of Terms</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            By accessing or using TraceLayer (&quot;Service&quot;), you agree to be bound by these Terms of Service. If you do not agree to these terms, do not use the Service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Description of Service</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            TraceLayer provides a continuous compliance evidence collection and monitoring platform. The Service integrates with third-party tools to automatically gather evidence for compliance frameworks including SOC 2, ISO 27001, and GDPR.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">3. Account Responsibilities</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You must notify us immediately of any unauthorized access. You must not share your account or credentials with third parties.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Acceptable Use</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            You agree not to misuse the Service. Prohibited uses include: attempting to gain unauthorized access, interfering with service operations, using the Service for unlawful purposes, or reverse engineering the platform.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Data and Privacy</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            Your use of the Service is governed by our <Link href="/privacy" className="text-brand-600 hover:underline">Privacy Policy</Link>. You retain ownership of your data. We process your data only to provide the Service.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Billing and Payments</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            Paid plans are billed through LemonSqueezy, our payment processor. Subscriptions renew automatically unless cancelled. Refunds are handled at our discretion. You may cancel your subscription at any time through the billing portal.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Limitation of Liability</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            The Service is provided &quot;as is.&quot; We do not guarantee that the Service will be error-free or uninterrupted. To the maximum extent permitted by law, TraceLayer shall not be liable for indirect, incidental, or consequential damages.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Termination</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            We may suspend or terminate your account if you violate these Terms. You may delete your account at any time from the Settings page. Upon termination, your data will be deleted within 30 days.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Changes to Terms</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            We may update these Terms from time to time. We will notify you of significant changes by email. Continued use of the Service after changes constitutes acceptance of the new Terms.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">10. Contact</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            For questions about these Terms, contact us at legal@tracelayer.io.
          </p>
        </section>
      </main>
    </div>
  );
}
