# AI harness: speaker notes (15–20 min)

Have these open in tabs: `docs/harness/README.md` (rendered, for the diagram), the `docs/plans/tl-f001-rate-limit-logging/` folder,
and `.github/workflows/ci.yml`.

---

## 1. Why we're doing this (2 min)

- Trust comes from **seeing the process**, not from picking the right model.
  - When a human teammate ships something, we trust it because there was a ticket, a plan, a review and tests,
    not because they're smart.
  - We should hold AI to the same standard, and make that process visible.
- Today every one of us has a personal AI setup. Plan mode, phase plans and review subagents all work, but each one
  stays on its owner's laptop. Nobody else can see it or repeat it.
- What's missing: **runs you can see and repeat**, **AI review in CI**, and **intake from tickets**.
- What this is *not*: a wall of prompt guardrails. The rules are short, and the skills say *what to check*
  ("test it on mobile"), not hard-coded values.

## 2. The harness in one diagram (3 min)

Show the Mermaid diagram in `docs/harness/README.md`.

- **Ticket → /intake → /plan → (human OK) → /build loop → /ship → PR → CI with AI review → human merge**
- Four roles: **planner, implementer, reviewer, tester**. Each is about 15 lines of markdown in `.claude/agents/`.
- Three skills hold the testing behaviour: **api-endpoint** (how a route is built here), **ui-check**
  (desktop and mobile screenshots), **security-check** (secrets, tenancy, authz, logs).
- `AGENTS.md` is the single source of truth. Claude, Devin, Cursor and Argo Helm all read the same file.
- Every task leaves a folder, `docs/plans/<id>/`. That folder is the audit trail.

## 3. Live walkthrough: `docs/plans/tl-f001-rate-limit-logging/` (6–7 min)

<!-- filled from the real run -->

## 4. Your personal system plus the shared harness (3 min)

- Keep your own setup. The harness only asks two things of it:
  1. read `AGENTS.md`
  2. leave the four files in `docs/plans/<id>/`
- How to start tomorrow: pick **one** playbook from `docs/harness/playbooks/` and run one real task with it.
  - Have a bug ticket? Use `fix-a-bug-from-a-ticket.md`, which starts with a failing test.
  - Afraid to touch some code? Use `write-tests-for-existing-code.md`.
- Not on Claude Code? Paste the role file (`.claude/agents/reviewer.md`) into your tool. It's plain markdown.

## 5. Where Devin fits (2 min)

- Devin is for **parallel** work: tasks that can run while you do something else and come back as a PR.
- It follows the same `AGENTS.md` and the same plan folder (`playbooks/run-a-task-in-devin.md`), then **opens the PR and
  follows CI through**: it fixes red builds and answers the AI review's must-fix items.
- First candidate: **Easy Engage load testing**. It's well scoped, it runs for a long time, and it's easy to check from the report.
- A human still approves the plan and merges the PR.

## 6. Next steps (1–2 min)

- **Easy Engage** gets the same harness files this week. Copy `AGENTS.md`, `.claude/` and `docs/harness/`, then
  rewrite the repo map, the run/test commands and the conventions.
- **Each person runs one task this week** through the harness and drops the plan folder link in the channel.
- Add the `ANTHROPIC_API_KEY` repo secret so the AI review comment runs on every PR.
- In two weeks, look at the plan folders together: which steps helped, and which were ceremony? Cut what didn't help.
