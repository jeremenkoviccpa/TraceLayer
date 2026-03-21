"""Google Analytics integration — collects web traffic, availability metrics, and user data."""
import json
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
GA4_API = "https://analyticsdata.googleapis.com/v1beta"
ADMIN_API = "https://analyticsadmin.googleapis.com/v1beta"
GA_SCOPES = "https://www.googleapis.com/auth/analytics.readonly"


class GoogleAnalyticsIntegration(IntegrationAdapter):
    def __init__(self):
        self._access_token: str | None = None
        self._property_id: str | None = None

    async def connect(self, credentials: dict) -> bool:
        sa_json = credentials.get("service_account_json", "").strip()
        property_id = credentials.get("property_id", "").strip()
        if not sa_json or not property_id:
            raise IntegrationAuthError("Service account JSON and GA4 property ID are required.")
        try:
            sa = json.loads(sa_json)
        except json.JSONDecodeError:
            raise IntegrationAuthError("Invalid JSON in service account credentials.")
        token = await self._get_token(sa)
        if not token:
            raise IntegrationAuthError("Could not obtain Google Analytics access token.")
        # Verify the property exists
        async with httpx.AsyncClient(timeout=10) as client:
            pid = property_id if property_id.startswith("properties/") else f"properties/{property_id}"
            r = await client.get(
                f"{ADMIN_API}/{pid}",
                headers={"Authorization": f"Bearer {token}"},
            )
            if r.status_code in (403, 404):
                raise IntegrationAuthError(f"Property '{property_id}' not found or service account lacks access.")
            r.raise_for_status()
        self._access_token = token
        self._property_id = property_id if property_id.startswith("properties/") else f"properties/{property_id}"
        return True

    async def _get_token(self, sa: dict) -> str | None:
        import time
        import jwt
        now = int(time.time())
        payload = {
            "iss": sa["client_email"],
            "scope": GA_SCOPES,
            "aud": OAUTH_TOKEN_URL,
            "iat": now,
            "exp": now + 3600,
        }
        try:
            signed = jwt.encode(payload, sa["private_key"], algorithm="RS256")
        except Exception:
            return None
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                OAUTH_TOKEN_URL,
                data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": signed},
            )
            if r.status_code != 200:
                return None
            return r.json().get("access_token")

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._access_token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            traffic = await self._collect_traffic_report(client, headers)
            property_info = await self._collect_property_info(client, headers)
        return traffic + property_info

    async def _collect_traffic_report(self, client, headers) -> list[dict]:
        body = {
            "dateRanges": [{"startDate": "30daysAgo", "endDate": "today"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "activeUsers"},
                {"name": "totalUsers"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
            ],
            "dimensions": [{"name": "date"}],
            "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": True}],
        }
        r = await client.post(
            f"{GA4_API}/{self._property_id}:runReport",
            headers=headers,
            json=body,
        )
        r.raise_for_status()
        data = r.json()
        rows = []
        dim_headers = [d["name"] for d in data.get("dimensionHeaders", [])]
        metric_headers = [m["name"] for m in data.get("metricHeaders", [])]
        for row in data.get("rows", []):
            record: dict = {}
            for i, dim in enumerate(row.get("dimensionValues", [])):
                record[dim_headers[i]] = dim["value"]
            for i, met in enumerate(row.get("metricValues", [])):
                record[metric_headers[i]] = met["value"]
            rows.append({"_type": "ga_traffic_row", **record})
        return rows

    async def _collect_property_info(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{ADMIN_API}/{self._property_id}",
            headers=headers,
        )
        r.raise_for_status()
        prop = r.json()
        return [{"_type": "ga_property", **prop}]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "ga_traffic_row":
                result.append(self._norm_traffic(item))
            elif t == "ga_property":
                result.append(self._norm_property(item))
        return result

    def _norm_traffic(self, raw: dict) -> dict:
        date_str = raw.get("date", "")
        ts = datetime.now(timezone.utc).isoformat()
        if date_str and len(date_str) == 8:
            ts = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}T00:00:00+00:00"
        return {
            "integration": "google_analytics",
            "control": "availability",
            "evidence_type": "web_traffic_metrics",
            "source_id": f"ga_traffic_{date_str}",
            "timestamp": ts,
            "data": {
                "date": date_str,
                "sessions": raw.get("sessions"),
                "active_users": raw.get("activeUsers"),
                "total_users": raw.get("totalUsers"),
                "bounce_rate": raw.get("bounceRate"),
                "avg_session_duration": raw.get("averageSessionDuration"),
            },
        }

    def _norm_property(self, raw: dict) -> dict:
        return {
            "integration": "google_analytics",
            "control": "availability",
            "evidence_type": "ga_property",
            "source_id": raw.get("name", "property"),
            "timestamp": raw.get("updateTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "name": raw.get("name"),
                "display_name": raw.get("displayName"),
                "industry_category": raw.get("industryCategory"),
                "time_zone": raw.get("timeZone"),
                "currency_code": raw.get("currencyCode"),
                "create_time": raw.get("createTime"),
            },
        }
