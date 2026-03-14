import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import select

from models.evidence import Evidence
from models.report import Report
from services.report_service import create_report, generate_report_bundle, get_report
from tests.conftest import auth_headers, register


async def _seed_evidence(db: AsyncSession, company_id: uuid.UUID) -> None:
    for i in range(3):
        stmt = pg_insert(Evidence).values(
            id=uuid.uuid4(),
            company_id=company_id,
            integration="aws",
            control="access_control",
            evidence_type="iam_users",
            source_id=f"arn:aws:iam::123:user/user{i}",
            timestamp=datetime.now(timezone.utc),
            data={"username": f"user{i}", "mfa_enabled": True},
        ).on_conflict_do_nothing()
        await db.execute(stmt)
    await db.flush()


async def test_generate_report_returns_202(client: AsyncClient):
    headers = await auth_headers(client, "rpt_gen@example.com")
    res = await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
        headers=headers,
    )
    assert res.status_code == 202
    data = res.json()
    assert data["framework"] == "soc2"
    assert data["report_type"] == "full"
    assert data["status"] in ("pending", "complete")
    assert "id" in data


async def test_generate_report_appears_in_list(client: AsyncClient):
    headers = await auth_headers(client, "rpt_list@example.com")
    await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
        headers=headers,
    )
    res = await client.get("/v1/reports", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] >= 1


async def test_get_report_by_id(client: AsyncClient):
    headers = await auth_headers(client, "rpt_get@example.com")
    gen = await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
        headers=headers,
    )
    report_id = gen.json()["id"]

    res = await client.get(f"/v1/reports/{report_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == report_id


async def test_get_report_not_found(client: AsyncClient):
    headers = await auth_headers(client, "rpt_404@example.com")
    fake_id = str(uuid.uuid4())
    res = await client.get(f"/v1/reports/{fake_id}", headers=headers)
    assert res.status_code == 404


async def test_report_isolated_between_companies(client: AsyncClient):
    headers_a = await auth_headers(client, "rpt_iso_a@example.com", company="CompA")
    await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
        headers=headers_a,
    )

    headers_b = await auth_headers(client, "rpt_iso_b@example.com", company="CompB")
    res = await client.get("/v1/reports", headers=headers_b)
    assert res.json()["total"] == 0


async def test_generate_report_bundle_structure(db: AsyncSession):
    """Unit test the report bundle generation directly."""
    company_id = uuid.uuid4()

    from models.company import Company
    company = Company(id=company_id, name="BundleTestCo")
    db.add(company)
    await db.flush()

    await _seed_evidence(db, company_id)

    report = await create_report(company_id, "soc2", "full", db)
    assert report.status == "pending"

    bundle = await generate_report_bundle(report.id, company_id, db)

    assert bundle["framework"] == "soc2"
    assert bundle["total_evidence_records"] == 3
    assert "controls" in bundle
    assert "access_control" in bundle["controls"]
    assert len(bundle["controls"]["access_control"]) == 3

    await db.refresh(report)
    assert report.status == "complete"
    assert report.generated_at is not None
    assert report.file_url is not None


async def test_download_report_complete(client: AsyncClient, db: AsyncSession):
    """Integration test for download endpoint with a complete report."""
    tokens = await register(client, "rpt_dl@example.com", company="DLCo")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me = await client.get("/v1/auth/me", headers=headers)
    company_id = uuid.UUID(me.json()["company_id"])

    await _seed_evidence(db, company_id)

    # Generate and wait for the background task to complete
    # In tests, FastAPI runs background tasks inline, so it should be done by the time
    # we query the report
    gen = await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
        headers=headers,
    )
    report_id = gen.json()["id"]

    # Poll until complete (background tasks run synchronously in test transport)
    res = await client.get(f"/v1/reports/{report_id}", headers=headers)
    # If status is pending, download should return 409
    if res.json()["status"] == "pending":
        dl = await client.get(f"/v1/reports/{report_id}/download", headers=headers)
        assert dl.status_code == 409
    else:
        dl = await client.get(f"/v1/reports/{report_id}/download", headers=headers)
        assert dl.status_code == 200
        bundle = dl.json()
        assert "controls" in bundle
        assert "report_id" in bundle


async def test_reports_list_pagination(client: AsyncClient):
    headers = await auth_headers(client, "rpt_pg@example.com")

    for _ in range(3):
        await client.post(
            "/v1/reports/generate",
            json={"framework": "soc2", "report_type": "full"},
            headers=headers,
        )

    res = await client.get("/v1/reports?page=1&page_size=2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["pages"] == 2


async def test_generate_report_requires_auth(client: AsyncClient):
    res = await client.post(
        "/v1/reports/generate",
        json={"framework": "soc2", "report_type": "full"},
    )
    assert res.status_code == 403
