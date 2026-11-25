# AGENTS.md — TraceLayer

The single source of truth for any coding agent working in this repo: Claude Code, Devin, Cursor or Argo Helm.
Tool-specific notes live elsewhere (`CLAUDE.md`, `.claude/`). If they disagree with this file, this file wins.

## What TraceLayer is

A multi-tenant compliance evidence platform. It connects to cloud and SaaS tools, collects evidence, maps it to
controls (SOC 2, ISO 27001, HIPAA and more), scores compliance, and produces audit reports.
Every customer is a **company** (tenant). Every row of customer data carries a `company_id`.

## Repo map

```
backend/            FastAPI, SQLAlchemy 2 async, Pydantic v2, Alembic (Python 3.11)
  api/v1/           one router per domain; mounted under /v1 in main.py
  core/             config, db session, security (JWT, Fernet), deps (auth), limiter, plan_gate
  models/ schemas/  ORM models / request+response schemas
  services/         business logic (keep routers thin)
  integrations/     one adapter per external tool
  migrations/       Alembic versions (run on startup)
  tests/            pytest; needs Postgres (see below)
frontend/           Next.js 14 app router, Tailwind
  app/(auth)/       login, register, ...
  app/(dashboard)/  the product
  lib/api.ts        typed API client (reads `detail` from error bodies)
docs/               runbook, security audit report, plans/, decisions/, harness/
.github/workflows/  ci.yml (build, lint, AI review), test.yml (pytest, typecheck)
```

## Run it locally

```bash
docker-compose up -d                               # Postgres 15 on :5432
cd backend && pip install -r requirements.txt -r requirements-dev.txt
cp ../.env.example .env                            # fill values locally; never commit .env
uvicorn main:app --reload                          # http://localhost:8000/docs
cd frontend && npm ci && npm run dev               # http://localhost:3000
```

## Test and lint

```bash
# backend: needs a tracelayer_test database
docker exec -it <pg-container> createdb -U tracelayer tracelayer_test
cd backend && pytest tests/ -q
cd backend && ruff check .
# frontend
cd frontend && npx tsc --noEmit && npm run build
```

Rate limits are disabled when `APP_ENV=test` (see `core/limiter.py`). Tests that need the limiter must enable it explicitly.

## Conventions

- **Tenancy:** every query on customer data filters by `current_user.company_id`. Never trust a `company_id` from the request body.
- **Auth:** routes use `Depends(get_current_user)`; admin-only routes use `get_current_admin`. Paid features use `core/plan_gate.py`.
- **Errors:** raise `HTTPException(status, detail="...")`. The frontend shows `detail` to the user, so write it for a human.
- **Secrets:** read only through `core/config.py` settings. Never log tokens, passwords, emails or credentials. Never print `.env` values.
- **Migrations:** new columns or tables need an Alembic version in `backend/migrations/versions/`.
- **Frontend:** API calls go through `lib/api.ts`. Pages must work on a phone; check mobile, not a list of pixel sizes.
- **Commits:** small, imperative subject line, one concern per commit. Branch per task; PR into `main`.

## Definition of done

1. Tests are green: backend `pytest`, plus frontend `tsc` and `build` if the frontend changed.
2. Lint is clean: `ruff check .`.
3. New behaviour has a test. A UI change has a desktop and mobile screenshot.
4. Docs are updated: README, the runbook, or the relevant `docs/` page.
5. The task folder `docs/plans/<id>/` has `ticket.md`, `plan.md`, `review.md` and `test-report.md`. Any lasting design choice gets an ADR in `docs/decisions/`.
6. The reviewer has no open must-fix items.

## The harness

How tasks flow from ticket to merged PR: `docs/harness/README.md`. Copy-paste playbooks: `docs/harness/playbooks/`.
