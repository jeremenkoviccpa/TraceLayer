import uuid
from sqlalchemy import Boolean, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class SoaItem(Base):
    __tablename__ = "soa_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    annex_ref: Mapped[str] = mapped_column(String(20), nullable=False)   # e.g. "5.1"
    annex_theme: Mapped[str] = mapped_column(String(50), nullable=False)  # Organizational/People/Physical/Technological
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    included: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    implementation_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="not_started")  # not_started, in_progress, implemented, not_applicable
    implementation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
