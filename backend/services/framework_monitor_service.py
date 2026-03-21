from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.framework_source_manifest import FrameworkSourceManifest
from models.framework_update_request import FrameworkUpdateRequest

logger = logging.getLogger(__name__)


async def check_all_frameworks(db: AsyncSession) -> list[dict]:
    """Loop over all FrameworkSourceManifest rows and check each for updates.

    Returns a list of result dicts, one per manifest.
    """
    result = await db.execute(select(FrameworkSourceManifest))
    manifests = result.scalars().all()

    results: list[dict] = []
    for manifest in manifests:
        try:
            outcome = await check_framework(manifest, db)
        except Exception as exc:
            logger.warning(
                "Unexpected error checking framework %s: %s",
                manifest.framework_key,
                exc,
                exc_info=True,
            )
            outcome = {
                "framework": manifest.framework_key,
                "changed": False,
                "old_hash": manifest.last_hash,
                "new_hash": None,
                "error": str(exc),
            }
        results.append(outcome)

    return results


async def check_framework(manifest: FrameworkSourceManifest, db: AsyncSession) -> dict:
    """Fetch the manifest source URL, hash the content, and record any change.

    Strategy: try HEAD first; if the server does not return a body fall back to
    a full GET.  Both requests use a 30-second timeout.

    Returns::

        {
            "framework": str,
            "changed": bool,
            "old_hash": str | None,
            "new_hash": str,
        }
    """
    framework_key: str = manifest.framework_key
    source_url: str = manifest.source_url
    old_hash: Optional[str] = manifest.last_hash
    new_hash: Optional[str] = None

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            # Try HEAD first to avoid downloading large files unnecessarily.
            head_response = await client.head(source_url, timeout=30)
            head_response.raise_for_status()

            if head_response.content:
                content = head_response.content
            else:
                # HEAD gave no body — fall back to GET.
                get_response = await client.get(source_url, timeout=30)
                get_response.raise_for_status()
                content = get_response.content

        new_hash = hashlib.sha256(content).hexdigest()

    except httpx.HTTPError as exc:
        logger.warning(
            "HTTP error while checking framework %s at %s: %s",
            framework_key,
            source_url,
            exc,
        )
        # Still update last_checked_at so we don't hammer a broken URL.
        manifest.last_checked_at = datetime.now(timezone.utc)
        await db.commit()
        return {
            "framework": framework_key,
            "changed": False,
            "old_hash": old_hash,
            "new_hash": None,
        }

    now = datetime.now(timezone.utc)
    changed = new_hash != old_hash

    if changed:
        manifest.pending_update = True
        manifest.pending_update_detected_at = now

        update_request = FrameworkUpdateRequest(
            id=uuid.uuid4(),
            framework_key=framework_key,
            detected_at=now,
            source_url=source_url,
            new_hash=new_hash,
            old_hash=old_hash,
            status="pending",
        )
        db.add(update_request)

        slack_webhook: Optional[str] = None
        try:
            from core.config import settings  # local import to avoid circular deps

            # Only use a Slack webhook if one is wired up via a future config field.
            # Currently the Settings model has no framework-specific webhook; we
            # accept None here and _send_slack_alert will skip gracefully.
            slack_webhook = getattr(settings, "framework_slack_webhook_url", None) or None
        except Exception:
            pass

        await _send_slack_alert(framework_key, source_url, slack_webhook)

    manifest.last_checked_at = now
    manifest.last_hash = new_hash

    await db.commit()

    return {
        "framework": framework_key,
        "changed": changed,
        "old_hash": old_hash,
        "new_hash": new_hash,
    }


async def _send_slack_alert(
    framework_key: str,
    source_url: str,
    webhook_url: Optional[str],
) -> None:
    """POST a Slack alert to webhook_url if provided. Errors are swallowed."""
    if not webhook_url:
        return

    payload = {
        "text": (
            f"\u26a0\ufe0f Framework update detected: {framework_key}. "
            f"Source: {source_url}. "
            "Review at /admin/framework-updates"
        )
    }

    try:
        async with httpx.AsyncClient() as client:
            await client.post(webhook_url, json=payload, timeout=10)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to send Slack alert for framework %s: %s", framework_key, exc)


async def get_pending_requests(db: AsyncSession) -> list[FrameworkUpdateRequest]:
    """Return all FrameworkUpdateRequest rows with status='pending', newest first."""
    result = await db.execute(
        select(FrameworkUpdateRequest)
        .where(FrameworkUpdateRequest.status == "pending")
        .order_by(FrameworkUpdateRequest.detected_at.desc())
    )
    return list(result.scalars().all())


async def approve_request(
    request_id: uuid.UUID,
    reviewed_by: str,
    notes: Optional[str],
    db: AsyncSession,
) -> FrameworkUpdateRequest:
    """Mark a FrameworkUpdateRequest as approved.

    Raises ValueError if the request is not found.
    """
    result = await db.execute(
        select(FrameworkUpdateRequest).where(FrameworkUpdateRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise ValueError(f"FrameworkUpdateRequest {request_id} not found")

    request.status = "approved"
    request.reviewed_by = reviewed_by
    request.reviewed_at = datetime.now(timezone.utc)
    request.review_notes = notes

    await db.commit()
    await db.refresh(request)
    return request


async def reject_request(
    request_id: uuid.UUID,
    reviewed_by: str,
    notes: Optional[str],
    db: AsyncSession,
) -> FrameworkUpdateRequest:
    """Mark a FrameworkUpdateRequest as rejected.

    Raises ValueError if the request is not found.
    """
    result = await db.execute(
        select(FrameworkUpdateRequest).where(FrameworkUpdateRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if request is None:
        raise ValueError(f"FrameworkUpdateRequest {request_id} not found")

    request.status = "rejected"
    request.reviewed_by = reviewed_by
    request.reviewed_at = datetime.now(timezone.utc)
    request.review_notes = notes

    await db.commit()
    await db.refresh(request)
    return request
