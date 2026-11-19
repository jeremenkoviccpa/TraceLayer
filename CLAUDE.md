Read and follow `AGENTS.md`. It is the source of truth for this repo.

## Claude Code notes

- Subagents live in `.claude/agents/` (planner, implementer, reviewer, tester). Slash commands are in `.claude/commands/`: `/intake`, `/plan`, `/build`, `/ship`.
- Skills are in `.claude/skills/`: `api-endpoint`, `ui-check`, `security-check`. Use them instead of re-deriving the pattern.
- Use plan mode for anything bigger than a one-file fix. The written plan goes to `docs/plans/<id>/plan.md`.
- Don't push or open PRs unless the user asks.
