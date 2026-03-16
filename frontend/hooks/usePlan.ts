import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

type Plan = "free" | "growth";

const CACHE_KEY = "billing_plan";
const CACHE_AT_KEY = "billing_plan_at";
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Internal admin account always has full Growth access
const INTERNAL_ADMIN = "admin@tracelayer.it.com";

export function usePlan(): { plan: Plan; loading: boolean; isPro: boolean } {
  const { user } = useAuth();
  const [plan, setPlan] = useState<Plan>("free");
  const [loading, setLoading] = useState(true);

  const isInternalAdmin = user?.email === INTERNAL_ADMIN;

  useEffect(() => {
    if (isInternalAdmin) { setLoading(false); return; }
    if (typeof window === "undefined") return;

    const cached = sessionStorage.getItem(CACHE_KEY);
    const cachedAt = Number(sessionStorage.getItem(CACHE_AT_KEY) || 0);

    if (cached && Date.now() - cachedAt < CACHE_TTL) {
      setPlan(cached as Plan);
      setLoading(false);
      return;
    }

    api
      .getSubscription()
      .then((billing) => {
        const p = (billing.plan === "growth" ? "growth" : "free") as Plan;
        setPlan(p);
        sessionStorage.setItem(CACHE_KEY, p);
        sessionStorage.setItem(CACHE_AT_KEY, String(Date.now()));
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [isInternalAdmin]);

  if (isInternalAdmin) return { plan: "growth", loading: false, isPro: true };
  return { plan, loading, isPro: plan === "growth" };
}

/** Call this after a successful upgrade to bust the cached plan. */
export function invalidatePlanCache() {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(CACHE_KEY);
    sessionStorage.removeItem(CACHE_AT_KEY);
  }
}
