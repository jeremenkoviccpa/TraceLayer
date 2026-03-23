import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SOC 2 Compliance Blog — Guides for Startup CTOs & Founders",
  description:
    "Practical SOC 2 guides for startup founders and CTOs. Compliance costs, audit checklists, Vanta alternatives, DIY SOC 2 playbooks, and framework comparisons. No fluff.",
  keywords: [
    "SOC 2 blog",
    "SOC 2 compliance guide",
    "SOC 2 for startups",
    "compliance automation blog",
    "startup security compliance",
    "SOC 2 audit guide",
  ],
  openGraph: {
    title: "SOC 2 Compliance Blog — Guides for Startup CTOs & Founders",
    description:
      "Practical SOC 2 compliance guides. Costs, checklists, Vanta alternatives, and DIY playbooks for seed to Series A startups.",
  },
  alternates: {
    canonical: "https://tracelayer.it.com/blog",
  },
};

export default function BlogLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
