from __future__ import annotations

"""
Bugcrowd integration via Bugcrowd REST API v4.

Credentials:
  api_token — Bugcrowd API token
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.bugcrowd.com"
_ACCEPT = "application/vnd.bugcrowd.v4+json"


class BugcrowdIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self._api_token}",
            "Accept": _ACCEPT,
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        self._api_token = api_token

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/organizations",
                headers=self._headers(),
            )
            if r.status_code == 401:
                self._api_token = None
                raise IntegrationAuthError("Invalid Bugcrowd API token.")
            if r.status_code != 200:
                self._api_token = None
                raise RuntimeError(f"Bugcrowd connect failed HTTP {r.status_code}")

        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_programs,
                self._collect_submissions,
                self._collect_organizations,
                self._collect_researchers,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Bugcrowd collection error in %s: %s",
                        fetch_fn.__name__,
                        exc,
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_programs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/programs",
            headers=self._headers(),
            params={"page[limit]": 25},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bugcrowd programs HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "program", **p} for p in body.get("data", [])]

    async def _collect_submissions(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/submissions",
            headers=self._headers(),
            params={
                "page[limit]": 50,
                "filter[severity][]": ["critical", "high"],
            },
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bugcrowd submissions HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "submission", **s} for s in body.get("data", [])]

    async def _collect_organizations(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        r = await client.get(
            f"{_BASE}/organizations",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Bugcrowd organizations HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "organization", **o} for o in body.get("data", [])]

    async def _collect_researchers(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/engagements",
            headers=self._headers(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Bugcrowd engagements HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "engagement", **e} for e in body.get("data", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "program":
                result.append(self._norm_program(item, now))
            elif t == "submission":
                result.append(self._norm_submission(item, now))
            elif t == "organization":
                result.append(self._norm_organization(item, now))
            elif t == "engagement":
                result.append(self._norm_engagement(item, now))
        return result

    def _norm_program(self, raw: dict, now: str) -> dict:
        attrs = raw.get("attributes") or {}
        return {
            "integration": "bugcrowd",
            "control": "vulnerability_management",
            "evidence_type": "bugcrowd_programs",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("starts_at") or now,
            "data": {
                "name": attrs.get("name"),
                "program_type": attrs.get("program_type"),
                "status": attrs.get("status"),
                "min_payout": attrs.get("min_payout"),
                "max_payout": attrs.get("max_payout"),
            },
        }

    def _norm_submission(self, raw: dict, now: str) -> dict:
        attrs = raw.get("attributes") or {}
        target = attrs.get("target")
        target_name = (
            target.get("name") if isinstance(target, dict) else None
        )
        return {
            "integration": "bugcrowd",
            "control": "vulnerability_management",
            "evidence_type": "bugcrowd_submissions",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("submitted_at") or now,
            "data": {
                "title": attrs.get("title"),
                "severity": attrs.get("severity"),
                "state": attrs.get("state"),
                "substate": attrs.get("substate"),
                "target_name": target_name,
            },
        }

    def _norm_organization(self, raw: dict, now: str) -> dict:
        attrs = raw.get("attributes") or {}
        return {
            "integration": "bugcrowd",
            "control": "access_control",
            "evidence_type": "bugcrowd_organizations",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": attrs.get("name"),
                "industry": attrs.get("industry"),
            },
        }

    def _norm_engagement(self, raw: dict, now: str) -> dict:
        attrs = raw.get("attributes") or {}
        return {
            "integration": "bugcrowd",
            "control": "vulnerability_management",
            "evidence_type": "bugcrowd_engagements",
            "source_id": str(raw.get("id", "")),
            "timestamp": attrs.get("starts_at") or now,
            "data": {
                "name": attrs.get("name"),
                "status": attrs.get("status"),
            },
        }
