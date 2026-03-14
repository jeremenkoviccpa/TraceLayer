import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    framework: Mapped[str] = mapped_column(String(50), nullable=False)
    fmt: Mapped[str] = mapped_column(String(10), nullable=False, default="json")  # "json" | "pdf"
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    file_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    storage_bucket: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    generated_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="reports")
