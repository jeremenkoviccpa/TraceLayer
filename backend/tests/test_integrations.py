import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from integrations.base import IntegrationAuthError
from tests.conftest import auth_headers, register


async def test_list_integrations_empty(client: AsyncClient):
    headers = await auth_headers(client, "list_empty@example.com")
    res = await client.get("/v1/integrations", headers=headers)
    assert res.status_code == 200
    assert res.json() == []


async def test_connect_integration_success(client: AsyncClient):
    headers = await auth_headers(client, "connect@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_adapter = AsyncMock()
        mock_adapter.connect = AsyncMock(return_value=True)
        mock_get.return_value = mock_adapter

        res = await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "github", "credentials": {"token": "ghp_test", "org": "testorg"}},
            headers=headers,
        )

    assert res.status_code == 201
    data = res.json()
    assert data["integration_type"] == "github"
    assert data["status"] == "active"
    assert "id" in data
    assert "credentials" not in data  # credentials must never be returned


async def test_connect_appears_in_list(client: AsyncClient):
    headers = await auth_headers(client, "list_after@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_get.return_value = AsyncMock(connect=AsyncMock(return_value=True))
        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "slack", "credentials": {"bot_token": "xoxb-test"}},
            headers=headers,
        )

    res = await client.get("/v1/integrations", headers=headers)
    assert res.status_code == 200
    types = [i["integration_type"] for i in res.json()]
    assert "slack" in types


async def test_connect_unknown_integration_type(client: AsyncClient):
    headers = await auth_headers(client, "badtype@example.com")
    res = await client.post(
        "/v1/integrations/connect",
        json={"integration_type": "nonexistent", "credentials": {}},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Unknown integration type" in res.json()["detail"]


async def test_connect_bad_credentials(client: AsyncClient):
    headers = await auth_headers(client, "badcreds@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_adapter = AsyncMock()
        mock_adapter.connect = AsyncMock(side_effect=IntegrationAuthError("Token invalid"))
        mock_get.return_value = mock_adapter

        res = await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "github", "credentials": {"token": "bad", "org": "org"}},
            headers=headers,
        )

    assert res.status_code == 422
    assert "Credential validation failed" in res.json()["detail"]


async def test_connect_idempotent_reconnect(client: AsyncClient):
    """Reconnecting an existing integration should update credentials, not create a duplicate."""
    headers = await auth_headers(client, "reconnect@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_get.return_value = AsyncMock(connect=AsyncMock(return_value=True))

        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "aws", "credentials": {"access_key_id": "k1", "secret_access_key": "s1", "region": "us-east-1"}},
            headers=headers,
        )
        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "aws", "credentials": {"access_key_id": "k2", "secret_access_key": "s2", "region": "us-east-1"}},
            headers=headers,
        )

    res = await client.get("/v1/integrations", headers=headers)
    aws_integrations = [i for i in res.json() if i["integration_type"] == "aws"]
    assert len(aws_integrations) == 1  # Should be exactly one, not two


async def test_disconnect_integration(client: AsyncClient):
    headers = await auth_headers(client, "disconnect@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_get.return_value = AsyncMock(connect=AsyncMock(return_value=True))
        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "slack", "credentials": {"bot_token": "xoxb-test"}},
            headers=headers,
        )

    res = await client.delete("/v1/integrations/slack", headers=headers)
    assert res.status_code == 204

    res = await client.get("/v1/integrations", headers=headers)
    assert res.json() == []


async def test_disconnect_nonexistent(client: AsyncClient):
    headers = await auth_headers(client, "discne@example.com")
    res = await client.delete("/v1/integrations/aws", headers=headers)
    assert res.status_code == 404


async def test_trigger_collect_queues_job(client: AsyncClient):
    headers = await auth_headers(client, "collect_trigger@example.com")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_get.return_value = AsyncMock(connect=AsyncMock(return_value=True))
        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "github", "credentials": {"token": "t", "org": "o"}},
            headers=headers,
        )

    with patch("api.v1.integrations.run_collector_job", new_callable=AsyncMock) as mock_job:
        res = await client.post("/v1/integrations/github/collect", headers=headers)
        assert res.status_code == 202

    # Job is queued as a background task — we just confirm the endpoint responds correctly


async def test_integrations_isolated_between_companies(client: AsyncClient):
    """Company A must not see company B's integrations."""
    headers_a = await auth_headers(client, "company_a@example.com", company="CompanyA")
    headers_b = await auth_headers(client, "company_b@example.com", company="CompanyB")

    with patch("services.integration_service.get_adapter") as mock_get:
        mock_get.return_value = AsyncMock(connect=AsyncMock(return_value=True))
        await client.post(
            "/v1/integrations/connect",
            json={"integration_type": "slack", "credentials": {"bot_token": "xoxb-a"}},
            headers=headers_a,
        )

    res = await client.get("/v1/integrations", headers=headers_b)
    assert res.json() == []
