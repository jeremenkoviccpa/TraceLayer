"""
Lattice integration via Lattice GraphQL API.

Credentials:
  api_token  — Lattice API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_GRAPHQL_URL = "https://api.latticehq.com/graphql"


class LatticeIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_token}",
            "Content-Type": "application/json",
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _GRAPHQL_URL,
                json={"query": "{ viewer { id email } }"},
                headers=headers,
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Lattice API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Lattice connect failed HTTP {r.status_code}")

            body = r.json()
            errors = body.get("errors")
            viewer = body.get("data", {}).get("viewer")

            if errors or viewer is None:
                raise IntegrationAuthError("Invalid Lattice API token.")

        self._api_token = api_token
        return True

    # ── GraphQL helper ─────────────────────────────────────────────────────────

    async def _gql(self, client: httpx.AsyncClient, query: str) -> dict:
        r = await client.post(
            _GRAPHQL_URL,
            json={"query": query},
            headers=self._headers(),
        )
        if r.status_code == 401:
            raise IntegrationAuthError("Invalid Lattice API token.")
        if r.status_code != 200:
            raise RuntimeError(f"Lattice GraphQL HTTP {r.status_code}")
        return r.json()

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_employees,
                self._collect_goals,
                self._collect_reviews,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Lattice collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        query = """
        {
          users(first: 100) {
            edges {
              node {
                id
                email
                name
                role { name }
                createdAt
                updatedAt
              }
            }
          }
        }
        """
        body = await self._gql(client, query)
        edges = body.get("data", {}).get("users", {}).get("edges", [])
        return [{"_type": "employee", **edge["node"]} for edge in edges if "node" in edge]

    async def _collect_goals(self, client: httpx.AsyncClient) -> list[dict]:
        query = """
        {
          goals(first: 50) {
            edges {
              node {
                id
                title
                status
                dueDate
                createdAt
              }
            }
          }
        }
        """
        body = await self._gql(client, query)
        edges = body.get("data", {}).get("goals", {}).get("edges", [])
        return [{"_type": "goal", **edge["node"]} for edge in edges if "node" in edge]

    async def _collect_reviews(self, client: httpx.AsyncClient) -> list[dict]:
        query = """
        {
          reviewCycles(first: 20) {
            edges {
              node {
                id
                name
                status
                startDate
                endDate
              }
            }
          }
        }
        """
        body = await self._gql(client, query)
        edges = body.get("data", {}).get("reviewCycles", {}).get("edges", [])
        return [{"_type": "review_cycle", **edge["node"]} for edge in edges if "node" in edge]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item, now))
            elif t == "goal":
                result.append(self._norm_goal(item, now))
            elif t == "review_cycle":
                result.append(self._norm_review_cycle(item, now))
        return result

    def _norm_employee(self, raw: dict, now: str) -> dict:
        role = raw.get("role")
        role_name = role.get("name") if isinstance(role, dict) else None
        return {
            "integration": "lattice",
            "control": "hr_security",
            "evidence_type": "lattice_employees",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("createdAt") or now,
            "data": {
                "email": raw.get("email"),
                "name": raw.get("name"),
                "role": role_name,
            },
        }

    def _norm_goal(self, raw: dict, now: str) -> dict:
        return {
            "integration": "lattice",
            "control": "hr_security",
            "evidence_type": "lattice_goals",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("createdAt") or now,
            "data": {
                "title": raw.get("title"),
                "status": raw.get("status"),
                "dueDate": raw.get("dueDate"),
            },
        }

    def _norm_review_cycle(self, raw: dict, now: str) -> dict:
        return {
            "integration": "lattice",
            "control": "hr_security",
            "evidence_type": "lattice_review_cycles",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("createdAt") or now,
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
                "startDate": raw.get("startDate"),
                "endDate": raw.get("endDate"),
            },
        }
