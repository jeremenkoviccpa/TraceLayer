from __future__ import annotations

"""
StackHawk integration via StackHawk REST API v1.

Credentials:
  api_key — StackHawk API key
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.stackhawk.com/api/v1"


class StackHawkIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {"X-ApiKey": self._api_key}  # type: ignore[return-value]

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        self._api_key = api_key

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/user",
                headers=self._headers(),
            )
            if r.status_code == 401:
                self._api_key = None
                raise IntegrationAuthError("Invalid StackHawk API key.")
            if r.status_code != 200:
                self._api_key = None
                raise RuntimeError(f"StackHawk connect failed HTTP {r.status_code}")

        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_applications,
                self._collect_scans,
                self._collect_findings,
                self._collect_organizations,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "StackHawk collection error in %s: %s",
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

    async def _collect_applications(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        r = await client.get(
            f"{_BASE}/app",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"StackHawk applications HTTP {r.status_code}")
        body = r.json()
        apps = (
            body.get("data", body) if isinstance(body, dict) else body
        ) or []
        if isinstance(apps, dict):
            apps = [apps]
        return [{"_type": "application", **a} for a in apps]

    async def _collect_scans(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/scan",
            headers=self._headers(),
            params={"pageSize": 50, "pageToken": 0},
        )
        if r.status_code != 200:
            raise RuntimeError(f"StackHawk scans HTTP {r.status_code}")
        body = r.json()
        scans = body.get("data", []) if isinstance(body, dict) else []
        return [{"_type": "scan", **s} for s in scans]

    async def _collect_findings(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/finding",
            headers=self._headers(),
            params={"pageSize": 100},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"StackHawk findings HTTP {r.status_code}")
        body = r.json()
        findings = body.get("data", []) if isinstance(body, dict) else []
        return [{"_type": "finding", **f} for f in findings]

    async def _collect_organizations(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        r = await client.get(
            f"{_BASE}/org",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"StackHawk organizations HTTP {r.status_code}")
        body = r.json()
        orgs = (
            body.get("data", body) if isinstance(body, dict) else body
        ) or []
        if isinstance(orgs, dict):
            orgs = [orgs]
        return [{"_type": "organization", **o} for o in orgs]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "application":
                result.append(self._norm_application(item, now))
            elif t == "scan":
                result.append(self._norm_scan(item, now))
            elif t == "finding":
                result.append(self._norm_finding(item, now))
            elif t == "organization":
                result.append(self._norm_organization(item, now))
        return result

    def _norm_application(self, raw: dict, now: str) -> dict:
        return {
            "integration": "stackhawk",
            "control": "vulnerability_management",
            "evidence_type": "stackhawk_applications",
            "source_id": str(
                raw.get("applicationId", "") or raw.get("id", "")
            ),
            "timestamp": raw.get("createdAt") or now,
            "data": {
                "name": raw.get("applicationName") or raw.get("name"),
                "environment": raw.get("env") or raw.get("environment"),
                "host": raw.get("host"),
            },
        }

    def _norm_scan(self, raw: dict, now: str) -> dict:
        findings = raw.get("findings")
        total = (
            findings.get("total")
            if isinstance(findings, dict)
            else findings
        )
        critical = (
            findings.get("critical") if isinstance(findings, dict) else None
        )
        return {
            "integration": "stackhawk",
            "control": "vulnerability_management",
            "evidence_type": "stackhawk_scans",
            "source_id": str(raw.get("scanId", "") or raw.get("id", "")),
            "timestamp": raw.get("startedAt") or now,
            "data": {
                "status": raw.get("status") or raw.get("scanStatus"),
                "findings": total,
                "criticalFindings": critical,
                "applicationId": raw.get("applicationId"),
            },
        }

    def _norm_finding(self, raw: dict, now: str) -> dict:
        return {
            "integration": "stackhawk",
            "control": "vulnerability_management",
            "evidence_type": "stackhawk_findings",
            "source_id": str(raw.get("findingId", "") or raw.get("id", "")),
            "timestamp": raw.get("lastSeen") or now,
            "data": {
                "name": raw.get("pluginName") or raw.get("name"),
                "severity": raw.get("severity"),
                "status": raw.get("status"),
                "cweId": raw.get("cweId"),
                "pluginId": raw.get("pluginId"),
            },
        }

    def _norm_organization(self, raw: dict, now: str) -> dict:
        return {
            "integration": "stackhawk",
            "control": "access_control",
            "evidence_type": "stackhawk_organizations",
            "source_id": str(raw.get("orgId", "") or raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("orgName") or raw.get("name"),
            },
        }
