from __future__ import annotations

"""
Veracode integration via Veracode REST API.

Credentials:
  api_id   — Veracode API ID
  api_key  — Veracode API Key (hex string)
"""

import hashlib
import hmac
import logging
import time
import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_VERACODE_API_HOST = "analysiscenter.veracode.com"
_BASE = "https://api.veracode.com"


class VeracodeIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_id: str | None = None
        self._api_key: str | None = None

    # ── HMAC signing ───────────────────────────────────────────────────────────

    def _generate_header(self, url: str, method: str) -> str:
        nonce = uuid.uuid4().hex
        ts = str(int(time.time() * 1000))
        parsed = urlparse(url)
        path = parsed.path + ("?" + parsed.query if parsed.query else "")
        data = (
            f"id={self._api_id}&host={_VERACODE_API_HOST}"
            f"&url={path}&method={method.upper()}"
        )
        nonce_bytes = bytes.fromhex(nonce)
        ts_bytes = ts.encode()
        key_nonce = hmac.new(
            bytes.fromhex(self._api_key), nonce_bytes, hashlib.sha256
        ).digest()
        key_date = hmac.new(key_nonce, ts_bytes, hashlib.sha256).digest()
        signing_key = hmac.new(
            key_date, b"vcode_request_version_1", hashlib.sha256
        ).digest()
        signature = hmac.new(
            signing_key, data.encode(), hashlib.sha256
        ).hexdigest()
        return (
            f"VERACODE-HMAC-SHA-256 id={self._api_id},"
            f"ts={ts},nonce={nonce},sig={signature}"
        )

    def _auth_headers(self, url: str, method: str = "GET") -> dict:
        return {"Authorization": self._generate_header(url, method)}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_id = credentials.get("api_id", "").strip()
        api_key = credentials.get("api_key", "").strip()

        if not api_id or not api_key:
            raise IntegrationAuthError("api_id and api_key are required.")

        self._api_id = api_id
        self._api_key = api_key

        url = f"{_BASE}/appsec/v1/applications?size=1"
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, headers=self._auth_headers(url))
            if r.status_code == 401:
                self._api_id = None
                self._api_key = None
                raise IntegrationAuthError("Invalid Veracode API credentials.")
            if r.status_code != 200:
                self._api_id = None
                self._api_key = None
                raise RuntimeError(f"Veracode connect failed HTTP {r.status_code}")

        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_applications,
                self._collect_findings,
                self._collect_policy_compliance,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Veracode collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_applications(self, client: httpx.AsyncClient) -> list[dict]:
        items: list[dict] = []
        url: str | None = f"{_BASE}/appsec/v1/applications?size=100"

        while url:
            r = await client.get(url, headers=self._auth_headers(url))
            if r.status_code != 200:
                raise RuntimeError(f"Veracode applications HTTP {r.status_code}")
            body = r.json()
            apps = body.get("_embedded", {}).get("applications", []) or body.get(
                "applications", []
            )
            items.extend({"_type": "application", **a} for a in apps)
            url = (
                body.get("_links", {}).get("next", {}).get("href")
                if body.get("_links", {}).get("next")
                else None
            )

        return items

    async def _collect_findings(self, client: httpx.AsyncClient) -> list[dict]:
        url = f"{_BASE}/appsec/v2/findings?size=100&violates_policy=true"
        r = await client.get(url, headers=self._auth_headers(url))
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Veracode findings HTTP {r.status_code}")
        body = r.json()
        findings = body.get("_embedded", {}).get("findings", []) or []
        return [{"_type": "finding", **f} for f in findings]

    async def _collect_policy_compliance(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        url = f"{_BASE}/appsec/v1/policies?size=100"
        r = await client.get(url, headers=self._auth_headers(url))
        if r.status_code != 200:
            raise RuntimeError(f"Veracode policies HTTP {r.status_code}")
        body = r.json()
        policies = body.get("_embedded", {}).get("policies", []) or []
        return [{"_type": "policy", **p} for p in policies]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "application":
                result.append(self._norm_application(item, now))
            elif t == "finding":
                result.append(self._norm_finding(item, now))
            elif t == "policy":
                result.append(self._norm_policy(item, now))
        return result

    def _norm_application(self, raw: dict, now: str) -> dict:
        profile = raw.get("profile") if isinstance(raw.get("profile"), dict) else {}
        policies = profile.get("policies", [])
        policy_compliance = (
            policies[0].get("policy_compliance_status") if policies else None
        )
        return {
            "integration": "veracode",
            "control": "vulnerability_management",
            "evidence_type": "veracode_applications",
            "source_id": str(raw.get("guid", "")),
            "timestamp": raw.get("created") or now,
            "data": {
                "name": profile.get("name", "") if profile else raw.get("name", ""),
                "business_criticality": profile.get("business_criticality")
                if profile
                else None,
                "policy_compliance_status": policy_compliance,
            },
        }

    def _norm_finding(self, raw: dict, now: str) -> dict:
        finding_details = raw.get("finding_details") or {}
        cwe = finding_details.get("cwe") if isinstance(finding_details, dict) else {}
        finding_status = raw.get("finding_status") or {}
        return {
            "integration": "veracode",
            "control": "vulnerability_management",
            "evidence_type": "veracode_findings",
            "source_id": str(raw.get("issue_id", "")),
            "timestamp": raw.get("found_date") or now,
            "data": {
                "scan_type": raw.get("scan_type"),
                "severity": raw.get("severity"),
                "cwe_id": cwe.get("id") if isinstance(cwe, dict) else None,
                "status": finding_status.get("status")
                if isinstance(finding_status, dict)
                else None,
            },
        }

    def _norm_policy(self, raw: dict, now: str) -> dict:
        return {
            "integration": "veracode",
            "control": "vulnerability_management",
            "evidence_type": "veracode_policies",
            "source_id": str(raw.get("guid", "")),
            "timestamp": raw.get("created") or now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "type": raw.get("type"),
                "vendor_policy": raw.get("vendor_policy"),
            },
        }
