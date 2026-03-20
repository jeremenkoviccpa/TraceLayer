/** @type {import('next').NextConfig} */
const nextConfig = {
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://client.crisp.chat https://*.paddle.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://client.crisp.chat https://*.paddle.com",
              "img-src 'self' data: blob: https://*.crisp.chat https://*.paddle.com",
              "font-src 'self' https://fonts.gstatic.com https://client.crisp.chat",
              "connect-src * wss://*.relay.crisp.chat",
              "frame-src https://*.paddle.com",
              "frame-ancestors 'self' https://*.paddle.com",
            ].join("; "),
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
