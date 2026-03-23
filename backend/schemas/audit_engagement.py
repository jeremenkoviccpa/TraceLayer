from datetime import datetime, date
from typing import Optional, Any
import uuid

from pydantic import BaseModel


class AuditEngagementCreate(BaseModel):
    auditor_email: str
    auditor_name: Optional[str] = None
    auditor_firm: Optional[str] = None
    framework: str
    obs_start: date
    obs_end: date
    send_email: bool = True


class AuditEngagementResponse(BaseModel):
    id: uuid.UUID
    framework: str
    obs_start: date
    obs_end: date
    auditor_email: str
    auditor_name: Optional[str]
    auditor_firm: Optional[str]
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_accessed_at: Optional[datetime]
    access_link: str

    class Config:
        from_attributes = True


class AuditEngagementView(BaseModel):
    """Public read-only view returned via token lookup. No auth required."""
    id: uuid.UUID
    framework: str
    obs_start: date
    obs_end: date
    auditor_email: str
    auditor_name: Optional[str]
    auditor_firm: Optional[str]
    customer_name: str
    created_at: datetime
    score: int
    passing_controls: int
    failing_controls: int
    evidence_count: int
    controls: list[dict[str, Any]]
    manual_controls: list[dict[str, Any]]
