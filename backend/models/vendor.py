import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # cloud | payment | identity | security | communication | other
    category: Mapped[str] = mapped_column(String(100), nullable=False, server_default="other")
    # low | medium | high | critical
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, server_default="medium")
    website: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    soc2_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    iso27001_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    hipaa_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    pci_dss_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    gdpr_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    iso42001_certified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    # Date of last review
    review_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Uploaded vendor SOC 2 report URL
    report_file_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
