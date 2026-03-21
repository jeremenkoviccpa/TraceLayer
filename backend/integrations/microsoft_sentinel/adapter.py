from __future__ import annotations

"""
Microsoft Sentinel integration via Azure REST API.

Credentials:
  tenant_id        — Azure AD tenant ID
  client_id        — Service principal / app client ID
  client_secret    — Service principal client secret
  subscription_id  — Azure subscription ID
  resource_group   — Resource group name
  workspace_name   — Log Analytics workspace name
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_API_VERSION = "2023-02-01-preview"
_TOKEN_URL_TMPL = (
    "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
)
_BASE_TMPL = (
    "https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}"
    "/providers/Microsoft.OperationalInsights/workspaces/{workspace}"
    "/providers/Microsoft.SecurityInsights"
)


class MicrosoftSentinelIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._tenant_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._subscription_id: str | None = None
        self._resource_group: str | None = None
        self._workspace_name: str | None = None
        self._token: str | None = None
        self._base: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        url = _TOKEN_URL_TMPL.format(tenant_id=self._tenant_id)
        r = await client.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://management.azure.com/.default",
            },
        )
        if r.status_code != 200:
            raise IntegrationAuthError(
                f"Failed to obtain Azure token HTTP {r.status_code}: {r.text}"
            )
        return r.json()["access_token"]

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()
        subscription_id = credentials.get("subscription_id", "").strip()
        resource_group = credentials.get("resource_group", "").strip()
        workspace_name = credentials.get("workspace_name", "").strip()

        if not all(
            [tenant_id, client_id, client_secret, subscription_id, resource_group, workspace_name]
        ):
            raise IntegrationAuthError(
                "tenant_id, client_id, client_secret, subscription_id, "
                "resource_group, and workspace_name are all required."
            )

        base = _BASE_TMPL.format(
            sub=subscription_id,
            rg=resource_group,
            workspace=workspace_name,
        )

        async with httpx.AsyncClient(timeout=15) as client:
            # Store temporarily so _get_token can use them
            self._tenant_id = tenant_id
            self._client_id = client_id
            self._client_secret = client_secret

            token = await self._get_token(client)

            r = await client.get(
                f"{base}/alertRules",
                headers={"Authorization": f"Bearer {token}"},
                params={"api-version": _API_VERSION},
            )
            if r.status_code in (401, 403):
                raise IntegrationAuthError(
                    "Invalid Microsoft Sentinel credentials or insufficient permissions."
                )
            if r.status_code != 200:
                raise RuntimeError(
                    f"Microsoft Sentinel connect failed HTTP {r.status_code}"
                )

        self._subscription_id = subscription_id
        self._resource_group = resource_group
        self._workspace_name = workspace_name
        self._token = token
        self._base = base
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Refresh token for the collection session
            try:
                self._token = await self._get_token(client)
            except Exception as exc:
                logger.warning("Sentinel token refresh failed: %s", exc)

            for fetch_fn in (
                self._collect_alert_rules,
                self._collect_incidents,
                self._collect_bookmarks,
                self._collect_data_connectors,
                self._collect_watchlists,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Sentinel collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_alert_rules(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/alertRules",
            headers=self._headers(),
            params={"api-version": _API_VERSION},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Sentinel alertRules HTTP {r.status_code}")
        return [{"_type": "alert_rule", **item} for item in r.json().get("value", [])]

    async def _collect_incidents(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/incidents",
            headers=self._headers(),
            params={"api-version": _API_VERSION, "$top": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Sentinel incidents HTTP {r.status_code}")
        return [{"_type": "incident", **item} for item in r.json().get("value", [])]

    async def _collect_bookmarks(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/bookmarks",
            headers=self._headers(),
            params={"api-version": _API_VERSION},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Sentinel bookmarks HTTP {r.status_code}")
        return [{"_type": "bookmark", **item} for item in r.json().get("value", [])]

    async def _collect_data_connectors(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/dataConnectors",
            headers=self._headers(),
            params={"api-version": _API_VERSION},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Sentinel dataConnectors HTTP {r.status_code}")
        return [{"_type": "data_connector", **item} for item in r.json().get("value", [])]

    async def _collect_watchlists(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._base}/watchlists",
            headers=self._headers(),
            params={"api-version": _API_VERSION},
        )
        if r.status_code == 404:
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Sentinel watchlists HTTP {r.status_code}")
        return [{"_type": "watchlist", **item} for item in r.json().get("value", [])]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "alert_rule":
                result.append(self._norm_alert_rule(item, now))
            elif t == "incident":
                result.append(self._norm_incident(item, now))
            elif t == "bookmark":
                result.append(self._norm_bookmark(item, now))
            elif t == "data_connector":
                result.append(self._norm_data_connector(item, now))
            elif t == "watchlist":
                result.append(self._norm_watchlist(item, now))
        return result

    def _norm_alert_rule(self, item: dict, now: str) -> dict:
        props = item.get("properties", {})
        return {
            "integration": "microsoft_sentinel",
            "control": "logging_monitoring",
            "evidence_type": "sentinel_alert_rules",
            "source_id": item.get("name", ""),
            "timestamp": props.get("createdTimeUtc") or now,
            "data": {
                "displayName": props.get("displayName"),
                "kind": item.get("kind"),
                "enabled": props.get("enabled"),
                "severity": props.get("severity"),
                "tactics": props.get("tactics", []),
            },
        }

    def _norm_incident(self, item: dict, now: str) -> dict:
        props = item.get("properties", {})
        return {
            "integration": "microsoft_sentinel",
            "control": "logging_monitoring",
            "evidence_type": "sentinel_incidents",
            "source_id": item.get("name", ""),
            "timestamp": props.get("createdTimeUtc") or now,
            "data": {
                "title": props.get("title"),
                "severity": props.get("severity"),
                "status": props.get("status"),
                "classification": props.get("classification"),
            },
        }

    def _norm_bookmark(self, item: dict, now: str) -> dict:
        props = item.get("properties", {})
        return {
            "integration": "microsoft_sentinel",
            "control": "logging_monitoring",
            "evidence_type": "sentinel_bookmarks",
            "source_id": item.get("name", ""),
            "timestamp": props.get("created") or now,
            "data": {
                "displayName": props.get("displayName"),
                "query": props.get("query"),
                "createdBy": props.get("createdBy", {}).get("name"),
            },
        }

    def _norm_data_connector(self, item: dict, now: str) -> dict:
        props = item.get("properties", {})
        data_types = props.get("dataTypes")
        state = (
            data_types.get("alerts", {}).get("state")
            if isinstance(data_types, dict)
            else None
        )
        return {
            "integration": "microsoft_sentinel",
            "control": "logging_monitoring",
            "evidence_type": "sentinel_data_connectors",
            "source_id": item.get("name", ""),
            "timestamp": now,
            "data": {
                "kind": item.get("kind"),
                "state": state,
            },
        }

    def _norm_watchlist(self, item: dict, now: str) -> dict:
        props = item.get("properties", {})
        return {
            "integration": "microsoft_sentinel",
            "control": "logging_monitoring",
            "evidence_type": "sentinel_watchlists",
            "source_id": item.get("name", ""),
            "timestamp": props.get("created") or now,
            "data": {
                "displayName": props.get("displayName"),
                "itemsSearchKey": props.get("itemsSearchKey"),
                "numberOfLinesToSkip": props.get("numberOfLinesToSkip"),
            },
        }
