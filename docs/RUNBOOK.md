# TraceLayer Operations Runbook

> Last updated: March 2026
> On-call contact: support@tracelayer.it.com

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Environment Variables](#environment-variables)
3. [Backup Strategy](#backup-strategy)
4. [Recovery Procedures](#recovery-procedures)
5. [Uptime Monitoring Setup](#uptime-monitoring-setup)
6. [Deployment Process](#deployment-process)
7. [Incident Response Checklist](#incident-response-checklist)
8. [Sentry Error Monitoring](#sentry-error-monitoring)

---

## Architecture Overview

| Layer       | Provider    | URL / Identifier                    |
|-------------|-------------|-------------------------------------|
| Frontend    | Vercel      | tracelayer.it.com                   |
| API backend | Railway     | api.tracelayer.it.com               |
| Database    | Supabase    | PostgreSQL (us-east-1)              |
| Storage     | Supabase    | Evidence files, audit PDFs          |
| Email       | Resend      | Transactional + weekly reports      |
| Error mon.  | Sentry      | Frontend + backend DSNs             |
| Payments    | LemonSqueezy| Growth plan checkouts               |
| AI          | Groq        | Audit package narrative generation  |

**Data flow:**
User → Vercel (Next.js) → Railway (FastAPI) → Supabase (Postgres + Storage)

---

## Environment Variables

### Backend (Railway)

| Variable                        | Description                                  |
|---------------------------------|----------------------------------------------|
| `DATABASE_URL`                  | Supabase PostgreSQL connection string        |
| `SECRET_KEY`                    | JWT signing key (min 32 chars, random)       |
| `FERNET_KEY`                    | Credential encryption key (Fernet-encoded)   |
| `RESEND_API_KEY`                | Resend API key for email delivery            |
| `EMAIL_FROM`                    | Sender address (e.g. noreply@tracelayer.it.com) |
| `APP_FRONTEND_URL`              | https://tracelayer.it.com                    |
| `BACKEND_URL`                   | https://api.tracelayer.it.com                |
| `SENTRY_DSN`                    | Backend Sentry DSN                           |
| `GOOGLE_CLIENT_ID`              | Google OAuth client ID                       |
| `GOOGLE_CLIENT_SECRET`          | Google OAuth client secret                   |
| `LS_API_KEY`                    | LemonSqueezy API key                         |
| `LS_STORE_ID`                   | LemonSqueezy store ID                        |
| `LS_GROWTH_VARIANT_ID`          | LemonSqueezy variant ID for Growth plan      |
| `LS_PARTNER_CLIENT_VARIANT_ID`  | LemonSqueezy variant ID for partner clients  |
| `LS_WEBHOOK_SECRET`             | LemonSqueezy webhook signing secret          |
| `GROQ_API_KEY`                  | Groq API key for AI features                 |
| `APP_ENV`                       | `production` / `development` / `test`        |

### Frontend (Vercel)

| Variable                        | Description                                  |
|---------------------------------|----------------------------------------------|
| `NEXT_PUBLIC_API_URL`           | https://api.tracelayer.it.com                |
| `NEXT_PUBLIC_SENTRY_DSN`        | Frontend Sentry DSN                          |
| `NEXT_PUBLIC_CRISP_WEBSITE_ID`  | Crisp live chat website ID (optional)        |

---

## Backup Strategy

### Database (Supabase)

Supabase automatically takes **daily point-in-time backups** retained for **7 days** on the free plan and **30 days** on paid plans. Backups are stored in a separate AWS region.

**Manual backup (run before migrations):**
```bash
pg_dump "$DATABASE_URL" \
  --format=custom \
  --no-owner \
  --no-privileges \
  -f "backup_$(date +%Y%m%d_%H%M%S).pgdump"
```

**Supabase dashboard backup:**
Project → Settings → Database → Backups → Download

**Backup verification schedule:**
Monthly — attempt a restore to a staging database and verify row counts.

### Object Storage (Supabase Storage)

Evidence files and generated PDF reports are stored in Supabase Storage buckets:
- `evidence` — raw evidence JSON and attached files
- `reports` — generated audit package PDFs

These buckets use Supabase's underlying S3-compatible storage which is replicated within the region. For an additional off-site copy, run the following monthly:

```bash
# Using Supabase CLI
supabase storage ls evidence
# Download critical files via the API or dashboard
```

### Configuration / Secrets

All environment variables are stored in Railway (backend) and Vercel (frontend). Document all variables in the table above and store a master copy in your password manager.

**Critical secret rotation checklist:**
- [ ] `SECRET_KEY` — rotate every 12 months; all existing JWTs will be invalidated on rotation
- [ ] `FERNET_KEY` — rotate requires re-encrypting all stored integration credentials; plan carefully
- [ ] `RESEND_API_KEY` — rotate immediately if compromised; email will stop until updated
- [ ] `GOOGLE_CLIENT_SECRET` — rotate in Google Cloud Console → update in Railway

---

## Recovery Procedures

### Scenario 1: Database corruption or accidental data deletion

1. **Identify scope** — determine which tables and time window are affected using the audit log
2. **Stop writes** — set `APP_ENV=maintenance` in Railway to return 503 (or deploy a maintenance page)
3. **Restore from Supabase backup:**
   - Go to Supabase Dashboard → Settings → Database → Backups
   - Select the last known-good backup
   - Click "Restore" (this creates a new project — swap the `DATABASE_URL` once done)
4. **Replay missed writes** if partial data can be recovered from application logs
5. **Verify** — check row counts on `users`, `companies`, `evidence`, `integrations`
6. **Resume** — remove maintenance flag, monitor error rate in Sentry

**RTO target:** < 4 hours
**RPO target:** < 24 hours (daily backup cadence)

### Scenario 2: Railway backend goes down

1. Check Railway dashboard for deployment errors or resource limits
2. Check Sentry for the most recent backend errors
3. If a bad deployment: Railway → Service → Deployments → click previous deployment → "Redeploy"
4. If region-level issue: Railway provides status at status.railway.app
5. The frontend will show errors but data is safe in Supabase

### Scenario 3: Encryption key loss (FERNET_KEY)

> **This is a critical scenario.** If the Fernet key is lost, all stored integration credentials become unrecoverable.

1. Set maintenance mode immediately
2. Notify affected customers
3. Ask customers to reconnect all integrations (credentials will need to be re-entered)
4. Generate a new Fernet key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
5. Deploy with new key
6. Remove maintenance mode

**Prevention:** Store the Fernet key in a password manager AND your cloud secrets manager. Never store only in Railway.

### Scenario 4: Vercel frontend outage

1. Check Vercel status at vercel-status.com
2. If a failed deployment, roll back: Vercel Dashboard → Project → Deployments → Promote previous deployment
3. The API and database remain unaffected

---

## Uptime Monitoring Setup

Point your uptime monitoring service at the health endpoint:

```
GET https://api.tracelayer.it.com/health
Expected response: {"status": "ok", "db": "ok"}
Check interval: 1 minute
Alert threshold: 2 consecutive failures
```

**Recommended services (free tiers available):**

| Service       | Setup                                                            |
|---------------|------------------------------------------------------------------|
| UptimeRobot   | uptimerobot.com → Add Monitor → HTTP(S) → paste URL above        |
| Better Uptime | betteruptime.com → Add monitor → Keyword monitor for `"ok"`     |
| statuspage.io | For a hosted public status page with subscriber notifications   |

**Add a status badge to this README once configured.**

Also monitor the frontend:
```
GET https://tracelayer.it.com
Expected: HTTP 200
```

---

## Deployment Process

### Backend (Railway)

Railway auto-deploys from the `main` branch on GitHub push.

```bash
# Manual deploy trigger
railway up

# View logs
railway logs --tail

# Run migrations manually (runs automatically on startup)
railway run alembic upgrade head
```

### Frontend (Vercel)

Vercel auto-deploys from the `main` branch.

```bash
# Manual deploy
vercel --prod

# Preview deploy
vercel
```

### Database migrations

Alembic migrations run automatically on backend startup via the advisory lock mechanism in `main.py`. To run manually:

```bash
cd backend
alembic upgrade head          # apply all pending
alembic downgrade -1          # roll back one
alembic history               # show migration history
alembic current               # show current revision
```

**Before any migration:**
1. Take a manual database backup (see above)
2. Test the migration on a staging database first
3. Deploy during low-traffic hours
4. Have the downgrade command ready

---

## Incident Response Checklist

When something goes wrong:

- [ ] **Acknowledge** — post in team Slack/chat that someone is investigating
- [ ] **Assess severity** — is customer data at risk? Is the service completely down?
- [ ] **Check Sentry** — look for error spikes in the last 15 minutes
- [ ] **Check Railway logs** — `railway logs --tail` or via dashboard
- [ ] **Check Supabase** — dashboard → health indicators
- [ ] **Update status page** — tracelayer.it.com/status (update manually or via a status service)
- [ ] **Notify customers** if impact is >15 minutes or data is affected
- [ ] **Resolve** — deploy fix or rollback
- [ ] **Post-mortem** — document root cause, timeline, and follow-up actions within 48 hours

**Breach notification requirement:** If personal data is involved, notify affected customers within **72 hours** per GDPR Article 33.

---

## Sentry Error Monitoring

### Backend

Sentry is initialised in `backend/main.py` when `SENTRY_DSN` is set:

```python
sentry_sdk.init(
    dsn=settings.sentry_dsn,
    environment=settings.app_env,
    traces_sample_rate=0.2,
    profiles_sample_rate=0.1,
)
```

### Frontend

Sentry is initialised in `sentry.client.config.ts` and `sentry.server.config.ts` when `NEXT_PUBLIC_SENTRY_DSN` is set.

### Alert configuration (set up in Sentry dashboard)

- **Error rate spike** → alert if >10 new errors in 5 minutes → notify on-call via email
- **New issue** → alert immediately for unhandled exceptions
- **Performance** → alert if p95 API latency exceeds 3 seconds

To test that Sentry is working:
```bash
# Backend test (triggers a test exception)
curl -X POST https://api.tracelayer.it.com/sentry-test  # if endpoint exists

# Frontend test: add ?sentry_test=1 to any URL and check the Sentry dashboard
```
