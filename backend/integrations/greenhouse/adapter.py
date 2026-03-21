from __future__ import annotations

"""
Greenhouse integration via Greenhouse Harvest API v1.

Credentials:
  api_key — Greenhouse Harvest API key (used as Basic auth username,
             empty string as password)
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://harvest.greenhouse.io/v1"
_MAX_PAGES = 2


class GreenhouseIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _auth(self) -> tuple[str, str]:
        # Greenhouse uses Basic auth: api_key as username, empty password
        return (self._api_key, "")

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/users",
                auth=(api_key, ""),
                params={"per_page": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Greenhouse API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Greenhouse connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_jobs,
                self._collect_candidates,
                self._collect_departments,
                self._collect_offices,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Greenhouse collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    def _parse_next_link(self, link_header: str) -> str | None:
        """Parse the Link header and return the 'next' URL if present."""
        if not link_header:
            return None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                url_part = part.split(";")[0].strip().strip("<>")
                return url_part
        return None

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        url: str | None = f"{_BASE}/users"
        params = {"per_page": 100}
        items: list[dict] = []
        pages = 0

        while url and pages < _MAX_PAGES:
            r = await client.get(url, auth=self._auth(), params=params if pages == 0 else None)
            if r.status_code != 200:
                raise RuntimeError(f"Greenhouse users HTTP {r.status_code}")
            items.extend([{"_type": "user", **u} for u in r.json()])
            url = self._parse_next_link(r.headers.get("Link", ""))
            pages += 1

        return items

    async def _collect_jobs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/jobs",
            auth=self._auth(),
            params={"per_page": 100, "status": "open"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Greenhouse jobs HTTP {r.status_code}")
        return [{"_type": "job", **j} for j in r.json()]

    async def _collect_candidates(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/candidates",
            auth=self._auth(),
            params={"per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Greenhouse candidates HTTP {r.status_code}")
        return [{"_type": "candidate", **c} for c in r.json()]

    async def _collect_departments(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/departments", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Greenhouse departments HTTP {r.status_code}")
        return [{"_type": "department", **d} for d in r.json()]

    async def _collect_offices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/offices", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Greenhouse offices HTTP {r.status_code}")
        return [{"_type": "office", **o} for o in r.json()]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "job":
                result.append(self._norm_job(item))
            elif t == "candidate":
                result.append(self._norm_candidate(item))
            elif t == "department":
                result.append(self._norm_department(item))
            elif t == "office":
                result.append(self._norm_office(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        emails = raw.get("emails") or []
        primary_email = raw.get("primary_email_address") or (
            emails[0].get("value") if emails else None
        )
        return {
            "integration": "greenhouse",
            "control": "hr_security",
            "evidence_type": "greenhouse_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "name": raw.get("name"),
                "primary_email_address": primary_email,
                "employee_id": raw.get("employee_id"),
                "site_admin": raw.get("site_admin"),
                "disabled": raw.get("disabled"),
            },
        }

    def _norm_job(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "greenhouse",
            "control": "hr_security",
            "evidence_type": "greenhouse_jobs",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
                "departments": [d.get("name") for d in raw.get("departments", [])],
                "offices": [o.get("name") for o in raw.get("offices", [])],
            },
        }

    def _norm_candidate(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "greenhouse",
            "control": "hr_security",
            "evidence_type": "greenhouse_candidates",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "company": raw.get("company"),
                "title": raw.get("title"),
            },
        }

    def _norm_department(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "integration": "greenhouse",
            "control": "hr_security",
            "evidence_type": "greenhouse_departments",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "parent_id": raw.get("parent_id"),
            },
        }

    def _norm_office(self, raw: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        location = raw.get("location")
        location_name = (
            location.get("name") if isinstance(location, dict) else location
        )
        return {
            "integration": "greenhouse",
            "control": "hr_security",
            "evidence_type": "greenhouse_offices",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "location": location_name,
            },
        }
