from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class VendorCreate(BaseModel):
    name: str
    category: str = "other"
    risk_level: str = "medium"
    website: Optional[str] = None
    contact_email: Optional[str] = None
    soc2_certified: bool = False
    iso27001_certified: bool = False
    hipaa_certified: bool = False
    review_date: Optional[datetime] = None
    notes: Optional[str] = None


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    risk_level: Optional[str] = None
    website: Optional[str] = None
    contact_email: Optional[str] = None
    soc2_certified: Optional[bool] = None
    iso27001_certified: Optional[bool] = None
    hipaa_certified: Optional[bool] = None
    review_date: Optional[datetime] = None
    notes: Optional[str] = None
    report_file_url: Optional[str] = None


class VendorResponse(BaseModel):
    id: str
    company_id: str
    name: str
    category: str
    risk_level: str
    website: Optional[str]
    contact_email: Optional[str]
    soc2_certified: bool
    iso27001_certified: bool
    hipaa_certified: bool
    review_date: Optional[datetime]
    notes: Optional[str]
    report_file_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
