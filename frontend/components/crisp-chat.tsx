"use client";

import Script from "next/script";

const CRISP_ID = process.env.NEXT_PUBLIC_CRISP_WEBSITE_ID;

/**
 * Loads the Crisp live chat widget.
 * Set NEXT_PUBLIC_CRISP_WEBSITE_ID in your environment to activate.
 * If the env var is absent, renders nothing.
 */
export function CrispChat() {
  if (!CRISP_ID) return null;
  return (
    <>
      <Script id="crisp-init" strategy="afterInteractive">
        {`window.$crisp=[];window.CRISP_WEBSITE_ID="${CRISP_ID}";`}
      </Script>
      <Script
        id="crisp-sdk"
        src="https://client.crisp.chat/l.js"
        strategy="afterInteractive"
        async
      />
    </>
  );
}
