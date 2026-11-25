# Run a task in Devin

**When:** a task can run in parallel while you work on something else, like load testing, a batch of integrations,
or test coverage.

**Paste this into Devin:**

> Repo: TraceLayer. Read AGENTS.md first and follow it. It's the source of truth.
> Task: <one sentence or issue link>. Task id: <id>.
> 1. Write docs/plans/<id>/ticket.md and plan.md (see .claude/agents/planner.md for the format). Message me the
>    plan summary and wait for my OK.
> 2. Implement on branch `devin/<id>` in small commits. Run `pytest tests/ -q` and `ruff check .` in backend/
>    after each step.
> 3. Review your own diff using .claude/agents/reviewer.md and .claude/skills/security-check/SKILL.md, then write
>    review.md. Fix every must-fix item.
> 4. Write tests and test-report.md (.claude/agents/tester.md). If UI changed, attach desktop and mobile screenshots.
> 5. Open a PR into main using docs/plans/<id>/pr.md as the description. Watch CI and fix failures until it's green.
>    Reply to the AI review comment's must-fix items.
> Don't touch .env files and don't print secret values.

**You:** read the plan when Devin messages you, then read the PR once CI is green. You merge.

**Good first candidates:** Easy Engage load testing, adding an integration adapter using an existing one as the
pattern, raising test coverage of one service.
