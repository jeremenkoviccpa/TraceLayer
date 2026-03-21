from __future__ import annotations

"""
Aqua Security integration via Aqua REST API.

Credentials:
  server_url — Base URL of the Aqua instance (e.g. "https://mycompany.cloud.aquasec.com")
  username   — Aqua username
  password   — Aqua password
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class AquasecIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._server_url: str | None = None
        self._token: str | None = None

    def _base(self) -> str:
        return self._server_url  # type: ignore[return-value]

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        server_url = credentials.get("server_url", "").strip().rstrip("/")
        username = credentials.get("username", "").strip()
        password = credentials.get("password", "").strip()

        if not server_url or not username or not password:
            raise IntegrationAuthError(
                "server_url, username, and password are required."
            )

        async with httpx.AsyncClient(timeout=15) as client:
            # Login to obtain token
            login_r = await client.post(
                f"{server_url}/api/v1/login",
                json={"id": username, "password": password},
            )
            if login_r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Aqua Security credentials.")
            if login_r.status_code != 200:
                raise RuntimeError(
                    f"Aqua Security login failed HTTP {login_r.status_code}"
                )
            token = login_r.json().get("token", "")
            if not token:
                raise IntegrationAuthError(
                    "Aqua Security login did not return a token."
                )

            # Verify token with /api/v1/users/me
            me_r = await client.get(
                f"{server_url}/api/v1/users/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if me_r.status_code in (401, 403):
                raise IntegrationAuthError("Invalid Aqua Security credentials.")
            if me_r.status_code != 200:
                raise RuntimeError(
                    f"Aqua Security users/me failed HTTP {me_r.status_code}"
                )

        self._server_url = server_url
        self._token = token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_images,
                self._collect_vulnerabilities,
                self._collect_policies,
                self._collect_audit_events,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Aqua Security collection error in %s: %s",
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

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/v1/users",
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Aqua users HTTP {r.status_code}")
        body = r.json()
        users = body if isinstance(body, list) else body.get("users", [])
        return [{"_type": "user", **u} for u in users]

    async def _collect_images(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/v1/images",
            headers=self._auth_headers(),
            params={"pagesize": 100, "page": 1},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Aqua images HTTP {r.status_code}")
        body = r.json()
        images = (
            body.get("results", []) if isinstance(body, dict) else body
        ) or []
        return [{"_type": "image", **img} for img in images]

    async def _collect_vulnerabilities(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/v1/risks/vulnerabilities",
            headers=self._auth_headers(),
            params={"pagesize": 50, "page": 1},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Aqua vulnerabilities HTTP {r.status_code}")
        body = r.json()
        vulns = body.get("result", []) if isinstance(body, dict) else []
        return [{"_type": "vulnerability", **v} for v in vulns]

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/v1/assurance_policy",
            headers=self._auth_headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Aqua policies HTTP {r.status_code}")
        body = r.json()
        policies = (
            body if isinstance(body, list) else body.get("result", [])
        ) or []
        return [{"_type": "policy", **p} for p in policies]

    async def _collect_audit_events(
        self, client: httpx.AsyncClient
    ) -> list[dict]:
        r = await client.get(
            f"{self._base()}/api/v1/audit",
            headers=self._auth_headers(),
            params={
                "pagesize": 100,
                "page": 1,
                "order_by": "time",
                "direction": "desc",
            },
        )
        if r.status_code in (404, 403):
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Aqua audit events HTTP {r.status_code}")
        body = r.json()
        events = body.get("data", []) if isinstance(body, dict) else []
        return [{"_type": "audit_event", **e} for e in events]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item, now))
            elif t == "image":
                result.append(self._norm_image(item, now))
            elif t == "vulnerability":
                result.append(self._norm_vulnerability(item, now))
            elif t == "policy":
                result.append(self._norm_policy(item, now))
            elif t == "audit_event":
                result.append(self._norm_audit_event(item, now))
        return result

    def _norm_user(self, raw: dict, now: str) -> dict:
        return {
            "integration": "aquasec",
            "control": "access_control",
            "evidence_type": "aquasec_users",
            "source_id": str(raw.get("id", "") or raw.get("name", "")),
            "timestamp": raw.get("created") or now,
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "role": raw.get("role"),
                "is_super_user": raw.get("is_super_user"),
            },
        }

    def _norm_image(self, raw: dict, now: str) -> dict:
        registry = raw.get("registry", "")
        name = raw.get("name", "")
        return {
            "integration": "aquasec",
            "control": "vulnerability_management",
            "evidence_type": "aquasec_images",
            "source_id": f"{registry}/{name}",
            "timestamp": raw.get("created") or now,
            "data": {
                "name": name,
                "registry": registry,
                "tag": raw.get("tag"),
                "scan_status": raw.get("scan_status"),
                "critical": raw.get("critical"),
                "high": raw.get("high"),
                "medium": raw.get("medium"),
                "disallowed": raw.get("disallowed"),
            },
        }

    def _norm_vulnerability(self, raw: dict, now: str) -> dict:
        return {
            "integration": "aquasec",
            "control": "vulnerability_management",
            "evidence_type": "aquasec_vulnerabilities",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("publish_date") or now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "severity": raw.get("aqua_severity") or raw.get("nvd_severity"),
                "resource_type": raw.get("resource_type"),
                "fix_version": raw.get("fix_version"),
            },
        }

    def _norm_policy(self, raw: dict, now: str) -> dict:
        return {
            "integration": "aquasec",
            "control": "vulnerability_management",
            "evidence_type": "aquasec_policies",
            "source_id": str(raw.get("name", "")),
            "timestamp": raw.get("created") or now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "assurance_type": raw.get("assurance_type"),
                "enabled": raw.get("enabled"),
                "blocking": raw.get("blocking"),
            },
        }

    def _norm_audit_event(self, raw: dict, now: str) -> dict:
        return {
            "integration": "aquasec",
            "control": "logging_monitoring",
            "evidence_type": "aquasec_audit_events",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("time") or now,
            "data": {
                "action": raw.get("action"),
                "category": raw.get("category"),
                "user": raw.get("user"),
                "result": raw.get("result"),
                "data": raw.get("data"),
            },
        }
