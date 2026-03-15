import { useEffect, useState } from "react";
import { api } from "@/lib/api";

type Plan = "free" | "growth";

const CACHE_KEY = "billing_plan";
const CACHE_AT_KEY = "billing_plan_at";
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export function usePlan(): { plan: Plan; loading: boolean; isPro: boolean } {
  const [plan, setPlan] = useState<Plan>("free");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
      .catch(() => {
        // default to free on error — safe, avoids showing locked content to paying users temporarily
      })
      .finally(() => setLoading(false));
  }, []);

  return { plan, loading, isPro: plan === "growth" };
}

/** Call this after a successful upgrade to bust the cached plan. */
export function invalidatePlanCache() {
  if (typeof window !== "undefined") {
    sessionStorage.removeItem(CACHE_KEY);
    sessionStorage.removeItem(CACHE_AT_KEY);
  }
}
