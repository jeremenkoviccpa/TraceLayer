import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

type Plan = "free" | "growth";

const CACHE_KEY = "billing_plan";
const CACHE_AT_KEY = "billing_plan_at";
const CACHE_TTL = 30 * 1000; // 30 seconds

// Internal accounts always have full Growth access
const INTERNAL_ADMINS = ["admin@tracelayer.it.com", "jeremenkovic23@gmail.com"];

export function usePlan(): { plan: Plan; loading: boolean; isPro: boolean } {
  const { user } = useAuth();
  const [plan, setPlan] = useState<Plan>("free");
  const [loading, setLoading] = useState(true);

  const isInternalAdmin = INTERNAL_ADMINS.includes(user?.email ?? "");

  useEffect(() => {
    if (!user) return; // wait for auth to resolve before fetching
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
  }, [user?.id, isInternalAdmin]); // re-run when user resolves (null → real user)

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
