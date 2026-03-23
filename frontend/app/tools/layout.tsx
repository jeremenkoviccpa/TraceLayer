import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Free SOC 2 Compliance Tools — Gap Scanner, Readiness Check & More",
  description:
    "4 free SOC 2 compliance tools for startups. Check your readiness in 60 seconds, scan for audit gaps, calculate your risk exposure, and score your tech stack. No signup required.",
  keywords: [
    "free SOC 2 gap analysis",
    "SOC 2 readiness check free",
    "SOC 2 compliance checker",
    "compliance stack scorer",
    "SOC 2 risk calculator",
    "free compliance tools for startups",
  ],
  openGraph: {
    title: "Free SOC 2 Compliance Tools — Gap Scanner, Readiness Check & More",
    description:
      "4 free SOC 2 compliance tools for startups. Check your readiness, scan for gaps, calculate risk. No signup required.",
  },
  alternates: {
    canonical: "https://tracelayer.it.com/tools",
  },
};

export default function ToolsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
