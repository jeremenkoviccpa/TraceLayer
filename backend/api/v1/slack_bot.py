import asyncio
import json
import urllib.request
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.device import Device
from models.policy import Policy
from models.policy_signature import PolicySignature
from models.slack_config import SlackConfig
from models.user import User

router = APIRouter(prefix="/slack", tags=["slack"])

APP_URL = "https://tracelayer.it.com"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _post_to_slack_sync(webhook_url: str, payload: dict) -> bool:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False


async def _post_to_slack(webhook_url: str, payload: dict) -> bool:
    return await asyncio.get_event_loop().run_in_executor(
        None, _post_to_slack_sync, webhook_url, payload
    )


async def _build_reminder_payload(company_id, db: AsyncSession) -> dict:
    """Count pending tasks across all company users and build Slack blocks."""
    users_result = await db.execute(
        select(User).where(User.company_id == company_id)
    )
    users = users_result.scalars().all()

    policies_result = await db.execute(
        select(Policy).where(Policy.company_id == company_id, Policy.content != "")
    )
    policies = policies_result.scalars().all()

    unsigned_count = 0
    unattested_count = 0

    for user in users:
        # Count unsigned policies
        for policy in policies:
            sig_result = await db.execute(
                select(PolicySignature).where(
                    PolicySignature.policy_id == policy.id,
                    PolicySignature.user_id == user.id,
                )
            )
            if not sig_result.scalar_one_or_none():
                unsigned_count += 1

        # Check device attestation
        dev_result = await db.execute(
            select(Device).where(Device.user_id == user.id)
        )
        if not dev_result.scalar_one_or_none():
            unattested_count += 1

    pending_total = unsigned_count + unattested_count
    if pending_total == 0:
        fields = [{"type": "mrkdwn", "text": "✅ *All tasks complete!*\nYour team is fully up to date."}]
    else:
        fields = []
        if unsigned_count:
            fields.append({"type": "mrkdwn", "text": f"📋 *{unsigned_count} unsigned {'policy' if unsigned_count == 1 else 'policies'}*\nTeam members need to review and sign."})
        if unattested_count:
            fields.append({"type": "mrkdwn", "text": f"💻 *{unattested_count} unattested {'device' if unattested_count == 1 else 'devices'}*\nEmployees need to confirm security settings."})

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": "🔒 TraceLayer Compliance Reminder", "emoji": True}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Your team has *{pending_total} pending compliance {'task' if pending_total == 1 else 'tasks'}*. Ask everyone to check their portal." if pending_total else "Your team is fully compliant — no pending tasks! 🎉",
            },
        },
    ]
    if fields:
        blocks.append({"type": "section", "fields": fields})
    blocks.append({
        "type": "section",
        "text": {"type": "mrkdwn", "text": f"→ *<{APP_URL}/portal|Open the compliance portal>*"},
    })
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"Sent by TraceLayer · {datetime.now(timezone.utc).strftime('%B %d, %Y')}"}],
    })
    return {"blocks": blocks}


# ── Schemas ────────────────────────────────────────────────────────────────────

class SlackConfigOut(BaseModel):
    webhook_url: str
    channel_name: Optional[str]
    reminder_enabled: bool
    last_sent_at: Optional[str]


class SlackConfigIn(BaseModel):
    webhook_url: str
    channel_name: Optional[str] = None
    reminder_enabled: bool = True


class SlackActionResponse(BaseModel):
    ok: bool
    message: str


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/config", response_model=Optional[SlackConfigOut])
async def get_slack_config(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SlackConfig).where(SlackConfig.company_id == current_user.company_id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        return None
    return SlackConfigOut(
        webhook_url=cfg.webhook_url,
        channel_name=cfg.channel_name,
        reminder_enabled=cfg.reminder_enabled,
        last_sent_at=cfg.last_sent_at.isoformat() if cfg.last_sent_at else None,
    )


@router.put("/config", response_model=SlackConfigOut)
async def save_slack_config(
    body: SlackConfigIn,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SlackConfig).where(SlackConfig.company_id == current_user.company_id)
    )
    cfg = result.scalar_one_or_none()
    if cfg:
        cfg.webhook_url = body.webhook_url
        cfg.channel_name = body.channel_name
        cfg.reminder_enabled = body.reminder_enabled
        cfg.updated_at = datetime.now(timezone.utc)
    else:
        cfg = SlackConfig(
            company_id=current_user.company_id,
            webhook_url=body.webhook_url,
            channel_name=body.channel_name,
            reminder_enabled=body.reminder_enabled,
        )
        db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return SlackConfigOut(
        webhook_url=cfg.webhook_url,
        channel_name=cfg.channel_name,
        reminder_enabled=cfg.reminder_enabled,
        last_sent_at=cfg.last_sent_at.isoformat() if cfg.last_sent_at else None,
    )


@router.post("/test", response_model=SlackActionResponse)
async def test_slack_webhook(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SlackConfig).where(SlackConfig.company_id == current_user.company_id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=400, detail="No Slack webhook configured")

    payload = {
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "✅ TraceLayer — Webhook connected!", "emoji": True}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Your Slack integration is working. Compliance reminders will be sent to this channel."}},
        ]
    }
    ok = await _post_to_slack(cfg.webhook_url, payload)
    if not ok:
        return SlackActionResponse(ok=False, message="Webhook delivery failed — check the URL and try again")
    return SlackActionResponse(ok=True, message="Test message sent successfully")


@router.post("/send-reminders", response_model=SlackActionResponse)
async def send_slack_reminders(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SlackConfig).where(SlackConfig.company_id == current_user.company_id)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        raise HTTPException(status_code=400, detail="No Slack webhook configured")

    payload = await _build_reminder_payload(current_user.company_id, db)
    ok = await _post_to_slack(cfg.webhook_url, payload)
    if not ok:
        return SlackActionResponse(ok=False, message="Failed to send reminders — check your webhook URL")

    cfg.last_sent_at = datetime.now(timezone.utc)
    await db.commit()
    channel = f" to {cfg.channel_name}" if cfg.channel_name else ""
    return SlackActionResponse(ok=True, message=f"Reminders sent{channel} successfully")
