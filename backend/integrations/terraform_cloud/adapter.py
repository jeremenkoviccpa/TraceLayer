"""
Terraform Cloud integration adapter.

Collects organization configuration, workspace inventory, and run history
from the Terraform Cloud JSON:API (https://app.terraform.io/api/v2).
"""

import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

TFC_API = "https://app.terraform.io/api/v2"
TFC_CONTENT_TYPE = "application/vnd.api+json"


class TerraformCloudIntegration(IntegrationAdapter):
    """Collects access-control and change-management evidence from Terraform Cloud."""

    def __init__(self) -> None:
        self._token: str | None = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        """Validate the API token by fetching /account/details."""
        api_token = (credentials.get("api_token") or "").strip()
        if not api_token:
            raise IntegrationAuthError("Terraform Cloud api_token is required.")

        headers = self._auth_headers(api_token)
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{TFC_API}/account/details", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Terraform Cloud API token.")
            r.raise_for_status()

        self._token = api_token
        return True

    # ------------------------------------------------------------------
    # collect_evidence
    # ------------------------------------------------------------------

    async def collect_evidence(self) -> list[dict]:
        headers = self._auth_headers(self._token)
        raw: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            # ── Account details ────────────────────────────────────────
            try:
                account = await self._collect_account(client, headers)
                raw.extend(account)
            except Exception:
                logger.exception("Terraform Cloud: failed to collect account details")

            # ── Organizations ──────────────────────────────────────────
            try:
                organizations = await self._collect_organizations(client, headers)
                raw.extend(organizations)
            except Exception:
                logger.exception("Terraform Cloud: failed to collect organizations")

            org_names = [
                o["_name"] for o in organizations if o.get("_type") == "organization"
            ]

            for org_name in org_names:
                # ── Workspaces ─────────────────────────────────────────
                try:
                    workspaces = await self._collect_workspaces(client, headers, org_name)
                    raw.extend(workspaces)
                except Exception:
                    logger.exception(
                        "Terraform Cloud: failed to collect workspaces for org %s", org_name
                    )

                # ── Runs ───────────────────────────────────────────────
                try:
                    runs = await self._collect_runs(client, headers, org_name)
                    raw.extend(runs)
                except Exception:
                    logger.exception(
                        "Terraform Cloud: failed to collect runs for org %s", org_name
                    )

        return raw

    # ------------------------------------------------------------------
    # normalize
    # ------------------------------------------------------------------

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result: list[dict] = []
        now = datetime.now(timezone.utc).isoformat()

        for item in raw_data:
            t = item.get("_type")
            if t == "organization":
                result.append(self._norm_organization(item, now))
            elif t == "workspace":
                result.append(self._norm_workspace(item, now))
            elif t == "run":
                result.append(self._norm_run(item, now))
            # "account" items are context-only; not emitted separately.

        return result

    # ------------------------------------------------------------------
    # Private helpers — collection
    # ------------------------------------------------------------------

    def _auth_headers(self, token: str) -> dict:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": TFC_CONTENT_TYPE,
        }

    async def _collect_account(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        r = await client.get(f"{TFC_API}/account/details", headers=headers)
        r.raise_for_status()
        data = r.json().get("data", {})
        attrs = data.get("attributes", {})
        return [{
            "_type": "account",
            "id": data.get("id"),
            "username": attrs.get("username"),
            "email": attrs.get("email"),
        }]

    async def _collect_organizations(
        self, client: httpx.AsyncClient, headers: dict
    ) -> list[dict]:
        r = await client.get(f"{TFC_API}/organizations", headers=headers)
        r.raise_for_status()
        orgs: list[dict] = []
        for item in r.json().get("data", []):
            attrs = item.get("attributes", {})
            orgs.append({
                "_type": "organization",
                "id": item.get("id"),
                # Keep the name accessible without digging into attrs downstream
                "_name": attrs.get("name"),
                "name": attrs.get("name"),
                "created_at": attrs.get("created-at"),
                "plan": attrs.get("plan"),
                "collaborator_auth_policy": attrs.get("collaborator-auth-policy"),
            })
        return orgs

    async def _collect_workspaces(
        self, client: httpx.AsyncClient, headers: dict, org_name: str
    ) -> list[dict]:
        workspaces: list[dict] = []
        page_number = 1
        while True:
            r = await client.get(
                f"{TFC_API}/organizations/{org_name}/workspaces",
                headers=headers,
                params={"page[size]": 100, "page[number]": page_number},
            )
            r.raise_for_status()
            body = r.json()
            items = body.get("data", [])
            if not items:
                break
            for item in items:
                attrs = item.get("attributes", {})
                vcs_repo = attrs.get("vcs-repo") or {}
                workspaces.append({
                    "_type": "workspace",
                    "id": item.get("id"),
                    "org_name": org_name,
                    "name": attrs.get("name"),
                    "environment": attrs.get("environment"),
                    "vcs_repo": vcs_repo.get("identifier"),
                    "locked": attrs.get("locked", False),
                    "terraform_version": attrs.get("terraform-version"),
                    "updated_at": attrs.get("updated-at"),
                })
            meta = body.get("meta", {})
            pagination = meta.get("pagination", {})
            if page_number >= pagination.get("total-pages", 1):
                break
            page_number += 1
        return workspaces

    async def _collect_runs(
        self, client: httpx.AsyncClient, headers: dict, org_name: str
    ) -> list[dict]:
        runs: list[dict] = []
        page_number = 1
        while True:
            r = await client.get(
                f"{TFC_API}/organizations/{org_name}/runs",
                headers=headers,
                params={"page[size]": 50, "page[number]": page_number},
            )
            r.raise_for_status()
            body = r.json()
            items = body.get("data", [])
            if not items:
                break
            for item in items:
                attrs = item.get("attributes", {})
                relationships = item.get("relationships", {})
                workspace_data = (
                    relationships.get("workspace", {}).get("data", {})
                )
                runs.append({
                    "_type": "run",
                    "id": item.get("id"),
                    "org_name": org_name,
                    "status": attrs.get("status"),
                    "created_at": attrs.get("created-at"),
                    "message": attrs.get("message"),
                    "workspace_id": workspace_data.get("id"),
                })
            meta = body.get("meta", {})
            pagination = meta.get("pagination", {})
            if page_number >= pagination.get("total-pages", 1):
                break
            page_number += 1
        return runs

    # ------------------------------------------------------------------
    # Private helpers — normalization
    # ------------------------------------------------------------------

    def _norm_organization(self, raw: dict, now: str) -> dict:
        return {
            "integration": "terraform_cloud",
            "control": "access_control",
            "evidence_type": "terraform_organizations",
            "source_id": raw.get("id") or raw.get("name", "unknown"),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "name": raw.get("name"),
                "plan": raw.get("plan"),
                "collaborator_auth_policy": raw.get("collaborator_auth_policy"),
                "created_at": raw.get("created_at"),
            },
        }

    def _norm_workspace(self, raw: dict, now: str) -> dict:
        return {
            "integration": "terraform_cloud",
            "control": "change_management",
            "evidence_type": "terraform_workspaces",
            "source_id": raw.get("id") or raw.get("name", "unknown"),
            "timestamp": raw.get("updated_at") or now,
            "data": {
                "name": raw.get("name"),
                "org_name": raw.get("org_name"),
                "environment": raw.get("environment"),
                "vcs_repo": raw.get("vcs_repo"),
                "locked": raw.get("locked", False),
                "terraform_version": raw.get("terraform_version"),
                "updated_at": raw.get("updated_at"),
            },
        }

    def _norm_run(self, raw: dict, now: str) -> dict:
        return {
            "integration": "terraform_cloud",
            "control": "change_management",
            "evidence_type": "terraform_runs",
            "source_id": raw.get("id", "unknown"),
            "timestamp": raw.get("created_at") or now,
            "data": {
                "status": raw.get("status"),
                "created_at": raw.get("created_at"),
                "message": raw.get("message"),
                "workspace_id": raw.get("workspace_id"),
                "org_name": raw.get("org_name"),
            },
        }
