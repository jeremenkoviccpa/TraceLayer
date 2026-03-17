import type { MetadataRoute } from "next";

const BASE_URL = "https://tracelayer.it.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: [
          "/",
          "/tools",
          "/partners",
          "/login",
          "/signup",
          "/security",
          "/dpa",
          "/status",
          "/privacy",
          "/terms",
          "/trust/",
        ],
        disallow: [
          "/dashboard",
          "/compliance",
          "/evidence",
          "/integrations",
          "/risks",
          "/pen-tests",
          "/vendors",
          "/access-reviews",
          "/training",
          "/policies",
          "/reports",
          "/questionnaire",
          "/audit-package",
          "/team",
          "/audit-log",
          "/settings",
          "/readiness",
        ],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
