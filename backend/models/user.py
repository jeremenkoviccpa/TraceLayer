import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    nudge_day1_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    nudge_day3_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    nudge_day7_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    partner_nudge_day1_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    partner_nudge_day3_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    partner_nudge_day7_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    totp_secret_enc: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    totp_backup_codes_enc: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    company: Mapped["Company"] = relationship(back_populates="users")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
