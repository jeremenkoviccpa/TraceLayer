# Start a feature

**When:** a new capability that's bigger than a one-file change.

```text
/intake "Admins can export the risk register as CSV from /risks"
/plan risk-register-csv-export
```

Read `plan.md` and push back on anything that looks wrong. Answer any open questions. Then:

```text
/build risk-register-csv-export
/ship risk-register-csv-export
```

**Prompt for tools without slash commands:**

> Follow AGENTS.md. Feature: <one sentence>. First write docs/plans/<id>/ticket.md and plan.md (goal, scope, steps,
> risks, test plan) and stop for my review. After I approve, implement in small commits, review your own diff with
> .claude/skills/security-check, add tests, and write review.md and test-report.md.

**Done when:** the definition of done in AGENTS.md is met and `pr.md` exists.
