from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BackgroundCheckCreate(BaseModel):
    employee_name: str
    employee_email: Optional[str] = None
    check_type: str = "standard"
    vendor: Optional[str] = None
    status: str = "pending"
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BackgroundCheckUpdate(BaseModel):
    employee_name: Optional[str] = None
    employee_email: Optional[str] = None
    check_type: Optional[str] = None
    vendor: Optional[str] = None
    status: Optional[str] = None
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class BackgroundCheckResponse(BaseModel):
    id: str
    company_id: str
    employee_name: str
    employee_email: Optional[str]
    check_type: str
    vendor: Optional[str]
    status: str
    initiated_at: Optional[datetime]
    completed_at: Optional[datetime]
    valid_until: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
