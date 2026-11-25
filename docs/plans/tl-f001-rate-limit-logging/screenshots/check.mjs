// ui-check for tl-f001: login page after the login rate limit (10/minute per IP) is hit.
// Usage: APP_URL=http://localhost:3456 API_URL=http://localhost:8765 OUT=<dir> LABEL=after node check.mjs
// Uses a throwaway example.com address and a wrong password. No real credentials.
import { chromium, devices } from "playwright";

const app = process.env.APP_URL ?? "http://localhost:3000";
const api = process.env.API_URL ?? "http://localhost:8000";
const out = process.env.OUT ?? ".";
const label = process.env.LABEL ?? "after";
const email = "ui-check@example.com";

// Use up the per-IP login budget so the next browser attempt gets a 429.
for (let i = 0; i < 10; i++) {
  await fetch(`${api}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: "wrong-password" }),
  });
}

const browser = await chromium.launch();
for (const [name, profile] of [["desktop", devices["Desktop Chrome"]], ["mobile", devices["iPhone 13"]]]) {
  const context = await browser.newContext(profile);
  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (m) => m.type() === "error" && consoleErrors.push(m.text()));
  let status = null;
  page.on("response", (r) => r.url().endsWith("/v1/auth/login") && (status = r.status()));

  await page.goto(`${app}/login`, { waitUntil: "networkidle" });
  await page.fill('input[type="email"]', email);
  await page.fill('input[type="password"]', "wrong-password");
  await Promise.all([
    page.waitForResponse((r) => r.url().endsWith("/v1/auth/login") && r.request().method() === "POST", { timeout: 15000 }),
    page.getByRole("button", { name: /sign in|log in/i }).first().click(),
  ]);
  await page.waitForTimeout(500);

  const path = `${out}/${label}-${name}.png`;
  await page.screenshot({ path, fullPage: false });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  console.log(JSON.stringify({ label, name, status, horizontalOverflow: overflow, consoleErrors: consoleErrors.length, path }));
  await context.close();
}
await browser.close();
