import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Free Compliance Tools — SOC 2, DPDP Act, CERT-In Gap Scanner & More",
  description:
    "4 free compliance tools for startups. Scan gaps for SOC 2, DPDP Act 2023, and CERT-In Directions 2022. Check readiness, calculate risk exposure, and score your tech stack. No signup required.",
  keywords: [
    "free SOC 2 gap analysis",
    "SOC 2 readiness check free",
    "SOC 2 compliance checker",
    "DPDP Act gap scanner",
    "DPDP Act compliance checker free",
    "CERT-In compliance checker",
    "India compliance tools free",
    "compliance stack scorer",
    "SOC 2 risk calculator",
    "DPDP Act risk calculator",
    "free compliance tools for startups",
  ],
  openGraph: {
    title: "Free Compliance Tools — SOC 2, DPDP Act, CERT-In Gap Scanner & More",
    description:
      "4 free compliance tools for startups — SOC 2, DPDP Act 2023 & CERT-In. Check readiness, scan for gaps, calculate risk. No signup required.",
  },
  alternates: {
    canonical: "https://tracelayer.it.com/tools",
  },
};

export default function ToolsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
