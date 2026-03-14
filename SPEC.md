# TraceLayer — Technical Architecture & Developer Specification

> Internal developer document. Not for distribution.

---

## 1. System Overview

TraceLayer is a **continuous compliance evidence collection system**.

It connects to company infrastructure platforms (AWS, GitHub, Slack, etc.), collects evidence related to security and compliance controls, normalizes that evidence, stores it in a structured format, and generates compliance reports.

Primary responsibilities:

- Collect infrastructure and system evidence from external integrations
- Normalize evidence into a unified format
- Map evidence to compliance controls (SOC 2, ISO 27001, etc.)
- Store evidence records with full audit trail
- Generate structured compliance reports (PDF and JSON)

Architecture style: **modular monolithic backend with pluggable integration adapters**.

---

## 2. High-Level Architecture

```
Frontend (Next.js)
        ↓
Backend API (FastAPI /v1/)
        ↓
Background Job Scheduler (APScheduler)
        ↓
Integration Adapters (AWS / GitHub / Slack / ...)
        ↓
Evidence Normalization Layer
        ↓
PostgreSQL Database (Supabase)
        ↓
Report Generator → Object Storage (Supabase Storage / S3)
```

---

## 3. Technology Stack

### Frontend
| Tool | Purpose |
|---|---|
| Next.js 14 | App framework |
| React | UI |
| TailwindCSS | Styling |
| shadcn/ui | Component library |

### Backend
| Tool | Purpose |
|---|---|
| Python 3.11+ | Runtime |
| FastAPI | API framework |
| Pydantic v2 | Data validation and schemas |
| SQLAlchemy 2.0 | ORM |
| Alembic | Database migrations |
| APScheduler | Background scheduled jobs |
| cryptography (Fernet) | Credential encryption at rest |
| python-jose | JWT token handling |
| httpx | Async HTTP client for integrations |
| Jinja2 | Report templates |
| WeasyPrint | HTML to PDF rendering |

### Database
| Tool | Purpose |
|---|---|
| PostgreSQL 15 (Supabase) | Primary database |

### Storage
| Tool | Purpose |
|---|---|
| Supabase Storage or S3-compatible | Report file storage |

### Hosting
| Layer | Provider |
|---|---|
| Frontend | Vercel |
| Backend | Railway or Render |
| Database | Supabase |

---

## 4. Repository Structure

```
tracelayer/
├── backend/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── integrations.py
│   │       ├── evidence.py
│   │       └── reports.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── evidence_service.py
│   │   ├── collector_service.py
│   │   └── report_service.py
│   ├── models/
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── integration.py
│   │   ├── evidence.py
│   │   ├── control.py
│   │   └── report.py
│   ├── integrations/
│   │   ├── base.py           # Abstract base class
│   │   ├── registry.py       # Integration factory registry
│   │   ├── aws/
│   │   │   └── adapter.py
│   │   ├── github/
│   │   │   └── adapter.py
│   │   └── slack/
│   │       └── adapter.py
│   ├── collectors/
│   │   ├── runner.py         # Collector execution engine
│   │   └── scheduler.py      # APScheduler setup
│   ├── reports/
│   │   ├── generator.py
│   │   └── templates/
│   │       └── report.html.j2
│   ├── utils/
│   │   ├── encryption.py     # Fernet helpers
│   │   ├── pagination.py
│   │   └── logging.py
│   ├── core/
│   │   ├── config.py         # Settings from env vars
│   │   ├── database.py       # SQLAlchemy session
│   │   └── security.py       # JWT logic
│   ├── migrations/           # Alembic migrations
│   ├── tests/
│   ├── main.py               # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── app/
│   ├── components/
│   └── lib/
├── docs/
│   └── SPEC.md
└── infrastructure/
    └── docker-compose.yml    # Local dev environment
```

---

## 5. Environment Configuration

All secrets and environment-specific values are managed via environment variables. Never hardcode credentials.

### Backend `.env`
```
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

Use `pydantic-settings` for typed config loading:

```python
# core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str
    secret_key: str
    database_url: str
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    fernet_key: str
    storage_bucket: str
    storage_endpoint: str
    storage_access_key: str
    storage_secret_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 6. Authentication Model

### Strategy
- JWT-based authentication
- Access token (short-lived, 30 min) + Refresh token (long-lived, 7 days)
- All protected routes require `Authorization: Bearer <access_token>` header
- Data access is strictly scoped by `company_id`

### Database Tables

**users**
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
email           TEXT UNIQUE NOT NULL
password_hash   TEXT NOT NULL
company_id      UUID NOT NULL REFERENCES companies(id)
role            TEXT NOT NULL DEFAULT 'member'   -- 'admin' | 'member'
created_at      TIMESTAMPTZ DEFAULT now()
```

**companies**
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
name        TEXT NOT NULL
created_at  TIMESTAMPTZ DEFAULT now()
```

**refresh_tokens**
```
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id     UUID NOT NULL REFERENCES users(id)
token_hash  TEXT NOT NULL
expires_at  TIMESTAMPTZ NOT NULL
created_at  TIMESTAMPTZ DEFAULT now()
```

### Token Flow
1. `POST /v1/auth/login` → returns `{ access_token, refresh_token }`
2. Client includes `access_token` in every request header
3. When access token expires, client calls `POST /v1/auth/refresh` with `refresh_token`
4. `POST /v1/auth/logout` invalidates the refresh token

---

## 7. Integration Framework

### Abstract Base Class

All integrations extend `IntegrationAdapter`:

```python
# integrations/base.py
from abc import ABC, abstractmethod
from typing import Any

class IntegrationAdapter(ABC):

    @abstractmethod
    def connect(self, credentials: dict) -> bool:
        """
        Validate credentials against the external API.
        Returns True if connection is successful.
        Raises IntegrationAuthError if credentials are invalid.
        """
        pass

    @abstractmethod
    def collect_evidence(self) -> list[dict]:
        """
        Fetch raw data from external system API.
        Must handle pagination and rate limiting internally.
        Returns list of raw evidence dicts.
        """
        pass

    @abstractmethod
    def normalize(self, raw_data: list[dict]) -> list[dict]:
        """
        Convert raw API data into normalized EvidenceRecord format.
        Returns list of normalized evidence dicts.
        """
        pass
```

### Rate Limit Handling

All integration adapters must implement retry logic with exponential backoff for rate-limited API responses (HTTP 429):

```python
# utils/retry.py
import asyncio
import httpx

async def request_with_backoff(client: httpx.AsyncClient, url: str, **kwargs) -> httpx.Response:
    for attempt in range(5):
        response = await client.get(url, **kwargs)
        if response.status_code == 429:
            wait = 2 ** attempt
            await asyncio.sleep(wait)
            continue
        response.raise_for_status()
        return response
    raise Exception("Max retries exceeded")
```

---

## 8. Integration Registry

The registry is a **factory**, not a collection of singletons. It returns a fresh adapter instance per call, allowing each collection job to load company-specific decrypted credentials.

```python
# integrations/registry.py
from integrations.aws.adapter import AWSIntegration
from integrations.github.adapter import GithubIntegration
from integrations.slack.adapter import SlackIntegration

INTEGRATION_REGISTRY: dict[str, type] = {
    "aws": AWSIntegration,
    "github": GithubIntegration,
    "slack": SlackIntegration,
}

def get_adapter(integration_type: str) -> object:
    cls = INTEGRATION_REGISTRY.get(integration_type)
    if not cls:
        raise ValueError(f"Unknown integration type: {integration_type}")
    return cls()   # fresh instance every time
```

---

## 9. Credential Encryption

Integration credentials are encrypted with **Fernet** (AES-128-CBC + HMAC) before storage. The Fernet key is stored as an environment variable, never in the database.

```python
# utils/encryption.py
from cryptography.fernet import Fernet
from core.config import settings
import json

_fernet = Fernet(settings.fernet_key.encode())

def encrypt_credentials(credentials: dict) -> str:
    return _fernet.encrypt(json.dumps(credentials).encode()).decode()

def decrypt_credentials(encrypted: str) -> dict:
    return json.loads(_fernet.decrypt(encrypted.encode()).decode())
```

Credentials are decrypted only inside the collector at runtime and never logged or returned via API.

---

## 10. Evidence Collection Flow

```
1. Scheduler triggers collector job (scheduled or manual)
2. Collector loads integration record from DB (by company_id + integration_type)
3. Credentials are decrypted in memory
4. Fresh adapter instance fetched from registry
5. adapter.connect(credentials) called to validate
6. adapter.collect_evidence() fetches raw data (with rate limit handling)
7. adapter.normalize(raw_data) produces EvidenceRecord list
8. Each EvidenceRecord is upserted into evidence table (idempotency)
9. Collector job status updated in integrations table
```

### Idempotency

Each evidence record has a deterministic `source_id` derived from the external object (e.g., GitHub user login, AWS IAM user ARN). Upserting on `(company_id, integration, evidence_type, source_id)` ensures re-running a collector never creates duplicate records.

---

## 11. Evidence Object Format

Normalized evidence produced by adapters:

```json
{
  "company_id": "uuid",
  "integration": "aws",
  "control": "access_control",
  "evidence_type": "iam_users",
  "source_id": "arn:aws:iam::123456789012:user/john",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "username": "john",
    "mfa_enabled": true,
    "last_login": "2024-01-14T08:00:00Z"
  }
}
```

---

## 12. Database Schema

All tables use UUIDs for primary keys. All timestamps are `TIMESTAMPTZ`.

### evidence
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
company_id      UUID NOT NULL REFERENCES companies(id)
integration     TEXT NOT NULL
control         TEXT NOT NULL
evidence_type   TEXT NOT NULL
source_id       TEXT NOT NULL
timestamp       TIMESTAMPTZ NOT NULL
data            JSONB NOT NULL
created_at      TIMESTAMPTZ DEFAULT now()
updated_at      TIMESTAMPTZ DEFAULT now()

UNIQUE(company_id, integration, evidence_type, source_id)
INDEX ON (company_id, control)
INDEX ON (company_id, integration)
```

### integrations
```
id                  UUID PRIMARY KEY DEFAULT gen_random_uuid()
company_id          UUID NOT NULL REFERENCES companies(id)
integration_type    TEXT NOT NULL
credentials_enc     TEXT NOT NULL        -- Fernet-encrypted JSON
status              TEXT NOT NULL DEFAULT 'active'   -- 'active' | 'error' | 'disconnected'
last_collected_at   TIMESTAMPTZ
last_error          TEXT
created_at          TIMESTAMPTZ DEFAULT now()

UNIQUE(company_id, integration_type)
```

### controls
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
name            TEXT NOT NULL
framework       TEXT NOT NULL    -- 'soc2' | 'iso27001' | 'hipaa'
category        TEXT NOT NULL    -- 'access_control' | 'change_management' | etc.
description     TEXT
```

### evidence_controls
```
evidence_id     UUID REFERENCES evidence(id)
control_id      UUID REFERENCES controls(id)
PRIMARY KEY (evidence_id, control_id)
```

### reports
```
id              UUID PRIMARY KEY DEFAULT gen_random_uuid()
company_id      UUID NOT NULL REFERENCES companies(id)
report_type     TEXT NOT NULL
framework       TEXT NOT NULL
status          TEXT NOT NULL DEFAULT 'pending'   -- 'pending' | 'complete' | 'error'
file_url        TEXT                              -- Object storage URL, set when complete
generated_at    TIMESTAMPTZ
created_at      TIMESTAMPTZ DEFAULT now()
```

---

## 13. Background Jobs

APScheduler runs inside the FastAPI process (sufficient for MVP). Each company with active integrations gets a scheduled collection job.

```python
# collectors/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from collectors.runner import run_collector

scheduler = AsyncIOScheduler()

def schedule_company(company_id: str, interval_hours: int = 24):
    scheduler.add_job(
        run_collector,
        "interval",
        hours=interval_hours,
        args=[company_id],
        id=f"collect_{company_id}",
        replace_existing=True,
    )

def start():
    scheduler.start()
```

Scheduler is started on FastAPI startup event in `main.py`.

Job failures are caught, logged, and written to `integrations.last_error`. They do not crash the process.

---

## 14. Compliance Control Mapping

Evidence-to-control mappings are seeded into the `controls` table and linked via `evidence_controls`. Mappings are defined in code as a seed file and applied during migrations.

### Example Mappings

| Evidence Type | Control Category | Framework |
|---|---|---|
| iam_users | access_control | soc2 |
| iam_policies | access_control | soc2 |
| cloudtrail_logs | logging_monitoring | soc2 |
| github_collaborators | access_control | soc2 |
| github_commits | change_management | soc2 |
| slack_admin_users | access_control | soc2 |

---

## 15. Initial Integrations

### AWS
Evidence collected:
- IAM users (MFA status, last login, access keys)
- IAM policies (attached policies, inline policies)
- CloudTrail logs (recent management events)

APIs used: IAM, CloudTrail, STS
Credentials: `{ "access_key_id": "", "secret_access_key": "", "region": "" }`

---

### GitHub
Evidence collected:
- Repositories (visibility, settings)
- Repository collaborators (permissions)
- Admin users
- Recent commit activity

APIs used: Repositories API, Collaborators API, Commits API
Credentials: `{ "token": "", "org": "" }`

---

### Slack
Evidence collected:
- Workspace users
- Admin users
- Workspace configuration

APIs used: Users API, Team API
Credentials: `{ "bot_token": "" }`

---

## 16. Report Generator

Reports are generated from stored evidence records.

### Steps
1. Query evidence records by `company_id` and `framework`
2. Group evidence by `control` category
3. Render Jinja2 HTML template with evidence data
4. Convert HTML to PDF using WeasyPrint
5. Upload PDF to object storage
6. Update `reports` record with `file_url` and `status = 'complete'`

### Supported Formats
- PDF (primary)
- JSON evidence bundle (raw export)

Report generation runs as a background task triggered by `POST /v1/reports/generate`. The endpoint returns immediately with a report `id`. The client polls `GET /v1/reports/{id}` to check status.

---

## 17. API Endpoints

All routes are prefixed with `/v1/`. All routes except `/v1/auth/register` and `/v1/auth/login` require authentication.

### Auth
```
POST   /v1/auth/register          Register new user + company
POST   /v1/auth/login             Login, returns access + refresh tokens
POST   /v1/auth/refresh           Refresh access token
POST   /v1/auth/logout            Invalidate refresh token
```

### Integrations
```
GET    /v1/integrations                     List company integrations
POST   /v1/integrations/connect             Connect new integration
DELETE /v1/integrations/{integration_type}  Disconnect integration
POST   /v1/integrations/{integration_type}/collect   Trigger manual collection
```

### Evidence
```
GET    /v1/evidence                         List evidence (paginated)
GET    /v1/evidence?control=access_control  Filter by control
GET    /v1/evidence?integration=aws         Filter by integration
```

### Reports
```
POST   /v1/reports/generate        Trigger report generation (async)
GET    /v1/reports                  List reports
GET    /v1/reports/{id}             Get report status + download URL
```

### Pagination

All list endpoints support:
```
?page=1&page_size=50
```

Response envelope:
```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 50,
  "pages": 0
}
```

---

## 18. Frontend Responsibilities

The frontend communicates with the backend exclusively via REST API.

### Pages / Views
- `/` — Dashboard (evidence summary, control status)
- `/auth/login` — Login
- `/auth/register` — Register + company setup
- `/integrations` — List and connect integrations
- `/evidence` — Browse evidence records, filter by control
- `/reports` — Generate and download compliance reports

---

## 19. CORS Configuration

Backend must whitelist the frontend origin:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.tracelayer.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 20. Logging

All log entries include `timestamp`, `company_id`, and `integration` where applicable.

Events to log:
- API requests (method, path, status code, duration)
- Collector job start / success / failure
- Report generation start / complete / failure
- Integration connect / disconnect

Use Python `logging` with structured output (JSON format in production).

---

## 21. Security Requirements

| Requirement | Implementation |
|---|---|
| Credentials encrypted at rest | Fernet encryption before DB write |
| API authentication | JWT Bearer token on all protected routes |
| Organization data isolation | All queries filtered by `company_id` from JWT claims |
| No secrets in logs | Credentials decrypted only in collector memory, never logged |
| No secrets in API responses | `credentials_enc` column never returned by API |
| Password hashing | bcrypt via `passlib` |

---

## 22. Local Development Setup

Requirements: Python 3.11+, Node 18+, Docker

```bash
# Start local PostgreSQL
docker-compose up -d

# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

---

## 23. Future Extensions

- Google Workspace integration
- Okta integration
- Jira integration
- ISO 27001 framework support
- HIPAA framework support
- Compliance scoring engine
- Continuous monitoring with alerting
- AI compliance assistant
- Policy management module
- Webhook support for real-time evidence push
