from __future__ import annotations

"""
Oracle Cloud Infrastructure (OCI) integration via OCI REST API.

Credentials:
  tenancy_ocid — OCID of the tenancy
  user_ocid    — OCID of the API-key user
  fingerprint  — API key fingerprint
  private_key  — PEM-encoded RSA private key content
  region       — OCI region identifier (e.g. "us-ashburn-1")
"""
import base64
import email.utils
import hashlib
import logging
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class OracleCloudIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._tenancy_ocid: str | None = None
        self._user_ocid: str | None = None
        self._fingerprint: str | None = None
        self._private_key: str | None = None
        self._region: str | None = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _identity_base(self) -> str:
        return f"https://identity.{self._region}.oraclecloud.com"

    # ── Request signing ────────────────────────────────────────────────────────

    def _sign_request(self, method: str, url: str, body: str = "") -> dict:
        parsed = urlparse(url)
        date = email.utils.formatdate(usegmt=True)
        host = parsed.netloc
        path = parsed.path + (f"?{parsed.query}" if parsed.query else "")

        body_bytes = body.encode("utf-8")
        body_hash = base64.b64encode(hashlib.sha256(body_bytes).digest()).decode()

        has_body = bool(body)

        # Build signing string — order matters for OCI
        signing_string_parts = [
            f"(request-target): {method.lower()} {path}",
            f"host: {host}",
            f"date: {date}",
        ]
        headers_list = ["(request-target)", "host", "date"]

        if has_body:
            signing_string_parts += [
                f"content-length: {len(body_bytes)}",
                f"content-type: application/json",
                f"x-content-sha256: {body_hash}",
            ]
            headers_list += ["content-length", "content-type", "x-content-sha256"]

        signing_string = "\n".join(signing_string_parts)

        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding

        private_key_bytes = (
            self._private_key.encode()
            if isinstance(self._private_key, str)
            else self._private_key
        )
        private_key_obj = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
        )
        signature = base64.b64encode(
            private_key_obj.sign(
                signing_string.encode(), padding.PKCS1v15(), hashes.SHA256()
            )
        ).decode()

        key_id = (
            f"{self._tenancy_ocid}/{self._user_ocid}/{self._fingerprint}"
        )
        headers_str = " ".join(headers_list)

        auth_header = (
            f'Signature version="1",keyId="{key_id}",'
            f'algorithm="rsa-sha256",headers="{headers_str}",'
            f'signature="{signature}"'
        )

        result: dict[str, str] = {
            "date": date,
            "host": host,
            "authorization": auth_header,
        }
        if has_body:
            result.update(
                {
                    "content-length": str(len(body_bytes)),
                    "content-type": "application/json",
                    "x-content-sha256": body_hash,
                }
            )
        return result

    async def _signed_get(self, client: httpx.AsyncClient, url: str) -> httpx.Response:
        headers = self._sign_request("GET", url)
        return await client.get(url, headers=headers)

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        tenancy_ocid = credentials.get("tenancy_ocid", "").strip()
        user_ocid = credentials.get("user_ocid", "").strip()
        fingerprint = credentials.get("fingerprint", "").strip()
        private_key = credentials.get("private_key", "").strip()
        region = credentials.get("region", "").strip()

        for field, value in [
            ("tenancy_ocid", tenancy_ocid),
            ("user_ocid", user_ocid),
            ("fingerprint", fingerprint),
            ("private_key", private_key),
            ("region", region),
        ]:
            if not value:
                raise IntegrationAuthError(f"{field} is required.")

        self._tenancy_ocid = tenancy_ocid
        self._user_ocid = user_ocid
        self._fingerprint = fingerprint
        self._private_key = private_key
        self._region = region

        url = (
            f"https://identity.{region}.oraclecloud.com"
            f"/20160918/compartments/{tenancy_ocid}"
        )

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                r = await self._signed_get(client, url)
                if r.status_code == 401:
                    raise IntegrationAuthError(
                        "Invalid OCI credentials (401 Unauthorized)."
                    )
                if r.status_code == 404:
                    # Tenancy OCID not found as compartment — treat as auth failure
                    raise IntegrationAuthError(
                        "OCI tenancy OCID not found or access denied."
                    )
                if r.status_code != 200:
                    raise RuntimeError(
                        f"OCI connect failed HTTP {r.status_code}: {r.text[:200]}"
                    )
        except IntegrationAuthError:
            self._tenancy_ocid = None
            self._user_ocid = None
            self._fingerprint = None
            self._private_key = None
            self._region = None
            raise

        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_groups,
                self._collect_policies,
                self._collect_compartments,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "OCI collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._identity_base()}/20160918/users"
            f"?compartmentId={self._tenancy_ocid}&limit=100"
        )
        r = await self._signed_get(client, url)
        if r.status_code != 200:
            raise RuntimeError(f"OCI users HTTP {r.status_code}")
        return [{"_type": "user", **u} for u in r.json()]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._identity_base()}/20160918/groups"
            f"?compartmentId={self._tenancy_ocid}&limit=100"
        )
        r = await self._signed_get(client, url)
        if r.status_code != 200:
            raise RuntimeError(f"OCI groups HTTP {r.status_code}")
        return [{"_type": "group", **g} for g in r.json()]

    async def _collect_policies(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._identity_base()}/20160918/policies"
            f"?compartmentId={self._tenancy_ocid}&limit=100"
        )
        r = await self._signed_get(client, url)
        if r.status_code != 200:
            raise RuntimeError(f"OCI policies HTTP {r.status_code}")
        return [{"_type": "policy", **p} for p in r.json()]

    async def _collect_compartments(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{self._identity_base()}/20160918/compartments"
            f"?compartmentId={self._tenancy_ocid}&limit=100"
        )
        r = await self._signed_get(client, url)
        if r.status_code != 200:
            raise RuntimeError(f"OCI compartments HTTP {r.status_code}")
        return [{"_type": "compartment", **c} for c in r.json()]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "group":
                result.append(self._norm_group(item))
            elif t == "policy":
                result.append(self._norm_policy(item))
            elif t == "compartment":
                result.append(self._norm_compartment(item))
        return result

    def _norm_user(self, item: dict) -> dict:
        return {
            "integration": "oracle_cloud",
            "control": "access_control",
            "evidence_type": "oci_users",
            "source_id": item.get("id", ""),
            "timestamp": item.get("timeCreated") or self._now(),
            "data": {
                "name": item.get("name"),
                "description": item.get("description"),
                "email": item.get("email"),
                "lifecycleState": item.get("lifecycleState"),
                "isMfaActivated": item.get("isMfaActivated"),
                "isBlocked": item.get("isBlocked"),
            },
        }

    def _norm_group(self, item: dict) -> dict:
        return {
            "integration": "oracle_cloud",
            "control": "access_control",
            "evidence_type": "oci_groups",
            "source_id": item.get("id", ""),
            "timestamp": item.get("timeCreated") or self._now(),
            "data": {
                "name": item.get("name"),
                "description": item.get("description"),
                "lifecycleState": item.get("lifecycleState"),
            },
        }

    def _norm_policy(self, item: dict) -> dict:
        return {
            "integration": "oracle_cloud",
            "control": "access_control",
            "evidence_type": "oci_policies",
            "source_id": item.get("id", ""),
            "timestamp": item.get("timeCreated") or self._now(),
            "data": {
                "name": item.get("name"),
                "description": item.get("description"),
                "statements": item.get("statements", []),
                "lifecycleState": item.get("lifecycleState"),
            },
        }

    def _norm_compartment(self, item: dict) -> dict:
        return {
            "integration": "oracle_cloud",
            "control": "cloud_infrastructure",
            "evidence_type": "oci_compartments",
            "source_id": item.get("id", ""),
            "timestamp": item.get("timeCreated") or self._now(),
            "data": {
                "name": item.get("name"),
                "description": item.get("description"),
                "lifecycleState": item.get("lifecycleState"),
            },
        }
