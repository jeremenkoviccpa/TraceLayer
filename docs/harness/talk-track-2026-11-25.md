# TraceLayer AI harness: talk track (Wed Nov 25, 16:00)

**Open in tabs:**
- `docs/harness/README.md` (the diagram)
- `docs/plans/tl-f001-rate-limit-logging/`
- `.github/workflows/ci.yml`
- `docs/harness/demo-run.md`

## 1. Why (1 min)
"We trust a teammate's change because there's a ticket, a plan, a review and tests, not because they're smart. Same standard for AI, and the process has to be visible."
Everyone has a personal AI setup, but it lives on one laptop. The harness makes runs you can see and repeat, adds AI review in CI, and starts from tickets.
It's not a wall of prompt rules. The rules are short, and the skills say what to check.

## 2. The flow (2 min, show the diagram)
- Ticket → /intake → /plan → human OK → /build (implement, review, test loop) → /ship → PR → CI + AI review → human merge.
- 4 roles: planner, implementer, reviewer, tester. Each is about 15 lines of markdown in `.claude/agents/`.
- 3 skills: api-endpoint, ui-check (desktop + mobile screenshots), security-check.
- `AGENTS.md` is the single source of truth: Claude, Devin, Cursor and Argo Helm all read it.
- Every task leaves `docs/plans/<id>/`. That's the audit trail.

## 3. Live walkthrough: tl-f001 (6 min)
A real security audit finding (TL-F001, Medium). Intake to ship in about 17 minutes, for about $3 to $6 in tokens.
1. **ticket.md:** intake found a real user bug the audit missed. A 429 returned `error`, the frontend reads `detail`, so users saw "Request failed".
2. **plan.md:** the planner wanted to mark the finding "Resolved" inside the auditor's signed report. A human said no. *The agent proposes, a person decides.*
3. **review.md (the strongest part):** round 1 found that if someone reverted the one line that turns the feature on, all 75 tests would still pass. The reviewer proved it by breaking a scratch copy. That got fixed, and round 2 came back clean. *A separate reviewer with fresh context caught what the implementer couldn't.*
4. **screenshots/:** before and after, on desktop and iPhone. "Request failed" became "Too many attempts. Please wait a minute".
5. **test-report.md and pr.md:** what was tested, and what wasn't and why. The PR text writes itself from the folder.
6. **Bonus:** the baseline check found `main` red three ways that nobody had noticed:
   - all 68 tests errored
   - 2,513 lint errors
   - the frontend build needed a secret

## 4. CI is green now (1 min). I re-ran it today
The same jobs as `ci.yml` and `test.yml`, run fresh from the branch:

| Job | Result |
|---|---|
| Backend lint (ruff 0.4.10) | all checks passed |
| Backend tests (pytest + Postgres) | **78 passed** in 25 s |
| Frontend typecheck (tsc) | passed |
| Frontend build (next build) | passed |
| main before the fix | **68 of 68 tests errored** (re-checked today) |

The AI review job posts the reviewer checklist as a PR comment. It only needs the repo secret `ANTHROPIC_API_KEY`. Without it, it skips and doesn't fail the PR.

## 5. How you start (2 min)
- Keep your own setup. The harness only asks two things: read `AGENTS.md`, and leave the 4 files in `docs/plans/<id>/`.
- Tomorrow: pick ONE playbook and run one real task:
  - `fix-a-bug-from-a-ticket.md`, which starts with a failing test
  - `write-tests-for-existing-code.md`, if you're scared of some code
  - `start-a-feature.md`
  - `review-a-pr-with-ai.md`
  - `run-a-task-in-devin.md`
- Not on Claude Code? Paste `.claude/agents/reviewer.md` into your tool. It's plain markdown.

## 6. Devin (1 min)
Devin is for parallel, long tasks that come back as a PR. It uses the same AGENTS.md and plan folder, and it follows CI through.
First candidate: the Easy Engage load test. A human still approves the plan and merges.

## 7. Next steps (1 min)
1. Easy Engage gets the same harness this week (copy AGENTS.md, `.claude/` and `docs/harness/`, then rewrite the repo map and commands).
2. Each person runs one task through it this week and posts the plan folder link.
3. Add the `ANTHROPIC_API_KEY` secret so the AI review runs on every PR.
4. In 2 weeks, review the plan folders together and cut the steps that were ceremony.

## Likely questions
- **"Would a human have caught the wiring gap?"** Maybe. The point is that the AI review runs on *every* PR, in CI, before a human looks.
- **"Isn't this slow and expensive?"** About 17 minutes and $3 to $6 for a real audit fix, including a review that found a must-fix.
- **"Do I have to use Claude?"** No. The role files are markdown, and Devin, Cursor and Argo Helm all work.
- **"What if the agent is wrong?"** The plan checkpoint and the human merge are the gates. The reviewer never edits code, and only the reviewer ticks the review boxes.
- **"Security?"** The security-check skill covers secrets, tenancy, authz and logs. The reviewer checked the `Authorization` header can't leak into logs.
