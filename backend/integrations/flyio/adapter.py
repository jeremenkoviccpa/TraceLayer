from __future__ import annotations

"""
Fly.io integration via Fly.io GraphQL API.

Credentials:
  auth_token — Fly.io personal access token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_GQL_URL = "https://api.fly.io/graphql"


class FlyioIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._auth_token: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._auth_token}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── GraphQL helper ─────────────────────────────────────────────────────────

    async def _gql(self, client: httpx.AsyncClient, query: str) -> dict:
        r = await client.post(
            _GQL_URL,
            headers=self._headers(),
            json={"query": query},
        )
        return r.json()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        auth_token = credentials.get("auth_token", "").strip()
        if not auth_token:
            raise IntegrationAuthError("auth_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _GQL_URL,
                headers={"Authorization": f"Bearer {auth_token}"},
                json={"query": "{ viewer { id email } }"},
            )

            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Fly.io auth token.")

            body = r.json()
            errors = body.get("errors")
            viewer = body.get("data", {}).get("viewer")

            if errors or not viewer:
                raise IntegrationAuthError("Invalid Fly.io auth token.")

        self._auth_token = auth_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_apps,
                self._collect_organizations,
                self._collect_certificates,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Fly.io collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_apps(self, client: httpx.AsyncClient) -> list[dict]:
        query = """
        {
          apps(type: "container") {
            nodes {
              id
              name
              status
              organization { id name }
              appUrl
              hostname
              createdAt
            }
          }
        }
        """
        body = await self._gql(client, query)
        nodes = body.get("data", {}).get("apps", {}).get("nodes", [])
        return [{"_type": "app", **node} for node in nodes]

    async def _collect_organizations(self, client: httpx.AsyncClient) -> list[dict]:
        query = """
        {
          viewer {
            organizations {
              nodes {
                id
                name
                slug
                type
                members {
                  edges {
                    node { id email name }
                    role
                  }
                }
              }
            }
          }
        }
        """
        body = await self._gql(client, query)
        nodes = (
            body.get("data", {})
            .get("viewer", {})
            .get("organizations", {})
            .get("nodes", [])
        )
        return [{"_type": "organization", **node} for node in nodes]

    async def _collect_certificates(self, client: httpx.AsyncClient) -> list[dict]:
        # Collect apps first to get names
        apps_raw = await self._collect_apps(client)
        app_names = [a.get("name") for a in apps_raw if a.get("name")]

        items: list[dict] = []
        for app_name in app_names[:3]:
            query = f"""
            {{
              app(name: "{app_name}") {{
                certificates {{
                  nodes {{
                    id
                    hostname
                    checked
                    expiresAt
                  }}
                }}
              }}
            }}
            """
            body = await self._gql(client, query)
            nodes = (
                body.get("data", {})
                .get("app", {})
                .get("certificates", {})
                .get("nodes", [])
            )
            for node in nodes:
                items.append({"_type": "certificate", **node})

        return items

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "app":
                result.append(self._norm_app(item))
            elif t == "organization":
                result.append(self._norm_organization(item))
            elif t == "certificate":
                result.append(self._norm_certificate(item))
        return result

    def _norm_app(self, item: dict) -> dict:
        org = item.get("organization")
        org_name = org.get("name") if isinstance(org, dict) else None
        return {
            "integration": "flyio",
            "control": "change_management",
            "evidence_type": "flyio_apps",
            "source_id": item.get("id", ""),
            "timestamp": item.get("createdAt") or self._now(),
            "data": {
                "name": item.get("name"),
                "status": item.get("status"),
                "appUrl": item.get("appUrl"),
                "hostname": item.get("hostname"),
                "organization": org_name,
            },
        }

    def _norm_organization(self, item: dict) -> dict:
        members = item.get("members", {})
        member_count = len(members.get("edges", [])) if isinstance(members, dict) else 0
        return {
            "integration": "flyio",
            "control": "access_control",
            "evidence_type": "flyio_organizations",
            "source_id": item.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": item.get("name"),
                "slug": item.get("slug"),
                "type": item.get("type"),
                "member_count": member_count,
            },
        }

    def _norm_certificate(self, item: dict) -> dict:
        return {
            "integration": "flyio",
            "control": "network_security",
            "evidence_type": "flyio_certificates",
            "source_id": item.get("id", ""),
            "timestamp": item.get("expiresAt") or self._now(),
            "data": {
                "hostname": item.get("hostname"),
                "checked": item.get("checked"),
                "expiresAt": item.get("expiresAt"),
            },
        }
