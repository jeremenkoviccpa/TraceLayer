import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class PenTest(Base):
    __tablename__ = "pen_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    vendor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # scheduled | in_progress | completed | remediated
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="scheduled")
    scope: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conducted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    next_scheduled_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    critical_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    high_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    medium_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    low_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    remediation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
