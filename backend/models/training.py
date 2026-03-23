import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class TrainingRecord(Base):
    __tablename__ = "training_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Assignee — soft reference by email (works for non-users too)
    assignee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    assignee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    # pending | completed | overdue
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    # True = renews annually; next cycle auto-created on completion
    annual: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auto_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    detection_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # Quiz delivery
    completion_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    quiz_score: Mapped[Optional[int]] = mapped_column(Integer(), nullable=True)
    quiz_passed: Mapped[bool] = mapped_column(Boolean(), nullable=False, server_default="false")
    quiz_attempts: Mapped[int] = mapped_column(Integer(), nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
