"""Okta Verify MFA integration — collects MFA factor enrollment and policy data from Okta."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError


class OktaVerifyIntegration(IntegrationAdapter):
    """
    Okta Verify is Okta's MFA authenticator app. This adapter queries the Okta API
    specifically for MFA factor enrollment, authenticator policies, and device assurance,
    providing dedicated evidence that Okta Verify (TOTP/push) is enforced org-wide.
    """

    def __init__(self):
        self._domain: str | None = None
        self._api_token: str | None = None

    async def connect(self, credentials: dict) -> bool:
        domain = credentials.get("domain", "").strip().rstrip("/")
        api_token = credentials.get("api_token", "").strip()
        if not domain or not api_token:
            raise IntegrationAuthError("Okta domain and API token are required.")
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        headers = {"Authorization": f"SSWS {api_token}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{domain}/api/v1/org", headers=headers)
            if r.status_code == 401:
                raise IntegrationAuthError("Invalid Okta API token.")
            r.raise_for_status()
        self._domain = domain
        self._api_token = api_token
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {"Authorization": f"SSWS {self._api_token}", "Accept": "application/json"}
        async with httpx.AsyncClient(timeout=30) as client:
            policies = await self._collect_mfa_policies(client, headers)
            users_mfa = await self._collect_user_factors(client, headers)
            authenticators = await self._collect_authenticators(client, headers)
        return policies + users_mfa + authenticators

    async def _collect_mfa_policies(self, client, headers) -> list[dict]:
        r = await client.get(
            f"{self._domain}/api/v1/policies",
            headers=headers,
            params={"type": "MFA_ENROLL"},
        )
        r.raise_for_status()
        return [{"_type": "okta_mfa_policy", **p} for p in r.json()]

    async def _collect_user_factors(self, client, headers) -> list[dict]:
        """Sample MFA factor enrollment for active users (first 200)."""
        users_r = await client.get(
            f"{self._domain}/api/v1/users",
            headers=headers,
            params={"filter": 'status eq "ACTIVE"', "limit": 200},
        )
        users_r.raise_for_status()
        records: list[dict] = []
        for user in users_r.json()[:50]:  # Cap at 50 to avoid rate limits
            uid = user["id"]
            fr = await client.get(f"{self._domain}/api/v1/users/{uid}/factors", headers=headers)
            if fr.status_code == 200:
                for factor in fr.json():
                    if factor.get("factorType") in ("token:software:totp", "push"):
                        records.append({"_type": "okta_user_factor", "user_id": uid,
                                        "user_email": user.get("profile", {}).get("email"), **factor})
        return records

    async def _collect_authenticators(self, client, headers) -> list[dict]:
        r = await client.get(f"{self._domain}/api/v1/authenticators", headers=headers)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return [{"_type": "okta_authenticator", **a} for a in r.json()]

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "okta_mfa_policy":
                result.append(self._norm_policy(item))
            elif t == "okta_user_factor":
                result.append(self._norm_factor(item))
            elif t == "okta_authenticator":
                result.append(self._norm_authenticator(item))
        return result

    def _norm_policy(self, raw: dict) -> dict:
        return {
            "integration": "okta_verify",
            "control": "access_control",
            "evidence_type": "mfa_policies",
            "source_id": raw["id"],
            "timestamp": raw.get("lastUpdated", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "name": raw.get("name"),
                "status": raw.get("status"),
                "type": raw.get("type"),
                "description": raw.get("description"),
            },
        }

    def _norm_factor(self, raw: dict) -> dict:
        return {
            "integration": "okta_verify",
            "control": "access_control",
            "evidence_type": "mfa_enrollments",
            "source_id": f"{raw['user_id']}_{raw['id']}",
            "timestamp": raw.get("lastUpdated", datetime.now(timezone.utc).isoformat()),
            "data": {
                "user_id": raw["user_id"],
                "user_email": raw.get("user_email"),
                "factor_id": raw["id"],
                "factor_type": raw.get("factorType"),
                "provider": raw.get("provider"),
                "status": raw.get("status"),
            },
        }

    def _norm_authenticator(self, raw: dict) -> dict:
        return {
            "integration": "okta_verify",
            "control": "access_control",
            "evidence_type": "okta_authenticators",
            "source_id": raw["id"],
            "timestamp": raw.get("lastUpdated", datetime.now(timezone.utc).isoformat()),
            "data": {
                "id": raw["id"],
                "key": raw.get("key"),
                "name": raw.get("name"),
                "type": raw.get("type"),
                "status": raw.get("status"),
            },
        }
