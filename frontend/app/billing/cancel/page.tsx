"use client";

import Link from "next/link";
import { XCircle, ArrowLeft, MessageCircle } from "lucide-react";

export default function BillingCancelPage() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm max-w-md w-full p-8 text-center">
        <div className="flex justify-center mb-5">
          <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
            <XCircle className="w-8 h-8 text-gray-400" />
          </div>
        </div>

        <h1 className="text-2xl font-bold text-gray-900 mb-2">No changes made</h1>
        <p className="text-gray-500 text-sm mb-6">
          You cancelled the checkout — your plan hasn&apos;t changed. You can upgrade any time from Settings.
        </p>

        <div className="flex flex-col gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center gap-2 bg-[var(--accent)] hover:opacity-90 text-white font-medium text-sm px-6 py-3 rounded-lg transition-opacity"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to Dashboard
          </Link>

          <a
            href="mailto:support@tracelayer.it.com"
            className="inline-flex items-center justify-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            <MessageCircle className="w-4 h-4" />
            Questions? Contact support
          </a>
        </div>
      </div>
    </div>
  );
}
