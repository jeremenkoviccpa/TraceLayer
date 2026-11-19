## Verdict: changes requested

Scope: `git diff 376659a..HEAD` (8367e90, d6a8f18, 8e6284c). Checked against `plan.md`, including the plan checkpoint, `ticket.md` and `AGENTS.md`.
Backend `pytest tests/ -q`: 75 passed. `ruff check .`: clean.

## Must-fix
- [x] backend/main.py:151 — No test checks that the production app uses the new handler. `tests/test_rate_limit.py` builds its own app at lines 28-39. No other test mentions `RateLimitExceeded`, the handler or a 429, and `rate_limit()` is a no-op under `APP_ENV=test`. If someone reverted this line to slowapi's `_rate_limit_exceeded_handler`, all 75 tests would still pass, while TL-F001 would quietly reopen and the login page would go back to "Request failed". That breaks the rule that the tests would fail without the change, and this one line is what makes the feature live. Fix: add a one-line test, e.g. `from main import app; assert app.exception_handlers[RateLimitExceeded] is rate_limit_exceeded_handler`.

## Nice-to-have
- [x] backend/tests/test_rate_limit.py:143-144 — The `Retry-After` assertion `0 < retry_after <= 60` can't tell the window-stats path (`backend/core/limiter.py:58-64`) from the fallback (`limiter.py:67`), because both give 60 right after the first hit. I checked by mutation on a scratch copy. With the plan's original call (`get_window_stats(*request.state.view_rate_limit)`, which always throws and falls back) all 7 tests still pass. With a hard-coded `"60"` they also all pass. So the "corrected in code" note in `plan.md` has no test behind it. I separately checked that the real path works: with `time.time` moved 45 s forward, it returns `Retry-After: 15`. Suggestion: patch `core.limiter.time.time` forward and assert the value is below 60.
- [ ] backend/core/limiter.py:20 — `RATE_LIMIT_DETAIL` always says "wait a minute". That's correct for all 7 current limits, which are all `/minute` in `api/v1/auth.py`. It would mislead users if an hourly limit were added later, since `Retry-After` would then say much longer. Consider building the message from the computed `Retry-After`, or adding a comment that ties the text to per-minute limits.
- [x] docs/RUNBOOK.md:304-305 — The runbook says every 429 "writes one WARNING log line". slowapi's own `ratelimit <limit> (<ip>) exceeded at endpoint: <scope>` warning (logger `slowapi`, emitted in `slowapi/extension.py` `__evaluate_limits`) still fires on every 429 too, and root logging is at INFO (`main.py:29-32`). Operators will see two lines per event. Mention the slowapi line and say to count only `rate_limit_exceeded`.

## Security check (`security-check` skill)
- **Audit findings touched:** TL-F001 (§11.4). This diff is its remediation. `docs/TraceLayer_Security_Audit_Report.md` is not changed in the diff, as the plan-checkpoint override of OQ4 requires. The remediation is recorded in `docs/RUNBOOK.md`.
- **1. Secrets:** none. Every grep hit is a variable name, a docstring or a test helper. `"not-the-real-secret-key"` at `backend/tests/test_rate_limit.py:100` is a deliberate wrong-key dummy. No `.env` files are in the diff.
- **2. Tenancy:** none. The diff adds no queries. `company_id` and `user_id` come only from a signature-, expiry- and `type`-checked token (`backend/core/limiter.py:39-52`). Mutation checks: with unverified claims, the wrong-key and expired tests fail; with the `type` check removed, the wrong-type test fails.
- **3. Authz on routes:** none. The diff adds no routes.
- **4. Logs and errors:** none. The log record holds the route template, method, limit, IP and UUIDs only. If the `Authorization` header is added to the record, 5 of the 7 tests fail. The `detail` text is generic and doesn't reveal whether a user exists.

Not part of this review: the ticket's "login page shows the message on desktop and mobile" check is the tester's step. Only `before-*` screenshots exist so far, and they are untracked.

## Fixes
- **Must-fix (main.py wiring), `c936242`:** added `test_production_app_uses_custom_429_handler` in
  `backend/tests/test_rate_limit.py`. It asserts `main.app.exception_handlers[RateLimitExceeded] is rate_limit_exceeded_handler`.
  Mutation check: putting slowapi's `_rate_limit_exceeded_handler` back in `main.py` makes it fail.
- **Nice-to-have 1 (Retry-After path), `c936242`:** added `test_retry_after_uses_time_left_in_window`. It swaps
  `core.limiter.time` for a clock 45 s ahead, so only the handler's clock moves and the limiter storage keeps real
  time, then asserts `Retry-After` is 14–16. Mutation check: the plan's original
  `get_window_stats(*request.state.view_rate_limit)` makes it fail (it gives 60). Also added
  `test_retry_after_falls_back_to_limit_period`, which makes `get_window_stats` raise and asserts the fallback gives `60`.
  The test fixture now exposes the app as `limited_app`, so the tests don't touch httpx private attributes.
- **Nice-to-have 2 ("wait a minute" text):** not changed, as instructed. Recorded under **Follow-ups (implementer)**
  in `plan.md` (`c359b09`).
- **Nice-to-have 3 (runbook wording), `c359b09`:** `docs/RUNBOOK.md` now says slowapi's own `ratelimit ... exceeded at
  endpoint` WARNING from logger `slowapi` also fires, so each 429 shows up as two lines. It says to count or alert
  only on `rate_limit_exceeded`.
- **Results:** `pytest tests/ -q` 78 passed (was 75). `ruff check .` all checks passed.
