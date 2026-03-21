from __future__ import annotations

"""
HashiCorp Vault integration via Vault HTTP API.

Credentials:
  address — Vault server address (e.g. https://vault.mycompany.com)
  token   — Vault token with read access to sys/auth, sys/policy, sys/audit
"""
import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class VaultIntegration(IntegrationAdapter):

    def __init__(self):
        self._address: str | None = None
        self._token: str | None = None

    def _headers(self) -> dict:
        return {
            "X-Vault-Token": self._token,
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self._address.rstrip('/')}/v1/{path}"

    async def connect(self, credentials: dict) -> bool:
        address = credentials.get("address", "").strip().rstrip("/")
        token = credentials.get("token", "").strip()
        if not address or not token:
            raise IntegrationAuthError("address and token are required")
        self._address = address
        self._token = token
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            resp = await client.get(
                self._url("auth/token/lookup-self"),
                headers=self._headers(),
            )
            if resp.status_code == 403:
                raise IntegrationAuthError("Invalid or insufficient Vault token")
            if resp.status_code not in (200, 204):
                resp.raise_for_status()
        return True

    async def collect_evidence(self, credentials: dict) -> list[dict]:
        await self.connect(credentials)
        evidence: list[dict] = []

        async with httpx.AsyncClient(timeout=30, verify=False) as client:
            # Auth methods
            resp = await client.get(self._url("sys/auth"), headers=self._headers())
            if resp.status_code == 200:
                for path, info in (resp.json().get("data") or resp.json()).items():
                    if isinstance(info, dict) and "type" in info:
                        evidence.append(self.normalize(
                            resource_type="auth_method",
                            resource_id=path.rstrip("/"),
                            data={"path": path, "type": info.get("type"), "description": info.get("description")},
                        ))

            # Policies
            resp = await client.get(
                self._url("sys/policies/acl"),
                headers=self._headers(),
                params={"list": "true"},
            )
            if resp.status_code == 200:
                keys = (resp.json().get("data") or {}).get("keys") or []
                for policy_name in keys:
                    evidence.append(self.normalize(
                        resource_type="policy",
                        resource_id=policy_name,
                        data={"name": policy_name},
                    ))

            # Audit devices
            resp = await client.get(self._url("sys/audit"), headers=self._headers())
            if resp.status_code == 200:
                for path, info in (resp.json().get("data") or resp.json()).items():
                    if isinstance(info, dict):
                        evidence.append(self.normalize(
                            resource_type="audit_device",
                            resource_id=path.rstrip("/"),
                            data={"path": path, "type": info.get("type"), "description": info.get("description")},
                        ))

            # Secrets engines
            resp = await client.get(self._url("sys/mounts"), headers=self._headers())
            if resp.status_code == 200:
                for path, info in (resp.json().get("data") or resp.json()).items():
                    if isinstance(info, dict) and "type" in info:
                        evidence.append(self.normalize(
                            resource_type="secrets_engine",
                            resource_id=path.rstrip("/"),
                            data={"path": path, "type": info.get("type"), "description": info.get("description")},
                        ))

        return evidence

    def normalize(self, raw_data=None, **kwargs):
        """Satisfies abstract interface; also works as single-item builder."""
        if raw_data is not None:
            return raw_data
        from datetime import datetime, timezone
        rt = kwargs.get("resource_type", "unknown")
        control_map = {
            "auth_method": "access_control",
            "policy": "access_control",
            "audit_device": "logging",
            "secrets_engine": "data_security",
        }
        return {
            "integration": "vault",
            "control": control_map.get(rt, "data_security"),
            "evidence_type": f"vault_{rt}",
            "source_id": kwargs.get("resource_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": kwargs.get("data", {}),
        }
