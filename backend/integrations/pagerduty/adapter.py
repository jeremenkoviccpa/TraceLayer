"""
PagerDuty integration via PagerDuty REST API.

Credentials:
  api_key — PagerDuty API key (REST API key, not user token)
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

PD_API = "https://api.pagerduty.com"


class PagerDutyIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token token={self._api_key}",
            "Accept": "application/vnd.pagerduty+json;version=2",
            "Content-Type": "application/json",
        }

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()

        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        headers = {
            "Authorization": f"Token token={api_key}",
            "Accept": "application/vnd.pagerduty+json;version=2",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{PD_API}/users",
                headers=headers,
                params={"limit": 1},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid PagerDuty API key.")
            if r.status_code == 403:
                raise IntegrationAuthError("PagerDuty API key lacks required permissions.")
            r.raise_for_status()

        self._api_key = api_key
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            results: list[dict] = []

            try:
                services = await self._collect_services(client)
                results.extend(services)
            except Exception as exc:
                results.append({"_type": "error", "_source": "services", "_error": str(exc)})

            try:
                incidents = await self._collect_incidents(client)
                results.extend(incidents)
            except Exception as exc:
                results.append({"_type": "error", "_source": "incidents", "_error": str(exc)})

            try:
                users = await self._collect_users(client)
                results.extend(users)
            except Exception as exc:
                results.append({"_type": "error", "_source": "users", "_error": str(exc)})

            try:
                schedules = await self._collect_schedules(client)
                results.extend(schedules)
            except Exception as exc:
                results.append({"_type": "error", "_source": "schedules", "_error": str(exc)})

            try:
                escalation_policies = await self._collect_escalation_policies(client)
                results.extend(escalation_policies)
            except Exception as exc:
                results.append({"_type": "error", "_source": "escalation_policies", "_error": str(exc)})

        return results

    async def _paginate(self, client: httpx.AsyncClient, path: str, key: str, extra_params: dict | None = None) -> list[dict]:
        """Generic cursor-less offset pagination for PagerDuty list endpoints."""
        items = []
        limit = 100
        offset = 0
        while True:
            params = {"limit": limit, "offset": offset}
            if extra_params:
                params.update(extra_params)
            r = await client.get(f"{PD_API}{path}", headers=self._headers(), params=params)
            r.raise_for_status()
            body = r.json()
            batch = body.get(key, [])
            items.extend(batch)
            if not body.get("more", False) or not batch:
                break
            offset += limit
        return items

    async def _collect_services(self, client: httpx.AsyncClient) -> list[dict]:
        raw = await self._paginate(client, "/services", "services")
        return [
            {
                "_type": "service",
                "id": s.get("id"),
                "name": s.get("name"),
                "status": s.get("status"),
                "escalation_policy": s.get("escalation_policy"),
                "created_at": s.get("created_at"),
            }
            for s in raw
        ]

    async def _collect_incidents(self, client: httpx.AsyncClient) -> list[dict]:
        raw = await self._paginate(
            client,
            "/incidents",
            "incidents",
            extra_params={
                "statuses[]": ["triggered", "acknowledged"],
                "date_range": "all",
            },
        )
        return [
            {
                "_type": "incident",
                "id": i.get("id"),
                "title": i.get("title"),
                "status": i.get("status"),
                "urgency": i.get("urgency"),
                "created_at": i.get("created_at"),
                "service": i.get("service"),
            }
            for i in raw
        ]

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        raw = await self._paginate(client, "/users", "users")
        return [
            {
                "_type": "user",
                "id": u.get("id"),
                "name": u.get("name"),
                "email": u.get("email"),
                "role": u.get("role"),
                "teams": u.get("teams", []),
            }
            for u in raw
        ]

    async def _collect_schedules(self, client: httpx.AsyncClient) -> list[dict]:
        raw = await self._paginate(client, "/schedules", "schedules")
        return [
            {
                "_type": "schedule",
                "id": s.get("id"),
                "name": s.get("name"),
                "time_zone": s.get("time_zone"),
                "teams": s.get("teams", []),
            }
            for s in raw
        ]

    async def _collect_escalation_policies(self, client: httpx.AsyncClient) -> list[dict]:
        raw = await self._paginate(client, "/escalation_policies", "escalation_policies")
        return [
            {
                "_type": "escalation_policy",
                "id": ep.get("id"),
                "name": ep.get("name"),
                "num_loops": ep.get("num_loops"),
                "escalation_rules": ep.get("escalation_rules", []),
            }
            for ep in raw
        ]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "service":
                result.append(self._norm_service(item))
            elif t == "incident":
                result.append(self._norm_incident(item))
            elif t == "user":
                result.append(self._norm_user(item))
            elif t == "schedule":
                result.append(self._norm_schedule(item))
            elif t == "escalation_policy":
                result.append(self._norm_escalation_policy(item))
            # skip error sentinels silently
        return result

    def _norm_service(self, raw: dict) -> dict:
        return {
            "integration": "pagerduty",
            "control": "logging_monitoring",
            "evidence_type": "pagerduty_services",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "status": raw.get("status"),
                "escalation_policy": raw.get("escalation_policy"),
            },
        }

    def _norm_incident(self, raw: dict) -> dict:
        return {
            "integration": "pagerduty",
            "control": "logging_monitoring",
            "evidence_type": "pagerduty_incidents",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "data": {
                "title": raw.get("title"),
                "status": raw.get("status"),
                "urgency": raw.get("urgency"),
                "service": raw.get("service"),
            },
        }

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "pagerduty",
            "control": "access_control",
            "evidence_type": "pagerduty_users",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "email": raw.get("email"),
                "role": raw.get("role"),
                "teams": [t.get("summary") for t in raw.get("teams", [])],
            },
        }

    def _norm_schedule(self, raw: dict) -> dict:
        return {
            "integration": "pagerduty",
            "control": "logging_monitoring",
            "evidence_type": "pagerduty_schedules",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "time_zone": raw.get("time_zone"),
                "teams": [t.get("summary") for t in raw.get("teams", [])],
            },
        }

    def _norm_escalation_policy(self, raw: dict) -> dict:
        return {
            "integration": "pagerduty",
            "control": "logging_monitoring",
            "evidence_type": "pagerduty_escalation_policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "num_loops": raw.get("num_loops"),
                "escalation_rules": raw.get("escalation_rules", []),
            },
        }
