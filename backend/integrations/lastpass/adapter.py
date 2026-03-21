"""
LastPass integration via LastPass Enterprise API.

Credentials:
  cid       — LastPass account number (Customer ID)
  provhash  — LastPass provisioning hash
"""
import logging
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

logger = logging.getLogger(__name__)

_API_URL = "https://lastpass.com/enterpriseapi.php"


class LastPassIntegration(IntegrationAdapter):

    def __init__(self):
        self._cid: str | None = None
        self._provhash: str | None = None

    def _payload(self, cmd: str, data: dict) -> dict:
        return {
            "cid": self._cid,
            "provhash": self._provhash,
            "cmd": cmd,
            "data": data,
        }

    # ── Connect ────────────────────────────────────────────────────────────────

    async def connect(self, credentials: dict) -> bool:
        cid = credentials.get("cid", "").strip()
        provhash = credentials.get("provhash", "").strip()

        if not cid or not provhash:
            raise IntegrationAuthError("cid and provhash are required.")

        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                _API_URL,
                json={
                    "cid": cid,
                    "provhash": provhash,
                    "cmd": "getuserdata",
                    "data": {"limit": 1},
                },
            )
            if r.status_code != 200:
                raise IntegrationAuthError(f"LastPass connect failed HTTP {r.status_code}")
            body = r.json()
            if body.get("status") == "FAIL":
                raise IntegrationAuthError(f"LastPass auth rejected: {body.get('error', 'unknown error')}")

        self._cid = cid
        self._provhash = provhash
        return True

    # ── Collect ────────────────────────────────────────────────────────────────

    async def collect_evidence(self) -> list[dict]:
        results: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for fetch_fn in (
                self._collect_users,
                self._collect_shared_folders,
                self._collect_groups,
                self._collect_dashboard,
            ):
                try:
                    items = await fetch_fn(client)
                    results.extend(items)
                except Exception as exc:
                    logger.warning("LastPass collection error in %s: %s", fetch_fn.__name__, exc)
                    results.append({"_type": "error", "_source": fetch_fn.__name__, "_error": str(exc)})

        return results

    async def _collect_users(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.post(_API_URL, json=self._payload("getuserdata", {}))
        if r.status_code != 200:
            raise RuntimeError(f"LastPass getuserdata HTTP {r.status_code}")
        body = r.json()
        users = body.get("Users", {})
        return [{"_type": "user", **u} for u in users.values()]

    async def _collect_shared_folders(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.post(_API_URL, json=self._payload("getSharedFolderData", {}))
        if r.status_code != 200:
            raise RuntimeError(f"LastPass getSharedFolderData HTTP {r.status_code}")
        body = r.json()
        folders = body.get("SharedFolders", {})
        return [{"_type": "shared_folder", **f} for f in folders.values()]

    async def _collect_groups(self, client: httpx.AsyncClient) -> list[dict]:
        r = await client.post(_API_URL, json=self._payload("getGroupData", {}))
        if r.status_code != 200:
            raise RuntimeError(f"LastPass getGroupData HTTP {r.status_code}")
        body = r.json()
        groups = body.get("Groups", {})
        return [{"_type": "group", **g} for g in groups.values()]

    async def _collect_dashboard(self, client: httpx.AsyncClient) -> list[dict]:
        # Best-effort — failures are silently skipped
        r = await client.post(
            _API_URL,
            json=self._payload("reporting", {"cmd": "getUserDetails", "UserName": ""}),
        )
        if r.status_code != 200:
            logger.warning("LastPass reporting/getUserDetails returned HTTP %s — skipping", r.status_code)
            return []
        body = r.json()
        if body.get("status") == "FAIL":
            logger.warning("LastPass reporting/getUserDetails FAIL — skipping")
            return []
        return []

    # ── Normalize ──────────────────────────────────────────────────────────────

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "user":
                result.append(self._norm_user(item))
            elif t == "shared_folder":
                result.append(self._norm_shared_folder(item))
            elif t == "group":
                result.append(self._norm_group(item))
        return result

    def _norm_user(self, raw: dict) -> dict:
        return {
            "integration": "lastpass",
            "control": "access_control",
            "evidence_type": "lastpass_users",
            "source_id": str(raw.get("username", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "username": raw.get("username"),
                "fullname": raw.get("fullname"),
                "mpstrength": raw.get("mpstrength"),
                "sites": raw.get("sites"),
                "notes": raw.get("notes"),
                "formfills": raw.get("formfills"),
                "applications": raw.get("applications"),
                "attachments": raw.get("attachments"),
                "neverloggedin": raw.get("neverloggedin"),
                "disabled": raw.get("disabled"),
                "admin": raw.get("admin"),
                "totalscore": raw.get("totalscore"),
                "mobiledevices": raw.get("mobiledevices"),
            },
        }

    def _norm_shared_folder(self, raw: dict) -> dict:
        return {
            "integration": "lastpass",
            "control": "access_control",
            "evidence_type": "lastpass_shared_folders",
            "source_id": str(raw.get("sharedfoldername", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "sharedfoldername": raw.get("sharedfoldername"),
                "score": raw.get("score"),
                "readonly": raw.get("readonly"),
                "give": raw.get("give"),
                "can_administer": raw.get("can_administer"),
            },
        }

    def _norm_group(self, raw: dict) -> dict:
        return {
            "integration": "lastpass",
            "control": "access_control",
            "evidence_type": "lastpass_groups",
            "source_id": str(raw.get("groupname", "")),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "groupname": raw.get("groupname"),
                "usernames": raw.get("users", []),
            },
        }
