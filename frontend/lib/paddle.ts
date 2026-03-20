import { initializePaddle, type Paddle } from "@paddle/paddle-js";

let paddle: Paddle | undefined;

/**
 * Opens Paddle checkout overlay for a given checkout URL.
 * Paddle Billing v2 returns ?_ptxn=txn_... URLs when a custom payment link domain is set.
 * This extracts the transaction ID and opens the Paddle.js overlay instead of redirecting.
 */
export async function openPaddleCheckout(checkoutUrl: string): Promise<void> {
  let transactionId: string | null = null;

  try {
    const url = new URL(checkoutUrl);
    transactionId = url.searchParams.get("_ptxn");
  } catch {
    // Invalid URL — fall back to redirect
  }

  if (!transactionId) {
    // Paddle-hosted URL (no custom domain) — just redirect
    window.location.href = checkoutUrl;
    return;
  }

  if (!paddle) {
    const isSandbox = process.env.NEXT_PUBLIC_PADDLE_SANDBOX === "true";
    paddle = await initializePaddle({
      environment: isSandbox ? "sandbox" : "production",
      token: process.env.NEXT_PUBLIC_PADDLE_TOKEN!,
    });
  }

  if (!paddle) {
    // initializePaddle failed — fall back to redirect
    window.location.href = checkoutUrl;
    return;
  }

  paddle.Checkout.open({ transactionId });
}
