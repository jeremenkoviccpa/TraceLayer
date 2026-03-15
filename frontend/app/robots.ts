import type { MetadataRoute } from "next";

const BASE_URL = "https://www.tracelayer.it.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/tools", "/login", "/signup", "/trust/"],
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
