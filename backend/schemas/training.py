from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TrainingCreate(BaseModel):
    assignee_email: str
    assignee_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    annual: bool = False
    notes: Optional[str] = None


class TrainingUpdate(BaseModel):
    assignee_email: Optional[str] = None
    assignee_name: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: Optional[str] = None
    annual: Optional[bool] = None
    notes: Optional[str] = None


class TrainingResponse(BaseModel):
    id: str
    company_id: str
    assignee_email: str
    assignee_name: Optional[str]
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    annual: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
