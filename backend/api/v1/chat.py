"""Global chat conversations CRUD + messaging."""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database import get_db
from core.deps import get_current_user
from models.chat_conversation import ChatConversation
from models.chat_message import ChatMessage
from models.integration import Integration
from models.user import User

router = APIRouter(prefix="/chat", tags=["chat"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageOut(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut]

    class Config:
        from_attributes = True


class RenameBody(BaseModel):
    title: str


class SendMessageBody(BaseModel):
    content: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _conv_out(conv: ChatConversation, message_count: int = 0) -> dict:
    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "message_count": message_count,
    }


def _msg_out(msg: ChatMessage) -> dict:
    return {
        "id": str(msg.id),
        "role": msg.role,
        "content": msg.content,
        "created_at": msg.created_at,
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/conversations")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatConversation)
        .where(
            ChatConversation.company_id == current_user.company_id,
            ChatConversation.user_id == current_user.id,
        )
        .order_by(ChatConversation.updated_at.desc())
    )
    convs = result.scalars().all()

    # Get message counts in one query
    from sqlalchemy import func
    counts_result = await db.execute(
        select(ChatMessage.conversation_id, func.count(ChatMessage.id).label("cnt"))
        .where(ChatMessage.conversation_id.in_([c.id for c in convs]))
        .group_by(ChatMessage.conversation_id)
    )
    count_map = {str(row.conversation_id): row.cnt for row in counts_result}

    return [_conv_out(c, count_map.get(str(c.id), 0)) for c in convs]


@router.post("/conversations", status_code=201)
async def create_conversation(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = ChatConversation(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        user_id=current_user.id,
        title="New conversation",
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return _conv_out(conv)


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatConversation)
        .options(selectinload(ChatConversation.messages))
        .where(
            ChatConversation.id == conv_id,
            ChatConversation.company_id == current_user.company_id,
            ChatConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at,
        "updated_at": conv.updated_at,
        "messages": [_msg_out(m) for m in conv.messages],
    }


@router.patch("/conversations/{conv_id}")
async def rename_conversation(
    conv_id: uuid.UUID,
    body: RenameBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatConversation).where(
            ChatConversation.id == conv_id,
            ChatConversation.company_id == current_user.company_id,
            ChatConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    title = body.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="Title cannot be empty")

    conv.title = title[:255]
    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(conv)
    return _conv_out(conv)


@router.delete("/conversations/{conv_id}", status_code=204)
async def delete_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatConversation).where(
            ChatConversation.id == conv_id,
            ChatConversation.company_id == current_user.company_id,
            ChatConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()


@router.post("/conversations/{conv_id}/messages", status_code=201)
async def send_message(
    conv_id: uuid.UUID,
    body: SendMessageBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ChatConversation)
        .options(selectinload(ChatConversation.messages))
        .where(
            ChatConversation.id == conv_id,
            ChatConversation.company_id == current_user.company_id,
            ChatConversation.user_id == current_user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Message cannot be empty")

    # Save user message
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="user",
        content=content,
    )
    db.add(user_msg)

    # Auto-title the conversation from the first message
    if conv.title == "New conversation" and len(conv.messages) == 0:
        conv.title = content[:60] + ("…" if len(content) > 60 else "")

    # Build history from existing messages
    history = [{"role": m.role, "content": m.content} for m in conv.messages]

    # Fetch connected integrations for context
    integrations_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    connected = [row[0] for row in integrations_result.all()]

    # Call AI
    from services.ai_service import chat_with_general_advisor
    from models.company import Company
    from models.score_snapshot import ScoreSnapshot

    company_result = await db.execute(
        select(Company).where(Company.id == current_user.company_id)
    )
    company = company_result.scalar_one_or_none()

    company_context = {
        "company_name": company.name if company else None,
        "connected_integrations": connected,
    }

    reply_text = await chat_with_general_advisor(content, history, company_context)

    # Save assistant reply
    assistant_msg = ChatMessage(
        id=uuid.uuid4(),
        conversation_id=conv.id,
        role="assistant",
        content=reply_text,
    )
    db.add(assistant_msg)

    conv.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "user_message": _msg_out(user_msg),
        "assistant_message": _msg_out(assistant_msg),
        "conversation_title": conv.title,
    }
