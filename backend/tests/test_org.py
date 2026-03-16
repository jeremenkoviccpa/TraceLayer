from httpx import AsyncClient

from tests.conftest import auth_headers, register


async def test_list_members_includes_self(client: AsyncClient):
    headers = await auth_headers(client, "org_self@example.com")
    res = await client.get("/v1/org/members", headers=headers)
    assert res.status_code == 200
    emails = [m["email"] for m in res.json()]
    assert "org_self@example.com" in emails


async def test_list_members_requires_auth(client: AsyncClient):
    res = await client.get("/v1/org/members")
    assert res.status_code == 403


async def test_invite_member_success(client: AsyncClient):
    headers = await auth_headers(client, "inviter@example.com")
    res = await client.post(
        "/v1/org/invites",
        json={"email": "newmember@example.com", "role": "member"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "newmember@example.com"
    assert data["role"] == "member"
    assert "invite_url" in data
    assert "token=" in data["invite_url"]
    assert data["accepted_at"] is None


async def test_invite_requires_admin(client: AsyncClient):
    """Non-admin users cannot send invites."""
    # Register as admin, create invite, accept it as member
    admin_headers = await auth_headers(client, "admin_for_invite@example.com", company="InviteCo")

    # Send invite
    invite_res = await client.post(
        "/v1/org/invites",
        json={"email": "member_user@example.com", "role": "member"},
        headers=admin_headers,
    )
    token = invite_res.json()["invite_url"].split("token=")[1]

    # Accept invite — creates member user
    await client.post(
        "/v1/org/invites/accept",
        json={"token": token, "password": "password123"},
    )

    # Login as member
    login_res = await client.post(
        "/v1/auth/login",
        json={"email": "member_user@example.com", "password": "password123"},
    )
    member_token = login_res.json()["access_token"]
    member_headers = {"Authorization": f"Bearer {member_token}"}

    # Member cannot invite
    res = await client.post(
        "/v1/org/invites",
        json={"email": "another@example.com", "role": "member"},
        headers=member_headers,
    )
    assert res.status_code == 403


async def test_invite_duplicate_email_replaces_old(client: AsyncClient):
    """Inviting same email twice revokes the old invite and creates a new one."""
    headers = await auth_headers(client, "re_inviter@example.com")

    res1 = await client.post(
        "/v1/org/invites",
        json={"email": "reinvited@example.com", "role": "member"},
        headers=headers,
    )
    id1 = res1.json()["id"]

    res2 = await client.post(
        "/v1/org/invites",
        json={"email": "reinvited@example.com", "role": "member"},
        headers=headers,
    )
    id2 = res2.json()["id"]

    assert id1 != id2

    # Only the new invite should be pending
    list_res = await client.get("/v1/org/invites", headers=headers)
    invite_ids = [i["id"] for i in list_res.json()]
    assert id2 in invite_ids
    assert id1 not in invite_ids


async def test_accept_invite_creates_user(client: AsyncClient):
    admin_headers = await auth_headers(client, "accept_admin@example.com", company="AcceptCo")

    invite_res = await client.post(
        "/v1/org/invites",
        json={"email": "accepted_user@example.com", "role": "member"},
        headers=admin_headers,
    )
    token = invite_res.json()["invite_url"].split("token=")[1]

    res = await client.post(
        "/v1/org/invites/accept",
        json={"token": token, "password": "newpassword123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()

    # Verify user is now in the company
    new_token = res.json()["access_token"]
    me_res = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_res.json()["email"] == "accepted_user@example.com"
    assert me_res.json()["role"] == "member"

    # Verify they appear in org members
    members_res = await client.get("/v1/org/members", headers=admin_headers)
    member_emails = [m["email"] for m in members_res.json()]
    assert "accepted_user@example.com" in member_emails


async def test_accept_invite_invalid_token(client: AsyncClient):
    res = await client.post(
        "/v1/org/invites/accept",
        json={"token": "not-a-real-token", "password": "password123"},
    )
    assert res.status_code == 400


async def test_accept_invite_used_token_fails(client: AsyncClient):
    """Once accepted, the token cannot be reused."""
    admin_headers = await auth_headers(client, "reuse_admin@example.com", company="ReuseCo")
    invite_res = await client.post(
        "/v1/org/invites",
        json={"email": "one_time@example.com", "role": "member"},
        headers=admin_headers,
    )
    token = invite_res.json()["invite_url"].split("token=")[1]

    # Accept once — succeeds
    await client.post("/v1/org/invites/accept", json={"token": token, "password": "password123"})

    # Try to accept again — must fail
    res = await client.post(
        "/v1/org/invites/accept",
        json={"token": token, "password": "password123"},
    )
    assert res.status_code == 400


async def test_revoke_invite(client: AsyncClient):
    headers = await auth_headers(client, "revoker@example.com")
    invite_res = await client.post(
        "/v1/org/invites",
        json={"email": "revoked@example.com", "role": "member"},
        headers=headers,
    )
    invite_id = invite_res.json()["id"]

    res = await client.delete(f"/v1/org/invites/{invite_id}", headers=headers)
    assert res.status_code == 204

    # Token should now be invalid
    token = invite_res.json()["invite_url"].split("token=")[1]
    accept_res = await client.post(
        "/v1/org/invites/accept",
        json={"token": token, "password": "password123"},
    )
    assert accept_res.status_code == 400


async def test_remove_member(client: AsyncClient):
    admin_headers = await auth_headers(client, "rm_admin@example.com", company="RemoveCo")

    invite_res = await client.post(
        "/v1/org/invites",
        json={"email": "to_be_removed@example.com", "role": "member"},
        headers=admin_headers,
    )
    token = invite_res.json()["invite_url"].split("token=")[1]
    accept_res = await client.post(
        "/v1/org/invites/accept",
        json={"token": token, "password": "password123"},
    )
    member_id = (
        await client.get(
            "/v1/auth/me",
            headers={"Authorization": f"Bearer {accept_res.json()['access_token']}"},
        )
    ).json()["id"]

    res = await client.delete(f"/v1/org/members/{member_id}", headers=admin_headers)
    assert res.status_code == 204

    members_res = await client.get("/v1/org/members", headers=admin_headers)
    emails = [m["email"] for m in members_res.json()]
    assert "to_be_removed@example.com" not in emails


async def test_cannot_remove_self(client: AsyncClient):
    tokens = await register(client, "self_remove@example.com")
    me = await client.get("/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    user_id = me.json()["id"]

    res = await client.delete(
        f"/v1/org/members/{user_id}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert res.status_code == 400


async def test_members_isolated_between_companies(client: AsyncClient):
    headers_a = await auth_headers(client, "iso_a@example.com", company="IsoA")
    headers_b = await auth_headers(client, "iso_b@example.com", company="IsoB")

    members_b = await client.get("/v1/org/members", headers=headers_b)
    emails_b = [m["email"] for m in members_b.json()]
    assert "iso_a@example.com" not in emails_b
