import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class SubjectRequest(Base):
    __tablename__ = "subject_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    requester_name: Mapped[str] = mapped_column(String(200), nullable=False)
    requester_email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)  # access / deletion / rectification / portability / objection / restriction
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="pending")  # pending / in_progress / completed / refused / extended
    response_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    regulation: Mapped[str] = mapped_column(String(20), nullable=False, server_default="gdpr")  # gdpr / ccpa / other
