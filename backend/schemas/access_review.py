from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AccessReviewCreate(BaseModel):
    title: str
    period: str
    reviewer_user_id: Optional[str] = None
    due_date: Optional[datetime] = None
    scope: Optional[str] = None


class AccessReviewUpdate(BaseModel):
    title: Optional[str] = None
    period: Optional[str] = None
    reviewer_user_id: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    users_reviewed: Optional[int] = None
    access_changes: Optional[int] = None
    scope: Optional[str] = None
    findings: Optional[str] = None
    notes: Optional[str] = None


class AccessReviewResponse(BaseModel):
    id: str
    company_id: str
    title: str
    period: str
    reviewer_user_id: Optional[str]
    reviewer_name: Optional[str]
    status: str
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    users_reviewed: int
    access_changes: int
    scope: Optional[str]
    findings: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
