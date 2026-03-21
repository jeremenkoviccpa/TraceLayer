from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False
    )
    to_control_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("controls.id", ondelete="CASCADE"), nullable=False
    )
    # relationship: equivalent | supersedes | related | subset
    relationship: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    from_control: Mapped["Control"] = relationship(
        "Control", foreign_keys=[from_control_id], back_populates="outgoing_mappings"
    )
    to_control: Mapped["Control"] = relationship(
        "Control", foreign_keys=[to_control_id], back_populates="incoming_mappings"
    )

    __table_args__ = (
        UniqueConstraint("from_control_id", "to_control_id"),
    )
