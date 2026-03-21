from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class FrameworkSourceManifest(Base):
    __tablename__ = "framework_source_manifests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_version: Mapped[str] = mapped_column(String(50), nullable=False)
    pending_update: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    pending_update_detected_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
