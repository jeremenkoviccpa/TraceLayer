import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.company import Company
from models.integration import Integration
from models.evidence import Evidence
from services.collector_service import run_collection
from utils.encryption import encrypt_credentials

GITHUB_CREDENTIALS = {"token": "ghp_test", "org": "testorg"}

MOCK_NORMALIZED = [
    {
        "integration": "github",
        "control": "access_control",
        "evidence_type": "github_members",
        "source_id": "user_alice",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"login": "alice", "role": "member"},
    },
    {
        "integration": "github",
        "control": "access_control",
        "evidence_type": "github_admin_members",
        "source_id": "admin_bob",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"login": "bob", "role": "admin"},
    },
]


async def _make_integration(db: AsyncSession, integration_type: str = "github") -> tuple[uuid.UUID, Integration]:
    company = Company(id=uuid.uuid4(), name="CollectorTestCo")
    db.add(company)
    await db.flush()

    integration = Integration(
        company_id=company.id,
        integration_type=integration_type,
        credentials_enc=encrypt_credentials(GITHUB_CREDENTIALS),
        status="active",
    )
    db.add(integration)
    await db.flush()
    return company.id, integration


async def test_run_collection_upserts_evidence(db: AsyncSession):
    company_id, _ = await _make_integration(db)

    with patch("services.collector_service.get_adapter") as mock_get:
        mock_adapter = AsyncMock()
        mock_adapter.connect = AsyncMock(return_value=True)
        mock_adapter.collect_evidence = AsyncMock(return_value=[{"_type": "raw"}])
        mock_adapter.normalize = lambda raw: MOCK_NORMALIZED
        mock_get.return_value = mock_adapter

        count = await run_collection(company_id, "github", db)

    assert count == 2

    result = await db.execute(select(Evidence).where(Evidence.company_id == company_id))
    records = result.scalars().all()
    assert len(records) == 2
    source_ids = {r.source_id for r in records}
    assert "user_alice" in source_ids
    assert "admin_bob" in source_ids


async def test_run_collection_is_idempotent(db: AsyncSession):
    """Running collection twice must not create duplicate records."""
    company_id, _ = await _make_integration(db, "slack")

    def make_mock():
        m = AsyncMock()
        m.connect = AsyncMock(return_value=True)
        m.collect_evidence = AsyncMock(return_value=[])
        m.normalize = lambda raw: MOCK_NORMALIZED[:1]  # one record
        return m

    with patch("services.collector_service.get_adapter", return_value=make_mock()):
        await run_collection(company_id, "slack", db)

    with patch("services.collector_service.get_adapter", return_value=make_mock()):
        await run_collection(company_id, "slack", db)

    result = await db.execute(select(Evidence).where(Evidence.company_id == company_id))
    assert len(result.scalars().all()) == 1


async def test_run_collection_updates_last_collected_at(db: AsyncSession):
    company_id, integration = await _make_integration(db)
    assert integration.last_collected_at is None

    with patch("services.collector_service.get_adapter") as mock_get:
        m = AsyncMock()
        m.connect = AsyncMock(return_value=True)
        m.collect_evidence = AsyncMock(return_value=[])
        m.normalize = lambda raw: []
        mock_get.return_value = m

        await run_collection(company_id, "github", db)

    await db.refresh(integration)
    assert integration.last_collected_at is not None
    assert integration.status == "active"
    assert integration.last_error is None


async def test_run_collection_marks_error_on_failure(db: AsyncSession):
    company_id, integration = await _make_integration(db)

    with patch("services.collector_service.get_adapter") as mock_get:
        m = AsyncMock()
        m.connect = AsyncMock(side_effect=RuntimeError("AWS connection refused"))
        mock_get.return_value = m

        with pytest.raises(RuntimeError):
            await run_collection(company_id, "github", db)

    await db.refresh(integration)
    assert integration.status == "error"
    assert "AWS connection refused" in integration.last_error


async def test_run_collection_missing_integration(db: AsyncSession):
    with pytest.raises(ValueError, match="not found"):
        await run_collection(uuid.uuid4(), "github", db)


async def test_run_collection_data_stored_correctly(db: AsyncSession):
    company_id, _ = await _make_integration(db)

    record = {
        "integration": "github",
        "control": "access_control",
        "evidence_type": "github_members",
        "source_id": "user_charlie",
        "timestamp": "2024-06-01T10:00:00+00:00",
        "data": {"login": "charlie", "mfa": True, "repos": 5},
    }

    with patch("services.collector_service.get_adapter") as mock_get:
        m = AsyncMock()
        m.connect = AsyncMock(return_value=True)
        m.collect_evidence = AsyncMock(return_value=[])
        m.normalize = lambda raw: [record]
        mock_get.return_value = m

        await run_collection(company_id, "github", db)

    result = await db.execute(
        select(Evidence).where(
            Evidence.company_id == company_id,
            Evidence.source_id == "user_charlie",
        )
    )
    ev = result.scalar_one()
    assert ev.data["login"] == "charlie"
    assert ev.data["mfa"] is True
    assert ev.control == "access_control"
    assert ev.evidence_type == "github_members"
