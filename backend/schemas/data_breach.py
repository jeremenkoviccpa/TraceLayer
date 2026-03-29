from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class DataBreachCreate(BaseModel):
    title: str
    occurred_at: Optional[datetime] = None
    discovered_at: Optional[datetime] = None
    breach_type: str = "confidentiality"
    severity: str = "medium"
    status: str = "investigating"
    affected_records: Optional[int] = None
    affected_systems: Optional[str] = None
    description: Optional[str] = None
    notification_required: bool = False
    dpa_notified_at: Optional[datetime] = None
    individuals_notified_at: Optional[datetime] = None
    dpbi_notified_at: Optional[datetime] = None
    dpbi_ref_number: Optional[str] = None
    root_cause: Optional[str] = None
    remediation: Optional[str] = None
    reporter_name: Optional[str] = None


class DataBreachUpdate(DataBreachCreate):
    title: Optional[str] = None


class DataBreachResponse(DataBreachCreate):
    id: uuid.UUID
    title: str

    model_config = {"from_attributes": True}
