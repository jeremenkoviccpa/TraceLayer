# Demo run: tl-f001-rate-limit-logging

The first real task through the harness, run on 2026-11-19 on branch `chore/ai-harness`. All artifacts are in
`docs/plans/tl-f001-rate-limit-logging/`.

**Task:** audit finding **TL-F001** (Medium, open): 429 events lack per-tenant structured logging.
At intake we also found a user-visible bug: the 429 body was `{"error": ...}`, the frontend reads `detail`, so the login page said "Request failed".

**Setup:**
- One orchestrating Claude Code session ran the commands.
- Each role ran as a **separate subagent** with its role file (`.claude/agents/*.md`) and no shared memory. The reviewer never saw the implementer's reasoning, only the diff.
- Model: Claude Opus 5.5 throughout.

## Timeline

| Time | Step | Who | Took | What happened |
|---|---|---|---|---|
| 09:19 | Baseline | orchestrator | ~5 min | Before touching anything, ran the suites on `main`. **All 68 backend tests errored** (a JSONB `server_default` broke `create_all`) and **ruff reported 2,513 errors** (CI installs unpinned ruff, and newer defaults turned on many more rules). Fixed both in a separate commit (`dae5a2f`) so the task starts green. |
| 09:24 | `/intake` | orchestrator | <1 min | `ticket.md`: the source quote from the audit, the problem, 5 acceptance criteria, out of scope |
| 09:25 | `/plan` | **planner** | 1 min 12 s | `plan.md`: 5 steps, risks and a test plan. Raised 4 open questions with defaults, and spotted an unrelated issue (the 2FA `totp_token` is a full access token). |
| 09:26 | human checkpoint | orchestrator | <1 min | Accepted 3 defaults. **Overrode one:** the planner wanted to mark TL-F001 "Resolved" inside the assessor's signed audit report. We don't edit a third party's attestation; the remediation goes in the runbook instead. |
| 09:27 | `/build` implement | **implementer** | 3 min 40 s | 3 commits (handler, tests, runbook). Found and corrected a wrong API call in the plan. 68 → 75 tests. |
| 09:31 | `/build` review #1 | **reviewer** | 3 min 15 s | **Changes requested.** 1 must-fix and 3 nice-to-haves. It checked its claims by breaking scratch copies of the code. |
| 09:35 | `/build` fix | implementer | 1 min 56 s | Fixed the must-fix and 2 nice-to-haves; the third became a follow-up. 75 → 78 tests. |
| 09:37 | `/build` review #2 | reviewer | 1 min 44 s | **Clean.** Re-ran its break-the-code checks against the new tests. |
| 09:39 | `/build` test | **tester** | 2 min 13 s | Ran the suites, the Playwright desktop and mobile check of the login page, and a live 429 with `curl`. Checked the log record for secrets. Wrote `test-report.md`. |
| 09:41 | `/ship` | orchestrator | ~3 min | Ran the frontend production build (CI parity) and found a third problem on `main`: `next build` fails without `RESEND_API_KEY`. Added a CI placeholder and wrote `pr.md`. |

**Wall clock from intake to ship: about 17 minutes.** About 14 of those were agents working; the rest was the
orchestrator and one human-style checkpoint.

## What the reviewer caught

1. **Must-fix: the feature could silently switch off.** The new tests built their own small app, and rate limits
   are disabled in the test environment. If someone reverted the one line in `main.py` that turns the handler on,
   **all 75 tests would still pass** and TL-F001 would reopen unnoticed. Fixed with a wiring test. The reviewer
   then put the old line back in a scratch copy and saw the new test fail.
2. **A test that couldn't fail.** The `Retry-After` check passed even with the plan's original, broken window
   calculation, or with a hard-coded `"60"`. Fixed with a clock-shifted test.
3. **The runbook overstated things.** It said one log line per 429, but slowapi writes a second one. The text was
   corrected so operators alert on the right line.

What the reviewer cleared (security-check skill):
- no secrets
- tenant IDs only from verified tokens, tested against forged, expired, wrong-type and garbage tokens
- the `Authorization` header can't leak into logs: adding it makes 5 of 7 tests fail

## What the run found outside the task (follow-ups to open)
- The 2FA `totp_token` is a full `type: access` token (`backend/api/v1/auth.py:137`). Found by the planner.
- Client IP behind Railway's proxy: uvicorn runs without `--forwarded-allow-ips`, so per-IP rate limiting probably
  sees the proxy's IP. Found by the implementer.
- `frontend/app/api/capture-lead/route.ts` constructs `Resend` at import time, so the build needs the key.
  Construct it lazily, then drop the CI placeholder.
- `main` CI was red on all three counts above, and nobody had noticed.

## Tokens and cost (estimate)

Per-subagent numbers as reported by Claude Code. "Context" is the subagent's context size when it finished.

| Agent | Context tokens | Tool calls |
|---|---|---|
| planner | 60k | 8 |
| implementer (build + fix) | 71k → 83k | 24 + 10 |
| reviewer (2 rounds) | 81k → 93k | 20 + 5 |
| tester | 73k | 17 |

**How the cost was estimated:**
- Agents re-send their context on every tool call, mostly as cache reads.
- That works out to roughly **4M input tokens read**, **~0.5M new input tokens** and **~50k output tokens** across the four agents.
- At Opus 5.5 prices ($4/MTok input, $0.20 cache reads, $20 output), that's about **$3–6 for the subagents**.
- The orchestrator session isn't included. Treat this as an order-of-magnitude estimate. Real numbers come from the usage dashboard.

## What we'd change in the harness after this run
- The orchestrator told the implementer it could tick review boxes, which contradicts `reviewer.md`, and the reviewer flagged
  it. Rule kept as written: **only the reviewer ticks**.
- Running a local dev backend safely needs a recipe. Settings auto-load `backend/.env`, so we ran from a
  separate directory with `env -i` and a throwaway DB. Worth adding to the `ui-check` skill.
- Add "run the baseline first" to `/build`. Starting on a red `main` would have made every later result
  meaningless.
