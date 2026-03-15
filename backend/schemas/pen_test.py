from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PenTestCreate(BaseModel):
    vendor_name: str
    status: str = "scheduled"
    scope: Optional[str] = None
    conducted_at: Optional[datetime] = None
    next_scheduled_at: Optional[datetime] = None
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    summary: Optional[str] = None
    remediation_notes: Optional[str] = None


class PenTestUpdate(BaseModel):
    vendor_name: Optional[str] = None
    status: Optional[str] = None
    scope: Optional[str] = None
    conducted_at: Optional[datetime] = None
    next_scheduled_at: Optional[datetime] = None
    critical_count: Optional[int] = None
    high_count: Optional[int] = None
    medium_count: Optional[int] = None
    low_count: Optional[int] = None
    summary: Optional[str] = None
    file_url: Optional[str] = None
    remediation_notes: Optional[str] = None


class PenTestResponse(BaseModel):
    id: str
    company_id: str
    vendor_name: str
    status: str
    scope: Optional[str]
    conducted_at: Optional[datetime]
    next_scheduled_at: Optional[datetime]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    summary: Optional[str]
    file_url: Optional[str]
    remediation_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
