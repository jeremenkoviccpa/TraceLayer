import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "TraceLayer — Automated Compliance for Startups";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "linear-gradient(135deg, #0f172a 0%, #1e293b 60%, #0f172a 100%)",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "80px 88px",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        {/* Logo row */}
        <div style={{ display: "flex", alignItems: "center", gap: "18px", marginBottom: "52px" }}>
          <div
            style={{
              width: "60px",
              height: "60px",
              borderRadius: "14px",
              background: "linear-gradient(135deg, #0d9488, #14b8a6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 24px rgba(13,148,136,0.4)",
            }}
          >
            <span style={{ color: "white", fontSize: "30px", fontWeight: "800" }}>T</span>
          </div>
          <span style={{ color: "white", fontSize: "34px", fontWeight: "700", letterSpacing: "-0.5px" }}>
            TraceLayer
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            color: "white",
            fontSize: "64px",
            fontWeight: "800",
            lineHeight: "1.05",
            marginBottom: "28px",
            maxWidth: "920px",
            letterSpacing: "-1.5px",
          }}
        >
          Automated Compliance for Startups
        </div>

        {/* Subheading */}
        <div style={{ color: "#94a3b8", fontSize: "26px", fontWeight: "400", marginBottom: "52px", maxWidth: "820px" }}>
          Continuously collect evidence for SOC 2, ISO 27001, HIPAA, GDPR & PCI DSS — across 18+ integrations.
        </div>

        {/* Framework pills */}
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
          {["SOC 2", "ISO 27001", "HIPAA", "GDPR", "PCI DSS"].map((fw) => (
            <div
              key={fw}
              style={{
                background: "rgba(255,255,255,0.08)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: "8px",
                padding: "8px 18px",
                color: "#e2e8f0",
                fontSize: "18px",
                fontWeight: "600",
              }}
            >
              {fw}
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size },
  );
}
