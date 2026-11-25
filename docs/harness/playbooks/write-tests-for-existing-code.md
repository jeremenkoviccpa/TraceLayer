# Write tests for existing code

**When:** code works but has no tests, and you want to change it safely later.

```text
/intake "Add tests for services/compliance_service.py score calculation (no behaviour change)"
/plan compliance-score-tests
/build compliance-score-tests
```

**Prompt for any tool:**

> Follow AGENTS.md. Use the tester role (.claude/agents/tester.md). Target: <file or module>. Don't change
> production code. Read it, list the behaviours worth pinning (happy path, edge cases, tenancy isolation, auth
> failures), then write tests in backend/tests/ using the fixtures in conftest.py. Run `pytest tests/ -q`.
> If a test reveals a bug, mark it `xfail` with a reason and list it in test-report.md. Don't fix it in the same task.

**Good tests here:**
- Use the `client` fixture and go through the HTTP API, like the existing `test_*.py` files.
- Always include a test that one company can't see another company's data.
- A test should fail if you revert the code it protects. If it wouldn't, it isn't testing anything.
