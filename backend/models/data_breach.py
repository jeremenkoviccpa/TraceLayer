import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class DataBreach(Base):
    __tablename__ = "data_breaches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    breach_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="confidentiality")  # confidentiality / integrity / availability
    severity: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")  # low / medium / high / critical
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="investigating")  # investigating / contained / resolved / closed
    affected_records: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    affected_systems: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notification_required: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    dpa_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    individuals_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dpbi_notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dpbi_ref_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reporter_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
