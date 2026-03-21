"""Cisco Webex integration — collects users, spaces, and meeting policies."""
from datetime import datetime, timezone
import re
from urllib.parse import parse_qs, urlparse

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

WEBEX_API = "https://webexapis.com/v1"


class WebExIntegration(IntegrationAdapter):
    def __init__(self):
        self._token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("access_token", "").strip()
        if not token:
            raise IntegrationAuthError("Webex access token is required.")
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"{WEBEX_API}/people/me",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Webex access token.")
            r.raise_for_status()
        self._token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            people = await self._collect_people(client, headers)
            rooms = await self._collect_rooms(client, headers)
        return people + rooms

    async def _collect_people(self, client, headers) -> list[dict]:
        items: list[dict] = []
        params: dict = {"max": 1000}
        while True:
            r = await client.get(f"{WEBEX_API}/people", headers=headers, params=params)
            r.raise_for_status()
            batch = r.json().get("items", [])
            items.extend([{"_type": "webex_person", **p} for p in batch])
            link = r.headers.get("Link", "")
            if 'rel="next"' not in link:
                break
            m = re.search(r'<([^>]+)>;\s*rel="next"', link)
            if not m:
                break
            qs = parse_qs(urlparse(m.group(1)).query)
            cursor = qs.get("after", [None])[0]
            if not cursor:
                break
            params = {"max": 1000, "after": cursor}
        return items

    async def _collect_rooms(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{WEBEX_API}/rooms",
            headers=headers,
            params={"max": 200, "type": "group"},
        )
        r.raise_for_status()
        return [{"_type": "webex_room", **room} for room in r.json().get("items", [])]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "webex_person":
                result.append(self._norm_person(item))
            elif t == "webex_room":
                result.append(self._norm_room(item))
        return result

    def _norm_person(self, raw: dict) -> dict:
        return {
            "integration": "webex",
            "control": "access_control",
            "evidence_type": "webex_users",
            "source_id": raw["id"],
            "timestamp": raw.get("lastModified", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "display_name": raw.get("displayName"),
                "emails": raw.get("emails", []),
                "status": raw.get("status"),
                "type": raw.get("type"),
                "org_id": raw.get("orgId"),
                "roles": raw.get("roles", []),
                "created": raw.get("created"),
            },
        }

    def _norm_room(self, raw: dict) -> dict:
        return {
            "integration": "webex",
            "control": "access_control",
            "evidence_type": "webex_spaces",
            "source_id": raw["id"],
            "timestamp": raw.get("lastActivity", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "title": raw.get("title"),
                "type": raw.get("type"),
                "is_locked": raw.get("isLocked", False),
                "is_announcement_only": raw.get("isAnnouncementOnly", False),
                "created": raw.get("created"),
            },
        }
