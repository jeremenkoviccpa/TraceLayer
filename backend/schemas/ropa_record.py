from typing import Optional
from pydantic import BaseModel
import uuid


class RopaRecordCreate(BaseModel):
    name: str
    role: str = "controller"
    purpose: Optional[str] = None
    legal_basis: Optional[str] = None
    data_categories: Optional[str] = None
    data_subjects: Optional[str] = None
    recipients: Optional[str] = None
    third_country_transfers: Optional[str] = None
    retention_period: Optional[str] = None
    security_measures: Optional[str] = None
    dpa_url: Optional[str] = None
    notes: Optional[str] = None


class RopaRecordUpdate(RopaRecordCreate):
    name: Optional[str] = None


class RopaRecordResponse(RopaRecordCreate):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}
