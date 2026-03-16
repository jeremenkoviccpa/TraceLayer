"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { PartnerClient } from "@/lib/types";
import { CheckCircle2, Loader2, AlertCircle, ArrowRight } from "lucide-react";
import Link from "next/link";

export default function PartnerClientSuccessPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<"polling" | "ready" | "timeout" | "error">("polling");
  const [client, setClient] = useState<PartnerClient | null>(null);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const attemptsRef = useRef(0);
  const MAX_ATTEMPTS = 20; // 20 × 3s = 60s

  // The client_name is passed as a query param from the checkout redirect
  const clientName = searchParams.get("client_name") ?? "";

  useEffect(() => {
    const poll = async () => {
      attemptsRef.current += 1;
      if (attemptsRef.current > MAX_ATTEMPTS) {
        clearInterval(pollRef.current!);
        setStatus("timeout");
        return;
      }

      try {
        const clients = await api.getPartnerClients();
        // Find the newly created client by matching name (case-insensitive)
        const found = clients.find(
          (c) => c.name.toLowerCase() === clientName.toLowerCase()
        ) ?? (clients.length > 0 ? clients[clients.length - 1] : null);

        if (found) {
          clearInterval(pollRef.current!);
          setClient(found);
          setStatus("ready");
        }
      } catch (err: unknown) {
        clearInterval(pollRef.current!);
        setError(err instanceof Error ? err.message : "Failed to verify payment");
        setStatus("error");
      }
    };

    // Start immediately, then poll every 3s
    poll();
    pollRef.current = setInterval(poll, 3000);
    return () => clearInterval(pollRef.current!);
  }, [clientName]);

  if (status === "polling") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-sm mx-auto">
          <div className="w-16 h-16 rounded-full bg-brand-50 flex items-center justify-center mx-auto mb-5">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Setting up workspace…</h1>
          <p className="text-sm text-gray-500">
            We&apos;re provisioning the client workspace. This usually takes a few seconds.
          </p>
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-sm mx-auto">
          <div className="w-16 h-16 rounded-full bg-red-50 flex items-center justify-center mx-auto mb-5">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h1>
          <p className="text-sm text-gray-500 mb-6">{error}</p>
          <Link href="/partner/clients" className="btn-primary mx-auto">
            Back to clients
          </Link>
        </div>
      </div>
    );
  }

  if (status === "timeout") {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="text-center max-w-sm mx-auto">
          <div className="w-16 h-16 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-5">
            <AlertCircle className="w-8 h-8 text-amber-500" />
          </div>
          <h1 className="text-xl font-bold text-gray-900 mb-2">Taking longer than expected</h1>
          <p className="text-sm text-gray-500 mb-2">
            Your payment was received but the workspace is still provisioning. Please check your client list in a moment.
          </p>
          <p className="text-xs text-gray-400 mb-6">
            If this persists, contact support — your payment has been recorded.
          </p>
          <Link href="/partner/clients" className="btn-primary mx-auto">
            Back to clients
          </Link>
        </div>
      </div>
    );
  }

  // Ready state
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-sm mx-auto">
        <div className="w-16 h-16 rounded-full bg-green-50 flex items-center justify-center mx-auto mb-5">
          <CheckCircle2 className="w-8 h-8 text-green-500" />
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          {client?.name ?? "Client"} is ready!
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          The compliance workspace has been created. You can now manage their data or share their Trust Center link.
        </p>
        <div className="flex flex-col gap-3">
          <button
            onClick={async () => {
              if (!client) return;
              try {
                const switchResponse = await api.switchToClient(client.id);
                api.activateClientContext(switchResponse);
                router.push("/dashboard");
              } catch {
                router.push("/partner/clients");
              }
            }}
            className="btn-primary mx-auto w-full justify-center"
          >
            Manage compliance
            <ArrowRight className="w-4 h-4" />
          </button>
          <Link href="/partner/clients" className="btn-secondary mx-auto w-full justify-center">
            Back to clients
          </Link>
        </div>
      </div>
    </div>
  );
}
