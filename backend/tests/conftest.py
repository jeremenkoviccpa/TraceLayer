"""
Test configuration and shared fixtures.

Requires a running PostgreSQL instance. Tests use a separate database
(tracelayer_test) and roll back each test via transaction savepoints,
so no data persists between tests.

Run with:
    cd backend && pytest tests/ -v
"""
import os
from unittest.mock import AsyncMock, patch

# ── Set environment before any app module is imported ──────────────────────
from cryptography.fernet import Fernet

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
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

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
