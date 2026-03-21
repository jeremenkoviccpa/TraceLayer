import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.ai_agent_event import AiAgentEvent
from models.api_key import ApiKey
from models.user import User
from schemas.ai_agent_event import (
    AiAgentEventCreate,
    AiAgentEventResponse,
    AiAgentEventUpdate,
    AiAgentSessionResponse,
)
from services.ai_agent_risk_service import compute_risk, infer_risk_flags

router = APIRouter(prefix="/ai-agent-events", tags=["ai-agent-events"])


def _to_response(e: AiAgentEvent) -> AiAgentEventResponse:
    return AiAgentEventResponse(
        id=str(e.id),
        company_id=str(e.company_id),
        agent_name=e.agent_name,
        agent_type=e.agent_type,
        action_type=e.action_type,
        target_tool=e.target_tool,
        target_url=e.target_url,
        data_categories=e.data_categories or [],
        input_summary=e.input_summary,
        output_summary=e.output_summary,
        session_id=e.session_id,
        chain_depth=e.chain_depth,
        parent_event_id=str(e.parent_event_id) if e.parent_event_id else None,
        risk_level=e.risk_level,
        risk_flags=e.risk_flags or [],
        status=e.status,
        duration_ms=e.duration_ms,
        is_flagged=e.is_flagged,
        reviewed_by=e.reviewed_by,
        reviewed_at=e.reviewed_at,
        notes=e.notes,
        created_at=e.created_at,
    )


def _risk_order(level: str) -> int:
    return {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(level, 0)


@router.get("", response_model=list[AiAgentEventResponse])
async def list_events(
    risk_level: Optional[str] = Query(None),
    agent_type: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    flagged_only: bool = Query(False),
    session_id: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(AiAgentEvent).where(AiAgentEvent.company_id == current_user.company_id)
    if risk_level:
        q = q.where(AiAgentEvent.risk_level == risk_level)
    if agent_type:
        q = q.where(AiAgentEvent.agent_type == agent_type)
    if action_type:
        q = q.where(AiAgentEvent.action_type == action_type)
    if flagged_only:
        q = q.where(AiAgentEvent.is_flagged.is_(True))
    if session_id:
        q = q.where(AiAgentEvent.session_id == session_id)
    q = q.order_by(desc(AiAgentEvent.created_at)).limit(limit)
    result = await db.execute(q)
    return [_to_response(e) for e in result.scalars().all()]


@router.get("/sessions", response_model=list[AiAgentSessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns events grouped by session_id for chain visualization."""
    result = await db.execute(
        select(AiAgentEvent)
        .where(
            AiAgentEvent.company_id == current_user.company_id,
            AiAgentEvent.session_id.isnot(None),
        )
        .order_by(desc(AiAgentEvent.created_at))
        .limit(500)
    )
    events = result.scalars().all()

    sessions: dict[str, list[AiAgentEvent]] = {}
    for e in events:
        sessions.setdefault(e.session_id, []).append(e)  # type: ignore[arg-type]

    out: list[AiAgentSessionResponse] = []
    for sid, evts in sessions.items():
        risk_levels = [e.risk_level for e in evts]
        out.append(AiAgentSessionResponse(
            session_id=sid,
            events=[_to_response(e) for e in evts],
            max_chain_depth=max(e.chain_depth for e in evts),
            max_risk_level=max(risk_levels, key=_risk_order),
            total_events=len(evts),
        ))
    return out


@router.post("", response_model=AiAgentEventResponse, status_code=201)
async def create_event(
    body: AiAgentEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually log an AI agent event from the dashboard."""
    return await _persist_event(body, current_user.company_id, db)


@router.post("/ingest", response_model=AiAgentEventResponse, status_code=201)
async def ingest_event(
    body: AiAgentEventCreate,
    db: AsyncSession = Depends(get_db),
):
    """Ingest endpoint for AI agents to self-report actions. Authenticated by API key in Authorization header."""
    import hashlib
    from fastapi import Request
    from fastapi.security.utils import get_authorization_scheme_param
    import starlette.requests

    # We can't use Depends here without a Request — handled manually
    raise HTTPException(status_code=501, detail="Use POST /v1/ai-agent-events/ingest-key")


@router.post("/ingest-key", response_model=AiAgentEventResponse, status_code=201)
async def ingest_event_with_key(
    body: AiAgentEventCreate,
    api_key: str = Query(..., alias="key"),
    db: AsyncSession = Depends(get_db),
):
    """Agents self-report via ?key=<raw_api_key>. Matches the existing API key system."""
    import hashlib
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked.is_(False))
    )
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    return await _persist_event(body, api_key_obj.company_id, db)


async def _persist_event(
    body: AiAgentEventCreate,
    company_id: uuid.UUID,
    db: AsyncSession,
) -> AiAgentEventResponse:
    # Infer additional flags the caller may have missed
    auto_flags = infer_risk_flags(
        body.data_categories,
        body.target_url,
        body.chain_depth,
        body.action_type,
    )
    merged_flags = list(set(body.risk_flags) | set(auto_flags))

    risk = compute_risk(
        body.data_categories,
        body.action_type,
        body.chain_depth,
        merged_flags,
    )

    event = AiAgentEvent(
        company_id=company_id,
        agent_name=body.agent_name,
        agent_type=body.agent_type,
        action_type=body.action_type,
        target_tool=body.target_tool,
        target_url=body.target_url,
        data_categories=body.data_categories,
        input_summary=body.input_summary,
        output_summary=body.output_summary,
        session_id=body.session_id,
        chain_depth=body.chain_depth,
        parent_event_id=body.parent_event_id,
        risk_level=risk,
        risk_flags=merged_flags,
        status=body.status,
        duration_ms=body.duration_ms,
        notes=body.notes,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return _to_response(event)


@router.patch("/{event_id}", response_model=AiAgentEventResponse)
async def update_event(
    event_id: uuid.UUID,
    body: AiAgentEventUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AiAgentEvent).where(
            AiAgentEvent.id == event_id,
            AiAgentEvent.company_id == current_user.company_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(event, field, value)
    if "reviewed_by" in updates and updates["reviewed_by"]:
        event.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(event)
    return _to_response(event)


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AiAgentEvent).where(
            AiAgentEvent.id == event_id,
            AiAgentEvent.company_id == current_user.company_id,
        )
    )
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    await db.delete(event)
    await db.commit()
