import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from models.base import Base


class PartnerDirectoryEntry(Base):
    __tablename__ = "partner_directory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "auditor" | "pen_test"
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    referral_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    frameworks: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    specialties: Mapped[Optional[list]] = mapped_column(ARRAY(String), nullable=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default="now()")
