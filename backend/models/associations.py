from sqlalchemy import Table, Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base

evidence_controls = Table(
    "evidence_controls",
    Base.metadata,
    Column("evidence_id", UUID(as_uuid=True), ForeignKey("evidence.id"), primary_key=True),
    Column("control_id", UUID(as_uuid=True), ForeignKey("controls.id"), primary_key=True),
)
