import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select, text

from api.v1 import access_reviews, access_reviews_v2, ai_agent_events, api_keys, assets, audit, audit_engagements, audit_sessions, auth, auth_google, auth_sso, background_checks, billing, business_continuity, change_requests, chat, compliance, custom_frameworks, data_breaches, data_flows, devices, devices_v2, documents, employee_portal, evidence, incidents, ingest, integrations, management_reviews, notifications, oauth_integrations, offboarding, onboarding, org, partner, partner_directory, pen_tests, pen_tests_v2, pentest_agency, policies, public, questionnaire, reports, risks, ropa, slack_bot, soa, sso, subject_requests, subprocessors, superadmin, training, trust, vendor_questionnaires, vendors, vulnerabilities
from api.v1.admin.framework_updates import manifests_router as framework_manifests_router
from api.v1.admin.framework_updates import router as framework_updates_router
from collectors.scheduler import schedule_integration
from collectors.scheduler import start as start_scheduler
from collectors.scheduler import stop as stop_scheduler
from collectors.scheduler import schedule_weekly_reports, schedule_daily_alerts, schedule_activation_nudges, schedule_partner_nudges, schedule_risk_detection, schedule_auto_detection, schedule_detection_digest, schedule_control_owner_reminders, schedule_framework_monitor, schedule_daily_snapshots, schedule_policy_expiry_checks
from core.config import settings
from core.database import AsyncSessionLocal
from core.limiter import limiter

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=0.2,
        profiles_sample_rate=0.1,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def _run_migrations() -> None:
    """Run Alembic migrations on startup, protected by a PostgreSQL advisory lock
    so only one instance runs migrations even when multiple replicas start at once.
    Skipped in test env — tests use Base.metadata.create_all instead.
    """
    if settings.app_env == "test":
        return

    import asyncio
    import subprocess

    # Advisory lock ID — arbitrary stable integer (spells "TL" in decimal)
    LOCK_ID = 84766

    async with AsyncSessionLocal() as db:
        # pg_advisory_lock blocks until the lock is available, ensuring
        # that only one replica runs migrations at a time.
        await db.execute(text(f"SELECT pg_advisory_lock({LOCK_ID})"))
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    ["alembic", "upgrade", "head"],
                    capture_output=True,
                    text=True,
                ),
            )
            if result.stdout:
                logger.info("Migrations: %s", result.stdout.strip())
            if result.returncode != 0:
                logger.error("Migration stderr: %s", result.stderr)
                raise RuntimeError("Alembic migration failed — see logs above")
            logger.info("Database migrations complete")
        finally:
            await db.execute(text(f"SELECT pg_advisory_unlock({LOCK_ID})"))


async def _reschedule_active_integrations() -> None:
    """On startup, re-add scheduler jobs for all active integrations."""
    from models.integration import Integration

    try:
        async with AsyncSessionLocal() as db:
            # Reschedule both "active" and "error" — errored integrations should still be retried
            result = await db.execute(
                select(Integration).where(Integration.status.in_(["active", "error"]))
            )
            integrations_list = result.scalars().all()
            for i in integrations_list:
                # Errored integrations get run_now so they retry shortly after startup
                schedule_integration(
                    str(i.company_id),
                    i.integration_type,
                    run_now=(i.status == "error"),
                )
            logger.info("Rescheduled %d integration(s) on startup", len(integrations_list))
    except Exception as exc:
        logger.warning("Could not reschedule integrations on startup: %s", exc)


async def _seed_demo_data() -> None:
    """Seed demo company/user/evidence if SEED_DEMO=true."""
    if not settings.seed_demo:
        return
    try:
        from scripts.seed_demo_full import seed
        await seed()
        logger.info("Demo seed complete")
    except Exception as exc:
        logger.warning("Demo seed failed (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Config: env=%s frontend_url=%s", settings.app_env, settings.app_frontend_url)
    if settings.app_env == "production":
        missing = [v for v, k in [
            ("PADDLE_SK", settings.paddle_sk),
            ("PADDLE_GROWTH_PRICE_ID", settings.paddle_growth_price_id),
            ("PADDLE_WEBHOOK_SECRET", settings.paddle_webhook_secret),
        ] if not k]
        if missing:
            raise RuntimeError(f"Missing required production config: {', '.join(missing)}")
    await _run_migrations()
    await _seed_demo_data()
    await _reschedule_active_integrations()
    await start_scheduler()
    schedule_weekly_reports()
    schedule_daily_alerts()
    schedule_activation_nudges()
    schedule_partner_nudges()
    schedule_risk_detection()
    schedule_auto_detection()
    schedule_detection_digest()
    schedule_control_owner_reminders()
    schedule_framework_monitor()
    schedule_daily_snapshots()
    schedule_policy_expiry_checks()
    yield
    await stop_scheduler()


_is_prod = settings.app_env == "production"
app = FastAPI(
    title="TraceLayer API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None if _is_prod else "/docs",
    redoc_url=None if _is_prod else "/redoc",
    openapi_url=None if _is_prod else "/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

app.include_router(auth.router, prefix="/v1")
app.include_router(auth_google.router, prefix="/v1")
app.include_router(auth_sso.router, prefix="/v1")
app.include_router(sso.router, prefix="/v1")
app.include_router(integrations.router, prefix="/v1")
app.include_router(oauth_integrations.router, prefix="/v1")
app.include_router(evidence.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")
app.include_router(org.router, prefix="/v1")
app.include_router(chat.router, prefix="/v1")
app.include_router(compliance.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(audit.router, prefix="/v1")
app.include_router(audit_sessions.router, prefix="/v1")
app.include_router(risks.router, prefix="/v1")
app.include_router(policies.router, prefix="/v1")
app.include_router(questionnaire.router, prefix="/v1")
app.include_router(training.router, prefix="/v1")
app.include_router(pen_tests.router, prefix="/v1")
app.include_router(vendors.router, prefix="/v1")
app.include_router(access_reviews.router, prefix="/v1")
app.include_router(trust.router, prefix="/v1")
app.include_router(partner.router, prefix="/v1")
app.include_router(audit_engagements.router, prefix="/v1")
app.include_router(partner_directory.router, prefix="/v1")
app.include_router(documents.router, prefix="/v1")
app.include_router(notifications.router, prefix="/v1")
app.include_router(incidents.router, prefix="/v1")
app.include_router(assets.router, prefix="/v1")
app.include_router(vulnerabilities.router, prefix="/v1")
app.include_router(business_continuity.router, prefix="/v1")
app.include_router(background_checks.router, prefix="/v1")
app.include_router(offboarding.router, prefix="/v1")
app.include_router(onboarding.router, prefix="/v1")
app.include_router(subprocessors.router, prefix="/v1")
app.include_router(vendor_questionnaires.router, prefix="/v1")
app.include_router(access_reviews_v2.router, prefix="/v1")
app.include_router(devices_v2.router, prefix="/v1")
app.include_router(pen_tests_v2.router, prefix="/v1")
app.include_router(pentest_agency.router, prefix="/v1")
app.include_router(soa.router, prefix="/v1")
app.include_router(ropa.router, prefix="/v1")
app.include_router(data_breaches.router, prefix="/v1")
app.include_router(subject_requests.router, prefix="/v1")
app.include_router(management_reviews.router, prefix="/v1")
app.include_router(api_keys.router, prefix="/v1")
app.include_router(data_flows.router, prefix="/v1")
app.include_router(devices.router, prefix="/v1")
app.include_router(employee_portal.router, prefix="/v1")
app.include_router(slack_bot.router, prefix="/v1")
app.include_router(ai_agent_events.router, prefix="/v1")
app.include_router(ingest.router, prefix="/v1")
app.include_router(superadmin.router, prefix="/v1")
app.include_router(framework_updates_router, prefix="/v1")
app.include_router(framework_manifests_router, prefix="/v1")
app.include_router(custom_frameworks.router, prefix="/v1")
app.include_router(change_requests.router, prefix="/v1")
app.include_router(public.router, prefix="/v1")


@app.get("/health")
async def health():
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    status = "ok" if db_ok else "degraded"
    return {"status": status, "db": "ok" if db_ok else "error", "env": settings.app_env}
