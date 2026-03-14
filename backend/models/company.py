import uuid
from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from models.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="company")
    integrations: Mapped[list["Integration"]] = relationship(back_populates="company")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="company")
    reports: Mapped[list["Report"]] = relationship(back_populates="company")
