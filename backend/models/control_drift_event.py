from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP
from sqlalchemy import ForeignKey

from models.base import Base


class ControlDriftEvent(Base):
    __tablename__ = "control_drift_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    control_category: Mapped[str] = mapped_column(String(100), nullable=False)
    control_name: Mapped[str] = mapped_column(String(255), nullable=False)
    previous_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    is_regression: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    trigger_integration: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    detected_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    alerted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
