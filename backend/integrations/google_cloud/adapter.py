"""
Google Cloud Platform integration adapter.

Collects GCP projects, IAM policies, and service accounts for
access control evidence.

Credentials:
  service_account_json — full service account JSON key as a string

Required IAM roles:
  roles/viewer  OR  roles/iam.securityReviewer on the target projects/org
  (resourcemanager.projects.list, resourcemanager.projects.getIamPolicy,
   iam.serviceAccounts.list)

Note: This adapter does NOT require domain-wide delegation.  The service
account itself must have the permissions above granted at the organization
or folder level so it can enumerate projects across the account.
"""
import base64
import json
import time
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPES = "https://www.googleapis.com/auth/cloud-platform.read-only"
_CRM = "https://cloudresourcemanager.googleapis.com/v1"
_IAM = "https://iam.googleapis.com/v1"

# Limit IAM policy + service account collection to first N projects so a
# single call does not take unbounded time for large orgs.
_MAX_IAM_PROJECTS = 5


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _make_jwt(sa: dict) -> str:
    """Build a signed RS256 JWT for service account authentication."""
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
    }).encode())

    signing_input = f"{header}.{payload}".encode()
    private_key = serialization.load_pem_private_key(
        sa["private_key"].encode(), password=None
    )
    signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{payload}.{_b64url(signature)}"


class GoogleCloudIntegration(IntegrationAdapter):

    def __init__(self):
        self._sa: dict | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        raw = credentials.get("service_account_json", "")
        try:
            sa = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            raise IntegrationAuthError("service_account_json is not valid JSON")

        required = {"type", "client_email", "private_key"}
        missing = required - sa.keys()
        if missing:
            raise IntegrationAuthError(
                f"service_account_json is missing required fields: {missing}"
            )
        if sa.get("type") != "service_account":
            raise IntegrationAuthError(
                "service_account_json must be of type 'service_account'"
            )

        token = await self._fetch_token(sa)

        # Quick validation — list 1 project
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_CRM}/projects",
                headers=self._auth_headers(token),
                params={"pageSize": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError(
                    "GCP auth failed (401): invalid service account credentials"
                )
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "GCP auth failed (403): service account lacks "
                    "resourcemanager.projects.list permission"
                )
            r.raise_for_status()

        self._sa = sa
        self._access_token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        self._access_token = await self._fetch_token(self._sa)
        async with httpx.AsyncClient(timeout=60) as client:
            projects = await self._collect_projects(client)
            iam_policies = await self._collect_iam_policies(client, projects)
            service_accounts = await self._collect_service_accounts(client, projects)
        return projects + iam_policies + service_accounts

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "project":
                result.append(self._norm_project(item, now))
            elif t == "iam_policy":
                result.append(self._norm_iam_policy(item, now))
            elif t == "service_account":
                result.append(self._norm_service_account(item, now))
        return result

    # ------------------------------------------------------------------
    # Token
    # ------------------------------------------------------------------

    async def _fetch_token(self, sa: dict) -> str:
        jwt = _make_jwt(sa)
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": jwt,
                },
            )
            if r.status_code in (400, 401):
                detail = ""
                try:
                    detail = r.json().get("error_description", "")
                except Exception:
                    pass
                raise IntegrationAuthError(
                    f"GCP token fetch failed ({r.status_code}): {detail}"
                )
            r.raise_for_status()
            return r.json()["access_token"]

    def _auth_headers(self, token: str | None = None) -> dict:
        return {
            "Authorization": f"Bearer {token or self._access_token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Collectors
    # ------------------------------------------------------------------

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        """
        List all GCP projects visible to the service account.
        Uses pageToken pagination.
        """
        items: list[dict] = []
        page_token: str | None = None

        while True:
            params: dict = {"pageSize": 500}
            if page_token:
                params["pageToken"] = page_token

            r = await client.get(
                f"{_CRM}/projects",
                headers=self._auth_headers(),
                params=params,
            )
            r.raise_for_status()
            data = r.json()

            for proj in data.get("projects", []):
                items.append({
                    "_type": "project",
                    "projectId": proj.get("projectId"),
                    "name": proj.get("name"),
                    "lifecycleState": proj.get("lifecycleState"),
                    "createTime": proj.get("createTime"),
                    "projectNumber": proj.get("projectNumber"),
                    "parent": proj.get("parent"),
                })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return items

    async def _collect_iam_policies(
        self, client: httpx.AsyncClient, projects: list[dict]
    ) -> list[dict]:
        """
        Fetch IAM policies for up to _MAX_IAM_PROJECTS projects.
        Each project's policy fetch is wrapped in its own try/except so a
        single 403 does not abort the rest.
        """
        items: list[dict] = []
        active = [
            p for p in projects if p.get("lifecycleState") == "ACTIVE"
        ][:_MAX_IAM_PROJECTS]

        for proj in active:
            project_id = proj.get("projectId", "")
            try:
                r = await client.post(
                    f"{_CRM}/projects/{project_id}:getIamPolicy",
                    headers=self._auth_headers(),
                    json={},  # empty request body required by the API
                )
                if r.status_code in (403, 404):
                    # Not permitted on this project — skip silently
                    continue
                r.raise_for_status()
                policy = r.json()
                items.append({
                    "_type": "iam_policy",
                    "project": project_id,
                    "version": policy.get("version"),
                    "bindings": policy.get("bindings", []),
                    "etag": policy.get("etag"),
                })
            except httpx.HTTPStatusError:
                # Non-fatal; continue with remaining projects
                pass

        return items

    async def _collect_service_accounts(
        self, client: httpx.AsyncClient, projects: list[dict]
    ) -> list[dict]:
        """
        List service accounts for up to _MAX_IAM_PROJECTS active projects.
        Supports pageToken pagination per project.
        """
        items: list[dict] = []
        active = [
            p for p in projects if p.get("lifecycleState") == "ACTIVE"
        ][:_MAX_IAM_PROJECTS]

        for proj in active:
            project_id = proj.get("projectId", "")
            try:
                page_token: str | None = None
                while True:
                    params: dict = {"pageSize": 100}
                    if page_token:
                        params["pageToken"] = page_token

                    r = await client.get(
                        f"{_IAM}/projects/{project_id}/serviceAccounts",
                        headers=self._auth_headers(),
                        params=params,
                    )
                    if r.status_code in (403, 404):
                        break  # skip this project
                    r.raise_for_status()
                    data = r.json()

                    for sa in data.get("accounts", []):
                        items.append({
                            "_type": "service_account",
                            "project": project_id,
                            "email": sa.get("email"),
                            "displayName": sa.get("displayName"),
                            "disabled": sa.get("disabled", False),
                            "uniqueId": sa.get("uniqueId"),
                            "description": sa.get("description"),
                        })

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

            except httpx.HTTPStatusError:
                # Non-fatal; continue with remaining projects
                pass

        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_project(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "google_cloud",
            "control": "access_control",
            "evidence_type": "gcp_projects",
            "source_id": raw.get("projectId", raw.get("projectNumber", "")),
            "timestamp": raw.get("createTime") or fallback_ts,
            "data": {
                "project_id": raw.get("projectId"),
                "name": raw.get("name"),
                "lifecycle_state": raw.get("lifecycleState"),
                "create_time": raw.get("createTime"),
                "project_number": raw.get("projectNumber"),
                "parent": raw.get("parent"),
            },
        }

    def _norm_iam_policy(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "google_cloud",
            "control": "access_control",
            "evidence_type": "gcp_iam_policies",
            "source_id": f"iam_policy_{raw.get('project', '')}",
            "timestamp": fallback_ts,
            "data": {
                "project": raw.get("project"),
                "version": raw.get("version"),
                "bindings": raw.get("bindings", []),
                "etag": raw.get("etag"),
            },
        }

    def _norm_service_account(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "google_cloud",
            "control": "access_control",
            "evidence_type": "gcp_service_accounts",
            "source_id": raw.get("uniqueId") or raw.get("email", ""),
            "timestamp": fallback_ts,
            "data": {
                "project": raw.get("project"),
                "email": raw.get("email"),
                "display_name": raw.get("displayName"),
                "disabled": raw.get("disabled", False),
                "description": raw.get("description"),
            },
        }
