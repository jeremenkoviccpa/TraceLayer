"use client";

import { Suspense, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";

function CallbackHandler() {
  const params = useSearchParams();

  useEffect(() => {
    const access = params.get("access_token");
    const refresh = params.get("refresh_token");
    const error = params.get("error");

    if (error || !access || !refresh) {
      window.location.href = `/login?error=${error ?? "oauth_failed"}`;
      return;
    }

    api.setTokens(access, refresh);
    const isNewUser = params.get("new_user") === "1";
    const isPartner = params.get("is_partner") === "1";
    // Full page reload so AuthProvider re-initialises with the new tokens
    if (isPartner) {
      window.location.href = "/partner/clients";
    } else {
      window.location.href = isNewUser ? "/onboarding" : "/dashboard";
    }
  }, []); // eslint-disable-line

  return null;
}

const Spinner = () => (
  <div className="min-h-screen flex items-center justify-center bg-white">
    <div className="flex flex-col items-center gap-3">
      <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-sm text-gray-400">Signing you in…</p>
    </div>
  </div>
);

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<Spinner />}>
      <Spinner />
      <CallbackHandler />
    </Suspense>
  );
}
