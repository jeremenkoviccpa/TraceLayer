"""
Google Workspace integration via Admin SDK Directory API.

Requires a service account with domain-wide delegation enabled.
Scopes needed:
  https://www.googleapis.com/auth/admin.directory.user.readonly
  https://www.googleapis.com/auth/admin.directory.group.readonly
"""
import base64
import json
import time
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_ADMIN_API = "https://admin.googleapis.com/admin/directory/v1"
_SCOPES = " ".join([
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
])


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(sa: dict, admin_email: str) -> str:
    """Build a signed JWT for service account impersonation."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    now = int(time.time())
    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload = _b64url(json.dumps({
        "iss": sa["client_email"],
        "scope": _SCOPES,
        "aud": _TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
        "sub": admin_email,
    }).encode())

    signing_input = f"{header}.{payload}".encode()
    private_key = serialization.load_pem_private_key(
        sa["private_key"].encode(), password=None
    )
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{payload}.{_b64url(signature)}"


class GoogleWorkspaceIntegration(IntegrationAdapter):

    def __init__(self):
        self._sa: dict | None = None
        self._admin_email: str | None = None
        self._access_token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        raw = credentials.get("service_account_json", "")
        admin_email = credentials.get("admin_email", "").strip()
        try:
            sa = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise IntegrationAuthError("service_account_json is not valid JSON")

        if not admin_email:
            raise IntegrationAuthError("admin_email is required")

        token = await self._fetch_token(sa, admin_email)
        # Quick validation — list 1 user
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_ADMIN_API}/users",
                headers={"Authorization": f"Bearer {token}"},
                params={"customer": "my_customer", "maxResults": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid service account credentials or missing domain-wide delegation")
            if r.status_code == 403:
                raise IntegrationAuthError("Service account lacks required scopes or admin_email is not a super-admin")
            r.raise_for_status()

        self._sa = sa
        self._admin_email = admin_email
        self._access_token = token
        return True

    async def _fetch_token(self, sa: dict, admin_email: str) -> str:
        jwt = _make_jwt(sa, admin_email)
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(_TOKEN_URL, data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt,
            })
            r.raise_for_status()
            return r.json()["access_token"]

    async def collect_evidence(self) -> list[dict]:
        self._access_token = await self._fetch_token(self._sa, self._admin_email)
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client, headers)
            groups = await self._collect_groups(client, headers)
        return users + groups

    async def _collect_users(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        users, token = [], None
        while True:
            params = {"customer": "my_customer", "maxResults": 500, "orderBy": "email"}
            if token:
                params["pageToken"] = token
            r = await client.get(f"{_ADMIN_API}/users", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            for u in data.get("users", []):
                users.append({"_type": "user", **u})
            token = data.get("nextPageToken")
            if not token:
                break
        return users

    async def _collect_groups(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        groups, token = [], None
        while True:
            params = {"customer": "my_customer", "maxResults": 200}
            if token:
                params["pageToken"] = token
            r = await client.get(f"{_ADMIN_API}/groups", headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
            for g in data.get("groups", []):
                groups.append({"_type": "group", **g})
            token = data.get("nextPageToken")
            if not token:
                break
        return groups

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
                if item.get("isAdmin") or item.get("isDelegatedAdmin"):
                    result.append(self._norm_admin(item))
            elif t == "group":
                result.append(self._norm_group(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "google_workspace",
            "control": "access_control",
            "evidence_type": "workspace_users",
            "source_id": raw["id"],
            "timestamp": raw.get("creationTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "email": raw.get("primaryEmail"),
                "full_name": raw.get("name", {}).get("fullName"),
                "is_admin": raw.get("isAdmin", False),
                "is_delegated_admin": raw.get("isDelegatedAdmin", False),
                "suspended": raw.get("suspended", False),
                "org_unit": raw.get("orgUnitPath"),
                "last_login": raw.get("lastLoginTime"),
            },
        }

    def _norm_admin(self, raw: dict) -> dict:
        return {
            "integration": "google_workspace",
            "control": "access_control",
            "evidence_type": "workspace_admin_members",
            "source_id": f"admin_{raw['id']}",
            "timestamp": raw.get("creationTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "email": raw.get("primaryEmail"),
                "is_super_admin": raw.get("isAdmin", False),
                "is_delegated_admin": raw.get("isDelegatedAdmin", False),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "google_workspace",
            "control": "access_control",
            "evidence_type": "workspace_groups",
            "source_id": raw["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "member_count": raw.get("directMembersCount"),
                "description": raw.get("description"),
            },
        }
