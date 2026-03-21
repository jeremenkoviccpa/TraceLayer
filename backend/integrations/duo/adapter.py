from __future__ import annotations
"""
Duo Security integration via Duo Admin API.

Credentials:
  integration_key — Duo Admin API integration key (DIxxx)
  secret_key      — Duo Admin API secret key
  api_hostname    — Duo API hostname, e.g. "api-xxxxxxxx.duosecurity.com"

Duo uses a custom HMAC-SHA1 request signing scheme. Each request is signed
with the current date, HTTP method, host, path, and sorted parameters.
"""
import base64
import hashlib
import hmac
import time
from datetime import datetime, timezone
from email.utils import formatdate
from urllib.parse import urlencode

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


def _duo_sign(ikey: str, skey: str, method: str, host: str, path: str, params: dict | None = None) -> dict:
    """
    Build Duo-signed request headers.
    Returns a dict with 'Date' and 'Authorization' headers.
    """
    date = formatdate()
    sorted_params = urlencode(sorted(params.items())) if params else ""
    canon = "\n".join([date, method.upper(), host.lower(), path, sorted_params])
    sig = hmac.new(skey.encode(), canon.encode(), hashlib.sha1).hexdigest()
    auth = base64.b64encode(f"{ikey}:{sig}".encode()).decode()
    return {"Date": date, "Authorization": f"Basic {auth}"}


class DuoIntegration(IntegrationAdapter):

    def __init__(self):
        self._ikey: str | None = None
        self._skey: str | None = None
        self._host: str | None = None

    def _base_url(self) -> str:
        return f"https://{self._host}"

    def _headers(self, method: str, path: str, params: dict | None = None) -> dict:
        headers = _duo_sign(self._ikey, self._skey, method, self._host, path, params)
        headers["Accept"] = "application/json"
        return headers

    async def connect(self, credentials: dict) -> bool:
        ikey = credentials.get("integration_key", "").strip()
        skey = credentials.get("secret_key", "").strip()
        host = credentials.get("api_hostname", "").strip()

        if not ikey or not skey or not host:
            raise IntegrationAuthError("integration_key, secret_key, and api_hostname are required")

        path = "/admin/v1/users"
        params = {"limit": "1"}
        headers = _duo_sign(ikey, skey, "GET", host, path, params)
        headers["Accept"] = "application/json"

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"https://{host}{path}",
                params=params,
                headers=headers,
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Duo credentials or HMAC signature mismatch")
            if r.status_code == 403:
                raise IntegrationAuthError("Duo integration key lacks Admin API permissions")
            r.raise_for_status()

        self._ikey = ikey
        self._skey = skey
        self._host = host
        return True

    async def collect_evidence(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=30) as client:
            users = await self._collect_users(client)
            groups = await self._collect_groups(client)
            policies = await self._collect_policies(client)
            auth_logs = await self._collect_auth_logs(client)
        return users + groups + policies + auth_logs

    async def _paginate(self, client: httpx.AsyncClient, path: str, extra_params: dict | None = None) -> list[dict]:
        """Generic offset-based paginator for Duo Admin API list endpoints."""
        results = []
        offset = 0
        limit = 100
        while True:
            params = {"limit": str(limit), "offset": str(offset)}
            if extra_params:
                params.update(extra_params)
            headers = self._headers("GET", path, params)
            r = await client.get(f"{self._base_url()}{path}", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            batch = data.get("response", [])
            results.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        try:
            raw = await self._paginate(client, "/admin/v1/users")
            return [
                {
                    "_type": "user",
                    "user_id": u.get("user_id"),
                    "username": u.get("username"),
                    "email": u.get("email"),
                    "status": u.get("status"),
                    "last_login": u.get("last_login"),
                    "phones_count": len(u.get("phones", [])),
                }
                for u in raw
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Duo users: {exc}") from exc

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        try:
            raw = await self._paginate(client, "/admin/v1/groups")
            return [
                {
                    "_type": "group",
                    "group_id": g.get("group_id"),
                    "name": g.get("name"),
                    "desc": g.get("desc"),
                    "status": g.get("status"),
                    "mobile_otp_enabled": g.get("mobile_otp_enabled"),
                }
                for g in raw
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Duo groups: {exc}") from exc

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        path = "/admin/v1/policies"
        try:
            params: dict = {}
            headers = self._headers("GET", path, params)
            r = await client.get(f"{self._base_url()}{path}", params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            policies = data.get("response", {})
            # Duo returns policies as a dict keyed by policy_key
            if isinstance(policies, dict):
                return [
                    {
                        "_type": "policy",
                        "policy_key": k,
                        "policy_name": v.get("policy_name"),
                        "sections": v.get("sections", {}),
                    }
                    for k, v in policies.items()
                ]
            # Some API versions return a list
            return [
                {
                    "_type": "policy",
                    "policy_key": p.get("policy_key"),
                    "policy_name": p.get("policy_name"),
                    "sections": p.get("sections", {}),
                }
                for p in (policies if isinstance(policies, list) else [])
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Duo policies: {exc}") from exc

    async def _collect_auth_logs(self, client: httpx.AsyncClient) -> list[dict]:
        path = "/admin/v1/logs/authentication"
        mintime = int(time.time()) - (30 * 24 * 60 * 60)  # 30 days ago
        try:
            params = {"mintime": str(mintime), "limit": "100"}
            headers = self._headers("GET", path, params)
            r = await client.get(
                f"{self._base_url()}{path}",
                params=params,
                headers=headers,
            )
            r.raise_for_status()
            data = r.json()
            logs = data.get("response", [])
            return [
                {
                    "_type": "auth_log",
                    "result": entry.get("result"),
                    "reason": entry.get("reason"),
                    "user": entry.get("user", {}).get("name") if isinstance(entry.get("user"), dict) else entry.get("user"),
                    "factor": entry.get("factor"),
                    "timestamp": entry.get("timestamp"),
                }
                for entry in (logs if isinstance(logs, list) else [])
            ]
        except Exception as exc:
            raise RuntimeError(f"Failed to collect Duo auth logs: {exc}") from exc

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
            elif t == "auth_log":
                result.append(self._norm_auth_log(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "duo",
            "control": "access_control",
            "evidence_type": "duo_users",
            "source_id": raw.get("user_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "username": raw.get("username"),
                "email": raw.get("email"),
                "status": raw.get("status"),
                "last_login": raw.get("last_login"),
                "phones_count": raw.get("phones_count", 0),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "duo",
            "control": "access_control",
            "evidence_type": "duo_groups",
            "source_id": raw.get("group_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": raw.get("name"),
                "desc": raw.get("desc"),
                "status": raw.get("status"),
                "mobile_otp_enabled": raw.get("mobile_otp_enabled"),
            },
        }

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "duo",
            "control": "access_control",
            "evidence_type": "duo_policies",
            "source_id": raw.get("policy_key", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "policy_name": raw.get("policy_name"),
                "sections": raw.get("sections", {}),
            },
        }

    def _norm_auth_log(self, raw: dict) -> dict:
        ts = raw.get("timestamp")
        iso_ts = (
            datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            if isinstance(ts, (int, float))
            else (ts or datetime.now(timezone.utc).isoformat())
        )
        return {
            "integration": "duo",
            "control": "access_control",
            "evidence_type": "duo_auth_logs",
            "source_id": f"{raw.get('user', 'unknown')}_{ts}",
            "timestamp": iso_ts,
            "data": {
                "result": raw.get("result"),
                "reason": raw.get("reason"),
                "user": raw.get("user"),
                "factor": raw.get("factor"),
            },
        }
