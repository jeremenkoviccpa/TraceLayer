import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP
from typing import Optional

from models.base import Base


class TrustPageView(Base):
    __tablename__ = "trust_page_views"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trust_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trust_pages.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    visitor_ip: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    visitor_country: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    referrer: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    user_agent_summary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    viewed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
