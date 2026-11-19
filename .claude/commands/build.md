---
description: Implement the plan, review it, fix until the review is clean, then test
argument-hint: <id>
---

Build `docs/plans/$ARGUMENTS/` with this loop:

0. **Baseline:** run the backend tests and lint on the starting commit. If they're already red, stop and tell me. Don't build on a red base.
1. **implementer** follows `plan.md`, committing after each step.
2. **reviewer** reviews `git diff main...HEAD` and writes `review.md`.
3. If `review.md` has open must-fix items, the **implementer** fixes them, then go back to step 2. Stop after 3 rounds and ask me.
4. **tester** adds the tests, runs the suites and the UI check, and writes `test-report.md`.
5. If tests fail, send the failures to the implementer, then repeat steps 2–4.

At the end, give me one line per step: who did what, and how many review rounds it took.
