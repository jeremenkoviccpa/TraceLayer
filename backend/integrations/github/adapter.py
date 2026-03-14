from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

GITHUB_API = "https://api.github.com"
ACCEPT = "application/vnd.github+json"


class GithubIntegration(IntegrationAdapter):

    def __init__(self):
        self._token: str | None = None
        self._org: str | None = None

    async def connect(self, credentials: dict) -> bool:
        token = credentials.get("token")
        org = credentials.get("org")
        headers = {"Authorization": f"Bearer {token}", "Accept": ACCEPT}
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{GITHUB_API}/orgs/{org}", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid GitHub token")
            if r.status_code == 404:
                raise IntegrationAuthError(f"Organization '{org}' not found or token lacks org access")
            r.raise_for_status()
        self._token = token
        self._org = org
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"Bearer {self._token}", "Accept": ACCEPT}
        async with httpx.AsyncClient(timeout=30) as client:
            repos = await self._collect_repos(client, headers)
            members = await self._collect_members(client, headers)
            admins = await self._collect_admins(client, headers)
        return repos + members + admins

    async def _collect_repos(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        repos = []
        page = 1
        while True:
            r = await client.get(
                f"{GITHUB_API}/orgs/{self._org}/repos",
                headers=headers,
                params={"per_page": 100, "page": page, "type": "all"},
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            repos.extend([{"_type": "repo", **repo} for repo in data])
            page += 1
        return repos

    async def _collect_members(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        members = []
        page = 1
        while True:
            r = await client.get(
                f"{GITHUB_API}/orgs/{self._org}/members",
                headers=headers,
                params={"per_page": 100, "page": page},
            )
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            members.extend([{"_type": "member", **m} for m in data])
            page += 1
        return members

    async def _collect_admins(self, client: httpx.AsyncClient, headers: dict) -> list[dict]:
        r = await client.get(
            f"{GITHUB_API}/orgs/{self._org}/members",
            headers=headers,
            params={"role": "admin", "per_page": 100},
        )
        r.raise_for_status()
        return [{"_type": "admin_member", **m} for m in r.json()]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "repo":
                result.append(self._norm_repo(item))
            elif t == "member":
                result.append(self._norm_member(item))
            elif t == "admin_member":
                result.append(self._norm_admin_member(item))
        return result

    def _norm_repo(self, raw: dict) -> dict:
        return {
            "integration": "github",
            "control": "change_management",
            "evidence_type": "repositories",
            "source_id": str(raw["id"]),
            "timestamp": raw.get("created_at", datetime.now(timezone.utc).isoformat()),
            "data": {
                "name": raw["name"],
                "full_name": raw["full_name"],
                "private": raw["private"],
                "visibility": raw.get("visibility"),
                "default_branch": raw.get("default_branch"),
                "updated_at": raw.get("updated_at"),
                "archived": raw.get("archived", False),
            },
        }

    def _norm_member(self, raw: dict) -> dict:
        return {
            "integration": "github",
            "control": "access_control",
            "evidence_type": "github_members",
            "source_id": raw["login"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "login": raw["login"],
                "id": raw["id"],
                "type": raw.get("type"),
                "site_admin": raw.get("site_admin", False),
            },
        }

    def _norm_admin_member(self, raw: dict) -> dict:
        return {
            "integration": "github",
            "control": "access_control",
            "evidence_type": "github_admin_members",
            "source_id": f"admin_{raw['login']}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "login": raw["login"],
                "id": raw["id"],
                "role": "admin",
                "site_admin": raw.get("site_admin", False),
            },
        }
