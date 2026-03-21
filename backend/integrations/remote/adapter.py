from __future__ import annotations

"""
Remote.com integration via Remote Gateway API v1.

Credentials:
  api_token — Remote.com API token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE_URL = "https://gateway.remote.com"


class RemoteIntegration(IntegrationAdapter):

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
            r = await client.get(
                f"{_BASE_URL}/v1/employments",
                headers=headers,
                params={"page": 1, "page_size": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Remote.com API token.")
            if r.status_code != 200:
                raise RuntimeError(f"Remote.com connect failed HTTP {r.status_code}")

        self._api_token = api_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_employments,
                self._collect_countries,
                self._collect_time_offs,
                self._collect_expenses,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Remote.com collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_employments(self, client: httpx.AsyncClient) -> list[dict]:
        employments: list[dict] = []
        page = 1
        page_size = 100

        while True:
            r = await client.get(
                f"{_BASE_URL}/v1/employments",
                headers=self._headers(),
                params={"page": page, "page_size": page_size},
            )
            if r.status_code != 200:
                raise RuntimeError(f"Remote.com employments HTTP {r.status_code}")
            body = r.json()
            data = body.get("data", {})
            if isinstance(data, dict):
                items = data.get("employments", []) or []
            else:
                items = data or []
            employments.extend([{"_type": "employment", **e} for e in items])
            if len(items) < page_size:
                break
            page += 1

        return employments

    async def _collect_countries(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/v1/countries",
            headers=self._headers(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"Remote.com countries HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", {})
        if isinstance(data, dict):
            countries = data.get("countries", []) or []
        else:
            countries = []
        return [{"_type": "country", **c} for c in countries]

    async def _collect_time_offs(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/v1/time-offs",
            headers=self._headers(),
            params={"page": 1, "page_size": 100},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Remote.com time-offs HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", {})
        if isinstance(data, dict):
            time_offs = data.get("time_offs", []) or []
        else:
            time_offs = []
        return [{"_type": "time_off", **t} for t in time_offs]

    async def _collect_expenses(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/v1/expenses",
            headers=self._headers(),
            params={"page": 1, "page_size": 100},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Remote.com expenses HTTP {r.status_code}")
        body = r.json()
        data = body.get("data", {})
        if isinstance(data, dict):
            expenses = data.get("expenses", []) or []
        else:
            expenses = []
        return [{"_type": "expense", **e} for e in expenses]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "employment":
                result.append(self._norm_employment(item))
            elif t == "country":
                result.append(self._norm_country(item))
            elif t == "time_off":
                result.append(self._norm_time_off(item))
            elif t == "expense":
                result.append(self._norm_expense(item))
        return result

    def _norm_employment(self, raw: dict) -> dict:
        now = self._now()
        country = raw.get("country")
        if isinstance(country, dict):
            country_code = country.get("code")
        else:
            country_code = raw.get("country_code") or country
        return {
            "integration": "remote",
            "control": "hr_security",
            "evidence_type": "remote_employments",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("provisional_start_date") or now,
            "data": {
                "full_name": raw.get("full_name") or raw.get("name"),
                "status": raw.get("status"),
                "country_code": raw.get("country_code") or country_code,
                "job_title": raw.get("job_title"),
                "type": raw.get("type"),
            },
        }

    def _norm_country(self, raw: dict) -> dict:
        return {
            "integration": "remote",
            "control": "hr_security",
            "evidence_type": "remote_countries",
            "source_id": raw.get("code", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "code": raw.get("code"),
                "supported_currencies": raw.get("supported_currencies", []),
            },
        }

    def _norm_time_off(self, raw: dict) -> dict:
        now = self._now()
        return {
            "integration": "remote",
            "control": "hr_security",
            "evidence_type": "remote_time_offs",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("start_date") or now,
            "data": {
                "status": raw.get("status"),
                "days_count": raw.get("days_count"),
                "type": raw.get("type"),
            },
        }

    def _norm_expense(self, raw: dict) -> dict:
        now = self._now()
        return {
            "integration": "remote",
            "control": "hr_security",
            "evidence_type": "remote_expenses",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("expense_date") or now,
            "data": {
                "status": raw.get("status"),
                "amount": raw.get("amount"),
                "currency": raw.get("currency"),
                "category": raw.get("category"),
            },
        }
