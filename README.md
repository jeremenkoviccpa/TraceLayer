# TraceLayer

Continuous compliance evidence collection platform. Connects to your cloud tools and SaaS apps, automatically collects evidence mapped to SOC 2, ISO 27001, and HIPAA controls, and generates audit-ready reports.

**Live:** Railway (backend) + Vercel (frontend)
**Demo account:** `demo@tracelayer.com` / `Demo1234!` (set `SEED_DEMO=true` in Railway to create)

---

## What's Built

### Core Platform
- Multi-tenant SaaS — each company gets isolated data
- JWT auth with refresh token rotation (httpOnly, hashed in DB)
- Role-based access: `admin` and `member`
- Rate-limited auth endpoints (slowapi)
- Fernet encryption for all integration credentials at rest

### Integrations (7)
| Integration | Evidence collected |
|---|---|
| AWS | IAM users, IAM policies, CloudTrail logs |
| GitHub | Repositories, org members, admin members |
| Slack | Users, workspace metadata |
| Google Workspace | Users, admin members, groups |
| Jira | Projects, users |
| Okta | Users, groups, policies |
| Azure AD | Users, groups, role assignments |

All integrations use API key / token auth — no OAuth flow required.

### Compliance Engine
- Scores per control: coverage (70%) + recency (20%) + volume (10%)
- Frameworks: **SOC 2**, **ISO 27001**, **HIPAA**
- Score history snapshots (max once/hour per company+framework)
- Manual controls checklist (pending / compliant / N/A + notes) per framework
- Evidence drill-down: click any control → filtered evidence table

### Reporting
- JSON evidence bundle (all evidence grouped by control)
- PDF audit report (WeasyPrint): cover page, executive summary with score ring, control breakdown table, per-control evidence tables
- Reports stored in Supabase Storage with signed download URLs
- Background task generation (202 Accepted → poll for completion)

### Dashboard
- Compliance score with 30-day trend line (Recharts)
- Evidence activity bar chart (14 days)
- Control breakdown with score bars and missing evidence hints
- Integration staleness badges (yellow >24h, red >48h)
- Action items panel for failing/warning controls
- Onboarding nudge for new accounts

### Team & Org
- Invite members by email (Resend) with 7-day expiry tokens
- Accept invite flow with password setup
- Remove members
- Company name management

### Email (Resend)
- Welcome email on registration → links to onboarding
- Invite email with accept link
- Collection failure alert to company admins
- Password changed notification

### Onboarding
- 3-step wizard: Welcome → Connect integration → Collect → Dashboard
- Auto-skips if integrations already connected

### Landing Page
- Public marketing page at `/`
- Auto-redirects logged-in users to dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy 2.0 async, Pydantic v2 |
| Auth | JWT (python-jose), bcrypt, refresh token rotation |
| Database | PostgreSQL via asyncpg + Alembic migrations |
| Scheduler | APScheduler (24h collection jobs) |
| PDF | Jinja2 + WeasyPrint 62.3 |
| Storage | Supabase Storage (signed URLs) |
| Email | Resend |
| Encryption | Fernet (cryptography) |
| Frontend | Next.js 14, React, TailwindCSS, Recharts |
| Deployment | Railway (backend), Vercel (frontend), Supabase (DB + storage) |

---

## Repository Structure

```
backend/
  api/v1/          # FastAPI routers (auth, integrations, evidence, reports, org, compliance)
  collectors/      # Scheduler + per-job runner
  integrations/    # Adapter per integration type + registry
  migrations/      # Alembic versions (001–008)
  models/          # SQLAlchemy ORM models
  reports/         # Jinja2 template + WeasyPrint generator
  schemas/         # Pydantic request/response schemas
  scripts/         # seed_demo.py
  services/        # Business logic (compliance, report, email, storage, org)
  core/            # Config, DB, security, rate limiter, deps

frontend/
  app/
    (auth)/        # login, register, accept-invite
    (dashboard)/   # dashboard, integrations, evidence, compliance, reports, team, settings, onboarding
  components/      # auth-provider, layout components
  lib/             # api.ts (typed API client), types.ts
```

---

## Getting Started (Local)

**Requirements:** Python 3.11+, Node 18+, Docker

### 1. Start Postgres
```bash
docker-compose up -d
```

### 2. Backend
```bash
cd backend


pip install -r requirements.txt

# macOS WeasyPrint deps
brew install pango

cp .env.example .env  # fill in values
uvicorn main:app --reload
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

### Backend (`backend/.env`)
```bash
# App
APP_ENV=development
SECRET_KEY=<random 32-byte hex>
CORS_ORIGINS=["http://localhost:3000"]
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/tracelayer

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption
FERNET_KEY=<generated with Fernet.generate_key()>

# Supabase Storage (reports)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=<service role key>
STORAGE_BUCKET=reports

# Email (Resend)
RESEND_API_KEY=<optional — logs to stdout if absent>
EMAIL_FROM=TraceLayer <noreply@yourdomain.com>

# Demo seed
SEED_DEMO=false  # set true once to create demo@tracelayer.com account
```

### Frontend (`frontend/.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

All routes prefixed with `/v1`.

**Auth:** `POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` · `PATCH /auth/me`

**Integrations:** `GET /integrations` · `POST /integrations/connect` · `DELETE /integrations/{type}` · `POST /integrations/{type}/collect`

**Evidence:** `GET /evidence?control=&integration=&page=&page_size=`

**Compliance:** `GET /compliance/score?framework=` · `GET /compliance/score-history` · `GET /compliance/evidence-activity` · `GET /compliance/manual-controls?framework=` · `PUT /compliance/manual-controls/{control_id}?framework=`

**Reports:** `POST /reports/generate` · `GET /reports` · `GET /reports/{id}` · `GET /reports/{id}/download?format=json|pdf`

**Org:** `GET /org/company` · `PATCH /org/company` · `GET /org/members` · `DELETE /org/members/{id}` · `GET /org/invites` · `POST /org/invites` · `DELETE /org/invites/{id}` · `POST /org/invites/accept`

**Health:** `GET /health`

---

## Database Migrations

| # | Description |
|---|---|
| 001 | Initial schema (users, companies, integrations, evidence, controls, reports, invitations, refresh tokens) |
| 002 | Invitations table |
| 003 | Report format field |
| 004 | Seed SOC 2 controls |
| 005 | Seed ISO 27001 + HIPAA controls |
| 006 | Report storage fields (bucket, path, mime type, file size) |
| 007 | Compliance score snapshots |
| 008 | Manual controls checklist |

Migrations run automatically on startup via `alembic upgrade head`.

---

## Deployment (Railway + Vercel)

### Backend (Railway)
- Root directory: `backend/`
- Build: Docker (uses `backend/Dockerfile` — includes WeasyPrint system deps)
- Required env vars: `SECRET_KEY`, `DATABASE_URL`, `FERNET_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- Optional: `RESEND_API_KEY`, `EMAIL_FROM`, `SEED_DEMO`, `STORAGE_BUCKET`

### Frontend (Vercel)
- Root directory: `frontend/`
- Framework: Next.js
- Required env var: `NEXT_PUBLIC_API_URL=https://your-railway-backend.up.railway.app`

---

## Roadmap

- [ ] Weekly compliance digest email
- [ ] Integration reconnect UX (inline re-auth when credentials expire)
- [ ] In-app audit log (who connected/disconnected/generated reports)
- [ ] Stripe billing (free tier + paid plans)
- [ ] 2FA / TOTP
- [ ] SSO / SAML
