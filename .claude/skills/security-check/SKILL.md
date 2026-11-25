---
name: security-check
description: Security pass over a diff in TraceLayer, covering secrets, tenant data leaks, authz on new routes and sensitive data in logs. The reviewer uses it on every task. Use it alone before merging anything that touches auth, routes, logging or integrations.
---

# Security check

Reference: `docs/TraceLayer_Security_Audit_Report.md`, sections 5 (access control, tenancy) and 11 (findings TL-F001…F007).
If the diff touches one of those findings, say so in the review.

Run against `git diff main...HEAD`:

## 1. Secrets
```bash
git diff main...HEAD | grep -nEi '(api[_-]?key|secret|password|token|BEGIN [A-Z ]*PRIVATE KEY|sk_live|AKIA[0-9A-Z]{16})' | grep '^+' 
```
Each hit is either a variable name (fine) or a value (must-fix). `.env` files never belong in the diff. Docs must not contain real logins, including the demo account in the README.

## 2. Tenancy
- Every new or changed query on customer data has `company_id == current_user.company_id`.
- No `company_id`, `user_id` or `org_id` is taken from the request body or query and used without checking it against the current user.
- Lists, exports and reports: could company A see one of company B's rows? If it's unclear, the tests should cover it (see `test_*_isolated_between_companies`).

## 3. Authz on routes
- Every new route has `get_current_user`, `get_current_admin` or a documented reason to be public (the `public.py` and `trust.py` patterns).
- Admin-only actions such as members, billing, integrations and API keys use `get_current_admin`.
- Public or unauthenticated routes have `@rate_limit(...)`.

## 4. Logs and errors
- Nothing sensitive in log calls: passwords, tokens, refresh tokens, emails, integration credentials or request bodies.
- Tenant and user IDs (UUIDs) are fine to log and help with investigations (TL-F001).
- Error `detail` strings don't leak stack traces, SQL or whether a user exists.

Report each issue as a must-fix with a `file:line`. If a section has nothing, write "none".
