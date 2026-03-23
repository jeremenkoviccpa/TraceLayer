import { NextRequest, NextResponse } from "next/server";

const BREVO_API_KEY = process.env.BREVO_API_KEY ?? "";
// Set this to your Brevo list ID for tool leads (create one called "Tool Leads")
const BREVO_LIST_ID = parseInt(process.env.BREVO_LEAD_LIST_ID ?? "2", 10);

export async function POST(req: NextRequest) {
  try {
    const { email, tool } = await req.json();

    if (!email || typeof email !== "string" || !email.includes("@")) {
      return NextResponse.json({ error: "Invalid email" }, { status: 400 });
    }

    if (BREVO_API_KEY) {
      await fetch("https://api.brevo.com/v3/contacts", {
        method: "POST",
        headers: {
          "api-key": BREVO_API_KEY,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email.toLowerCase().trim(),
          attributes: {
            SOURCE: "tool_lead",
            TOOL: tool ?? "unknown",
          },
          listIds: [BREVO_LIST_ID],
          updateEnabled: true,
        }),
      });
    }

    return NextResponse.json({ ok: true });
  } catch {
    // Never block the user — if Brevo is down, still unlock results
    return NextResponse.json({ ok: true });
  }
}
