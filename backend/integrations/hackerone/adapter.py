"""
HackerOne integration via HackerOne API v1.

Credentials:
  api_username — HackerOne API username
  api_token    — HackerOne API token
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_BASE = "https://api.hackerone.com/v1"


class HackerOneIntegration(IntegrationAdapter):

    def __init__(self):
        self._username: str | None = None
        self._token: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._username, self._token)

    async def connect(self, credentials: dict) -> bool:
        username = credentials.get("api_username", "").strip()
        token = credentials.get("api_token", "").strip()

        if not username or not token:
            raise IntegrationAuthError("api_username and api_token are required")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/me",
                auth=(username, token),
                headers={"Accept": "application/json"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid HackerOne credentials")
            if r.status_code == 403:
                raise IntegrationAuthError("HackerOne credentials lack required permissions")
            r.raise_for_status()

        self._username = username
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            programs = await self._collect_programs(client)
            reports = await self._collect_reports(client, programs)
        return programs + reports

    async def _collect_programs(self, client: httpx.AsyncClient) -> list[dict]:
        programs = []
        try:
            url = f"{_BASE}/me/programs"
            while url:
                r = await client.get(
                    url,
                    auth=self._auth(),
                    headers={"Accept": "application/json"},
                )
                r.raise_for_status()
                data = r.json()
                for prog in data.get("data", []):
                    attrs = prog.get("attributes", {})
                    programs.append(
                        {
                            "_type": "program",
                            "id": prog.get("id"),
                            "handle": attrs.get("handle"),
                            "name": attrs.get("name"),
                            "started_accepting_at": attrs.get("started_accepting_at"),
                            "resolved_report_count": attrs.get("resolved_report_count"),
                            "signal": attrs.get("signal"),
                            "coverage": attrs.get("coverage"),
                        }
                    )
                # Pagination via links.next
                links = data.get("links", {})
                url = links.get("next")
        except Exception as exc:
            raise RuntimeError(f"Failed to collect HackerOne programs: {exc}") from exc
        return programs

    async def _collect_reports(self, client: httpx.AsyncClient, programs: list[dict]) -> list[dict]:
        reports = []
        handles = [p.get("handle") for p in programs if p.get("handle")]
        if not handles:
            return reports

        for handle in handles:
            try:
                url = f"{_BASE}/reports"
                params = {
                    "filter[program][]": handle,
                    "page[size]": "100",
                }
                while url:
                    r = await client.get(
                        url,
                        auth=self._auth(),
                        headers={"Accept": "application/json"},
                        params=params if url == f"{_BASE}/reports" else None,
                    )
                    r.raise_for_status()
                    data = r.json()
                    for rep in data.get("data", []):
                        attrs = rep.get("attributes", {})
                        relationships = rep.get("relationships", {})
                        severity = relationships.get("severity", {}).get("data", {})
                        reports.append(
                            {
                                "_type": "report",
                                "id": rep.get("id"),
                                "title": attrs.get("title"),
                                "state": attrs.get("state"),
                                "severity": severity.get("id") if severity else attrs.get("severity_rating"),
                                "created_at": attrs.get("created_at"),
                                "closed_at": attrs.get("closed_at"),
                                "bounty_amount": attrs.get("bounty_amount"),
                                "program_handle": handle,
                            }
                        )
                    links = data.get("links", {})
                    url = links.get("next")
                    params = None  # Params are embedded in the next URL
            except Exception:
                # Don't abort full collection if one program's reports fail
                continue

        return reports

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "program":
                result.append(self._norm_program(item))
            elif t == "report":
                result.append(self._norm_report(item))
        return result

    def _norm_program(self, raw: dict) -> dict:
        return {
            "integration": "hackerone",
            "control": "vulnerability_management",
            "evidence_type": "hackerone_programs",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("started_accepting_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "handle": raw.get("handle"),
                "name": raw.get("name"),
                "resolved_report_count": raw.get("resolved_report_count"),
                "signal": raw.get("signal"),
                "coverage": raw.get("coverage"),
            },
        }

    def _norm_report(self, raw: dict) -> dict:
        return {
            "integration": "hackerone",
            "control": "vulnerability_management",
            "evidence_type": "hackerone_reports",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "state": raw.get("state"),
                "severity": raw.get("severity"),
                "closed_at": raw.get("closed_at"),
                "bounty_amount": raw.get("bounty_amount"),
                "program_handle": raw.get("program_handle"),
            },
        }
