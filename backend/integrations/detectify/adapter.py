"""
Detectify integration via Detectify REST API v2.

Credentials:
  api_token  — Detectify API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.detectify.com/rest/v2"


class DetectifyIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {"X-Detectify-Token": self._api_token}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()
        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/profiles/",
                headers={"X-Detectify-Token": api_token},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Detectify API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Detectify connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_scan_profiles,
                self._collect_findings,
                self._collect_domains,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Detectify collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_scan_profiles(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/profiles/", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Detectify profiles HTTP {r.status_code}")
        body = r.json()
        profiles = body if isinstance(body, list) else body.get("profiles", [])
        return [{"_type": "scan_profile", **p} for p in profiles]

    async def _collect_findings(self, client: httpx.AsyncClient) -> list[dict]:
        # Attempt the flat findings endpoint first; gracefully skip on 404.
        r = await client.get(
            f"{_BASE}/findings/",
            headers=self._headers(),
            params={"pageSize": 100},
        )
        if r.status_code == 404:
            logger.info("Detectify /findings/ endpoint not available — skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Detectify findings HTTP {r.status_code}")
        body = r.json()
        findings = body if isinstance(body, list) else body.get("findings", [])
        return [{"_type": "finding", **f} for f in findings]

    async def _collect_domains(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/domains/", headers=self._headers())
        if r.status_code != 200:
            raise RuntimeError(f"Detectify domains HTTP {r.status_code}")
        body = r.json()
        domains = body if isinstance(body, list) else body.get("domains", [])
        return [{"_type": "domain", **d} for d in domains]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "scan_profile":
                result.append(self._norm_scan_profile(item, now))
            elif t == "finding":
                result.append(self._norm_finding(item, now))
            elif t == "domain":
                result.append(self._norm_domain(item, now))
        return result

    def _norm_scan_profile(self, raw: dict, now: str) -> dict:
        score = raw.get("score")
        return {
            "integration": "detectify",
            "control": "vulnerability_management",
            "evidence_type": "detectify_scan_profiles",
            "source_id": str(raw.get("token", "")),
            "timestamp": raw.get("created") or now,
            "data": {
                "name": raw.get("name"),
                "endpoint": raw.get("endpoint"),
                "status": raw.get("status"),
                "scan_schedule": raw.get("scan_schedule"),
            },
        }

    def _norm_finding(self, raw: dict, now: str) -> dict:
        score = raw.get("score")
        severity = (
            score.get("cvss3") if isinstance(score, dict) else score
        )
        definition = raw.get("definition")
        definition_title = (
            definition.get("title") if isinstance(definition, dict) else None
        )
        return {
            "integration": "detectify",
            "control": "vulnerability_management",
            "evidence_type": "detectify_findings",
            "source_id": str(raw.get("uuid", "")),
            "timestamp": raw.get("found_at") or now,
            "data": {
                "title": raw.get("title"),
                "severity": severity,
                "url": raw.get("url"),
                "definition": definition_title,
            },
        }

    def _norm_domain(self, raw: dict, now: str) -> dict:
        return {
            "integration": "detectify",
            "control": "vulnerability_management",
            "evidence_type": "detectify_domains",
            "source_id": str(raw.get("name", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
            },
        }
