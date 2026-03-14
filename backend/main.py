import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import select

from api.v1 import auth, compliance, evidence, integrations, org, reports
from collectors.scheduler import schedule_integration
from collectors.scheduler import start as start_scheduler
from collectors.scheduler import stop as stop_scheduler
from core.config import settings
from core.database import AsyncSessionLocal
from core.limiter import limiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


async def _run_migrations() -> None:
    """Run Alembic migrations on startup."""
    import asyncio
    from alembic import command
    from alembic.config import Config

    loop = asyncio.get_event_loop()
    alembic_cfg = Config("alembic.ini")
    await loop.run_in_executor(None, command.upgrade, alembic_cfg, "head")
    logger.info("Database migrations applied")


async def _reschedule_active_integrations() -> None:
    """On startup, re-add scheduler jobs for all active integrations."""
    from models.integration import Integration

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Integration).where(Integration.status == "active"))
            integrations_list = result.scalars().all()
            for i in integrations_list:
                schedule_integration(str(i.company_id), i.integration_type)
            logger.info("Rescheduled %d active integration(s) on startup", len(integrations_list))
    except Exception as exc:
        logger.warning("Could not reschedule integrations on startup: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _run_migrations()
    await _reschedule_active_integrations()
    await start_scheduler()
    yield
    await stop_scheduler()


app = FastAPI(title="TraceLayer API", version="1.0.0", lifespan=lifespan)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/v1")
app.include_router(integrations.router, prefix="/v1")
app.include_router(evidence.router, prefix="/v1")
app.include_router(reports.router, prefix="/v1")
app.include_router(org.router, prefix="/v1")
app.include_router(compliance.router, prefix="/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
