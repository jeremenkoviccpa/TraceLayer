import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditSessionCreate(BaseModel):
    label: Optional[str] = None
    expires_days: Optional[int] = 90  # None = never expires


class AuditSessionResponse(BaseModel):
    id: uuid.UUID
    token: str
    label: Optional[str]
    expires_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class PublicControlScore(BaseModel):
    name: str
    score: int
    status: str  # "passing" | "warning" | "failing" | "no_evidence"


class PublicFrameworkView(BaseModel):
    framework: str
    label: str
    overall_score: int
    controls: list[PublicControlScore]


class PublicAuditView(BaseModel):
    company_name: str
    session_label: Optional[str]
    generated_at: str
    frameworks: list[PublicFrameworkView]
