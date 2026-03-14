import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from models.evidence import Evidence
from tests.conftest import auth_headers, register


async def _seed_evidence(db: AsyncSession, company_id: uuid.UUID, count: int = 3) -> None:
    """Insert evidence records directly into the DB for testing queries."""
    for i in range(count):
        stmt = pg_insert(Evidence).values(
            id=uuid.uuid4(),
            company_id=company_id,
            integration="github" if i % 2 == 0 else "aws",
            control="access_control" if i < 2 else "change_management",
            evidence_type="github_members" if i % 2 == 0 else "iam_users",
            source_id=f"source_{i}",
            timestamp=datetime.now(timezone.utc),
            data={"index": i, "test": True},
        ).on_conflict_do_nothing()
        await db.execute(stmt)
    await db.flush()


async def _get_company_id(client: AsyncClient, email: str) -> uuid.UUID:
    tokens = await register(client, email)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    me = await client.get("/v1/auth/me", headers=headers)
    return uuid.UUID(me.json()["company_id"])


async def test_list_evidence_empty(client: AsyncClient):
    headers = await auth_headers(client, "ev_empty@example.com")
    res = await client.get("/v1/evidence", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1


async def test_list_evidence_pagination_shape(client: AsyncClient):
    headers = await auth_headers(client, "ev_shape@example.com")
    res = await client.get("/v1/evidence?page=1&page_size=10", headers=headers)
    assert res.status_code == 200
    data = res.json()
    for key in ("items", "total", "page", "page_size", "pages"):
        assert key in data


async def test_list_evidence_with_seeded_data(client: AsyncClient, db: AsyncSession):
    company_id = await _get_company_id(client, "ev_seeded@example.com")
    await _seed_evidence(db, company_id, count=5)

    headers = {"Authorization": f"Bearer {(await register(client, 'ev_seeded_token@example.com'))['access_token']}"}
    # Use a fresh user for the same company is complex; query directly via the seeded company's user
    # Re-register and get the right token using the seeded company's email
    tokens_res = await client.post(
        "/v1/auth/login",
        json={"email": "ev_seeded@example.com", "password": "password123"},
    )
    token = tokens_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/v1/evidence", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 5


async def test_filter_by_control(client: AsyncClient, db: AsyncSession):
    company_id = await _get_company_id(client, "ev_ctrl@example.com")
    await _seed_evidence(db, company_id, count=3)

    tokens_res = await client.post(
        "/v1/auth/login",
        json={"email": "ev_ctrl@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {tokens_res.json()['access_token']}"}

    res = await client.get("/v1/evidence?control=access_control", headers=headers)
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["control"] == "access_control"


async def test_filter_by_integration(client: AsyncClient, db: AsyncSession):
    company_id = await _get_company_id(client, "ev_int@example.com")
    await _seed_evidence(db, company_id, count=4)

    tokens_res = await client.post(
        "/v1/auth/login",
        json={"email": "ev_int@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {tokens_res.json()['access_token']}"}

    res = await client.get("/v1/evidence?integration=github", headers=headers)
    assert res.status_code == 200
    for item in res.json()["items"]:
        assert item["integration"] == "github"


async def test_evidence_page_size_respected(client: AsyncClient, db: AsyncSession):
    company_id = await _get_company_id(client, "ev_page@example.com")
    await _seed_evidence(db, company_id, count=10)

    tokens_res = await client.post(
        "/v1/auth/login",
        json={"email": "ev_page@example.com", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {tokens_res.json()['access_token']}"}

    res = await client.get("/v1/evidence?page_size=3", headers=headers)
    data = res.json()
    assert len(data["items"]) <= 3
    assert data["total"] == 10


async def test_evidence_isolated_between_companies(client: AsyncClient, db: AsyncSession):
    """Company A must not see company B's evidence."""
    company_a_id = await _get_company_id(client, "ev_iso_a@example.com")
    await _seed_evidence(db, company_a_id, count=3)

    headers_b = await auth_headers(client, "ev_iso_b@example.com", company="CompanyB")
    res = await client.get("/v1/evidence", headers=headers_b)
    assert res.json()["total"] == 0


async def test_evidence_requires_auth(client: AsyncClient):
    res = await client.get("/v1/evidence")
    assert res.status_code == 403
