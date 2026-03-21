"""
Elastic Security integration via Elasticsearch and Kibana REST APIs.

Credentials:
  cloud_id  — Elastic Cloud ID (format: "name:base64encodedstring")
  api_key   — Elastic API key in "id:api_key_value" format
"""
import base64
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ElasticIntegration(IntegrationAdapter):

    def __init__(self):
        self._cloud_id: str | None = None
        self._api_key: str | None = None
        self._es_url: str | None = None
        self._kibana_url: str | None = None

    # ── Cloud ID parsing ───────────────────────────────────────────────────────

    def _parse_cloud_id(self, cloud_id: str) -> tuple[str, str]:
        """Return (es_url, kibana_url) parsed from an Elastic Cloud ID."""
        try:
            _, encoded = cloud_id.split(":", 1)
            # Pad to a valid base64 length
            decoded = base64.b64decode(encoded + "==").decode("utf-8")
            parts = decoded.split("$")
            host = parts[0]
            es_uuid = parts[1] if len(parts) > 1 else ""
            kibana_uuid = parts[2] if len(parts) > 2 else ""
            es_url = f"https://{es_uuid}.{host}"
            kibana_url = f"https://{kibana_uuid}.{host}"
            return es_url, kibana_url
        except Exception:
            # Fallback: treat cloud_id as a direct URL for both endpoints
            return cloud_id, cloud_id

    # ── Auth helpers ───────────────────────────────────────────────────────────

    def _auth_headers(self) -> dict:
        """Return Authorization header using Base64-encoded api_key."""
        encoded = base64.b64encode(self._api_key.encode()).decode()
        return {"Authorization": f"ApiKey {encoded}"}

    def _kibana_headers(self) -> dict:
        """Return headers required by Kibana (auth + kbn-xsrf)."""
        headers = self._auth_headers()
        headers["kbn-xsrf"] = "true"
        return headers

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        cloud_id = credentials.get("cloud_id", "").strip()
        api_key = credentials.get("api_key", "").strip()

        if not cloud_id or not api_key:
            raise IntegrationAuthError("cloud_id and api_key are required.")

        es_url, kibana_url = self._parse_cloud_id(cloud_id)
        encoded = base64.b64encode(api_key.encode()).decode()
        headers = {"Authorization": f"ApiKey {encoded}"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{es_url}/", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Elastic API key.")
            if r.status_code != 200:
                raise RuntimeError(f"Elastic connect failed HTTP {r.status_code}")

        self._cloud_id = cloud_id
        self._api_key = api_key
        self._es_url = es_url
        self._kibana_url = kibana_url
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_detection_rules,
                self._collect_index_patterns,
                self._collect_spaces,
                self._collect_alerts,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Elastic collection error in %s: %s",
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

    async def _collect_detection_rules(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._kibana_url}/api/detection_engine/rules/_find"
            "?per_page=100"
        )
        r = await client.get(url, headers=self._kibana_headers())
        if r.status_code != 200:
            raise RuntimeError(f"Elastic detection rules HTTP {r.status_code}")
        body = r.json()
        return [{"_type": "detection_rule", **rule} for rule in body.get("data", [])]

    async def _collect_index_patterns(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._kibana_url}/api/saved_objects/_find"
            "?type=index-pattern&per_page=100"
        )
        r = await client.get(url, headers=self._kibana_headers())
        if r.status_code != 200:
            raise RuntimeError(f"Elastic index patterns HTTP {r.status_code}")
        body = r.json()
        return [
            {"_type": "index_pattern", **obj}
            for obj in body.get("saved_objects", [])
        ]

    async def _collect_spaces(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{self._kibana_url}/api/spaces/space",
            headers=self._kibana_headers(),
        )
        if r.status_code == 404:
            logger.warning("Elastic spaces endpoint returned 404 — skipping")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Elastic spaces HTTP {r.status_code}")
        spaces = r.json()  # Returns a JSON list
        if not isinstance(spaces, list):
            spaces = []
        return [{"_type": "space", **s} for s in spaces]

    async def _collect_alerts(self, client: httpx.AsyncClient) -> list[dict]:
        url = f"{self._kibana_url}/api/detection_engine/signals/search"
        payload = {
            "query": {
                "bool": {
                    "filter": [
                        {"range": {"@timestamp": {"gte": "now-7d"}}}
                    ]
                }
            },
            "size": 50,
        }
        r = await client.post(url, headers=self._kibana_headers(), json=payload)
        if r.status_code != 200:
            raise RuntimeError(f"Elastic alerts HTTP {r.status_code}")
        body = r.json()
        hits = body.get("hits", {}).get("hits", [])
        return [{"_type": "alert", **hit} for hit in hits]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "detection_rule":
                result.append(self._norm_detection_rule(item))
            elif t == "index_pattern":
                result.append(self._norm_index_pattern(item))
            elif t == "space":
                result.append(self._norm_space(item))
            elif t == "alert":
                result.append(self._norm_alert(item))
        return result

    def _norm_detection_rule(self, raw: dict) -> dict:
        return {
            "integration": "elastic",
            "control": "logging_monitoring",
            "evidence_type": "elastic_detection_rules",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("created_at") or _now(),
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "enabled": raw.get("enabled"),
                "risk_score": raw.get("risk_score"),
                "severity": raw.get("severity"),
                "type": raw.get("type"),
            },
        }

    def _norm_index_pattern(self, raw: dict) -> dict:
        attrs = raw.get("attributes", {})
        return {
            "integration": "elastic",
            "control": "logging_monitoring",
            "evidence_type": "elastic_index_patterns",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("updated_at") or _now(),
            "data": {
                "title": attrs.get("title"),
                "time_field": attrs.get("timeFieldName"),
            },
        }

    def _norm_space(self, raw: dict) -> dict:
        return {
            "integration": "elastic",
            "control": "access_control",
            "evidence_type": "elastic_spaces",
            "source_id": raw.get("id", ""),
            "timestamp": _now(),
            "data": {
                "id": raw.get("id"),
                "name": raw.get("name"),
                "description": raw.get("description"),
                "disabledFeatures": raw.get("disabledFeatures", []),
            },
        }

    def _norm_alert(self, raw: dict) -> dict:
        source = raw.get("_source", {})
        signal = source.get("signal", {})
        rule = signal.get("rule", {})
        return {
            "integration": "elastic",
            "control": "logging_monitoring",
            "evidence_type": "elastic_alerts",
            "source_id": raw.get("_id", ""),
            "timestamp": source.get("@timestamp") or _now(),
            "data": {
                "rule_name": rule.get("name"),
                "severity": rule.get("severity"),
                "status": signal.get("status"),
            },
        }
