import json
import re
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TIMESTAMP

from models.base import Base

_DEFAULT_FRAMEWORKS = '["soc2","iso27001","hipaa","gdpr","pci_dss","ccpa","nist_csf"]'


class TrustPage(Base):
    __tablename__ = "trust_pages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    show_score: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    show_policies: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    show_integrations: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    custom_headline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    frameworks_json: Mapped[str] = mapped_column(Text, nullable=False, server_default=_DEFAULT_FRAMEWORKS)
    # Custom domain support
    custom_domain: Mapped[Optional[str]] = mapped_column(String(253), nullable=True)
    domain_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    domain_verification_token: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    @property
    def frameworks(self) -> list[str]:
        try:
            return json.loads(self.frameworks_json)
        except Exception:
            return ["soc2", "iso27001", "hipaa"]

    @frameworks.setter
    def frameworks(self, value: list[str]) -> None:
        self.frameworks_json = json.dumps(value)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:80].strip("-") or "my-company"
