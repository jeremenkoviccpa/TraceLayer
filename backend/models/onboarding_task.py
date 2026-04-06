import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    employee_email: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    hired_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Per-task statuses: pending | completed | skipped
    policy_ack_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    training_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    device_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    background_check_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    access_provisioned_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")

    overall_status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_progress")
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("company_id", "employee_email", name="uq_onboarding_tasks_company_email"),
    )
