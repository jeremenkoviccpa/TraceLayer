# Plan: tl-f001-rate-limit-logging

**Goal:** Replace slowapi's default 429 handler with one that writes a tenant- and route-aware `rate_limit_exceeded` log record and returns a human `detail`, closing audit finding TL-F001.

## Scope
- **In:** a custom `RateLimitExceeded` handler in `core/limiter.py`, wired in `main.py`; a 429 body of `{detail, error}`; a `Retry-After` header on 429s (see OQ2); backend tests; a check that the login page shows the message.
- **Out:** rate-limit values and which routes are limited (all 8 limited routes are in `api/v1/auth.py`); per-tenant keys; SIEM/alerting; a JSON log formatter for the whole app; fixing `X-Forwarded-For` handling for the client IP.

## Steps
1. **Handler + log record.** `backend/core/limiter.py`: add `rate_limit_exceeded_handler(request, exc)`.
   - Route: `request.scope["route"].path`, the template such as `/v1/auth/login`. Use `null` when there is no route.
   - Fields: `method`, `limit=str(exc.limit.limit)`, `client_ip=get_remote_address(request)`.
   - Tenant: read `Authorization: Bearer`, then `decode_access_token`. Accept the token only if the signature and expiry are valid and `type == "access"`. On any error (`JWTError`, wrong type, missing claims), set `company_id` and `user_id` to `null`. No DB lookup.
   - Logging: `logger.warning("rate_limit_exceeded %s", json.dumps(fields), extra={"rate_limit": fields})`. Never log the header, token, query string or body.
2. **Response.** Same handler. Return `JSONResponse(429, {"detail": "Too many attempts. Please wait a minute and try again.", "error": "Rate limit exceeded: <limit>"})`.
   - Keep the call to `limiter._inject_headers(...)` (a no-op today, because `headers_enabled=False`).
   - Then set `Retry-After` to the seconds left in the window. Get the reset time from `limiter.limiter.get_window_stats(*request.state.view_rate_limit)`. If that fails, fall back to the limit's period in seconds.
3. **Wire it.** `backend/main.py`: import the new handler and use it in place of `_rate_limit_exceeded_handler`. Drop the unused import.
4. **Tests.** New `backend/tests/test_rate_limit.py`. Build a tiny FastAPI app with a fresh `Limiter`, our handler, and a `/v1/things/{thing_id}` route limited to `1/minute`. This gives a real 429 even under `APP_ENV=test`. Cases are under **Test plan**.
5. **Docs.** Add a short runbook note in `docs/RUNBOOK.md` covering the log line name, its fields and how to query it. Don't edit the audit report (see OQ4).

## Risks
- **Auth/tenancy:** a forged or expired token must never set `company_id`. Only signature-verified claims are used. The partner context switch puts the acting tenant's `company_id` in the claim, which is the right one to log.
- **Existing issue (not fixed here):** the 2FA `totp_token` (`auth.py:137`) is a full `type: "access"` token. It will be logged like any other access token. Flag it to security separately.
- **Secrets/PII:** the log record must not contain the header, token, email or body. A test asserts this.
- **Behaviour other code depends on:** we keep `error` in the body, and the frontend already reads `detail`. Turning on slowapi `headers_enabled` globally would make every limited route need a `response` param, so we don't.
- **Migrations:** none.

## Test plan
- **Anonymous 429:** exactly one `rate_limit_exceeded` record with `route == "/v1/things/{thing_id}"` (not `/v1/things/123`), method, limit and IP, and `company_id`/`user_id` set to `None`.
- **Authenticated 429:** a token from `create_access_token` yields the matching `company_id`/`user_id`.
- **Forged token:** signed with the wrong key, or expired, gives `None` for both fields. The log text contains no token substring and no email.
- **Response:** status 429, a `detail` string, `error` kept, and a `Retry-After` integer greater than 0.
- **Commands:** `cd backend && pytest tests/ -q && ruff check .`. No frontend code change, so `tsc`/`build` are optional.
- **UI check:** run uvicorn with `APP_ENV=development`, fail login 11 times, then take desktop and mobile screenshots of the message. Save them to `docs/plans/tl-f001-rate-limit-logging/screenshots/`.

## Decision record
None. This is a local handler change, not a lasting design choice.

## Open questions (defaults assumed above, marked OQ)
1. **Field name:** the audit says `organization_id`, the codebase says `company_id`. **Default: `company_id`.**
2. **`Retry-After`:** slowapi sends none today (`headers_enabled=False`), so "no worse" is already met. **Default: add it in the handler only (step 2).**
3. **Frontend fallback** for a 429 without JSON, for example from a proxy. **Default: no `api.ts` change.** The backend `detail` is enough.
4. **Audit report status:** **Default: update §11.4 to "Resolved" with the PR link in the same PR.**

## Plan checkpoint (orchestrator, 09:26)
- OQ1–3: defaults accepted.
- **OQ4 overridden:** the audit report is a third-party assessor's signed attestation, so we don't edit its findings
  register. Record the remediation in `docs/RUNBOOK.md` and the PR; the owner tells the assessor.
- Follow-up ticket to open: the 2FA `totp_token` is a full access token (`auth.py:137`).

## Follow-ups (implementer)
- **Client IP behind the proxy:** Railway/Procfile/Dockerfile start uvicorn without `--forwarded-allow-ips`, so uvicorn
  ignores `X-Forwarded-For` from Railway's proxy. `client_ip` in the new log line (and the per-IP limit key itself) is
  then likely the proxy's address. Out of scope here (see **Out**); worth its own ticket. Noted in `docs/RUNBOOK.md`.
- **Plan detail corrected in code:** slowapi stores `request.state.view_rate_limit` as `(RateLimitItem, [key, scope])`,
  so the call is `get_window_stats(item, *args)`, not `get_window_stats(*view_rate_limit)`.
- **Route count:** `api/v1/auth.py` has 7 `@rate_limit` routes, not 8 as the Scope says. No code impact.
- **429 message assumes per-minute limits (review round 1, nice-to-have 2):** `RATE_LIMIT_DETAIL` in
  `backend/core/limiter.py` always says "wait a minute". True for all 7 current limits (all `/minute`), but an hourly
  limit added later would contradict its `Retry-After`. Build the text from the computed `Retry-After`, or tie it to
  per-minute limits, when that happens.
