from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.associations import evidence_controls
from models.base import Base


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    framework_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    evidence: Mapped[list["Evidence"]] = relationship(secondary=evidence_controls, back_populates="controls")
    outgoing_mappings: Mapped[list["ControlMapping"]] = relationship(
        "ControlMapping", foreign_keys="ControlMapping.from_control_id", back_populates="from_control"
    )
    incoming_mappings: Mapped[list["ControlMapping"]] = relationship(
        "ControlMapping", foreign_keys="ControlMapping.to_control_id", back_populates="to_control"
    )
