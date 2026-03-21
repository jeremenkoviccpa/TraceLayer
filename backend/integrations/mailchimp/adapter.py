"""Mailchimp integration — collects audience lists, members count, and account security settings."""
from datetime import datetime, timezone
import re

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class MailchimpIntegration(IntegrationAdapter):
    def __init__(self):
        self._api_key: str | None = None
        self._base_url: str | None = None

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("Mailchimp API key is required.")
        # API key contains the datacenter: e.g. xxxxx-us1
        m = re.search(r"-(\w+)$", api_key)
        if not m:
            raise IntegrationAuthError("Invalid Mailchimp API key format. It should end with a datacenter (e.g. -us1).")
        dc = m.group(1)
        base_url = f"https://{dc}.api.mailchimp.com/3.0"
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{base_url}/", auth=("anystring", api_key))
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Mailchimp API key.")
            r.raise_for_status()
        self._api_key = api_key
        self._base_url = base_url
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            account = await self._collect_account(client)
            lists = await self._collect_lists(client)
            api_keys = await self._collect_api_keys(client)
        return account + lists + api_keys

    async def _collect_account(self, client) -> list[dict]:
        r = await client.get(f"{self._base_url}/", auth=("anystring", self._api_key))
        r.raise_for_status()
        return [{"_type": "mailchimp_account", **r.json()}]

    async def _collect_lists(self, client) -> list[dict]:
        items: list[dict] = []
        offset = 0
        count = 100
        while True:
            r = await client.get(
                f"{self._base_url}/lists",
                auth=("anystring", self._api_key),
                params={"count": count, "offset": offset, "fields": "lists.id,lists.name,lists.stats,lists.date_created,lists.email_type_option,total_items"},
            )
            r.raise_for_status()
            data = r.json()
            batch = data.get("lists", [])
            items.extend([{"_type": "mailchimp_list", **lst} for lst in batch])
            total = data.get("total_items", 0)
            offset += count
            if offset >= total:
                break
        return items

    async def _collect_api_keys(self, client) -> list[dict]:
        r = await client.get(
            f"{self._base_url}/authorized-apps",
            auth=("anystring", self._api_key),
        )
        if r.status_code == 403:
            return []
        r.raise_for_status()
        apps = r.json().get("apps", [])
        return [{"_type": "mailchimp_app", **app} for app in apps]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "mailchimp_account":
                result.append(self._norm_account(item))
            elif t == "mailchimp_list":
                result.append(self._norm_list(item))
            elif t == "mailchimp_app":
                result.append(self._norm_app(item))
        return result

    def _norm_account(self, raw: dict) -> dict:
        return {
            "integration": "mailchimp",
            "control": "data_protection",
            "evidence_type": "mailchimp_account",
            "source_id": str(raw.get("account_id", "account")),
            "timestamp": raw.get("last_login", datetime.now(timezone.utc).isoformat()),
            "data": {
                "account_id": raw.get("account_id"),
                "account_name": raw.get("account_name"),
                "email": raw.get("email"),
                "contact": raw.get("contact", {}),
                "industry_stats": raw.get("industry_stats"),
                "total_subscribers": raw.get("total_subscribers"),
            },
        }

    def _norm_list(self, raw: dict) -> dict:
        return {
            "integration": "mailchimp",
            "control": "data_protection",
            "evidence_type": "mailchimp_audiences",
            "source_id": raw["id"],
            "timestamp": raw.get("date_created", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "member_count": raw.get("stats", {}).get("member_count"),
                "unsubscribe_count": raw.get("stats", {}).get("unsubscribe_count"),
                "email_type_option": raw.get("email_type_option"),
                "date_created": raw.get("date_created"),
            },
        }

    def _norm_app(self, raw: dict) -> dict:
        return {
            "integration": "mailchimp",
            "control": "access_control",
            "evidence_type": "mailchimp_authorized_apps",
            "source_id": str(raw.get("id", "unknown")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "description": raw.get("description"),
                "users": raw.get("users", []),
            },
        }
