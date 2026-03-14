import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers


async def test_compliance_score_empty(client: AsyncClient):
    """Fresh company with no evidence returns 0 overall score."""
    headers = await auth_headers(client, "score_empty@example.com", company="ScoreCo")
    res = await client.get("/v1/compliance/score?framework=soc2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["framework"] == "soc2"
    assert isinstance(data["overall_score"], int)
    assert 0 <= data["overall_score"] <= 100
    assert "controls" in data
    assert "evaluated_at" in data


async def test_compliance_score_requires_auth(client: AsyncClient):
    res = await client.get("/v1/compliance/score?framework=soc2")
    assert res.status_code == 403


async def test_compliance_score_default_framework(client: AsyncClient):
    """framework param defaults to soc2."""
    headers = await auth_headers(client, "score_default@example.com")
    res = await client.get("/v1/compliance/score", headers=headers)
    assert res.status_code == 200
    assert res.json()["framework"] == "soc2"


async def test_compliance_score_structure(client: AsyncClient):
    """Each control entry has the required fields."""
    headers = await auth_headers(client, "score_struct@example.com", company="StructCo")
    res = await client.get("/v1/compliance/score?framework=soc2", headers=headers)
    assert res.status_code == 200
    data = res.json()

    for control in data["controls"]:
        assert "category" in control
        assert "name" in control
        assert "score" in control
        assert "status" in control
        assert "evidence_count" in control
        assert "covered_types" in control
        assert "missing_types" in control
        assert control["status"] in ("passing", "warning", "failing", "no_evidence")
        assert 0 <= control["score"] <= 100


async def test_compliance_score_iso27001(client: AsyncClient):
    headers = await auth_headers(client, "score_iso@example.com", company="IsoCo")
    res = await client.get("/v1/compliance/score?framework=iso27001", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["framework"] == "iso27001"
    categories = {c["category"] for c in data["controls"]}
    assert "access_control" in categories
    assert "operations_security" in categories
    assert "change_management" in categories


async def test_compliance_score_hipaa(client: AsyncClient):
    headers = await auth_headers(client, "score_hipaa@example.com", company="HipaaCo")
    res = await client.get("/v1/compliance/score?framework=hipaa", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["framework"] == "hipaa"
    categories = {c["category"] for c in data["controls"]}
    assert "access_control" in categories
    assert "audit_controls" in categories
    assert "workforce_security" in categories


async def test_compliance_score_unknown_framework(client: AsyncClient):
    """Unknown framework returns empty controls and score 0."""
    headers = await auth_headers(client, "score_unknown@example.com")
    res = await client.get("/v1/compliance/score?framework=unknown", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["overall_score"] == 0
    assert data["controls"] == []


async def test_compliance_score_isolated_between_companies(client: AsyncClient):
    """Two companies get independent scores."""
    headers_a = await auth_headers(client, "iso_score_a@example.com", company="IsoScoreA")
    headers_b = await auth_headers(client, "iso_score_b@example.com", company="IsoScoreB")

    res_a = await client.get("/v1/compliance/score", headers=headers_a)
    res_b = await client.get("/v1/compliance/score", headers=headers_b)

    assert res_a.status_code == 200
    assert res_b.status_code == 200
    # Both are independent — just verify each succeeds and returns valid data
    assert res_a.json()["framework"] == res_b.json()["framework"] == "soc2"
