import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from models.base import Base


class RopaRecord(Base):
    __tablename__ = "ropa_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="controller")  # controller / processor / joint_controller
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    legal_basis: Mapped[str | None] = mapped_column(String(100), nullable=True)  # consent, contract, legal_obligation, vital_interests, public_task, legitimate_interests
    data_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_subjects: Mapped[str | None] = mapped_column(Text, nullable=True)
    recipients: Mapped[str | None] = mapped_column(Text, nullable=True)
    third_country_transfers: Mapped[str | None] = mapped_column(Text, nullable=True)
    retention_period: Mapped[str | None] = mapped_column(String(200), nullable=True)
    security_measures: Mapped[str | None] = mapped_column(Text, nullable=True)
    dpa_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
