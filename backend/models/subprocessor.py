import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class Subprocessor(Base):
    __tablename__ = "subprocessors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    purpose: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_categories: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    legal_basis: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    transfer_mechanism: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dpa_signed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    dpa_signed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
