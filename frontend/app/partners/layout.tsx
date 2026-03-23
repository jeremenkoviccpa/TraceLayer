import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Partner Program — Auditors, Consultants & Pen Test Firms",
  description:
    "Join the TraceLayer partner program. Auditors receive pre-organized SOC 2 customers. Consultants manage client compliance from one login. Pen test firms get qualified referrals at exactly the right moment.",
  keywords: [
    "SOC 2 auditor partner program",
    "compliance consultant partner",
    "vCISO partner program",
    "SOC 2 audit partner",
    "pen test referral program",
    "compliance software partner",
  ],
  openGraph: {
    title: "TraceLayer Partner Program — Auditors, Consultants & Pen Test Firms",
    description:
      "Auditors get pre-organized customers. Consultants manage all clients from one login. Pen test firms get warm referrals at the right moment.",
  },
  alternates: {
    canonical: "https://tracelayer.it.com/partners",
  },
};

export default function PartnersLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
