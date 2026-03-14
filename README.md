# TraceLayer - Continuous Compliance Evidence Collection

TraceLayer is a continuous compliance evidence collection system. It connects to company infrastructure platforms (AWS, GitHub, Slack, etc.), collects evidence related to security and compliance controls, normalizes it, stores it with an audit trail, and generates compliance reports.

## What This Project Does
- Connects to external integrations (AWS, GitHub, Slack)
- Collects and normalizes evidence for compliance controls
- Stores evidence in PostgreSQL with auditability
- Generates PDF and JSON reports
- Runs scheduled background collection jobs

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
  -> Report Generator -> Object Storage

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
alembic upgrade head
uvicorn main:app --reload
```

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

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/tracelayer

# JWT
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Encryption
FERNET_KEY=<generated Fernet key>

# Storage
STORAGE_BUCKET=tracelayer-reports
STORAGE_ENDPOINT=<supabase or s3 endpoint>
STORAGE_ACCESS_KEY=<key>
STORAGE_SECRET_KEY=<secret>
```

## API Overview
All routes are prefixed with `/v1`.

Auth:
- `POST /v1/auth/register`
- `POST /v1/auth/login`
- `POST /v1/auth/refresh`
- `POST /v1/auth/logout`

Integrations:
- `GET /v1/integrations`
- `POST /v1/integrations/connect`
- `DELETE /v1/integrations/{integration_type}`
- `POST /v1/integrations/{integration_type}/collect`

Evidence:
- `GET /v1/evidence`

Reports:
- `POST /v1/reports/generate`
- `GET /v1/reports`
- `GET /v1/reports/{id}`

## Current Auth Model
- JWT access token (short-lived)
- Refresh token (stored hashed in DB)
- Email + password registration/login

## Initial Integrations
- AWS (IAM, CloudTrail)
- GitHub (repos, collaborators, commits)
- Slack (users, admins, workspace config)

## Deployment
- Backend: Railway or Render
- Frontend: Vercel
- Database: Supabase

## Roadmap (Short)
- ISO 27001 support
- More integrations (Google Workspace, Okta, Jira)
- Continuous monitoring and alerting
- Compliance scoring

## Contributing
PRs are welcome. Please keep changes focused and include tests when relevant.

## License
TBD
