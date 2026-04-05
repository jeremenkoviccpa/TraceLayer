import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";

const WOODPECKER_API_KEY = process.env.WOODPECKER_API_KEY ?? "";
const resend = new Resend(process.env.RESEND_API_KEY ?? "");

const TOOL_LABELS: Record<string, string> = {
  "gap-scanner": "Compliance Gap Scanner",
  "readiness": "SOC 2 Readiness Checker",
  "stack-scorer": "Tech Stack Compliance Scorer",
};

function getThankYouHtml(tool: string): string {
  const toolLabel = TOOL_LABELS[tool] ?? "TraceLayer Free Tool";
  return `<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/></head>
<body style="margin:0;padding:0;background:#f7f3ed;font-family:system-ui,-apple-system,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f7f3ed;padding:40px 16px;">
    <tr><td align="center">
      <table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">

        <!-- Header -->
        <tr>
          <td style="background:#0f172a;padding:32px 40px;">
            <table cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:linear-gradient(135deg,#0d9488,#14b8a6);border-radius:10px;width:36px;height:36px;text-align:center;vertical-align:middle;">
                  <span style="color:white;font-size:20px;font-weight:800;line-height:36px;">T</span>
                </td>
                <td style="padding-left:12px;color:white;font-size:18px;font-weight:700;vertical-align:middle;">TraceLayer</td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px 40px 32px;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#0d9488;text-transform:uppercase;letter-spacing:0.05em;">Thanks for using</p>
            <h1 style="margin:0 0 20px;font-size:24px;font-weight:800;color:#0f172a;line-height:1.2;">${toolLabel}</h1>
            <p style="margin:0 0 24px;font-size:15px;color:#475569;line-height:1.6;">
              Your results are ready above. If you found them useful, TraceLayer can automate the entire compliance process for you — continuous evidence collection, audit reports, and real-time alerts when something breaks.
            </p>

            <!-- CTA -->
            <table cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
              <tr>
                <td style="background:#0d9488;border-radius:10px;">
                  <a href="https://app.tracelayer.it.com/register" style="display:inline-block;padding:14px 28px;color:white;font-size:15px;font-weight:700;text-decoration:none;">
                    Start free — no credit card
                  </a>
                </td>
              </tr>
            </table>

            <!-- What's included -->
            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;border-radius:12px;padding:20px 24px;margin-bottom:24px;">
              <tr><td>
                <p style="margin:0 0 12px;font-size:13px;font-weight:700;color:#0f172a;">Free plan includes:</p>
                <p style="margin:0 0 6px;font-size:14px;color:#475569;">✓ &nbsp;SOC 2 framework — automated evidence collection</p>
                <p style="margin:0 0 6px;font-size:14px;color:#475569;">✓ &nbsp;Up to 3 integrations (GitHub, AWS, Slack…)</p>
                <p style="margin:0 0 6px;font-size:14px;color:#475569;">✓ &nbsp;Risk register, policy templates, team access</p>
                <p style="margin:0;font-size:14px;color:#475569;">✓ &nbsp;No consultants, no $20K/year tools</p>
              </td></tr>
            </table>

            <p style="margin:0;font-size:14px;color:#94a3b8;">
              Questions? Reply to this email — we read every one.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #f1f5f9;">
            <p style="margin:0;font-size:12px;color:#94a3b8;">
              TraceLayer · <a href="https://tracelayer.it.com" style="color:#94a3b8;">tracelayer.it.com</a><br/>
              You received this because you used one of our free compliance tools.
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>`;
}

export async function POST(req: NextRequest) {
  try {
    const { email, tool } = await req.json();

    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json({ error: "Invalid email" }, { status: 400 });
    }

    const normalizedEmail = email.toLowerCase().trim();
    const toolName = tool ?? "unknown";

    // Save to our own DB
    const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
    if (backendUrl) {
      await fetch(`${backendUrl}/v1/public/capture-lead`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: normalizedEmail, tool: toolName }),
      }).catch(() => {}); // fire-and-forget, never block the user
    }

    // Add to Woodpecker
    if (WOODPECKER_API_KEY) {
      await fetch(`https://api.woodpecker.co/rest/v1/add_prospects_list?api_key=${WOODPECKER_API_KEY}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          update: "true",
          prospects: [{ email: normalizedEmail, snippet1: "tool_lead", snippet2: toolName }],
        }),
      });
    }

    // Send thank you email
    if (process.env.RESEND_API_KEY) {
      await resend.emails.send({
        from: "TraceLayer <hello@tracelayer.it.com>",
        to: normalizedEmail,
        subject: `Your ${TOOL_LABELS[toolName] ?? "compliance"} results are ready`,
        html: getThankYouHtml(toolName),
      });
    }

    return NextResponse.json({ ok: true });
  } catch {
    // Never block the user
    return NextResponse.json({ ok: true });
  }
}
