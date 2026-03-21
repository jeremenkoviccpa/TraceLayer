from __future__ import annotations
"""
Microsoft Teams integration adapter via Microsoft Graph API.

Collects Teams groups, their members, and all Entra ID users for
access control evidence.

Credentials:
  tenant_id     — Azure AD tenant ID (GUID)
  client_id     — App registration client ID
  client_secret — App registration client secret

Required API permissions (application, not delegated):
  Team.ReadBasic.All, GroupMember.Read.All, User.Read.All
"""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

_GRAPH = "https://graph.microsoft.com/v1.0"
_TOKEN_URL_TPL = "https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
_SCOPE = "https://graph.microsoft.com/.default"


class MicrosoftTeamsIntegration(IntegrationAdapter):

    def __init__(self):
        self._tenant_id: str | None = None
        self._client_id: str | None = None
        self._client_secret: str | None = None
        self._access_token: str | None = None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def connect(self, credentials: dict) -> bool:
        tenant_id = credentials.get("tenant_id", "").strip()
        client_id = credentials.get("client_id", "").strip()
        client_secret = credentials.get("client_secret", "").strip()

        if not tenant_id or not client_id or not client_secret:
            raise IntegrationAuthError(
                "tenant_id, client_id, and client_secret are required"
            )

        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret

        token = await self._get_token()

        # Validate token by fetching org info
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                f"{_GRAPH}/organization",
                headers=self._auth_headers(token),
            )
            if r.status_code == 401:
                raise IntegrationAuthError(
                    "Microsoft Teams auth failed (401): invalid client credentials"
                )
            if r.status_code == 403:
                raise IntegrationAuthError(
                    "Microsoft Teams auth failed (403): app registration lacks "
                    "required permissions (Team.ReadBasic.All, GroupMember.Read.All, "
                    "User.Read.All)"
                )
            r.raise_for_status()

        self._access_token = token
        return True

    async def collect_evidence(self) -> list[dict]:
        self._access_token = await self._get_token()
        async with httpx.AsyncClient(timeout=60) as client:
            teams = await self._collect_teams(client)
            members = await self._collect_all_members(client, teams)
            users = await self._collect_users(client)
        return teams + members + users

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        now = datetime.now(timezone.utc).isoformat()
        for item in raw_data:
            t = item.get("_type")
            if t == "team":
                result.append(self._norm_team(item, now))
            elif t == "member":
                result.append(self._norm_member(item, now))
            elif t == "user":
                result.append(self._norm_user(item, now))
        return result

    # ------------------------------------------------------------------
    # Token
    # ------------------------------------------------------------------

    async def _get_token(self) -> str:
        token_url = _TOKEN_URL_TPL.format(tenant_id=self._tenant_id)
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                token_url,
                data={
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": _SCOPE,
                    "grant_type": "client_credentials",
                },
            )
            if r.status_code in (400, 401):
                detail = ""
                try:
                    detail = r.json().get("error_description", "")
                except Exception:
                    pass
                raise IntegrationAuthError(
                    f"Microsoft Teams token fetch failed ({r.status_code}): {detail}"
                )
            r.raise_for_status()
            return r.json()["access_token"]

    def _auth_headers(self, token: str | None = None) -> dict:
        return {
            "Authorization": f"Bearer {token or self._access_token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Collectors
    # ------------------------------------------------------------------

    async def _paginate(
        self,
        client: httpx.AsyncClient,
        url: str,
        tag: str,
        field_map: dict | None = None,
    ) -> list[dict]:
        """
        Walk Graph's @odata.nextLink pagination and return tagged items.
        field_map: if provided, extract only these keys from each item.
        """
        items: list[dict] = []
        while url:
            r = await client.get(url, headers=self._auth_headers())
            r.raise_for_status()
            data = r.json()
            for item in data.get("value", []):
                if field_map:
                    item = {k: item.get(v) for k, v in field_map.items()}
                items.append({"_type": tag, **item})
            url = data.get("@odata.nextLink")
        return items

    async def _collect_teams(self, client: httpx.AsyncClient) -> list[dict]:
        """
        Use the Groups endpoint filtered to Teams-provisioned groups.
        $filter on resourceProvisioningOptions is supported at v1.0.
        """
        url = (
            f"{_GRAPH}/groups"
            "?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')"
            "&$select=id,displayName,description,visibility,createdDateTime"
            "&$top=100"
        )
        items: list[dict] = []
        while url:
            r = await client.get(url, headers=self._auth_headers())
            r.raise_for_status()
            data = r.json()
            for grp in data.get("value", []):
                items.append({
                    "_type": "team",
                    "id": grp.get("id"),
                    "displayName": grp.get("displayName"),
                    "description": grp.get("description"),
                    "visibility": grp.get("visibility"),
                    "createdDateTime": grp.get("createdDateTime"),
                })
            url = data.get("@odata.nextLink")
        return items

    async def _collect_all_members(
        self, client: httpx.AsyncClient, teams: list[dict]
    ) -> list[dict]:
        """
        For each team, collect its members.  Failures per-team are caught
        so a single inaccessible team does not abort the entire run.
        """
        all_members: list[dict] = []
        for team in teams:
            team_id = team.get("id")
            team_name = team.get("displayName", "")
            try:
                url = f"{_GRAPH}/groups/{team_id}/members?$top=100"
                while url:
                    r = await client.get(url, headers=self._auth_headers())
                    r.raise_for_status()
                    data = r.json()
                    for m in data.get("value", []):
                        all_members.append({
                            "_type": "member",
                            "team_id": team_id,
                            "team_name": team_name,
                            "displayName": m.get("displayName"),
                            "mail": m.get("mail"),
                            "userType": m.get("userType"),
                            "id": m.get("id"),
                        })
                    url = data.get("@odata.nextLink")
            except httpx.HTTPStatusError as exc:
                # Log and continue; a 403 on a specific team is not fatal
                if exc.response.status_code not in (403, 404):
                    raise
        return all_members

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        url = (
            f"{_GRAPH}/users"
            "?$select=id,displayName,mail,accountEnabled,userType,assignedLicenses,createdDateTime"
            "&$top=100"
        )
        items: list[dict] = []
        while url:
            r = await client.get(url, headers=self._auth_headers())
            r.raise_for_status()
            data = r.json()
            for u in data.get("value", []):
                items.append({
                    "_type": "user",
                    "id": u.get("id"),
                    "displayName": u.get("displayName"),
                    "mail": u.get("mail"),
                    "accountEnabled": u.get("accountEnabled"),
                    "userType": u.get("userType"),
                    "assignedLicenses": u.get("assignedLicenses", []),
                    "createdDateTime": u.get("createdDateTime"),
                })
            url = data.get("@odata.nextLink")
        return items

    # ------------------------------------------------------------------
    # Normalizers
    # ------------------------------------------------------------------

    def _norm_team(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "microsoft_teams",
            "control": "access_control",
            "evidence_type": "teams_teams",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdDateTime") or fallback_ts,
            "data": {
                "display_name": raw.get("displayName"),
                "description": raw.get("description"),
                "visibility": raw.get("visibility"),
                "created_at": raw.get("createdDateTime"),
            },
        }

    def _norm_member(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "microsoft_teams",
            "control": "access_control",
            "evidence_type": "teams_members",
            "source_id": f"{raw.get('team_id', '')}_{raw.get('id', '')}",
            "timestamp": fallback_ts,
            "data": {
                "team_id": raw.get("team_id"),
                "team_name": raw.get("team_name"),
                "display_name": raw.get("displayName"),
                "mail": raw.get("mail"),
                "user_type": raw.get("userType"),
            },
        }

    def _norm_user(self, raw: dict, fallback_ts: str) -> dict:
        return {
            "integration": "microsoft_teams",
            "control": "access_control",
            "evidence_type": "teams_users",
            "source_id": raw.get("id", ""),
            "timestamp": raw.get("createdDateTime") or fallback_ts,
            "data": {
                "display_name": raw.get("displayName"),
                "mail": raw.get("mail"),
                "account_enabled": raw.get("accountEnabled"),
                "user_type": raw.get("userType"),
                "licensed": bool(raw.get("assignedLicenses")),
            },
        }
