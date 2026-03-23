from typing import Optional
import uuid

from pydantic import BaseModel


class PartnerDirectoryEntryResponse(BaseModel):
    id: uuid.UUID
    partner_type: str
    name: str
    description: Optional[str]
    website: Optional[str]
    referral_url: Optional[str]
    contact_email: Optional[str]
    frameworks: Optional[list[str]]
    specialties: Optional[list[str]]
    is_featured: bool

    class Config:
        from_attributes = True
