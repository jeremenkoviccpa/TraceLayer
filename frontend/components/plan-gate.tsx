"use client";

import { useRouter } from "next/navigation";
import { Lock, Zap } from "lucide-react";
import { usePlan } from "@/hooks/usePlan";

interface PlanGateProps {
  children: React.ReactNode;
  /** Label shown in the upgrade prompt */
  feature?: string;
  /** "blur" = children visible but blurred + overlay. "hide" = children replaced entirely. "inline" = just show the prompt, no children. */
  mode?: "blur" | "hide" | "inline";
}

function UpgradePrompt({ feature, compact }: { feature: string; compact?: boolean }) {
  const router = useRouter();
  if (compact) {
    return (
      <button
        onClick={() => router.push("/settings#billing")}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-amber-700 bg-amber-50 border border-amber-200 hover:bg-amber-100 px-2.5 py-1 rounded-lg transition-colors"
      >
        <Lock className="w-3 h-3" />
        Growth only · Upgrade
      </button>
    );
  }
  return (
    <div className="flex flex-col items-center text-center p-8 max-w-sm mx-auto">
      <div className="w-14 h-14 bg-amber-50 rounded-2xl flex items-center justify-center mb-4 border border-amber-100">
        <Lock className="w-7 h-7 text-amber-500" />
      </div>
      <h3 className="font-semibold text-gray-900 text-base mb-2">{feature}</h3>
      <p className="text-sm text-gray-500 mb-5 leading-relaxed">
        Upgrade to Growth to unlock AI-powered features, PDF reports, unlimited integrations, and more.
      </p>
      <button
        onClick={() => router.push("/settings#billing")}
        className="flex items-center gap-2 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm px-5 py-2.5 rounded-xl transition-colors shadow-sm"
      >
        <Zap className="w-4 h-4" /> Upgrade to Growth — $49/mo
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

  // While loading, render children normally (avoids flicker for pro users)
  if (loading) return <>{children}</>;

  // Pro users: render as-is
  if (plan === "growth") return <>{children}</>;

  if (mode === "inline") {
    return <UpgradePrompt feature={feature} />;
  }

  if (mode === "hide") {
    return (
      <div className="bg-white rounded-2xl border border-gray-100 shadow-card">
        <UpgradePrompt feature={feature} />
      </div>
    );
  }

  // mode === "blur" (default): show children blurred with overlay
  return (
    <div className="relative rounded-2xl overflow-hidden">
      <div className="select-none pointer-events-none" style={{ filter: "blur(5px)", opacity: 0.35 }}>
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-white/60 backdrop-blur-[2px]">
        <div className="bg-white border border-gray-200 rounded-2xl shadow-card-md p-6 max-w-sm mx-4 w-full">
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
