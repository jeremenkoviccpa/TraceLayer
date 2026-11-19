# Review a PR with AI

**Automatically:** every PR into `main` gets an **AI review** comment from CI with the reviewer's checklist,
if the repo secret `ANTHROPIC_API_KEY` is set.

**By hand, in Claude Code:**

```bash
gh pr checkout 57
```
```text
Use the reviewer subagent on this branch against main. If docs/plans/<id>/plan.md exists, review against it.
Write the result to /tmp/review-57.md, not into the repo.
```

**Any other tool:** paste `.claude/agents/reviewer.md` and `.claude/skills/security-check/SKILL.md` as the instructions,
then give it `git diff main...HEAD`.

**How to use the result:**
- Must-fix items block the merge. The PR author fixes them or explains why they don't apply.
- Nice-to-have items are the author's call.
- The AI review adds to the human review and doesn't replace it. A human still approves and merges.
