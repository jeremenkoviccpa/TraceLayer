import type { Metadata } from "next";
import { Sora } from "next/font/google";
import "./globals.css";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { AuthProvider } from "@/components/auth-provider";
import { CookieConsent } from "@/components/cookie-consent";
import { CrispChat } from "@/components/crisp-chat";
import { PostHogProvider } from "@/components/posthog-provider";

const sora = Sora({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  display: "swap",
  variable: "--font-sora",
});

const BASE_URL = "https://tracelayer.it.com";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "TraceLayer — SOC 2 Compliance Automation for Startups",
    template: "%s | TraceLayer",
  },
  description:
    "TraceLayer automates SOC 2 compliance evidence collection for startups. Connect AWS, GitHub, Okta and 120+ tools — evidence collects every 24h, audit report in one click. Start free, no credit card.",
  keywords: [
    "SOC 2 compliance software",
    "SOC 2 automation for startups",
    "compliance automation tool",
    "ISO 27001 automation",
    "HIPAA compliance software",
    "continuous compliance monitoring",
    "SOC 2 evidence collection",
    "compliance software for startups",
    "SOC 2 readiness tool",
    "GDPR compliance automation",
    "PCI DSS compliance tool",
    "affordable SOC 2 software",
    "Vanta alternative",
    "Drata alternative",
  ],
  authors: [{ name: "TraceLayer", url: BASE_URL }],
  creator: "TraceLayer",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: BASE_URL,
    siteName: "TraceLayer",
    title: "TraceLayer — SOC 2 Compliance Automation for Startups",
    description:
      "Stop losing enterprise deals over SOC 2. Automate evidence collection across GitHub, AWS, Slack & 20+ integrations. Get audit-ready in weeks.",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "TraceLayer — SOC 2 Compliance Automation for Startups" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TraceLayer — SOC 2 Compliance Automation for Startups",
    description:
      "Stop losing enterprise deals over SOC 2. Automate evidence collection across GitHub, AWS, Slack & 20+ integrations. Get audit-ready in weeks.",
    images: ["/opengraph-image"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  icons: {
    icon: "/logo-icon.png",
    apple: "/logo-icon.png",
  },
  alternates: {
    canonical: BASE_URL,
  },
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    name: "TraceLayer",
    url: BASE_URL,
    description:
      "Automated SOC 2 compliance evidence collection and monitoring for startups. Connects to AWS, GitHub, Okta, Slack and 120+ tools.",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    offers: [
      {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
        description: "Free plan — SOC 2 framework, up to 3 integrations",
      },
      {
        "@type": "Offer",
        price: "149",
        priceCurrency: "USD",
        description: "Growth plan — all 7 frameworks, 120+ integrations, AI features, PDF reports",
      },
    ],
    creator: {
      "@type": "Organization",
      name: "TraceLayer",
      url: BASE_URL,
    },
  },
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "TraceLayer",
    url: BASE_URL,
    logo: `${BASE_URL}/logo-icon.png`,
    contactPoint: {
      "@type": "ContactPoint",
      email: "hello@tracelayer.it.com",
      contactType: "customer support",
    },
    sameAs: [],
  },
  {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: [
      {
        "@type": "Question",
        name: "How long does SOC 2 setup take with TraceLayer?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Most teams are collecting evidence within 5 minutes of signup. You paste an API key, TraceLayer connects to your tools, and evidence starts flowing immediately. No agents, no code, no week-long setup.",
        },
      },
      {
        "@type": "Question",
        name: "Is TraceLayer a Vanta alternative?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. TraceLayer offers continuous SOC 2 compliance automation starting from $0 (free plan) to $149/mo — compared to Vanta's $15,000–$20,000/year. It supports SOC 2, ISO 27001, HIPAA, GDPR, PCI DSS, CCPA, and NIST CSF.",
        },
      },
      {
        "@type": "Question",
        name: "Which compliance frameworks does TraceLayer support?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "TraceLayer supports SOC 2 Type I & II, ISO 27001, HIPAA, GDPR, PCI DSS, CCPA, and NIST CSF — all mapped simultaneously from a single set of integrations.",
        },
      },
      {
        "@type": "Question",
        name: "Does TraceLayer have a free plan?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. The free plan includes SOC 2 framework coverage, automated evidence collection, up to 3 integrations, risk register, policy templates, and up to 3 team members. No credit card required.",
        },
      },
      {
        "@type": "Question",
        name: "Can I use TraceLayer for a SOC 2 Type II audit?",
        acceptedAnswer: {
          "@type": "Answer",
          text: "Yes. TraceLayer collects continuous, timestamped evidence across your full observation period — exactly what auditors need for Type II. The AI Audit Package generates a formatted PDF report your auditor can use directly.",
        },
      },
    ],
  },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={sora.variable}>
      <body style={{ fontFamily: "var(--font-sora), ui-sans-serif, system-ui, sans-serif" }}>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        <PostHogProvider>
          <AuthProvider>{children}</AuthProvider>
        </PostHogProvider>
        <CookieConsent />
        <CrispChat />
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
