import type { Metadata } from "next";
import { Sora } from "next/font/google";
import "./globals.css";
import { Analytics } from "@vercel/analytics/react";
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

const BASE_URL = "https://www.tracelayer.it.com";

export const metadata: Metadata = {
  metadataBase: new URL(BASE_URL),
  title: {
    default: "TraceLayer — Automated SOC 2 & Compliance for Startups",
    template: "%s | TraceLayer",
  },
  description:
    "TraceLayer continuously collects compliance evidence and monitors your SOC 2, ISO 27001, HIPAA, GDPR, and PCI DSS posture across 18+ integrations. Get audit-ready without the manual work.",
  keywords: [
    "SOC 2 compliance software",
    "compliance automation",
    "ISO 27001 automation",
    "HIPAA compliance tool",
    "continuous compliance monitoring",
    "audit evidence collection",
    "compliance software for startups",
    "SOC 2 readiness",
    "GDPR compliance",
    "PCI DSS compliance",
  ],
  authors: [{ name: "TraceLayer", url: BASE_URL }],
  creator: "TraceLayer",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: BASE_URL,
    siteName: "TraceLayer",
    title: "TraceLayer — Automated SOC 2 & Compliance for Startups",
    description:
      "Continuously collect SOC 2, ISO 27001, HIPAA & GDPR evidence across 18+ integrations. Get audit-ready without the manual work.",
    images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: "TraceLayer — Automated Compliance for Startups" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "TraceLayer — Automated SOC 2 & Compliance for Startups",
    description:
      "Continuously collect SOC 2, ISO 27001, HIPAA & GDPR evidence across 18+ integrations. Get audit-ready without the manual work.",
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

const jsonLd = {
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  name: "TraceLayer",
  url: BASE_URL,
  description:
    "Automated compliance evidence collection and monitoring for SOC 2, ISO 27001, HIPAA, GDPR, and PCI DSS.",
  applicationCategory: "BusinessApplication",
  operatingSystem: "Web",
  offers: {
    "@type": "Offer",
    price: "0",
    priceCurrency: "USD",
    description: "Free plan available",
  },
  creator: {
    "@type": "Organization",
    name: "TraceLayer",
    url: BASE_URL,
  },
};

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
      </body>
    </html>
  );
}
