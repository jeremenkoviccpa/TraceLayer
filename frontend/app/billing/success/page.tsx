"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircle2, Zap, ArrowRight, Loader2 } from "lucide-react";

export default function BillingSuccessPage() {
  const [countdown, setCountdown] = useState(8);

  useEffect(() => {
    const interval = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(interval);
          window.location.href = "/dashboard";
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm max-w-md w-full p-8 text-center">
        {/* Icon */}
        <div className="flex justify-center mb-5">
          <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center">
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          </div>
        </div>

        {/* Heading */}
        <h1 className="text-2xl font-bold text-gray-900 mb-2">You&apos;re on Growth!</h1>
        <p className="text-gray-500 text-sm mb-6">
          Your subscription is now active. Unlimited integrations, AI Compliance Advisor, and all frameworks are unlocked.
        </p>

        {/* Feature list */}
        <div className="bg-gradient-to-br from-teal-50 to-emerald-50 rounded-xl p-4 mb-6 text-left space-y-2">
          {[
            "Unlimited integrations",
            "AI Compliance Advisor",
            "SOC 2, ISO 27001 & GDPR",
            "Priority support",
          ].map((f) => (
            <div key={f} className="flex items-center gap-2 text-sm text-teal-800">
              <Zap className="w-4 h-4 text-teal-600 shrink-0" />
              {f}
            </div>
          ))}
        </div>

        {/* CTA */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 bg-[var(--accent)] hover:opacity-90 text-white font-medium text-sm px-6 py-3 rounded-lg transition-opacity w-full justify-center"
        >
          Go to Dashboard
          <ArrowRight className="w-4 h-4" />
        </Link>

        {/* Auto-redirect notice */}
        <p className="text-xs text-gray-400 mt-4 flex items-center justify-center gap-1.5">
          <Loader2 className="w-3 h-3 animate-spin" />
          Redirecting in {countdown}s…
        </p>
      </div>
    </div>
  );
}
