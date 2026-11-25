# ADR-0001: AI harness for agent-driven work

- **Status:** accepted
- **Date:** 2026-11-19
- **Task:** `docs/plans/tl-f001-rate-limit-logging/` (the first run)

## Context
Teammates already use AI agents (Claude Code, Devin, Cursor, Argo Helm) with their own prompts and habits.
What's missing is a shared process that others can see and repeat: where a task starts, what "done" means, who reviews,
and a record someone can audit afterwards. Long guardrail prompts in each tool drift apart and get ignored.

## Decision
- `AGENTS.md` is the single, tool-neutral source of truth. `CLAUDE.md` only points to it.
- Work moves through four roles (planner, implementer, reviewer, tester) and four commands (`/intake`, `/plan`, `/build`, `/ship`).
- Each task leaves a folder `docs/plans/<id>/` with ticket, plan, review, test report and screenshots.
- Testing behaviour lives in small skills (`ui-check`, `security-check`, `api-endpoint`) that say what to check and how, rather than hard-coded values ("test it on mobile" means Playwright device profiles, not a list of widths).
- CI runs tests, lint and an AI review on every PR. A human still merges.

## Consequences
- Anyone can open a PR's plan folder and see why the change exists and how it was checked.
- Personal setups stay personal. The harness only adds shared roles and outputs on top.
- It costs a few minutes and some tokens per task. Fine for features and fixes, overkill for one-line typo fixes, so skip it there.
- The AI review needs the `ANTHROPIC_API_KEY` repo secret. Without it, the job skips and doesn't fail.
- Revisit if the plan folders stop being read, or if review comments get ignored more often than not.
