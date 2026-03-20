"""
Linear integration via GraphQL API.

Credentials:
  api_key — Linear personal API key (lin_api_xxxx)

Evidence collected:
  - Teams + team members   → change_management / linear_teams
                           → access_control   / linear_members
  - Issues (recent 250)    → change_management / linear_issues
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

LINEAR_API = "https://api.linear.app/graphql"

_VIEWER_QUERY = "{ viewer { id name email } }"

_TEAMS_QUERY = """
{
  teams {
    nodes {
      id
      name
      key
      description
      members {
        nodes {
          id
          name
          email
          admin
          active
          createdAt
        }
      }
    }
  }
}
"""

_ISSUES_QUERY = """
{
  issues(first: 250, orderBy: updatedAt) {
    nodes {
      id
      title
      state {
        name
        type
      }
      priority
      priorityLabel
      assignee {
        name
        email
      }
      team {
        name
        key
      }
      labels {
        nodes {
          name
        }
      }
      createdAt
      updatedAt
      completedAt
      canceledAt
    }
  }
}
"""


class LinearIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": self._api_key,
            "Content-Type": "application/json",
        }

    async def _gql(self, client: httpx.AsyncClient, query: str) -> dict:
        """Execute a GraphQL query and return the parsed response dict."""
        r = await client.post(LINEAR_API, json={"query": query}, headers=self._headers())
        r.raise_for_status()
        return r.json()

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = (credentials.get("api_key") or credentials.get("token") or "").strip()
        if not api_key:
            raise IntegrationAuthError("Linear API Key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                LINEAR_API,
                json={"query": _VIEWER_QUERY},
                headers={"Authorization": api_key, "Content-Type": "application/json"},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid Linear API key — check the key value and its permissions."
                )
            r.raise_for_status()
            body = r.json()
            if "errors" in body:
                msg = body["errors"][0].get("message", "Authentication failed")
                raise IntegrationAuthError(f"Linear auth error: {msg}")
            viewer = body.get("data", {}).get("viewer")
            if not viewer:
                raise IntegrationAuthError("Linear: could not retrieve viewer identity.")

        self._api_key = api_key
        return True

    # ── Collection ────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                team_items = await self._collect_teams(client)
                results.extend(team_items)
            except Exception as exc:
                logger.error("Linear: failed to collect teams: %s", exc)

            try:
                issues = await self._collect_issues(client)
                results.extend(issues)
            except Exception as exc:
                logger.error("Linear: failed to collect issues: %s", exc)

        return results

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch all teams and flatten team_member records out of them."""
        body = await self._gql(client, _TEAMS_QUERY)
        if "errors" in body:
            raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))

        teams_raw = body.get("data", {}).get("teams", {}).get("nodes", [])
        items: list[dict] = []
        for team in teams_raw:
            # Emit team record (strip members node — captured separately)
            items.append({"_type": "team", **{k: v for k, v in team.items() if k != "members"}})
            # Emit individual member records tagged with team context
            for member in team.get("members", {}).get("nodes", []):
                items.append(
                    {
                        "_type": "team_member",
                        "_team_id": team["id"],
                        "_team_name": team["name"],
                        **member,
                    }
                )
        return items

    async def _collect_issues(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch the most recent 250 issues."""
        body = await self._gql(client, _ISSUES_QUERY)
        if "errors" in body:
            raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))

        issues_raw = body.get("data", {}).get("issues", {}).get("nodes", [])
        return [{"_type": "issue", **issue} for issue in issues_raw]

    # ── Normalize ─────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "team":
                result.append(self._norm_team(item))
            elif t == "team_member":
                result.append(self._norm_team_member(item))
            elif t == "issue":
                result.append(self._norm_issue(item))
        return result

    def _norm_team(self, raw: dict) -> dict:
        return {
            "integration": "linear",
            "control": "change_management",
            "evidence_type": "linear_teams",
            "source_id": raw["id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "key": raw.get("key"),
                "description": raw.get("description"),
            },
        }

    def _norm_team_member(self, raw: dict) -> dict:
        return {
            "integration": "linear",
            "control": "access_control",
            "evidence_type": "linear_members",
            "source_id": raw["id"],
            "timestamp": raw.get("createdAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "email": raw.get("email"),
                "admin": raw.get("admin", False),
                "active": raw.get("active", True),
                "team_id": raw.get("_team_id"),
                "team_name": raw.get("_team_name"),
            },
        }

    def _norm_issue(self, raw: dict) -> dict:
        label_names = [lbl["name"] for lbl in raw.get("labels", {}).get("nodes", [])]
        return {
            "integration": "linear",
            "control": "change_management",
            "evidence_type": "linear_issues",
            "source_id": raw["id"],
            "timestamp": raw.get("updatedAt", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "title": raw.get("title"),
                "state": raw.get("state", {}).get("name"),
                "state_type": raw.get("state", {}).get("type"),
                "priority": raw.get("priority"),
                "priority_label": raw.get("priorityLabel"),
                "assignee_name": (raw.get("assignee") or {}).get("name"),
                "assignee_email": (raw.get("assignee") or {}).get("email"),
                "team_name": (raw.get("team") or {}).get("name"),
                "team_key": (raw.get("team") or {}).get("key"),
                "labels": label_names,
                "created_at": raw.get("createdAt"),
                "updated_at": raw.get("updatedAt"),
                "completed_at": raw.get("completedAt"),
                "canceled_at": raw.get("canceledAt"),
            },
        }
