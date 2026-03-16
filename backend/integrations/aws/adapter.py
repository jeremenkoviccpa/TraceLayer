import asyncio
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from integrations.base import IntegrationAdapter, IntegrationAuthError


def _serialize(obj):
    """Recursively convert datetime/date objects in dicts for JSON storage."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return obj


class AWSIntegration(IntegrationAdapter):

    def __init__(self):
        self._session = None

    async def connect(self, credentials: dict) -> bool:
        loop = asyncio.get_event_loop()
        try:
            session = boto3.Session(
                aws_access_key_id=credentials["access_key_id"],
                aws_secret_access_key=credentials["secret_access_key"],
                region_name=credentials.get("region", "us-east-1"),
            )
            await loop.run_in_executor(
                None, lambda: session.client("sts").get_caller_identity()
            )
            self._session = session
            return True
        except (ClientError, NoCredentialsError) as e:
            raise IntegrationAuthError(str(e))

    async def collect_evidence(self) -> list[dict]:
        loop = asyncio.get_event_loop()
        results = await asyncio.gather(
            loop.run_in_executor(None, self._sync_collect_iam_users),
            loop.run_in_executor(None, self._sync_collect_iam_policies),
            loop.run_in_executor(None, self._sync_collect_cloudtrail_logs),
        )
        combined = []
        for batch in results:
            combined.extend(batch)
        return combined

    def _sync_collect_iam_users(self) -> list[dict]:
        iam = self._session.client("iam")
        users = []
        paginator = iam.get_paginator("list_users")
        for page in paginator.paginate():
            users.extend(page["Users"])

        # Enrich with MFA status
        for user in users:
            try:
                mfa = iam.list_mfa_devices(UserName=user["UserName"])
                user["_mfa_enabled"] = len(mfa["MFADevices"]) > 0
            except ClientError:
                user["_mfa_enabled"] = False

        return [{"_type": "iam_user", **_serialize(u)} for u in users]

    def _sync_collect_iam_policies(self) -> list[dict]:
        iam = self._session.client("iam")
        policies = []
        paginator = iam.get_paginator("list_policies")
        for page in paginator.paginate(Scope="Local"):
            policies.extend(page["Policies"])
        return [{"_type": "iam_policy", **_serialize(p)} for p in policies]

    def _sync_collect_cloudtrail_logs(self) -> list[dict]:
        ct = self._session.client("cloudtrail")
        try:
            response = ct.lookup_events(MaxResults=100)
            return [{"_type": "cloudtrail_event", **_serialize(e)} for e in response.get("Events", [])]
        except ClientError:
            return []

    def normalize(self, raw_data: list[dict]) -> list[dict]:
        result = []
        for item in raw_data:
            t = item.get("_type")
            if t == "iam_user":
                result.append(self._norm_iam_user(item))
            elif t == "iam_policy":
                result.append(self._norm_iam_policy(item))
            elif t == "cloudtrail_event":
                result.append(self._norm_cloudtrail(item))
        return result

    def _norm_iam_user(self, raw: dict) -> dict:
        return {
            "integration": "aws",
            "control": "access_control",
            "evidence_type": "iam_users",
            "source_id": raw["Arn"],
            "timestamp": raw.get("CreateDate", datetime.now(timezone.utc).isoformat()),
            "data": {
                "username": raw["UserName"],
                "arn": raw["Arn"],
                "user_id": raw["UserId"],
                "path": raw["Path"],
                "mfa_enabled": raw.get("_mfa_enabled", False),
                "password_last_used": raw.get("PasswordLastUsed"),
                "created_at": raw.get("CreateDate"),
            },
        }

    def _norm_iam_policy(self, raw: dict) -> dict:
        return {
            "integration": "aws",
            "control": "access_control",
            "evidence_type": "iam_policies",
            "source_id": raw["Arn"],
            "timestamp": raw.get("CreateDate", datetime.now(timezone.utc).isoformat()),
            "data": {
                "policy_name": raw["PolicyName"],
                "arn": raw["Arn"],
                "attachment_count": raw.get("AttachmentCount", 0),
                "description": raw.get("Description", ""),
                "created_at": raw.get("CreateDate"),
            },
        }

    def _norm_cloudtrail(self, raw: dict) -> dict:
        return {
            "integration": "aws",
            "control": "logging_monitoring",
            "evidence_type": "cloudtrail_logs",
            "source_id": raw.get("EventId", raw.get("EventName", "")),
            "timestamp": raw.get("EventTime", datetime.now(timezone.utc).isoformat()),
            "data": {
                "event_name": raw.get("EventName"),
                "event_source": raw.get("EventSource"),
                "username": raw.get("Username"),
                "event_time": raw.get("EventTime"),
                "resources": raw.get("Resources", []),
            },
        }
