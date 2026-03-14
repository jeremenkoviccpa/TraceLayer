import Link from "next/link";

export const metadata = { title: "Privacy Policy – TraceLayer" };

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-200 px-6 py-4 flex items-center justify-between max-w-4xl mx-auto">
        <Link href="/" className="font-bold text-gray-900 text-lg">TraceLayer</Link>
        <Link href="/login" className="text-sm text-brand-600 hover:underline">Sign in</Link>
      </header>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-sm text-gray-400 mb-10">Last updated: March 14, 2026</p>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">1. Who We Are</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            TraceLayer (&quot;we&quot;, &quot;us&quot;) operates the TraceLayer compliance platform. This policy explains how we collect, use, and protect your personal data.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">2. Data We Collect</h2>
          <ul className="text-gray-600 text-sm leading-relaxed space-y-2 list-disc list-inside">
            <li><strong>Account data:</strong> Email address, company name, password (hashed)</li>
            <li><strong>Integration credentials:</strong> API keys and tokens you provide — stored encrypted at rest</li>
            <li><strong>Compliance evidence:</strong> Data collected from your connected tools (IAM users, repositories, etc.)</li>
            <li><strong>Usage data:</strong> Audit logs of actions performed in the platform</li>
            <li><strong>Billing data:</strong> Handled by LemonSqueezy — we store only subscription status and IDs</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">3. How We Use Your Data</h2>
          <ul className="text-gray-600 text-sm leading-relaxed space-y-2 list-disc list-inside">
            <li>To provide and operate the Service</li>
            <li>To send transactional emails (verification, password reset, alerts)</li>
            <li>To process payments through LemonSqueezy</li>
            <li>To improve the Service and diagnose errors</li>
          </ul>
          <p className="text-gray-600 text-sm leading-relaxed mt-3">
            We do not sell your data. We do not use your compliance evidence data for any purpose other than providing the Service to you.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">4. Data Storage and Security</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            Your data is stored in the European Union (EU) region. Integration credentials are encrypted at rest using AES-256. We use HTTPS for all data in transit. Access to production data is restricted to authorised personnel only.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">5. Your GDPR Rights</h2>
          <p className="text-gray-600 text-sm leading-relaxed mb-3">
            If you are in the EU/EEA, you have the following rights:
          </p>
          <ul className="text-gray-600 text-sm leading-relaxed space-y-2 list-disc list-inside">
            <li><strong>Access:</strong> Export all your data from Settings → Account → Export Data</li>
            <li><strong>Erasure:</strong> Delete your account and all data from Settings → Account → Delete Account</li>
            <li><strong>Portability:</strong> Your data export is provided in machine-readable JSON format</li>
            <li><strong>Rectification:</strong> Update your data from the Settings page</li>
            <li><strong>Objection:</strong> Contact us at privacy@tracelayer.io</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">6. Cookies</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            We use only essential cookies — specifically, tokens stored in localStorage to keep you signed in. We do not use advertising or tracking cookies. We do not use Google Analytics or similar tracking services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">7. Third-Party Services</h2>
          <ul className="text-gray-600 text-sm leading-relaxed space-y-1 list-disc list-inside">
            <li><strong>LemonSqueezy</strong> — payment processing (<Link href="https://www.lemonsqueezy.com/privacy" className="text-brand-600 hover:underline" target="_blank">their privacy policy</Link>)</li>
            <li><strong>Resend</strong> — transactional email delivery</li>
            <li><strong>Sentry</strong> — error monitoring (anonymised stack traces only)</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-3">8. Data Retention</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            We retain your data for as long as your account is active. After account deletion, all personal data is permanently deleted within 30 days. Anonymised aggregate statistics may be retained indefinitely.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-gray-900 mb-3">9. Contact</h2>
          <p className="text-gray-600 text-sm leading-relaxed">
            For privacy questions or to exercise your rights, contact us at{" "}
            <a href="mailto:privacy@tracelayer.io" className="text-brand-600 hover:underline">privacy@tracelayer.io</a>.
          </p>
        </section>
      </main>
    </div>
  );
}
