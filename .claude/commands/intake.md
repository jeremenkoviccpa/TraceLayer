---
description: Turn a GitHub issue, audit finding or free text into docs/plans/<id>/ticket.md
argument-hint: <issue-number | url | text>
---

Create a ticket for: $ARGUMENTS

1. If it's a GitHub issue number or URL, read it with `gh issue view`. Otherwise use the text as given.
2. Pick an id: the issue number if there is one (`gh-123`), otherwise a short slug (`tl-f001-rate-limit-logging`).
3. Write `docs/plans/<id>/ticket.md`:
   - **Source:** a link or a quote
   - **Problem:** what's wrong, and who notices
   - **Acceptance criteria:** a checklist of things someone can verify
   - **Out of scope**
4. Print the id and the path. Don't plan or write code yet.
