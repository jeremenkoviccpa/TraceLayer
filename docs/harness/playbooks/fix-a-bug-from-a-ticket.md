# Fix a bug from a ticket

**When:** there's a GitHub issue, a Sentry error or a customer report.

```text
/intake 142                      # or paste the Sentry title / customer text
/plan gh-142
```

Ask the planner for a **failing test first**: the plan's first step should be a test that reproduces the bug.

```text
/build gh-142
/ship gh-142
```

**Prompt for any tool:**

> Follow AGENTS.md. Bug: <paste>. Step 1: write a test that fails because of this bug, and show me it failing.
> Step 2: the smallest fix that makes it pass. Step 3: run the full backend suite and ruff. Write
> docs/plans/gh-<n>/ticket.md, plan.md and test-report.md. If the bug is visible in the UI, run the ui-check skill on desktop and mobile.

**Watch for:** fixes that change behaviour other code depends on. The reviewer should flag them, and you should read `review.md`.
