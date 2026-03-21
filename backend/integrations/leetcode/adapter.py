"""LeetCode Business integration — collects assessments, candidates, and completion records."""
from datetime import datetime, timezone

import httpx

from integrations.base import IntegrationAdapter, IntegrationAuthError

LEETCODE_API = "https://leetcode.com/graphql"
LEETCODE_BUSINESS_API = "https://leetcode.com/api"


class LeetCodeIntegration(IntegrationAdapter):
    """
    LeetCode Business provides API access for enterprise assessment management.
    Uses session-based authentication with a CSRF token.
    """

    def __init__(self):
        self._session_cookie: str | None = None
        self._csrf_token: str | None = None
        self._org_slug: str | None = None

    async def connect(self, credentials: dict) -> bool:
        session = credentials.get("session_cookie", "").strip()
        csrf = credentials.get("csrf_token", "").strip()
        org_slug = credentials.get("org_slug", "").strip()
        if not session or not csrf:
            raise IntegrationAuthError("Session cookie and CSRF token are required.")
        headers = {
            "Cookie": f"LEETCODE_SESSION={session}; csrftoken={csrf}",
            "X-CSRFToken": csrf,
            "Referer": "https://leetcode.com",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                LEETCODE_API,
                headers=headers,
                json={"query": "{ user { username } }"},
            )
            if r.status_code == 401 or (r.status_code == 200 and not r.json().get("data", {}).get("user")):
                raise IntegrationAuthError("Invalid LeetCode session. Please provide a valid LEETCODE_SESSION cookie.")
            r.raise_for_status()
        self._session_cookie = session
        self._csrf_token = csrf
        self._org_slug = org_slug
        return True

    async def collect_evidence(self) -> list[dict]:
        headers = {
            "Cookie": f"LEETCODE_SESSION={self._session_cookie}; csrftoken={self._csrf_token}",
            "X-CSRFToken": self._csrf_token,
            "Referer": "https://leetcode.com",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            assessments = await self._collect_assessments(client, headers)
            profile = await self._collect_profile(client, headers)
        return assessments + profile

    async def _collect_assessments(self, client, headers) -> list[dict]:
        query = """
        query assessmentList($skip: Int!, $first: Int!) {
          assessmentList(skip: $skip, first: $first) {
            total
            assessments {
              id
              title
              state
              startTime
              endTime
              duration
              totalQuestions
              totalParticipants
            }
          }
        }
        """
        items: list[dict] = []
        skip = 0
        first = 20
        while True:
            r = await client.post(
                LEETCODE_API,
                headers=headers,
                json={"query": query, "variables": {"skip": skip, "first": first}},
            )
            r.raise_for_status()
            data = r.json().get("data", {}).get("assessmentList", {})
            batch = data.get("assessments", [])
            if not batch:
                break
            items.extend([{"_type": "leetcode_assessment", **a} for a in batch])
            skip += first
            if skip >= data.get("total", 0):
                break
        return items

    async def _collect_profile(self, client, headers) -> list[dict]:
        query = "{ user { username userSlug realName } }"
        r = await client.post(LEETCODE_API, headers=headers, json={"query": query})
        r.raise_for_status()
        user = r.json().get("data", {}).get("user", {})
        if user:
            return [{"_type": "leetcode_account", **user}]
        return []

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "leetcode_assessment":
                result.append(self._norm_assessment(item))
            elif t == "leetcode_account":
                result.append(self._norm_account(item))
        return result

    def _norm_assessment(self, raw: dict) -> dict:
        start = raw.get("startTime")
        ts = (
            datetime.fromtimestamp(int(start), tz=timezone.utc).isoformat()
            if start
            else datetime.now(timezone.utc).isoformat()
        )
        return {
            "integration": "leetcode",
            "control": "hr_security",
            "evidence_type": "leetcode_assessments",
            "source_id": str(raw["id"]),
            "timestamp": ts,
            "data": {
                "id": raw["id"],
                "title": raw.get("title"),
                "state": raw.get("state"),
                "duration": raw.get("duration"),
                "total_questions": raw.get("totalQuestions"),
                "total_participants": raw.get("totalParticipants"),
                "start_time": ts,
                "end_time": raw.get("endTime"),
            },
        }

    def _norm_account(self, raw: dict) -> dict:
        return {
            "integration": "leetcode",
            "control": "hr_security",
            "evidence_type": "leetcode_account",
            "source_id": raw.get("userSlug", "account"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "username": raw.get("username"),
                "user_slug": raw.get("userSlug"),
                "real_name": raw.get("realName"),
            },
        }
