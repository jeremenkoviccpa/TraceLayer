from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class FrameworkUpdateRequest(Base):
    __tablename__ = "framework_update_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_key: Mapped[str] = mapped_column(String(50), nullable=False)
    detected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    new_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    old_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    ai_extraction_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # status: pending | approved | rejected
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
