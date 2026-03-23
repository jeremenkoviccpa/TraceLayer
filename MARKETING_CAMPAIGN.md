# TraceLayer Cold Email Campaign

## Lead List

| Segment | Count | Core Pain |
|---|---|---|
| CTO | 714 | Enterprise deals slipping because compliance isn't ready |
| VP Engineering | 227 | Engineers dragged into compliance busywork every quarter |
| Head / Director of Engineering | 154 | Last-minute audit scrambles eating sprint capacity |
| CISO / Security | 117 | Auditors rejecting screenshots, demanding timestamped evidence |
| **Total** | **1,272** | |

---

## Offer: Founding Member Pricing

**Don't do a free trial. Do a permanent founder discount.**

The free plan already handles trial objections. A permanent price lock creates something better: urgency with no expiry date.

- **Price:** $99/mo locked forever (standard is $149/mo)
- **Savings:** $600/year, every year, no renegotiation
- **Slots:** 100 — keeps it credible and scarce
- **Deadline:** 14 days from Day 0
- **Requirement:** Connect at least 1 integration within 30 days of signing up
- **Bonus:** Founding Member badge on their public Trust Center page

---

## Sequence Overview

| # | Day | Subject | Angle |
|---|---|---|---|
| 1 | Day 0 | *quick question, {{first_name}}* | Cold open — call out the pain in one sentence |
| 2 | Day 3 | *how [similar company] cut SOC 2 prep to 2 weeks* | Social proof — make it concrete |
| 3 | Day 7 | *the part nobody mentions* | Reframe — evidence collection is the actual problem, not compliance |
| 4 | Day 11 | *what your auditor actually wants* | Education — product depth without being salesy |
| 5 | Day 14 | *closing this tonight* | Hard close — founding member deadline |

**Cold email rules for this sequence:**
- Plain text only — no images, no logos, no HTML formatting. Looks like a personal email.
- Under 150 words for Email 1–3. Email 4–5 can go slightly longer.
- One CTA per email. Never two.
- Subject lines that look like they came from a colleague, not a marketing team.
- First sentence has no "I" — start with them, not you.
- Never mention features until Email 3+.

---

## Personalization Variables

| Variable | Source | Used in |
|---|---|---|
| `{{first_name}}` | Lead list | Every email |
| `{{company}}` | Lead list | Email 1, 2 subject line A/B |
| `{{title_segment}}` | Derived from Title column | Email 3 variant selection |
| `{{region_segment}}` | Derived from Country column | Email 1 framework line, subject line B |

**Title segmentation logic:**
- `CTO` → Segment A (deal velocity copy)
- `VP Engineering`, `Head of Engineering`, `Director of Engineering` → Segment B (engineering time copy)
- `CISO`, `Security` → Segment C (evidence quality copy)

**Region segmentation logic:**

| Country | Region Segment | Lead framework angle | Subject line B variant |
|---|---|---|---|
| United States, Canada | `us` | SOC 2 first | `{{company}} + SOC 2` |
| United Kingdom | `uk` | ISO 27001 + UK GDPR | `{{company}} + ISO 27001` |
| Germany, France, Netherlands, Sweden, Denmark, Finland, Norway, Austria, Belgium, Switzerland | `eu` | GDPR + ISO 27001 | `{{company}} + GDPR` |
| Australia, New Zealand, Singapore, India | `apac` | ISO 27001 | `{{company}} + ISO 27001` |
| All others | `us` (default) | SOC 2 first | `{{company}} + SOC 2` |

**Why it matters:** US CTOs lose deals because prospects require SOC 2. EU CTOs face GDPR fines and ISO 27001 procurement requirements. UK CTOs deal with both post-Brexit. Same product, different fear — the opening line should reflect theirs.

**Region-specific framework line in Email 1** — swap this one sentence based on `{{region_segment}}`:

| Segment | Line to use |
|---|---|
| `us` | `SOC 2, ISO 27001, HIPAA — all mapped simultaneously.` |
| `uk` | `ISO 27001, UK GDPR, SOC 2 — all mapped simultaneously.` |
| `eu` | `GDPR, ISO 27001, SOC 2 — all mapped simultaneously.` |
| `apac` | `ISO 27001, SOC 2, GDPR — all mapped simultaneously.` |

---

## Email 1 — Day 0 (Cold Open)

**To:** All 1,272 leads
**Subject A:** `quick question, {{first_name}}`
**Subject B:** `{{company}} + SOC 2`
**Subject C:** `compliance eating your deals?`
**Preview:** How many enterprise deals slipped this quarter because your SOC 2 wasn't ready?

> Test all three subjects on a 10% sample split before sending the full list. Pick the winner by open rate after 4 hours.

---

```
{{first_name}},

How many enterprise deals has compliance held up this quarter?

For most CTOs I talk to, it's at least one. Usually two. And the fix — hiring a consultant, running manual evidence collection across 14 spreadsheets — takes 3–6 months and costs more than the deal itself.

We built TraceLayer to close that gap. Connect your AWS, GitHub, or Okta and it collects compliance evidence automatically every 24 hours. SOC 2, ISO 27001, HIPAA — all mapped simultaneously.

Start free here (no credit card): https://app.tracelayer.it.com/register

Most teams have evidence flowing in 5 minutes.

— Nemanja
Founder, TraceLayer

P.S. Launching a founding member offer this week — $99/mo locked in permanently for the first 100 customers. More on that Thursday.
```

---

## Email 2 — Day 3 (Social Proof)

**To:** Everyone who didn't convert from Email 1
**Subject:** `how [company] cut SOC 2 prep to 2 weeks`
**Preview:** Concrete steps. No consultant.

> For the top 200 leads by company size, replace "[company]" with a real similar company name from their industry. For the rest, use a generic descriptor that fits their segment (e.g., "how a Series B SaaS cut SOC 2 prep to 2 weeks").

---

```
{{first_name}},

Quick story.

Sarah Chen joined a Series B SaaS as Head of Security with a 6-week deadline to hit SOC 2 — or lose an enterprise deal.

The old approach would have taken 3 months.

She connected AWS, GitHub, Okta, and Slack to TraceLayer on a Monday. By Thursday they had a 78% readiness score. Two weeks later, she handed the auditor a formatted PDF — every control mapped, every piece of evidence timestamped, audit narrative already written.

Deal closed.

If that's the kind of timeline you need: https://app.tracelayer.it.com/register

Founding member slots ($99/mo permanently) are going fast — down to under 100. Use code FMD99 while checking out to get it!

— Nemanja
```

---

## Email 3 — Day 7 (Reframe the Problem)

**To:** Everyone who hasn't signed up
**Send two variants based on `{{title_segment}}`**

---

### Segment A — CTO

**Subject:** `the compliance problem nobody talks about`
**Preview:** It's not the audit. It's the evidence collection.

```
{{first_name}},

Everyone talks about compliance like the hard part is the audit itself.

It's not. The hard part is evidence collection — pulling screenshots from AWS, chasing engineers to document access reviews, copying data into a spreadsheet that's already outdated by the time the auditor sees it.

That's the part that eats 3 months and delays the deal.

TraceLayer automates it. Evidence collected from 100+ integrations every 24 hours. The moment a control breaks, you get a Slack alert. When you're ready, one click generates the audit PDF.

Founding member pricing — $99/mo permanently — closes in 7 days.

https://app.tracelayer.it.com/register

— Nemanja
```

---

### Segment B — VP / Head / Director of Engineering

**Subject:** `12% of your engineering time`
**Preview:** That's what manual compliance is costing you on average.

```
{{first_name}},

Engineering teams lose an average of 12% of their time to manual compliance work.

Pulling evidence, documenting access reviews, filling out vendor questionnaires, rebuilding the spreadsheet every quarter.

That's one engineer, gone — not on product, on paperwork.

TraceLayer runs your entire compliance program automatically in the background. Evidence collected every 24 hours. Alerts when something breaks. Audit report in one click.

Your engineers build. TraceLayer handles compliance.

$99/mo permanently (standard is $149) — founding member offer closes in 7 days.

https://app.tracelayer.it.com/register

— Nemanja
```

---

### Segment C — CISO / Security

**Subject:** `what auditors actually want now`
**Preview:** Screenshots aren't enough anymore.

```
{{first_name}},

Auditors have changed what they accept.

Screenshots don't cut it. They want timestamped, continuous evidence collected across the full observation period — proof that controls were actually operating, not just configured once.

TraceLayer pulls timestamped records directly from your source systems every 24 hours. IAM reviews from Okta, deployment logs from GitHub, CloudTrail events from AWS — all mapped to the right criteria, all with a continuous timestamp chain.

Every piece of evidence your auditor needs, collected automatically.

Founding member pricing ($99/mo, locked permanently) closes in 7 days.

https://app.tracelayer.it.com/register

— Nemanja
```

---

## Email 4 — Day 11 (Product Depth)

**To:** Everyone who hasn't signed up
**Subject:** `what we collected for one SOC 2 audit`
**Preview:** 3,241 evidence records. Zero screenshots.

```
{{first_name}},

Here's what TraceLayer collected automatically for a recent SOC 2 audit:

Access Control (CC6)
– IAM users with MFA status, pulled from Okta + AWS every 24h
– Access review records with reviewer, scope, findings, timestamp
– Terminated user offboarding checklists

Change Management (CC8)
– GitHub PRs with approval records
– CI/CD deployment logs
– Terraform infrastructure-as-code runs

Monitoring (CC7)
– CloudTrail event logs
– Datadog monitor history
– Snyk vulnerability scans with severity + remediation status

All timestamped. All mapped to the right criteria. All collected without anyone on the team doing anything.

3,241 evidence records across 4 integrations — in 2 weeks.

Free to start, no credit card: https://app.tracelayer.it.com/register

Founding member pricing ($99/mo permanently) closes in 3 days.

— Nemanja

P.S. Reply if you'd like a quick live walkthrough. I'll show you the actual evidence records from a real audit.
```

---

## Email 5 — Day 14 (Hard Close)

**To:** Everyone who hasn't signed up
**Subject:** `closing this tonight`
**Preview:** After midnight it goes back to $149/mo.

```
{{first_name}},

Tonight at midnight the founding member pricing closes.

After that, TraceLayer Growth is $149/mo. The 100 founding member slots lock in $99/mo permanently — $600/year back in your pocket, every year.

What you get:
– 100+ integrations (AWS, GitHub, Okta, Datadog, Snyk, and more)
– All 7 frameworks (SOC 2, ISO 27001, HIPAA, GDPR, PCI DSS, CCPA, NIST CSF)
– AI questionnaire autofill
– One-click audit PDF package
– Compliance drift alerts
– Public Trust Center page
– Founding Member badge

The free plan stays free — start there if you want to see evidence flowing before you decide.

https://app.tracelayer.it.com/register

Reply if you have any questions before midnight. I'll get back to you within the hour.

— Nemanja
Founder, TraceLayer
```

---

## Sending Strategy

### Tools (pick one)
- **Instantly.ai** — best for deliverability at this volume, built-in warmup
- **Lemlist** — better if you want per-lead personalization images/snippets
- **Apollo Sequences** — if your leads are already in Apollo, easiest to set up

### Deliverability
- Warm your sending domain for **at least 2 weeks** before Day 0
- Use a subdomain: `hello@mail.tracelayer.it.com` — never your root domain
- Send max **200/day per inbox** — spread across 7 inboxes for the full 1,272
- Enable DKIM, SPF, DMARC before Day 0 or your open rates tank

### Timing
- **Send Tuesday–Thursday, 9–11am recipient local time**
- Avoid Mondays (inbox chaos) and Fridays (nobody acts on Fridays)
- Use timezone detection in your tool if available

### Non-opener re-send
Re-send Email 1 with a different subject line to non-openers after 48 hours. Expect 20–30% additional opens on the re-send. Don't re-send to anyone who opened.

### Reply handling
- Any reply (even "not interested") gets a personal response from Nemanja
- Tag positive replies immediately and move to a personal follow-up thread
- "Not interested" replies: ask one question — "What would have to be true for this to be worth 10 minutes?" — optional, only for high-value accounts

---

## Subject Line A/B Test (Email 1)

| Variant | Subject | Best for |
|---|---|---|
| A | `quick question, {{first_name}}` | Feels most personal, highest open rate |
| B | `{{company}} + SOC 2` | High relevance, good for named accounts |
| C | `compliance eating your deals?` | Most direct, slightly lower open rate |

Run a 10% split (127 leads) across all three. Winner by open rate at 4 hours gets the remaining 90%.

---

## Founding Member Offer Details

| | Value |
|---|---|
| Price | $99/mo (normally $149/mo) |
| Savings | $600/year, every year |
| Slots | 100 |
| Lock-in | Permanent — price never increases for founding members |
| Deadline | 14 days from Day 0 |
| Requirement | Connect at least 1 integration within 30 days |
| Bonus | Founding Member badge on Trust Center page |

---

## Expected Results

| Metric | Conservative | Optimistic |
|---|---|---|
| Open rate | 35% | 50% |
| Reply rate | 3% | 7% |
| Click rate | 8% | 15% |
| Free signups | 60 | 120 |
| Founding member conversions | 15 | 40 |
| MRR from campaign | $1,485 | $3,960 |

The number that matters most: **free → paid conversion over 60 days.** Every free signup is pipeline. Most compliance tools convert 8–15% to annual billing within 60 days of signup.

---

## What to Do First

1. **This week:** Warm the sending domain (`hello@mail.tracelayer.it.com`). Set up DKIM/SPF/DMARC.
2. **Before Day 0:** Import leads into Instantly/Lemlist. Segment by `{{title_segment}}` for Email 3 routing.
3. **Day 0:** Send Email 1 with 3-way subject line test. Monitor open rate at 4h, send winner to remaining 90%.
4. **Day 0 evening:** Check for replies. Respond personally to all of them.
5. **Day 3–14:** Let the sequence run. Check replies daily. Move hot leads to direct email thread.

---

## Partner Ecosystem Strategy

### The Big Picture

Vanta and Drata built significant moats — and significant revenue — not just from SaaS subscriptions but from partner networks. Auditors, pen test firms, and policy consultants pay referral fees or listing fees, and they send customers back in return. TraceLayer becomes the platform customers never leave because everything they need to reach SOC 2 is available in one place.

**Positioning:** *"From first integration to signed audit report — without leaving TraceLayer."*

This is a fundamentally stronger value prop than evidence collection alone. Evidence collection gets them to 80%. Partners get them to 100%.

---

### Partner Category 1 — Auditors (Highest Value)

**Who to target:**

| Firm | Notes |
|------|-------|
| Prescient Assurance | Startup-friendly, fast, works heavily with Drata/Vanta customers |
| Johanson Group | Well-known in the SMB/startup SOC 2 space |
| A-LIGN | Larger, enterprise-grade, good for customers going upmarket |
| BARR Advisory | Strong reputation, active partner program |
| Schellman | Premium/enterprise tier, ISO 27001 specialists too |

**Deal structure:**
- 10–20% referral fee per audit started, or flat $1–2k intro fee per warm lead
- TraceLayer earns this passively — customer clicks "I'm ready for audit," gets connected
- Auditors love it: customer arrives already 80%+ compliant, observation period running, evidence organized → faster, easier audit for them

**Product trigger:**
- When Readiness score ≥ 75%, show a banner: *"You're audit-ready. Meet our certified auditor partners →"*
- Add a **"Ready for Audit" badge** customers can display on their Trust Center once they hit the threshold

**Revenue estimate:** 3–5 audits/month × $1,500 avg referral = **$4,500–7,500/mo** once the partner flywheel is running

---

### Partner Category 2 — Pen Test Firms (Easiest to Close)

**Who to target:**

| Firm | Notes |
|------|-------|
| Cobalt | Marketplace model, API-friendly, already has formal referral program |
| NetSPI | Strong enterprise focus |
| Synack | Crowdsourced, fast turnaround |
| Rapid7 | Larger firm, good for customers who want a full security suite |
| Secureworks | Enterprise, good for HIPAA/PCI customers |

**Deal structure:**
- $500–2k per referred engagement, or rev-share (5–10%)
- Cobalt already has a partner portal — sign up immediately

**Product trigger:**
- Pen Tests page already exists in TraceLayer
- Add a **"Schedule a pen test with a vetted partner →"** CTA when the pen test section is empty
- Show a warning on the compliance page when no pen test evidence exists for 12+ months

**Revenue estimate:** 2–4 referrals/month × $750 avg = **$1,500–3,000/mo**

---

### Partner Category 3 — Policy & vCISO Consultants

**Who to target:**
- Boutique vCISO firms (1–10 person shops that serve Series A–B startups)
- Policy writing specialists (firms that sell templated + customized policy packs)
- Security consulting firms that do gap assessments

**Deal structure:**
- Listing fee: $500–2k/year for "Preferred Partner" status + logo placement
- Referral fee: $300–800 per customer handed off for policy writing
- Or: build a **Policy Template Pack** add-on inside TraceLayer ($500–2k one-time, or included in higher tier) and partner with a vCISO to white-label it

**Product trigger:**
- Manual controls section shows 6 policy controls as "Pending"
- Add: *"Need help writing these? Our policy partners can deliver them in 5 business days →"*

**Revenue estimate:** Lower per-deal, but volume is high — every customer needs policies. $800–2k/mo once running.

---

### Revenue Summary

| Partner Type | Referrals/mo | Avg Fee | Monthly Revenue |
|---|---|---|---|
| Auditors | 3–5 | $1,500 | $4,500–7,500 |
| Pen test firms | 2–4 | $750 | $1,500–3,000 |
| Policy consultants | 3–6 | $500 | $1,500–3,000 |
| **Total** | | | **$7,500–13,500/mo** |

That's $90–160k/year in partner revenue on top of SaaS subscriptions — at near-zero marginal cost once the relationships are established.

---

### What to Build in the Product

**Phase 1 (minimal, launch now):**
- `/partners` page — already exists as a directory shell
- Add partner logo + short description + "Get introduced" button (routes to a Calendly or email)
- Add contextual CTAs on: Pen Tests page (no test on file), Readiness page (score ≥ 75%), Manual Controls (policies pending)

**Phase 2 (after first 50 customers):**
- "Ready for Audit" badge on Trust Center when Readiness ≥ 75%
- Partner referral tracking (UTM + internal referral ID per partner)
- Partner dashboard so auditors can see which customers referred them

**Phase 3 (scale):**
- White-labeled policy template pack inside TraceLayer
- Partner-facing portal (similar to your current Partner Program)
- Co-marketing: auditor partners send their prospects to TraceLayer, TraceLayer sends audit-ready customers to them

---

### When to Start

| Phase | Timing | Action |
|---|---|---|
| **Pre-launch (now)** | Before Day 0 | Email Cobalt partner program, email 2–3 auditors (Prescient, Johanson). Subject: *"We send you pre-qualified SOC 2 customers — want warm leads?"* They will respond. |
| **Launch week** | Day 0–7 | Add partner CTAs inside the product. Pen Tests page, Readiness page, Manual Controls section. Zero code needed — just links. |
| **Month 1** | 30 days post-launch | Sign first 2 auditor agreements and 1 pen test agreement. Add their logos to `/partners`. |
| **Month 2–3** | After 20–30 customers | Start tracking referrals. Add "Ready for Audit" trigger based on Readiness score. |
| **Month 4–6** | After 50 customers | Launch Policy Pack add-on. Co-marketing with 1–2 auditor partners (they mention TraceLayer in their onboarding emails). |
| **Month 6+** | At scale | Full partner portal. Revenue share automated. Partner flywheel self-sustaining. |

---

### Email Templates to Send This Week

**To auditors (Prescient, Johanson, A-LIGN):**

```
Hi [Name],

I'm Nemanja, founder of TraceLayer — we automate SOC 2 evidence collection for
engineering teams (120+ integrations, continuous evidence every 24h).

Our customers reach 75–85% readiness before they ever engage an auditor. I'd like
to send those customers to you.

When a customer hits our "Ready for Audit" threshold, we surface a list of vetted
audit partners. I'd like [Firm] to be on that list.

Happy to set up a 20-minute call to discuss terms. Do you have time this week?

— Nemanja
Founder, TraceLayer
tracelayer.it.com
```

**To Cobalt (pen test partner):**

```
Hi [Name],

I'm Nemanja, founder of TraceLayer — continuous compliance automation for
engineering teams pursuing SOC 2.

SOC 2 requires an annual pen test, and our customers ask us for recommendations
constantly. I see Cobalt has a partner program — I'd like to explore how we can
send you qualified referrals.

Our customers are typically Series A–B SaaS companies, 20–200 employees,
mid-way through their SOC 2 journey. Warm, qualified leads.

Can we connect this week?

— Nemanja
```

---

### The Compounding Advantage

Once the partner flywheel starts:

1. **Auditor refers a prospect** → prospect signs up for TraceLayer → TraceLayer sends them back to auditor when ready
2. **Customer gets audited** → posts about it on LinkedIn → tags TraceLayer → inbound leads
3. **Pen test firm refers prospect** → same loop
4. **vCISO consultant recommends TraceLayer** to every client → steady inbound

Each partner relationship compounds. The first 5 partners are the hardest. After that, other firms approach you asking to be listed.

This is how Vanta went from $0 to $100M ARR faster than any compliance tool in history — not just product, but the ecosystem they built around it.
