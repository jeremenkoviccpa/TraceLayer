"use client";

import { useEffect, useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMsg, setErrorMsg] = useState("");

  useEffect(() => {
    if (!token) {
      setErrorMsg("No verification token found. Please use the link from your email.");
      setStatus("error");
      return;
    }
    api.verifyEmail(token)
      .then(() => setStatus("success"))
      .catch((err: unknown) => {
        setErrorMsg(err instanceof Error ? err.message : "Verification failed. The link may have expired.");
        setStatus("error");
      });
  }, [token]);

  if (status === "loading") {
    return (
      <div className="text-center py-4">
        <Loader2 className="w-8 h-8 animate-spin text-brand-600 mx-auto mb-3" />
        <p className="text-sm text-gray-500">Verifying your email…</p>
      </div>
    );
  }

  if (status === "success") {
    return (
      <div className="text-center">
        <div className="flex justify-center mb-4">
          <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6 text-emerald-600" />
          </div>
        </div>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Email verified!</h2>
        <p className="text-sm text-gray-500 mb-6">
          Your email address has been confirmed. Your account is fully active.
        </p>
        <Link
          href="/dashboard"
          className="inline-flex items-center justify-center bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm px-6 py-2.5 rounded-lg transition-colors"
        >
          Go to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="text-center">
      <div className="flex justify-center mb-4">
        <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
          <XCircle className="w-6 h-6 text-red-500" />
        </div>
      </div>
      <h2 className="text-lg font-semibold text-gray-900 mb-2">Verification failed</h2>
      <p className="text-sm text-gray-500 mb-6">{errorMsg}</p>
      <Link
        href="/dashboard"
        className="text-sm text-brand-600 hover:underline font-medium"
      >
        Go to Dashboard to request a new link
      </Link>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">TraceLayer</h1>
          <p className="text-gray-500 mt-1">Email verification</p>
        </div>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <Suspense fallback={
            <div className="flex justify-center py-4">
              <Loader2 className="w-6 h-6 animate-spin text-brand-600" />
            </div>
          }>
            <VerifyEmailContent />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
