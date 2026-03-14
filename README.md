# TraceLayer - Continuous Compliance Evidence Collection

TraceLayer is a continuous compliance evidence collection system. It connects to company infrastructure platforms (AWS, GitHub, Slack), collects evidence for compliance controls, normalizes it, stores it in PostgreSQL, and generates reports.

## What This Project Does
- Connects to external integrations (AWS, GitHub, Slack) and validates credentials
- Encrypts integration credentials at rest (Fernet)
- Collects and normalizes evidence, then maps it to control categories
- Stores evidence and report metadata in PostgreSQL
- Generates JSON evidence bundles and PDF reports (WeasyPrint)
- Computes compliance scores per framework based on coverage + recency
- Runs scheduled background collection jobs (default every 24h)
- Supports org member invites and role-based access (admin/user)
- Rate limits auth endpoints in non-test environments
- Exposes a `/health` endpoint

## Tech Stack
- Backend: FastAPI, SQLAlchemy 2.0, Pydantic v2, APScheduler
- Auth: JWT access + refresh tokens
- Storage: PostgreSQL (Supabase compatible)
- Frontend: Next.js 14, React, TailwindCSS
- Reports: Jinja2 + WeasyPrint

## Architecture (High Level)
Frontend (Next.js)
  -> Backend API (FastAPI /v1)
  -> Background Scheduler (APScheduler)
  -> Integration Adapters (AWS/GitHub/Slack)
  -> Evidence Normalization Layer
  -> PostgreSQL
  -> Report Generator (PDF saved to `/tmp/tracelayer_reports`)

## Repository Structure
- `backend/` FastAPI backend and services
- `frontend/` Next.js frontend
- `docker-compose.yml` Local Postgres for development
- `SPEC.md` Detailed system specification

## Getting Started (Local)
Requirements:
- Python 3.11+
- Node 18+
- Docker

### 1) Start Postgres
```bash
docker-compose up -d
```

### 2) Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Migrations run automatically on app startup (skipped in `APP_ENV=test`).

### 3) Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables
Create a `.env` file in `backend/` with:
```bash
# App
APP_ENV=development
SECRET_KEY=<random 32-byte hex>
CORS_ORIGINS=["http://localhost:3000"]
FRONTEND_URL=http://localhost:3000

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/tracelayer

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption
FERNET_KEY=<generated Fernet key>

# Email (Invites)
RESEND_API_KEY=<optional>
EMAIL_FROM="TraceLayer <onboarding@resend.dev>"
```

## API Overview
All routes are prefixed with `/v1`.

Auth:
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`
- `GET /v1/auth/me`

Integrations:
- `GET /v1/integrations`
- `POST /v1/integrations/connect`
- `DELETE /v1/integrations/{integration_type}`
- `POST /v1/integrations/{integration_type}/collect`

Evidence:
- `GET /v1/evidence` (supports `control`, `integration`, `page`, `page_size`)

Reports:
- `POST /v1/reports/generate`
- `GET /v1/reports`
- `GET /v1/reports/{id}`
- `GET /v1/reports/{id}/download?format=json|pdf`

Org:
- `GET /v1/org/members`
- `DELETE /v1/org/members/{user_id}`
- `GET /v1/org/invites`
- `POST /v1/org/invites`
- `DELETE /v1/org/invites/{invite_id}`
- `POST /v1/org/invites/accept`

Compliance:
- `GET /v1/compliance/score?framework=soc2|iso27001|hipaa`

## Current Auth Model
- JWT access token (short-lived)
- Refresh token (rotated, stored hashed in DB)
- Email + password registration/login
- Basic role model: `admin` and `user`

## Integrations & Evidence Types
- AWS: IAM users (`iam_users`), IAM policies (`iam_policies`), CloudTrail events (`cloudtrail_logs`)
- GitHub: org repositories (`repositories`), members (`github_members`), admin members (`github_admin_members`)
- Slack: users (`slack_users`), workspace/team metadata (`slack_workspace`)

## Integration Credentials
- AWS: `access_key_id`, `secret_access_key`, optional `region` (defaults to `us-east-1`)
- GitHub: `token`, `org`
- Slack: `bot_token`

## Supported Frameworks
- SOC 2
- ISO 27001
- HIPAA

Compliance scores are based on evidence coverage, recency, and volume.

## Reports
- JSON report: assembled evidence bundle per control category
- PDF report: generated via WeasyPrint and stored on disk at `/tmp/tracelayer_reports`

PDF generation requires WeasyPrint system deps.
macOS: `brew install pango`
Ubuntu: `apt-get install libpango-1.0-0 libpangoft2-1.0-0`

## Deployment
- Backend: Railway or Render
- Frontend: Vercel
- Database: Supabase

## Roadmap (Short)
- More integrations (Google Workspace, Okta, Jira)
- Continuous monitoring and alerting
- Report export to object storage

## Contributing
PRs are welcome. Please keep changes focused and include tests when relevant.

## License
TBD
