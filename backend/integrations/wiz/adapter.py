from __future__ import annotations
"""
Wiz integration via Wiz GraphQL API with OAuth2 client credentials.

Credentials:
  client_id     — Wiz OAuth2 client ID
  client_secret — Wiz OAuth2 client secret
  api_endpoint  — e.g. "https://api.us20.app.wiz.io/graphql"
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_TOKEN_URL = "https://auth.app.wiz.io/oauth/token"

_ISSUES_QUERY = """
query Issues($after: String) {
  issues(
    first: 100
    after: $after
    filterBy: { status: [OPEN, IN_PROGRESS] }
  ) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      title
      severity
      status
      createdAt
      resolvedAt
      entitySnapshot {
        type
        name
      }
    }
  }
}
"""

_RESOURCES_QUERY = """
query CloudResources($after: String) {
  cloudResources(first: 100, after: $after) {
    pageInfo { hasNextPage endCursor }
    nodes {
      id
      name
      type
      region
      cloudPlatform
    }
  }
}
"""

_ME_QUERY = "{ me { id } }"


class WizIntegration(IntegrationAdapter):

    def __init__(self):
        self._access_token: str | None = None
        self._api_endpoint: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def _get_token(self, client_id: str, client_secret: str) -> str:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _TOKEN_URL,
                json={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "audience": "wiz-api",
                },
            )
            if r.status_code in (400, 401, 403):
                raise IntegrationAuthError(f"Wiz OAuth2 token request failed: {r.text}")
            r.raise_for_status()
            data = r.json()
            token = data.get("access_token")
            if not token:
                raise IntegrationAuthError("Wiz OAuth2 response did not include access_token")
            return token

    async def connect(self, credentials: dict) -> bool:
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        api_endpoint = credentials.get("api_endpoint", "").strip().rstrip("/")

        if not client_id or not client_secret or not api_endpoint:
            raise IntegrationAuthError("client_id, client_secret, and api_endpoint are required")

        token = await self._get_token(client_id, client_secret)

        # Validate token with a lightweight query
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                api_endpoint,
                json={"query": _ME_QUERY},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Wiz access token was rejected by the API endpoint")
            r.raise_for_status()
            body = r.json()
            if "errors" in body:
                raise IntegrationAuthError(f"Wiz GraphQL auth check failed: {body['errors']}")

        self._access_token = token
        self._api_endpoint = api_endpoint
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=60) as client:
            issues = await self._collect_issues(client)
            resources = await self._collect_cloud_resources(client)
        return issues + resources

    async def _graphql(self, client: httpx.AsyncClient, query: str, variables: dict | None = None) -> dict:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        r = await client.post(self._api_endpoint, json=payload, headers=self._headers())
        r.raise_for_status()
        return r.json()

    async def _collect_issues(self, client: httpx.AsyncClient) -> list[dict]:
        issues = []
        cursor = None
        try:
            while True:
                variables = {"after": cursor} if cursor else {}
                data = await self._graphql(client, _ISSUES_QUERY, variables)
                page = data.get("data", {}).get("issues", {})
                for node in page.get("nodes", []):
                    issues.append({"_type": "issue", **node})
                page_info = page.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Wiz issues: {exc}") from exc
        return issues

    async def _collect_cloud_resources(self, client: httpx.AsyncClient) -> list[dict]:
        resources = []
        cursor = None
        try:
            while True:
                variables = {"after": cursor} if cursor else {}
                data = await self._graphql(client, _RESOURCES_QUERY, variables)
                page = data.get("data", {}).get("cloudResources", {})
                for node in page.get("nodes", []):
                    resources.append({"_type": "cloud_resource", **node})
                page_info = page.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Wiz cloud resources: {exc}") from exc
        return resources

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "issue":
                result.append(self._norm_issue(item))
            elif t == "cloud_resource":
                result.append(self._norm_cloud_resource(item))
        return result

    def _norm_issue(self, raw: dict) -> dict:
        entity = raw.get("entitySnapshot") or {}
        return {
            "integration": "wiz",
            "control": "vulnerability_management",
            "evidence_type": "wiz_issues",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdAt") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "severity": raw.get("severity"),
                "status": raw.get("status"),
                "resolved_at": raw.get("resolvedAt"),
                "entity_type": entity.get("type"),
                "entity_name": entity.get("name"),
            },
        }

    def _norm_cloud_resource(self, raw: dict) -> dict:
        return {
            "integration": "wiz",
            "control": "access_control",
            "evidence_type": "wiz_cloud_resources",
            "source_id": raw.get("id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "type": raw.get("type"),
                "region": raw.get("region"),
                "cloud_platform": raw.get("cloudPlatform"),
            },
        }
