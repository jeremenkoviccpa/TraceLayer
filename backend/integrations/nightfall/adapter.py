"""
Nightfall AI integration via Nightfall REST API v3.

Credentials:
  api_key  — Nightfall API key
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.nightfall.ai/v3"


class NightfallIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_key: str | None = None

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_key = credentials.get("api_key", "").strip()
        if not api_key:
            raise IntegrationAuthError("api_key is required.")

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(f"{_BASE}/health", headers=headers)

            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Nightfall API key.")

            if r.status_code == 404:
                # Fall back to /user/me to validate the key
                r2 = await client.get(f"{_BASE}/user/me", headers=headers)
                if r2.status_code == 401:
                    raise IntegrationAuthError("Invalid Nightfall API key.")
                if r2.status_code not in (200, 404):
                    raise RuntimeError(
                        f"Nightfall connect fallback failed HTTP {r2.status_code}"
                    )
            elif r.status_code != 200:
                raise RuntimeError(f"Nightfall connect failed HTTP {r.status_code}")

        self._api_key = api_key
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_policies,
                self._collect_detectors,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Nightfall collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/policies",
            headers=self._headers(),
            params={"pageSize": 50},
        )
        if r.status_code == 404:
            logger.info("Nightfall /policies endpoint not available — skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Nightfall policies HTTP {r.status_code}")
        body = r.json()
        if isinstance(body, list):
            policies = body
        elif isinstance(body, dict):
            policies = body.get("policies") or body.get("data") or []
        else:
            policies = []
        return [{"_type": "policy", **p} for p in policies]

    async def _collect_detectors(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/detectors/library",
            headers=self._headers(),
        )
        if r.status_code == 404:
            logger.info("Nightfall /detectors/library endpoint not available — skipping.")
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Nightfall detectors HTTP {r.status_code}")
        body = r.json()
        if isinstance(body, list):
            detectors = body
        elif isinstance(body, dict):
            detectors = body.get("detectors") or body.get("data") or []
        else:
            detectors = []
        return [{"_type": "detector", **d} for d in detectors]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "policy":
                result.append(self._norm_policy(item, now))
            elif t == "detector":
                result.append(self._norm_detector(item, now))
        return result

    def _norm_policy(self, raw: dict, now: str) -> dict:
        raw_detectors = raw.get("detectors", [])
        detector_names = [
            d.get("name") if isinstance(d, dict) else d
            for d in raw_detectors
        ][:5]
        return {
            "integration": "nightfall",
            "control": "data_classification",
            "evidence_type": "nightfall_policies",
            "source_id": str(raw.get("id", "")),
            "timestamp": raw.get("createdAt") or now,
            "data": {
                "name": raw.get("name"),
                "detectors": detector_names,
                "alertConfig": raw.get("alertConfig"),
            },
        }

    def _norm_detector(self, raw: dict, now: str) -> dict:
        return {
            "integration": "nightfall",
            "control": "data_classification",
            "evidence_type": "nightfall_detectors",
            "source_id": str(raw.get("id", "")),
            "timestamp": now,
            "data": {
                "name": raw.get("name"),
                "description": raw.get("description"),
                "category": raw.get("category"),
            },
        }
