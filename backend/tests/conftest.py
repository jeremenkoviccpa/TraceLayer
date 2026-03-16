"""
Test configuration and shared fixtures.

Requires a running PostgreSQL instance. Tests use a separate database
(tracelayer_test) and roll back each test via transaction savepoints,
so no data persists between tests.

Run with:
    cd backend && pytest tests/ -v
"""
import os
import uuid
from unittest.mock import AsyncMock, patch

# ── Set environment before any app module is imported ──────────────────────
from cryptography.fernet import Fernet

# ── Seed data (mirrors Alembic migrations 004 + 005) ───────────────────────
SEED_CONTROLS = [
    # SOC 2
    {"id": uuid.UUID("00000000-0000-0000-0000-000000000001"), "name": "Access Control", "framework": "soc2", "category": "access_control", "description": "Controls to manage who has access to systems and data."},
    {"id": uuid.UUID("00000000-0000-0000-0000-000000000002"), "name": "Logging & Monitoring", "framework": "soc2", "category": "logging_monitoring", "description": "Controls to ensure system activity is logged and monitored."},
    {"id": uuid.UUID("00000000-0000-0000-0000-000000000003"), "name": "Change Management", "framework": "soc2", "category": "change_management", "description": "Controls to manage changes to systems and code."},
    # ISO 27001
    {"id": uuid.UUID("00000000-0000-0000-0001-000000000001"), "name": "Access Control (A.9)", "framework": "iso27001", "category": "access_control", "description": "Business requirements for access control."},
    {"id": uuid.UUID("00000000-0000-0000-0001-000000000002"), "name": "Operations Security (A.12)", "framework": "iso27001", "category": "operations_security", "description": "Operational procedures, protection from malware, backup, logging."},
    {"id": uuid.UUID("00000000-0000-0000-0001-000000000003"), "name": "Communications Security (A.13)", "framework": "iso27001", "category": "communications_security", "description": "Network security management."},
    {"id": uuid.UUID("00000000-0000-0000-0001-000000000004"), "name": "System Acquisition & Change Control (A.14)", "framework": "iso27001", "category": "change_management", "description": "Security requirements for information systems."},
    # HIPAA
    {"id": uuid.UUID("00000000-0000-0000-0002-000000000001"), "name": "Access Control (§164.312(a))", "framework": "hipaa", "category": "access_control", "description": "Technical policies to allow only authorized persons to access ePHI."},
    {"id": uuid.UUID("00000000-0000-0000-0002-000000000002"), "name": "Audit Controls (§164.312(b))", "framework": "hipaa", "category": "audit_controls", "description": "Mechanisms to record and examine activity in systems containing ePHI."},
    {"id": uuid.UUID("00000000-0000-0000-0002-000000000003"), "name": "Workforce Security (§164.308(a)(3))", "framework": "hipaa", "category": "workforce_security", "description": "Policies to ensure workforce members have appropriate access to ePHI."},
]

_FERNET_KEY = os.getenv("FERNET_KEY", Fernet.generate_key().decode())

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-use")
os.environ.setdefault(
    "DATABASE_URL",
    os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://tracelayer:tracelayer@localhost:5432/tracelayer_test",
    ),
)
os.environ["FERNET_KEY"] = _FERNET_KEY
os.environ.setdefault("STORAGE_BUCKET", "")
os.environ.setdefault("STORAGE_ENDPOINT", "")
os.environ.setdefault("STORAGE_ACCESS_KEY", "")
os.environ.setdefault("STORAGE_SECRET_KEY", "")

# ── Now import app modules ──────────────────────────────────────────────────
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

import sqlalchemy as sa

from core.database import get_db
from main import app
from models.base import Base

TEST_DB_URL = os.environ["DATABASE_URL"]


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            sa.text(
                "INSERT INTO controls (id, name, framework, category, description) VALUES "
                + ", ".join(
                    f"('{c['id']}', :name_{i}, :framework_{i}, :category_{i}, :description_{i})"
                    for i, c in enumerate(SEED_CONTROLS)
                )
            ).bindparams(
                **{k: v for i, c in enumerate(SEED_CONTROLS) for k, v in {
                    f"name_{i}": c["name"],
                    f"framework_{i}": c["framework"],
                    f"category_{i}": c["category"],
                    f"description_{i}": c["description"],
                }.items()}
            )
        )
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine):
    """
    Each test gets a connection with an open transaction.
    The transaction is rolled back after the test, keeping the DB clean.
    """
    conn = await test_engine.connect()
    await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    yield session
    await session.close()
    await conn.rollback()
    await conn.close()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    """
    HTTP test client wired to the test DB session.
    Scheduler lifecycle and job scheduling are patched out.
    """
    async def _override_db():
        yield db

    app.dependency_overrides[get_db] = _override_db

    with (
        patch("collectors.scheduler.start", new_callable=AsyncMock),
        patch("collectors.scheduler.stop", new_callable=AsyncMock),
        patch("api.v1.integrations.schedule_integration"),
        patch("api.v1.integrations.unschedule_integration"),
        patch("services.report_service.upload_bytes"),
        patch(
            "services.report_service.create_signed_url",
            return_value="https://storage.example.com/signed/report?token=test",
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ── Shared helpers ──────────────────────────────────────────────────────────

async def register(client: AsyncClient, email: str, password: str = "password123", company: str = "Test Co"):
    res = await client.post(
        "/v1/auth/register",
        json={"email": email, "password": password, "company_name": company},
    )
    assert res.status_code == 201, res.text
    return res.json()


async def auth_headers(client: AsyncClient, email: str, **kwargs) -> dict:
    data = await register(client, email, **kwargs)
    return {"Authorization": f"Bearer {data['access_token']}"}
