from __future__ import annotations

"""
Deel integration via Deel REST API v2.

Credentials:
  api_token — Deel API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.letsdeel.com/rest/v2"


class DeelIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._api_token: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_token}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_token = credentials.get("api_token", "").strip()

        if not api_token:
            raise IntegrationAuthError("api_token is required.")

        headers = {"Authorization": f"Bearer {api_token}"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{_BASE_URL}/people", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Deel API token.")
            if r.status_code == 403:
                # Fall back to contracts endpoint
                r2 = await client.get(
                    f"{_BASE_URL}/contracts",
                    headers=headers,
                    params={"limit": 1},
                )
                if r2.status_code == 401:
                    raise IntegrationAuthError("Invalid Deel API token.")
                if r2.status_code not in (200, 403):
                    raise RuntimeError(f"Deel connect failed HTTP {r2.status_code}")
            elif r.status_code != 200:
                raise RuntimeError(f"Deel connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_contracts,
                self._collect_people,
                self._collect_organizations,
                self._collect_invoices,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Deel collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_contracts(self, client: httpx.AsyncClient) -> list[dict]:
        contracts: list[dict] = []
        limit = 100
        offset = 0

        while True:
            r = await client.get(
                f"{_BASE_URL}/contracts",
                headers=self._headers(),
                params={"limit": limit, "offset": offset},
            )
            if r.status_code != 200:
                raise RuntimeError(f"Deel contracts HTTP {r.status_code}")
            body = r.json()
            data = body.get("data", {})
            if isinstance(data, dict):
                page = data.get("list", []) or []
            else:
                page = data or []
            contracts.extend([{"_type": "contract", **c} for c in page])
            if len(page) < limit:
                break
            offset += limit

        return contracts

    async def _collect_people(self, client: httpx.AsyncClient) -> list[dict]:
        people: list[dict] = []
        limit = 100
        offset = 0

        while True:
            r = await client.get(
                f"{_BASE_URL}/people",
                headers=self._headers(),
                params={"limit": limit, "offset": offset},
            )
            if r.status_code != 200:
                raise RuntimeError(f"Deel people HTTP {r.status_code}")
            body = r.json()
            data = body.get("data", {})
            if isinstance(data, dict):
                page = data.get("list", []) or []
            else:
                page = data or []
            people.extend([{"_type": "person", **p} for p in page])
            if len(page) < limit:
                break
            offset += limit

        return people

    async def _collect_organizations(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/organizations",
            headers=self._headers(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Deel organizations HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", []) or []
        return [{"_type": "organization", **o} for o in data]

    async def _collect_invoices(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/invoices",
            headers=self._headers(),
            params={"limit": 50},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Deel invoices HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", {})
        if isinstance(data, dict):
            invoices = data.get("list", []) or []
        else:
            invoices = []
        return [{"_type": "invoice", **i} for i in invoices]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "contract":
                result.append(self._norm_contract(item))
            elif t == "person":
                result.append(self._norm_person(item))
            elif t == "organization":
                result.append(self._norm_organization(item))
            elif t == "invoice":
                result.append(self._norm_invoice(item))
        return result

    def _norm_contract(self, raw: dict) -> dict:
        now = self._now()
        return {
            "integration": "deel",
            "control": "hr_security",
            "evidence_type": "deel_contracts",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "title": raw.get("job_title") or raw.get("title"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "country": raw.get("country"),
                "currency": raw.get("currency"),
            },
        }

    def _norm_person(self, raw: dict) -> dict:
        now = self._now()
        return {
            "integration": "deel",
            "control": "hr_security",
            "evidence_type": "deel_people",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "full_name": raw.get("full_name"),
                "email": raw.get("email"),
                "type": raw.get("type"),
                "status": raw.get("status"),
                "country": raw.get("country"),
            },
        }

    def _norm_organization(self, raw: dict) -> dict:
        return {
            "integration": "deel",
            "control": "hr_security",
            "evidence_type": "deel_organizations",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "country": raw.get("country"),
            },
        }

    def _norm_invoice(self, raw: dict) -> dict:
        now = self._now()
        return {
            "integration": "deel",
            "control": "hr_security",
            "evidence_type": "deel_invoices",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "status": raw.get("status"),
                "amount": raw.get("amount"),
                "currency": raw.get("currency"),
                "due_date": raw.get("due_date"),
            },
        }
