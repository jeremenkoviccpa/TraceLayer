"""
Checkr integration via Checkr REST API v1.

Credentials:
  api_key  — Checkr API key (used as Basic auth username; password is empty)
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.checkr.com/v1"


class CheckrIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _auth(self) -> tuple[str, str]:
        # Checkr uses HTTP Basic auth: api_key as username, empty password.
        return (self._api_key, "")

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/accounts",
                auth=(api_key, ""),
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Checkr API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Checkr connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_candidates,
                self._collect_reports,
                self._collect_packages,
                self._collect_account,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Checkr collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_candidates(self, client: httpx.AsyncClient) -> list[dict]:
        candidates: list[dict] = []
        url: str | None = f"{_BASE}/candidates"
        params = {"per_page": 100}

        while url:
            r = await client.get(url, auth=self._auth(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"Checkr candidates HTTP {r.status_code}")
            body = r.json()
            page_data = body.get("data", [])
            candidates.extend(page_data)
            url = body.get("next_href")
            params = {}  # next_href already contains query params

        return [{"_type": "candidate", **c} for c in candidates]

    async def _collect_reports(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/reports",
            auth=self._auth(),
            params={"per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Checkr reports HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "report", **rpt} for rpt in body.get("data", [])]

    async def _collect_packages(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/packages", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Checkr packages HTTP {r.status_code}")
        body = r.json()
        packages = body.get("data") if isinstance(body, dict) else body
        if packages is None:
            packages = []
        return [{"_type": "package", **p} for p in packages]

    async def _collect_account(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(f"{_BASE}/accounts", auth=self._auth())
        if r.status_code != 200:
            raise RuntimeError(f"Checkr account HTTP {r.status_code}")
        body = r.json()
        if isinstance(body, dict) and "data" in body:
            account = body["data"][0] if body["data"] else {}
        else:
            account = body
        return [{"_type": "account", **account}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "candidate":
                result.append(self._norm_candidate(item, now))
            elif t == "report":
                result.append(self._norm_report(item, now))
            elif t == "package":
                result.append(self._norm_package(item, now))
            elif t == "account":
                result.append(self._norm_account(item, now))
        return result

    def _norm_candidate(self, raw: dict, now: str) -> dict:
        return {
            "integration": "checkr",
            "control": "hr_security",
            "evidence_type": "checkr_candidates",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "first_name": raw.get("first_name"),
                "last_name": raw.get("last_name"),
                "email": raw.get("email"),
                "dob": raw.get("dob"),
            },
        }

    def _norm_report(self, raw: dict, now: str) -> dict:
        return {
            "integration": "checkr",
            "control": "hr_security",
            "evidence_type": "checkr_reports",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "status": raw.get("status"),
                "result": raw.get("result"),
                "package": raw.get("package"),
                "candidate_id": raw.get("candidate_id"),
                "completed_at": raw.get("completed_at"),
            },
        }

    def _norm_package(self, raw: dict, now: str) -> dict:
        return {
            "integration": "checkr",
            "control": "hr_security",
            "evidence_type": "checkr_packages",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "slug": raw.get("slug"),
                "price": raw.get("price"),
            },
        }

    def _norm_account(self, raw: dict, now: str) -> dict:
        return {
            "integration": "checkr",
            "control": "hr_security",
            "evidence_type": "checkr_account",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "uri": raw.get("uri"),
                "authorized": raw.get("authorized"),
                "credentialed": raw.get("credentialed"),
            },
        }
