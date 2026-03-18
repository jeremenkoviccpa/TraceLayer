from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import uuid


class SubjectRequestCreate(BaseModel):
    requester_name: str
    requester_email: Optional[str] = None
    request_type: str
    received_at: datetime
    due_at: Optional[datetime] = None
    status: str = "pending"
    response_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    regulation: str = "gdpr"


class SubjectRequestUpdate(SubjectRequestCreate):
    requester_name: Optional[str] = None
    request_type: Optional[str] = None
    received_at: Optional[datetime] = None


class SubjectRequestResponse(SubjectRequestCreate):
    id: uuid.UUID
    requester_name: str

    model_config = {"from_attributes": True}
