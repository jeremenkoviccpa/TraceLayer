import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class PartnerClientPayment(Base):
    __tablename__ = "partner_client_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    partner_company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    client_company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="SET NULL"), nullable=True
    )
    ls_order_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True, unique=True)
    ls_checkout_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=9900)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    client_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    paid_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
