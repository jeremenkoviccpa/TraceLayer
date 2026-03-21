from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class DataFlow(Base):
    __tablename__ = "data_flows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)

    # The data being processed
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)       # e.g. "email_address"
    data_category: Mapped[str] = mapped_column(String(50), nullable=False)    # "personal" | "sensitive" | "financial" | "operational"

    # The tool/vendor processing it
    tool: Mapped[str] = mapped_column(String(100), nullable=False)             # integration_type or "custom"
    tool_label: Mapped[str] = mapped_column(String(255), nullable=False)       # display name

    # Where data goes
    region: Mapped[str] = mapped_column(String(100), nullable=False, default="unknown")  # "us", "eu", "global"

    # Risk & compliance
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")  # "low"|"medium"|"high"|"critical"
    regulations: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)          # ["gdpr", "ccpa", ...]

    # Context
    purpose: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # GDPR legal basis
    is_auto_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_cross_border: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
