---
description: Write the summary, changelog line and PR description for a finished task
argument-hint: <id>
---

For `docs/plans/$ARGUMENTS/`:

1. Check the definition of done in `AGENTS.md`. Every item needs evidence in the folder. If any is missing, say which and stop.
2. Write `docs/plans/$ARGUMENTS/pr.md` with:
   - **Summary:** 2–3 sentences
   - **Changelog:** one line, user-facing
   - **PR description:** what changed, why, how it was tested (link `test-report.md` and the screenshots) and what the review caught (link `review.md`)
3. Don't push or open the PR. Print the `gh pr create` command for me to run.
