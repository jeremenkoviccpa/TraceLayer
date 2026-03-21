from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class AiAgentEvent(Base):
    __tablename__ = "ai_agent_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    # Which agent fired this
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)   # "GPT-4o", "Claude 3.5", "custom-crm-agent"
    agent_type: Mapped[str] = mapped_column(String(50), nullable=False)    # "openai"|"anthropic"|"gemini"|"custom"

    # What it did
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)   # "api_call"|"tool_use"|"data_read"|"data_write"|"function_call"
    target_tool: Mapped[str] = mapped_column(String(200), nullable=False)  # "salesforce"|"stripe"|"external_api"
    target_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # What data moved
    data_categories: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)   # ["pii","financial","health"]
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Chain tracking
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    chain_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_event_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ai_agent_events.id", ondelete="SET NULL"), nullable=True
    )

    # Risk assessment
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    risk_flags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Outcome
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Review workflow
    is_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
