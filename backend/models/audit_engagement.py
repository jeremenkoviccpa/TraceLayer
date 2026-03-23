import secrets
import uuid
from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, ForeignKey, Date, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base


def _generate_token() -> str:
    return secrets.token_urlsafe(48)


class AuditEngagement(Base):
    __tablename__ = "audit_engagements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    obs_start: Mapped[date] = mapped_column(Date, nullable=False)
    obs_end: Mapped[date] = mapped_column(Date, nullable=False)
    access_token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, default=_generate_token)
    auditor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    auditor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    auditor_firm: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")
    expires_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
