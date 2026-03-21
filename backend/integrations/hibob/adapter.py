from __future__ import annotations

"""
HiBob integration via HiBob REST API v1.

Credentials:
  service_user_id    — HiBob service user ID
  service_user_token — HiBob service user token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.hibob.com/v1"


class HiBobIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._service_user_id: str | None = None
        self._service_user_token: str | None = None

    def _auth(self) -> tuple[str, str]:
        return (self._service_user_id, self._service_user_token)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        service_user_id = credentials.get("service_user_id", "").strip()
        service_user_token = credentials.get("service_user_token", "").strip()

        if not service_user_id or not service_user_token:
            raise IntegrationAuthError("service_user_id and service_user_token are required.")

        auth = (service_user_id, service_user_token)

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE_URL}/people",
                auth=auth,
                params={"humanReadable": "true", "includeHumanReadable": "true", "limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid HiBob credentials.")
            if r.status_code != 200:
                raise RuntimeError(f"HiBob connect failed HTTP {r.status_code}")

        self._service_user_id = service_user_id
        self._service_user_token = service_user_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_employees,
                self._collect_departments,
                self._collect_positions,
                self._collect_company_info,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("HiBob collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_employees(self, client: httpx.AsyncClient) -> list[dict]:
        employees: list[dict] = []
        url = f"{_BASE_URL}/people"
        params: dict = {"humanReadable": "true", "limit": 100}

        while url:
            r = await client.get(url, auth=self._auth(), params=params)
            if r.status_code != 200:
                raise RuntimeError(f"HiBob employees HTTP {r.status_code}")
            body = r.json()
            page = body.get("employees", []) or body.get("data", []) or []
            employees.extend([{"_type": "employee", **e} for e in page])
            next_link = body.get("nextLink")
            url = next_link if next_link else None
            params = {}  # next_link already contains query params

        return employees

    async def _collect_departments(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company/named-lists/department",
            auth=self._auth(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"HiBob departments HTTP {r.status_code}")
        body = r.json()
        values = body.get("values", []) or []
        return [{"_type": "department", **v} for v in values]

    async def _collect_positions(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company/named-lists/site",
            auth=self._auth(),
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"HiBob sites HTTP {r.status_code}")
        body = r.json()
        values = body.get("values", []) or []
        return [{"_type": "site", **v} for v in values]

    async def _collect_company_info(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE_URL}/company/details",
            auth=self._auth(),
        )
        if r.status_code != 200:
            raise RuntimeError(f"HiBob company details HTTP {r.status_code}")
        body = r.json() or {}
        return [{"_type": "company", **body}]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "employee":
                result.append(self._norm_employee(item))
            elif t == "department":
                result.append(self._norm_department(item))
            elif t == "site":
                result.append(self._norm_site(item))
            elif t == "company":
                result.append(self._norm_company(item))
        return result

    def _norm_employee(self, raw: dict) -> dict:
        now = self._now()
        work = raw.get("work")
        work_dict = work if isinstance(work, dict) else {}
        return {
            "integration": "hibob",
            "control": "hr_security",
            "evidence_type": "hibob_employees",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("creationDateTime") or now,
            "data": {
                "firstName": raw.get("firstName"),
                "lastName": raw.get("lastName"),
                "email": raw.get("email"),
                "department": work_dict.get("department"),
                "title": work_dict.get("title"),
                "startDate": work_dict.get("startDate"),
                "isActive": raw.get("isManager", False) is not None,
            },
        }

    def _norm_department(self, raw: dict) -> dict:
        return {
            "integration": "hibob",
            "control": "hr_security",
            "evidence_type": "hibob_departments",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name") or raw.get("value"),
                "active": raw.get("active"),
            },
        }

    def _norm_site(self, raw: dict) -> dict:
        return {
            "integration": "hibob",
            "control": "hr_security",
            "evidence_type": "hibob_sites",
            "source_id": raw.get("id", ""),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name") or raw.get("value"),
            },
        }

    def _norm_company(self, raw: dict) -> dict:
        return {
            "integration": "hibob",
            "control": "hr_security",
            "evidence_type": "hibob_company",
            "source_id": raw.get("id", "company"),
            "timestamp": self._now(),
            "data": {
                "name": raw.get("name"),
                "country": raw.get("country"),
                "industry": raw.get("industry"),
            },
        }
