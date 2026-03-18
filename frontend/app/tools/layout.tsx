import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Free SOC 2 Compliance Tools for Startups",
  description:
    "Check your SOC 2 readiness in 60 seconds, scan for compliance gaps, and find out exactly what to fix before your audit. Free — no signup required.",
  openGraph: {
    title: "Free SOC 2 Compliance Tools for Startups | TraceLayer",
    description:
      "Check your SOC 2 readiness in 60 seconds, scan for compliance gaps, and find out exactly what to fix before your audit. Free — no signup required.",
  },
  alternates: {
    canonical: "https://www.tracelayer.it.com/tools",
  },
};

export default function ToolsLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
