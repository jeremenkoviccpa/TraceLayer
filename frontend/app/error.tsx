"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
          <div className="text-center max-w-md">
            <div className="flex justify-center mb-4">
              <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center">
                <AlertTriangle className="w-7 h-7 text-red-500" />
              </div>
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h1>
            <p className="text-gray-500 text-sm mb-8">
              An unexpected error occurred. Our team has been notified.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <button
                onClick={reset}
                className="inline-flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors"
              >
                Try again
              </button>
              <Link
                href="/dashboard"
                className="text-sm text-gray-500 hover:text-gray-700 underline underline-offset-2"
              >
                Back to Dashboard
              </Link>
            </div>
            <div className="mt-8 flex items-center justify-center gap-4 text-xs text-gray-400">
              <Link href="/status" className="hover:text-gray-600">System status</Link>
              <a href="mailto:support@tracelayer.it.com" className="hover:text-gray-600">Contact support</a>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
