from __future__ import annotations

"""
Netlify integration via Netlify REST API v1.

Credentials:
  access_token — Netlify personal access token
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_BASE = "https://api.netlify.com/api/v1"


class NetlifyIntegration(IntegrationAdapter):

    def __init__(self) -> None:
        self._access_token: str | None = None
        self._account_id: str | None = None
        self._account_slug: str | None = None

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        access_token = credentials.get("access_token", "").strip()
        if not access_token:
            raise IntegrationAuthError("access_token is required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_BASE}/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Netlify access token.")
            if r.status_code != 200:
                raise RuntimeError(f"Netlify connect failed HTTP {r.status_code}")

        self._access_token = access_token
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # Resolve account id/slug upfront; tolerate failure
            try:
                await self._resolve_account(client)
            except Exception as exc:
                logger.warning("Netlify: could not resolve account: %s", exc)

            for fetch_fn in (
                self._collect_sites,
                self._collect_members,
                self._collect_env_vars,
                self._collect_deploys,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning(
                        "Netlify collection error in %s: %s", fetch_fn.__name__, exc
                    )
                    results.append(
                        {
                            "_type": "error",
                            "_source": fetch_fn.__name__,
                            "_error": str(exc),
                        }
                    )

        return results

    async def _resolve_account(self, client: httpx.AsyncClient) -> None:
        r = await client.get(f"{_BASE}/accounts", headers=self._headers())
        if r.status_code != 200:
            return
        accounts: list[dict] = r.json()
        if not accounts:
            return
        first = accounts[0]
        self._account_id = first.get("id")
        self._account_slug = first.get("slug")

    async def _collect_sites(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.get(
            f"{_BASE}/sites",
            headers=self._headers(),
            params={"per_page": 100},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Netlify sites HTTP {r.status_code}")
        sites: list[dict] = r.json()
        return [{"_type": "site", **s} for s in sites]

    async def _collect_members(self, client: httpx.AsyncClient) -> list[dict]:
        if not self._account_slug:
            return []

        r = await client.get(
            f"{_BASE}/{self._account_slug}/members",
            headers=self._headers(),
        )
        if r.status_code in (403, 404):
            return []
        if r.status_code != 200:
            raise RuntimeError(f"Netlify members HTTP {r.status_code}")

        members: list[dict] = r.json()
        return [{"_type": "member", **m} for m in members]

    async def _collect_env_vars(self, client: httpx.AsyncClient) -> list[dict]:
        if not self._account_id:
            return []

        # Gather site ids from sites collection
        sites_raw = await self._collect_sites(client)
        site_ids = [s.get("id") for s in sites_raw if s.get("id")]

        items: list[dict] = []
        for site_id in site_ids[:3]:
            r = await client.get(
                f"{_BASE}/accounts/{self._account_id}/env",
                headers=self._headers(),
                params={"site_id": site_id},
            )
            if r.status_code == 404:
                continue
            if r.status_code != 200:
                logger.warning(
                    "Netlify env vars for site %s HTTP %s", site_id, r.status_code
                )
                continue

            body = r.json()
            # API may return {"env_vars": [...]} or a plain list
            if isinstance(body, dict):
                env_vars = body.get("env_vars", [])
            else:
                env_vars = body

            for ev in env_vars:
                items.append({"_type": "env_var", **ev})

        return items

    async def _collect_deploys(self, client: httpx.AsyncClient) -> list[dict]:
        sites_raw = await self._collect_sites(client)
        site_ids = [s.get("id") for s in sites_raw if s.get("id")]

        items: list[dict] = []
        for site_id in site_ids[:3]:
            r = await client.get(
                f"{_BASE}/sites/{site_id}/deploys",
                headers=self._headers(),
                params={"per_page": 10},
            )
            if r.status_code != 200:
                logger.warning(
                    "Netlify deploys for site %s HTTP %s", site_id, r.status_code
                )
                continue

            deploys: list[dict] = r.json()
            for d in deploys:
                items.append({"_type": "deploy", **d})

        return items

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        for item in raw_data:
            t = item.get("_type")
            if t == "site":
                result.append(self._norm_site(item))
            elif t == "member":
                result.append(self._norm_member(item))
            elif t == "env_var":
                result.append(self._norm_env_var(item))
            elif t == "deploy":
                result.append(self._norm_deploy(item))
        return result

    def _norm_site(self, item: dict) -> dict:
        repo = item.get("repo")
        repo_url = repo.get("repo_url") if isinstance(repo, dict) else None
        pub_deploy = item.get("published_deploy")
        pub_deploy_id = pub_deploy.get("id") if isinstance(pub_deploy, dict) else None
        return {
            "integration": "netlify",
            "control": "change_management",
            "evidence_type": "netlify_sites",
            "source_id": item.get("id", ""),
            "timestamp": item.get("created_at") or self._now(),
            "data": {
                "name": item.get("name"),
                "url": item.get("url"),
                "ssl": item.get("ssl"),
                "repo": repo_url,
                "published_deploy": pub_deploy_id,
            },
        }

    def _norm_member(self, item: dict) -> dict:
        return {
            "integration": "netlify",
            "control": "access_control",
            "evidence_type": "netlify_members",
            "source_id": item.get("id", ""),
            "timestamp": item.get("created_at") or self._now(),
            "data": {
                "email": item.get("email"),
                "full_name": item.get("full_name"),
                "role": item.get("role"),
                "mfa_enabled": item.get("mfa_enabled"),
            },
        }

    def _norm_env_var(self, item: dict) -> dict:
        return {
            "integration": "netlify",
            "control": "change_management",
            "evidence_type": "netlify_env_vars",
            "source_id": item.get("key", ""),
            "timestamp": self._now(),
            "data": {
                "key": item.get("key"),
                "scopes": item.get("scopes", []),
                "is_secret": item.get("is_secret", False),
            },
        }

    def _norm_deploy(self, item: dict) -> dict:
        return {
            "integration": "netlify",
            "control": "change_management",
            "evidence_type": "netlify_deploys",
            "source_id": item.get("id", ""),
            "timestamp": item.get("created_at") or self._now(),
            "data": {
                "state": item.get("state"),
                "branch": item.get("branch"),
                "commit_ref": item.get("commit_ref"),
                "deploy_url": item.get("deploy_url"),
                "error_message": item.get("error_message"),
            },
        }
