import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # The employee this device belongs to (optional — can be unassigned)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # laptop | desktop | mobile | tablet | server | other
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="laptop")
    # macos | windows | linux | ios | android | other
    os_type: Mapped[str] = mapped_column(String(50), nullable=False, server_default="macos")
    os_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # Attestation — set when the employee self-attests
    attested_by_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    disk_encrypted: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    lockscreen_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    antivirus_installed: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    last_attested_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
