import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "TraceLayer — Stop chasing compliance. Let it run itself.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          background: "#f7f3ed",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          justifyContent: "center",
          padding: "80px 96px",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        {/* Logo row */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "48px" }}>
          <div
            style={{
              width: "40px",
              height: "40px",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0d9488, #14b8a6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <span style={{ color: "white", fontSize: "22px", fontWeight: "800" }}>T</span>
          </div>
          <span style={{ color: "#0f172a", fontSize: "26px", fontWeight: "700", letterSpacing: "-0.3px" }}>
            TraceLayer
          </span>
        </div>

        {/* Headline */}
        <div
          style={{
            color: "#0f172a",
            fontSize: "72px",
            fontWeight: "800",
            lineHeight: "1.05",
            marginBottom: "0px",
            letterSpacing: "-2px",
          }}
        >
          Stop chasing compliance.
        </div>
        <div
          style={{
            color: "#0d9488",
            fontSize: "72px",
            fontWeight: "800",
            lineHeight: "1.05",
            marginBottom: "32px",
            letterSpacing: "-2px",
          }}
        >
          Let it run itself.
        </div>

        {/* Subheading */}
        <div
          style={{
            color: "#475569",
            fontSize: "24px",
            fontWeight: "400",
            marginBottom: "48px",
            maxWidth: "860px",
            lineHeight: "1.5",
          }}
        >
          Connect your tools once — evidence collects across SOC 2, ISO 27001, DPDP Act, CERT-In & 5 more frameworks.
        </div>

        {/* Pills */}
        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
          {["Seed & Series A/B CTOs", "Indian startups & SaaS", "DPDP Act compliance", "No $20K Vanta quotes"].map((label) => (
            <div
              key={label}
              style={{
                background: "rgba(13,148,136,0.08)",
                border: "1px solid rgba(13,148,136,0.25)",
                borderRadius: "100px",
                padding: "8px 18px",
                color: "#0f766e",
                fontSize: "17px",
                fontWeight: "600",
              }}
            >
              {label}
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size },
  );
}
