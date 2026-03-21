"""Google Authenticator / Google 2-Step Verification integration — collects 2SV enrollment via Google Admin SDK."""
import json
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
ADMIN_API = "https://admin.googleapis.com/admin/directory/v1"
SCOPES = "https://www.googleapis.com/auth/admin.directory.user.readonly"


class GoogleAuthenticatorIntegration(IntegrationAdapter):
    """
    Google Authenticator is Google's TOTP app for 2-Step Verification. This adapter
    queries the Google Workspace Admin SDK to collect 2SV enrollment status per user,
    security keys, and org-wide 2SV enforcement policies as compliance evidence.
    """

    def __init__(self):
        self._access_token: str | None = None
        self._admin_email: str | None = None

    async def connect(self, credentials: dict) -> bool:
        sa_json = credentials.get("service_account_json", "").strip()
        admin_email = credentials.get("admin_email", "").strip()
        if not sa_json or not admin_email:
            raise IntegrationAuthError("Service account JSON and admin email are required.")
        try:
            sa = json.loads(sa_json)
        except json.JSONDecodeError:
            raise IntegrationAuthError("Invalid JSON in service account credentials.")
        token = await self._get_token(sa, admin_email)
        if not token:
            raise IntegrationAuthError("Could not obtain Google access token. Verify domain-wide delegation is configured.")
        self._access_token = token
        self._admin_email = admin_email
        return True

    async def _get_token(self, sa: dict, admin_email: str) -> str | None:
        import time
        import jwt  # PyJWT — available in most Python envs
        now = int(time.time())
        payload = {
            "iss": sa["client_email"],
            "sub": admin_email,
            "scope": SCOPES,
            "aud": OAUTH_TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        }
        try:
            signed = jwt.encode(payload, sa["private_key"], algorithm="RS256")
        except Exception as exc:
            raise IntegrationAuthError(f"Failed to sign JWT: {exc}")
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                OAUTH_TOKEN_URL,
                data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": signed},
            )
            if r.status_code != 200:
                return None
            return r.json().get("access_token")

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client, headers)
        return users

    async def _collect_users(self, client, headers) -> list[dict]:
        items: list[dict] = []
        params: dict = {"customer": "my_customer", "maxResults": 500, "projection": "full"}
        while True:
            r = await client.get(f"{ADMIN_API}/users", headers=headers, params=params)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Insufficient permissions. Ensure domain-wide delegation includes admin.directory.user.readonly scope.")
            r.raise_for_status()
            data = r.json()
            for user in data.get("users", []):
                items.append({"_type": "google_user_2sv", **user})
            token = data.get("nextPageToken")
            if not token:
                break
            params["pageToken"] = token
        return items

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            if item.get("_type") == "google_user_2sv":
                result.append(self._norm_user(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "google_authenticator",
            "control": "access_control",
            "evidence_type": "google_2sv_enrollment",
            "source_id": raw["id"],
            "timestamp": raw.get("lastLoginTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "email": raw.get("primaryEmail"),
                "full_name": raw.get("name", {}).get("fullName"),
                "is_enrolled_in_2sv": raw.get("isEnrolledIn2Sv", False),
                "is_enforced_in_2sv": raw.get("isEnforcedIn2Sv", False),
                "is_admin": raw.get("isAdmin", False),
                "is_suspended": raw.get("suspended", False),
                "org_unit_path": raw.get("orgUnitPath"),
                "last_login_time": raw.get("lastLoginTime"),
                "creation_time": raw.get("creationTime"),
            },
        }
