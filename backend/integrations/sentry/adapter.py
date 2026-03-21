from __future__ import annotations
"""
Sentry integration via Sentry Web API.

Credentials:
  auth_token — Sentry User Auth Token (Bearer)
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

SENTRY_API = "https://sentry.io/api/0"


class SentryIntegration(IntegrationAdapter):

    def __init__(self):
        self._auth_token: str | None = None
        self._org_slug: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._auth_token}",
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        auth_token = credentials.get("auth_token", "").strip()

        if not auth_token:
            raise IntegrationAuthError("auth_token is required.")

        headers = {"Authorization": f"Bearer {auth_token}"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{SENTRY_API}/", headers=headers)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Sentry auth token or insufficient permissions.")
            r.raise_for_status()

            # Resolve the first accessible organization slug now, so collect_evidence
            # doesn't need to make an unauthenticated assumption.
            orgs_r = await client.get(f"{SENTRY_API}/organizations/", headers=headers)
            orgs_r.raise_for_status()
            orgs = orgs_r.json()
            if not orgs:
                raise IntegrationAuthError("No Sentry organizations accessible with this token.")
            org_slug = orgs[0].get("slug")
            if not org_slug:
                raise IntegrationAuthError("Could not determine Sentry organization slug.")

        self._auth_token = auth_token
        self._org_slug = org_slug
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            results: list[dict] = []

            try:
                orgs = await self._collect_organizations(client)
                results.extend(orgs)
            except Exception as exc:
                results.append({"_type": "error", "_source": "organizations", "_error": str(exc)})

            try:
                projects = await self._collect_projects(client)
                results.extend(projects)
            except Exception as exc:
                results.append({"_type": "error", "_source": "projects", "_error": str(exc)})

            try:
                members = await self._collect_members(client)
                results.extend(members)
            except Exception as exc:
                results.append({"_type": "error", "_source": "members", "_error": str(exc)})

            try:
                issues = await self._collect_issues(client)
                results.extend(issues)
            except Exception as exc:
                results.append({"_type": "error", "_source": "issues", "_error": str(exc)})

        return results

    async def _collect_organizations(self, client: httpx.AsyncClient) -> list[dict]:
        """Fetch all accessible organizations and tag with _type."""
        r = await client.get(f"{SENTRY_API}/organizations/", headers=self._headers())
        r.raise_for_status()
        orgs = r.json()
        return [
            {
                "_type": "organization",
                "id": o.get("id"),
                "slug": o.get("slug"),
                "name": o.get("name"),
                "status": o.get("status"),
                "date_created": o.get("dateCreated"),
            }
            for o in orgs
        ]

    async def _collect_projects(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate all projects for the org using cursor-based pagination."""
        projects = []
        url = f"{SENTRY_API}/organizations/{self._org_slug}/projects/"
        while url:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            for p in r.json():
                projects.append({
                    "_type": "project",
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "platform": p.get("platform"),
                    "status": p.get("status"),
                    "team": p.get("team"),
                    "date_created": p.get("dateCreated"),
                })
            url = _next_cursor_url(r)
        return projects

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate all organization members."""
        members = []
        url = f"{SENTRY_API}/organizations/{self._org_slug}/members/"
        while url:
            r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            for m in r.json():
                members.append({
                    "_type": "member",
                    "id": m.get("id"),
                    "email": m.get("email"),
                    "role": m.get("role"),
                    "pending": m.get("pending", False),
                    "date_created": m.get("dateCreated"),
                })
            url = _next_cursor_url(r)
        return members

    async def _collect_issues(self, client: httpx.AsyncClient) -> list[dict]:
        """Paginate issues for the org (limit 100 per page)."""
        issues = []
        url = f"{SENTRY_API}/organizations/{self._org_slug}/issues/"
        params = {"limit": 100}
        # Only apply params to the first request; subsequent pages use Link header URLs
        first = True
        while url:
            if first:
                r = await client.get(url, headers=self._headers(), params=params)
                first = False
            else:
                r = await client.get(url, headers=self._headers())
            r.raise_for_status()
            for i in r.json():
                issues.append({
                    "_type": "issue",
                    "id": i.get("id"),
                    "title": i.get("title"),
                    "level": i.get("level"),
                    "status": i.get("status"),
                    "first_seen": i.get("firstSeen"),
                    "last_seen": i.get("lastSeen"),
                    "project": i.get("project"),
                })
            url = _next_cursor_url(r)
        return issues

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "organization":
                result.append(self._norm_organization(item))
            elif t == "project":
                result.append(self._norm_project(item))
            elif t == "member":
                result.append(self._norm_member(item))
            elif t == "issue":
                result.append(self._norm_issue(item))
            # skip error sentinels silently
        return result

    def _norm_organization(self, raw: dict) -> dict:
        return {
            "integration": "sentry",
            "control": "logging_monitoring",
            "evidence_type": "sentry_organizations",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("date_created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "slug": raw.get("slug"),
                "name": raw.get("name"),
                "status": raw.get("status"),
            },
        }

    def _norm_project(self, raw: dict) -> dict:
        return {
            "integration": "sentry",
            "control": "logging_monitoring",
            "evidence_type": "sentry_projects",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("date_created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "platform": raw.get("platform"),
                "status": raw.get("status"),
                "team": raw.get("team"),
            },
        }

    def _norm_member(self, raw: dict) -> dict:
        return {
            "integration": "sentry",
            "control": "access_control",
            "evidence_type": "sentry_members",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("date_created") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "email": raw.get("email"),
                "role": raw.get("role"),
                "pending": raw.get("pending", False),
            },
        }

    def _norm_issue(self, raw: dict) -> dict:
        return {
            "integration": "sentry",
            "control": "logging_monitoring",
            "evidence_type": "sentry_issues",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("first_seen") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "level": raw.get("level"),
                "status": raw.get("status"),
                "first_seen": raw.get("first_seen"),
                "last_seen": raw.get("last_seen"),
                "project": raw.get("project"),
            },
        }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _next_cursor_url(response: httpx.Response) -> str | None:
    """
    Parse the Link header for a 'next' relation.
    Sentry uses:  <https://...>; rel="next"; results="true"; cursor="..."
    Only follow if results="true" to avoid fetching an empty final page.
    """
    link_header = response.headers.get("Link", "")
    if not link_header:
        return None

    for segment in link_header.split(","):
        parts = [p.strip() for p in segment.split(";")]
        if len(parts) < 2:
            continue
        url_part = parts[0].strip("<> ")
        attrs = {}
        for attr in parts[1:]:
            if "=" in attr:
                k, v = attr.split("=", 1)
                attrs[k.strip()] = v.strip().strip('"')
        if attrs.get("rel") == "next" and attrs.get("results") == "true":
            return url_part

    return None
