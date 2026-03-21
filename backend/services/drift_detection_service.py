from __future__ import annotations

"""
Compliance drift detection — runs after each evidence collection.

Compares the newly computed control statuses against cached snapshots.
On regression (status degraded), creates a ControlDriftEvent record and
fires an immediate Slack / Teams / email alert.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from models.company import Company
from models.control_drift_event import ControlDriftEvent
from models.control_status_snapshot import ControlStatusSnapshot

logger = logging.getLogger(__name__)

# Lower number = better status
STATUS_ORDER: dict[str, int] = {
    "passing":     0,
    "warning":     1,
    "failing":     2,
    "no_evidence": 3,
}

FRAMEWORKS = ["soc2", "iso27001", "hipaa", "gdpr", "pci_dss", "ccpa", "nist_csf"]

DEFAULT_PREFS = {"compliance_drift": True}


async def run_drift_detection(
    company_id: uuid.UUID,
    trigger_integration: str,
    db: AsyncSession,
) -> list[ControlDriftEvent]:
    """
    Run drift detection for one company after a collection cycle.

    Returns all ControlDriftEvent rows created (regressions + recoveries).
    """
    from services.compliance_service import get_compliance_score

    # Load all existing snapshots for this company into a lookup dict
    snapshot_rows = await db.execute(
        select(ControlStatusSnapshot).where(
            ControlStatusSnapshot.company_id == company_id
        )
    )
    snapshots: dict[tuple[str, str], ControlStatusSnapshot] = {
        (s.framework, s.control_category): s
        for s in snapshot_rows.scalars().all()
    }

    now = datetime.now(timezone.utc)
    drift_events: list[ControlDriftEvent] = []
    regressions: list[ControlDriftEvent] = []

    for framework in FRAMEWORKS:
        try:
            score_data = await get_compliance_score(company_id, framework, db)
        except Exception as exc:
            logger.warning(
                "Drift detection: failed to get compliance score for company=%s framework=%s: %s",
                company_id, framework, exc,
            )
            continue

        for control in score_data.get("controls", []):
            category: str = control["category"]
            name: str = control["name"]
            new_status: str = control["status"]
            new_score: int = control["score"]

            key = (framework, category)
            snapshot = snapshots.get(key)

            if snapshot is None:
                # First time we've seen this control — create a baseline snapshot
                new_snapshot = ControlStatusSnapshot(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    framework=framework,
                    control_category=category,
                    status=new_status,
                    score=new_score,
                    updated_at=now,
                )
                db.add(new_snapshot)
                snapshots[key] = new_snapshot
                continue

            previous_status: str = snapshot.status

            if new_status == previous_status:
                # No status change — just refresh the score and timestamp
                snapshot.score = new_score
                snapshot.updated_at = now
                continue

            # Status changed — create a drift event
            is_regression = (
                STATUS_ORDER.get(new_status, 99) > STATUS_ORDER.get(previous_status, 99)
            )
            event = ControlDriftEvent(
                id=uuid.uuid4(),
                company_id=company_id,
                framework=framework,
                control_category=category,
                control_name=name,
                previous_status=previous_status,
                new_status=new_status,
                is_regression=is_regression,
                trigger_integration=trigger_integration,
                detected_at=now,
                alerted_at=None,
            )
            db.add(event)
            drift_events.append(event)

            if is_regression:
                regressions.append(event)

            # Update the snapshot to reflect the new status
            snapshot.status = new_status
            snapshot.score = new_score
            snapshot.updated_at = now

    await db.commit()

    if regressions:
        await _fire_drift_alerts(company_id, regressions, trigger_integration, db)

    return drift_events


async def _fire_drift_alerts(
    company_id: uuid.UUID,
    regressions: list[ControlDriftEvent],
    trigger_integration: str,
    db: AsyncSession,
) -> None:
    """Fire Slack / Teams alerts for control regressions."""
    company_result = await db.execute(
        select(Company).where(Company.id == company_id)
    )
    company = company_result.scalar_one_or_none()
    if not company:
        return

    prefs = {**DEFAULT_PREFS, **(company.notification_prefs or {})}
    if not prefs.get("compliance_drift", True):
        return

    # Build the human-readable message
    bullet_lines = "\n".join(
        f"• {e.control_name} ({e.framework.upper()}) — {e.previous_status} → {e.new_status}"
        for e in regressions
    )
    message = (
        f"⚠️ Compliance drift detected — {company.name}\n\n"
        f"The following controls degraded after collecting from {trigger_integration}:\n\n"
        f"{bullet_lines}\n\n"
        f"Review at: {settings.app_frontend_url}/dashboard"
    )

    # Slack
    if company.slack_webhook_url:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    company.slack_webhook_url,
                    json={"text": message},
                    timeout=10,
                )
        except Exception as exc:
            logger.warning(
                "Failed to send drift Slack alert for company %s: %s", company_id, exc
            )

    # Teams (Adaptive Card)
    if company.teams_webhook_url:
        try:
            facts = [
                {
                    "title": f"{e.control_name} ({e.framework.upper()})",
                    "value": f"{e.previous_status} → {e.new_status}",
                }
                for e in regressions
            ]
            payload = {
                "type": "message",
                "attachments": [{
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "TextBlock",
                                "text": f"⚠️ Compliance drift detected — {company.name}",
                                "weight": "bolder",
                                "size": "medium",
                            },
                            {
                                "type": "TextBlock",
                                "text": f"Controls degraded after collecting from {trigger_integration}:",
                                "wrap": True,
                            },
                            {"type": "FactSet", "facts": facts},
                            {
                                "type": "TextBlock",
                                "text": f"Review at: {settings.app_frontend_url}/dashboard",
                                "wrap": True,
                            },
                        ],
                    },
                }],
            }
            async with httpx.AsyncClient() as client:
                await client.post(
                    company.teams_webhook_url,
                    json=payload,
                    timeout=10,
                )
        except Exception as exc:
            logger.warning(
                "Failed to send drift Teams alert for company %s: %s", company_id, exc
            )

    # Mark alert timestamp on each regression event
    now = datetime.now(timezone.utc)
    for event in regressions:
        event.alerted_at = now

    await db.commit()
