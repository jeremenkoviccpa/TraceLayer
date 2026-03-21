from __future__ import annotations
"""
Kubernetes integration via the Kubernetes API server.

Credentials:
  api_url               — Base URL of the kube API server (e.g. "https://k8s.example.com:6443")
  service_account_token — Bearer token for authentication
  verify_ssl            — Whether to verify TLS (default True; pass "false" or False to disable)
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)


class KubernetesIntegration(IntegrationAdapter):

    def __init__(self):
        self._api_url: str | None = None
        self._token: str | None = None
        self._verify_ssl: bool = True

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
        }

    @staticmethod
    def _parse_verify_ssl(value) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() not in ("false", "0", "no")
        return bool(value)

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        api_url = credentials.get("api_url", "").rstrip("/").strip()
        token = credentials.get("service_account_token", "").strip()
        verify_ssl = self._parse_verify_ssl(credentials.get("verify_ssl", True))

        if not api_url or not token:
            raise IntegrationAuthError("api_url and service_account_token are required.")

        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=15, verify=verify_ssl) as client:
            r = await client.get(f"{api_url}/api", headers=headers)
            if r.status_code in (401, 403):
                raise IntegrationAuthError("Kubernetes token rejected or insufficient permissions.")
            if r.status_code != 200:
                raise RuntimeError(f"Kubernetes connect failed HTTP {r.status_code}")

        self._api_url = api_url
        self._token = token
        self._verify_ssl = verify_ssl
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30, verify=self._verify_ssl) as client:
            for fetch_fn in (
                self._collect_namespaces,
                self._collect_rbac_bindings,
                self._collect_cluster_roles,
                self._collect_pods,
                self._collect_network_policies,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("Kubernetes collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _get_items(self, client: httpx.AsyncClient, path: str, params: dict | None = None) -> list[dict]:
        r = await client.get(
            f"{self._api_url}{path}",
            headers=self._headers(),
            params=params,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Kubernetes {path} HTTP {r.status_code}")
        return r.json().get("items", [])

    async def _collect_namespaces(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._get_items(client, "/api/v1/namespaces")
        return [{"_type": "namespaces", **ns} for ns in items]

    async def _collect_rbac_bindings(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._get_items(
            client, "/apis/rbac.authorization.k8s.io/v1/clusterrolebindings"
        )
        return [{"_type": "rbac_bindings", **rb} for rb in items]

    async def _collect_cluster_roles(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._get_items(
            client, "/apis/rbac.authorization.k8s.io/v1/clusterroles"
        )
        return [{"_type": "cluster_roles", **cr} for cr in items]

    async def _collect_pods(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._get_items(client, "/api/v1/pods", params={"limit": 100})
        return [{"_type": "pods", **pod} for pod in items]

    async def _collect_network_policies(self, client: httpx.AsyncClient) -> list[dict]:
        items = await self._get_items(
            client, "/apis/networking.k8s.io/v1/networkpolicies"
        )
        return [{"_type": "network_policies", **np} for np in items]

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "namespaces":
                result.append(self._norm_namespace(item))
            elif t == "rbac_bindings":
                result.append(self._norm_rbac_binding(item))
            elif t == "cluster_roles":
                result.append(self._norm_cluster_role(item))
            elif t == "pods":
                result.append(self._norm_pod(item))
            elif t == "network_policies":
                result.append(self._norm_network_policy(item))
        return result

    def _meta(self, raw: dict) -> dict:
        meta = raw.get("metadata", {})
        return {
            "name": meta.get("name"),
            "namespace": meta.get("namespace"),
            "created_at": meta.get("creationTimestamp"),
        }

    def _norm_namespace(self, raw: dict) -> dict:
        m = self._meta(raw)
        return {
            "integration": "kubernetes",
            "control": "infrastructure",
            "evidence_type": "namespaces",
            "source_id": m["name"] or "",
            "timestamp": m["created_at"] or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": m["name"],
                "created_at": m["created_at"],
                "status_phase": raw.get("status", {}).get("phase"),
            },
        }

    def _norm_rbac_binding(self, raw: dict) -> dict:
        m = self._meta(raw)
        role_ref = raw.get("roleRef", {})
        subjects = raw.get("subjects", [])
        return {
            "integration": "kubernetes",
            "control": "access_control",
            "evidence_type": "rbac_bindings",
            "source_id": m["name"] or "",
            "timestamp": m["created_at"] or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": m["name"],
                "created_at": m["created_at"],
                "role_ref_kind": role_ref.get("kind"),
                "role_ref_name": role_ref.get("name"),
                "subjects": [
                    {"kind": s.get("kind"), "name": s.get("name"), "namespace": s.get("namespace")}
                    for s in subjects
                ],
            },
        }

    def _norm_cluster_role(self, raw: dict) -> dict:
        m = self._meta(raw)
        return {
            "integration": "kubernetes",
            "control": "access_control",
            "evidence_type": "cluster_roles",
            "source_id": m["name"] or "",
            "timestamp": m["created_at"] or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": m["name"],
                "created_at": m["created_at"],
                "rule_count": len(raw.get("rules", [])),
            },
        }

    def _norm_pod(self, raw: dict) -> dict:
        m = self._meta(raw)
        return {
            "integration": "kubernetes",
            "control": "infrastructure",
            "evidence_type": "pods",
            "source_id": f"{m['namespace']}/{m['name']}" if m["namespace"] else (m["name"] or ""),
            "timestamp": m["created_at"] or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": m["name"],
                "namespace": m["namespace"],
                "created_at": m["created_at"],
                "status_phase": raw.get("status", {}).get("phase"),
            },
        }

    def _norm_network_policy(self, raw: dict) -> dict:
        m = self._meta(raw)
        return {
            "integration": "kubernetes",
            "control": "network_security",
            "evidence_type": "network_policies",
            "source_id": f"{m['namespace']}/{m['name']}" if m["namespace"] else (m["name"] or ""),
            "timestamp": m["created_at"] or datetime.now(timezone.utc).isoformat(),
            "data": {
                "name": m["name"],
                "namespace": m["namespace"],
                "created_at": m["created_at"],
            },
        }
