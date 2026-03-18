import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class ManagementReview(Base):
    __tablename__ = "management_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    review_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attendees: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    inputs_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # what was reviewed (audit results, incidents, risk changes, etc.)
    decisions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")  # [{item, owner, due_date, done}]
    next_review_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False, server_default="satisfactory")  # satisfactory / needs_improvement / critical_findings
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
