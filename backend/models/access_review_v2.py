import uuid
from datetime import datetime
from typing import Optional, List

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class AccessReviewV2(Base):
    __tablename__ = "access_reviews_v2"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False, server_default="soc2")
    review_period: Mapped[str] = mapped_column(String(50), nullable=False, server_default="quarterly")
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="in_progress")
    due_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    items: Mapped[List["AccessReviewItem"]] = relationship(
        "AccessReviewItem", back_populates="review", cascade="all, delete-orphan"
    )


class AccessReviewItem(Base):
    __tablename__ = "access_review_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    review_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("access_reviews_v2.id", ondelete="CASCADE"), nullable=False
    )
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    user_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    system_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role_or_permission: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    decision: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    review: Mapped["AccessReviewV2"] = relationship("AccessReviewV2", back_populates="items")
