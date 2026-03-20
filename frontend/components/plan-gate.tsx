"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Lock, Zap, Sparkles, Loader2 } from "lucide-react";
import { usePlan } from "@/hooks/usePlan";
import { api } from "@/lib/api";
import { openPaddleCheckout } from "@/lib/paddle";

interface PlanGateProps {
  children: React.ReactNode;
  feature?: string;
  mode?: "blur" | "hide" | "inline";
}

function UpgradePrompt({ feature, compact }: { feature: string; compact?: boolean }) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      await openPaddleCheckout(checkout_url);
    } catch {
      // Fall back to settings page if checkout fails
      router.push("/settings#billing");
    } finally {
      setLoading(false);
    }
  };

  if (compact) {
    return (
      <button
        onClick={handleUpgrade}
        disabled={loading}
        className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-lg border border-amber-200/80 bg-gradient-to-r from-amber-50 to-orange-50 text-amber-700 hover:from-amber-100 hover:to-orange-100 hover:border-amber-300 disabled:opacity-60 transition-all duration-150 shadow-sm"
      >
        {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Lock className="w-3 h-3 text-amber-500" />}
        Growth only
        <span className="w-px h-3 bg-amber-200" />
        <span className="text-brand-600 font-bold">Upgrade →</span>
      </button>
    );
  }

  return (
    <div className="flex flex-col items-center text-center py-8 px-7 max-w-xs mx-auto">
      {/* Icon */}
      <div className="relative mb-5">
        <div className="w-14 h-14 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl flex items-center justify-center border border-amber-100 shadow-sm shadow-amber-100">
          <Lock className="w-6 h-6 text-amber-500" />
        </div>
        <div className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-gradient-to-br from-brand-500 to-teal-500 flex items-center justify-center shadow-md">
          <Sparkles className="w-2.5 h-2.5 text-white" />
        </div>
      </div>

      {/* Eyebrow */}
      <p className="text-[10px] font-extrabold tracking-widest uppercase text-brand-600 mb-2">
        Growth Plan
      </p>

      {/* Headline */}
      <h3 className="text-[15px] font-bold text-gray-900 mb-2 leading-snug">{feature}</h3>

      {/* Body */}
      <p className="text-xs text-gray-400 leading-relaxed mb-6">
        Unlock AI-powered features, PDF reports, Trust Center, and unlimited integrations.
      </p>

      {/* CTA */}
      <button
        onClick={handleUpgrade}
        disabled={loading}
        className="inline-flex items-center gap-2 bg-gradient-to-r from-brand-600 to-teal-600 hover:from-brand-500 hover:to-teal-500 disabled:opacity-60 text-white font-semibold text-sm px-5 py-2.5 rounded-xl shadow-lg shadow-brand-900/20 hover:shadow-brand-900/30 hover:-translate-y-px active:translate-y-0 transition-all duration-150"
      >
        {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Zap className="w-3.5 h-3.5" />}
        {loading ? "Opening checkout…" : "Upgrade to Growth — $149/mo"}
      </button>
    </div>
  );
}

export function PlanGate({
  children,
  feature = "Growth feature",
  mode = "blur",
}: PlanGateProps) {
  const { plan, loading } = usePlan();

  if (loading) return <>{children}</>;
  if (plan === "growth") return <>{children}</>;

  if (mode === "inline") {
    return <UpgradePrompt feature={feature} />;
  }

  if (mode === "hide") {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm">
        <UpgradePrompt feature={feature} />
      </div>
    );
  }

  // blur mode
  return (
    <div className="relative rounded-2xl overflow-hidden">
      {/* Blurred content */}
      <div
        className="select-none pointer-events-none"
        style={{ filter: "blur(6px)", opacity: 0.28 }}
      >
        {children}
      </div>

      {/* Overlay */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="absolute inset-0 bg-gradient-to-b from-white/50 via-white/80 to-white/50 backdrop-blur-[1px]" />
        <div className="relative bg-white/95 border border-gray-100 rounded-2xl shadow-2xl shadow-black/[0.08] ring-1 ring-black/[0.03]">
          <UpgradePrompt feature={feature} />
        </div>
      </div>
    </div>
  );
}

/** Compact inline badge + button — use inside a row or card header */
export function UpgradeBadge({ feature }: { feature: string }) {
  const { plan, loading } = usePlan();
  if (loading || plan === "growth") return null;
  return <UpgradePrompt feature={feature} compact />;
}

/** Returns a function that opens Stripe checkout (falls back to settings#billing). */
export function useUpgrade() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const trigger = async () => {
    setLoading(true);
    try {
      const { checkout_url } = await api.createCheckout();
      await openPaddleCheckout(checkout_url);
    } catch {
      router.push("/settings#billing");
    } finally {
      setLoading(false);
    }
  };
  return { trigger, loading };
}
