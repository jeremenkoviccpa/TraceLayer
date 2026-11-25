# tl-f001-rate-limit-logging

**Source:** Security audit report, finding **TL-F001** (Medium, "Open — In Progress"),
`docs/TraceLayer_Security_Audit_Report.md` §11.4:

> When the API rate limiter triggers (HTTP 429 responses), the current log entry includes a timestamp and IP address
> but does not include the authenticated tenant identifier or the specific API endpoint targeted.
> **Recommendation:** Add `organization_id` and normalized endpoint path to rate-limit event log entries.

Found during intake: the 429 body from slowapi's default handler is `{"error": "Rate limit exceeded: 10 per 1 minute"}`.
`frontend/lib/api.ts` reads `json.detail`, so a user who hits the login limit only sees **"Request failed"**.

## Problem
- **Security/ops:** we can't tell whether a burst of 429s targets one tenant, or which endpoint is being hit, so the
  partner-facing audit finding stays open.
- **Users:** someone locked out by the login limit gets a vague error and no hint to wait.

## Acceptance criteria
- [ ] Every 429 from the limiter writes one structured log record `rate_limit_exceeded` with: normalized route
      template (e.g. `/v1/auth/login`, not raw path with IDs), HTTP method, the limit that was hit, client IP, and
      `company_id` / `user_id` when the request carries a **valid** access token (else `null`).
- [ ] The log never contains tokens, passwords, emails or request bodies.
- [ ] The 429 response body has a human `detail` message (and keeps `error` for backward compatibility); the
      `Retry-After` behaviour is no worse than today.
- [ ] Login page shows that message on desktop and mobile.
- [ ] Tests cover: the log fields for an anonymous request, the tenant fields for an authenticated request, a forged
      token not being trusted, and the response body.

## Out of scope
- Changing any rate-limit values or which routes are limited.
- Per-tenant rate-limit keys (limits stay per-IP).
- Shipping logs to a SIEM / alerting on them.
