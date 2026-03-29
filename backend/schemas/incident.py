from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class IncidentCreate(BaseModel):
    title: str
    description: Optional[str] = None
    severity: str = "medium"
    status: str = "open"
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_systems: Optional[str] = None
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None
    reporter_user_id: Optional[str] = None
    certin_reported_at: Optional[datetime] = None
    certin_ref_number: Optional[str] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    affected_systems: Optional[str] = None
    root_cause: Optional[str] = None
    lessons_learned: Optional[str] = None
    reporter_user_id: Optional[str] = None
    certin_reported_at: Optional[datetime] = None
    certin_ref_number: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    company_id: str
    title: str
    description: Optional[str]
    severity: str
    status: str
    detected_at: Optional[datetime]
    resolved_at: Optional[datetime]
    affected_systems: Optional[str]
    root_cause: Optional[str]
    lessons_learned: Optional[str]
    reporter_user_id: Optional[str]
    reporter_name: Optional[str]
    auto_detected: bool = False
    detection_key: Optional[str] = None
    certin_reported_at: Optional[datetime] = None
    certin_ref_number: Optional[str] = None
    created_at: datetime
    updated_at: datetime
