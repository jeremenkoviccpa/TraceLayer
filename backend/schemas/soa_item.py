from typing import Optional
from pydantic import BaseModel
import uuid


class SoaItemUpdate(BaseModel):
    included: Optional[bool] = None
    justification: Optional[str] = None
    implementation_status: Optional[str] = None
    implementation_notes: Optional[str] = None


class SoaItemResponse(BaseModel):
    id: uuid.UUID
    annex_ref: str
    annex_theme: str
    title: str
    included: bool
    justification: Optional[str] = None
    implementation_status: str
    implementation_notes: Optional[str] = None

    model_config = {"from_attributes": True}
