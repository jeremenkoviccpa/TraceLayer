from httpx import AsyncClient

from tests.conftest import register


async def test_register_success(client: AsyncClient):
    res = await client.post(
        "/v1/auth/register",
        json={"email": "new@example.com", "password": "password123", "company_name": "Acme"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dupe@example.com", "password": "password123", "company_name": "Acme"}
    await client.post("/v1/auth/register", json=payload)
    res = await client.post("/v1/auth/register", json=payload)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"]


async def test_register_creates_admin_role(client: AsyncClient):
    tokens = await register(client, "admin@example.com")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    res = await client.get("/v1/auth/me", headers=headers)
    assert res.status_code == 200
    assert res.json()["role"] == "admin"


async def test_login_success(client: AsyncClient):
    await register(client, "login@example.com", password="mypassword")
    res = await client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()


async def test_login_wrong_password(client: AsyncClient):
    await register(client, "wrongpass@example.com", password="correct")
    res = await client.post(
        "/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "incorrect"},
    )
    assert res.status_code == 401
    assert "Invalid credentials" in res.json()["detail"]


async def test_login_unknown_email(client: AsyncClient):
    res = await client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert res.status_code == 401


async def test_me_returns_user(client: AsyncClient):
    tokens = await register(client, "me@example.com", company="MyCo")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    res = await client.get("/v1/auth/me", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "me@example.com"
    assert "id" in data
    assert "company_id" in data


async def test_me_requires_auth(client: AsyncClient):
    res = await client.get("/v1/auth/me")
    assert res.status_code == 403  # Missing Bearer header


async def test_me_invalid_token(client: AsyncClient):
    res = await client.get("/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert res.status_code == 401


async def test_refresh_returns_new_tokens(client: AsyncClient):
    tokens = await register(client, "refresh@example.com")
    res = await client.post(
        "/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Tokens should be rotated (different from original)
    assert data["refresh_token"] != tokens["refresh_token"]


async def test_refresh_old_token_invalidated(client: AsyncClient):
    tokens = await register(client, "rotate@example.com")
    original_refresh = tokens["refresh_token"]

    # Use the refresh token once
    await client.post("/v1/auth/refresh", json={"refresh_token": original_refresh})

    # Using the original again should fail
    res = await client.post("/v1/auth/refresh", json={"refresh_token": original_refresh})
    assert res.status_code == 401


async def test_refresh_invalid_token(client: AsyncClient):
    res = await client.post("/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert res.status_code == 401


async def test_logout_invalidates_refresh_token(client: AsyncClient):
    tokens = await register(client, "logout@example.com")

    res = await client.post("/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 204

    # Refresh after logout must fail
    res = await client.post("/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert res.status_code == 401


async def test_logout_unknown_token_is_noop(client: AsyncClient):
    """Logging out with an unknown token should not error."""
    res = await client.post("/v1/auth/logout", json={"refresh_token": "unknown-token"})
    assert res.status_code == 204


async def test_health(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
