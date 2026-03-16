import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class PartnerClientResponse(BaseModel):
    id: uuid.UUID
    name: str
    plan: str
    created_at: datetime
    trust_page_slug: Optional[str] = None
    trust_page_enabled: Optional[bool] = None

    model_config = {"from_attributes": True}


class PartnerCheckoutRequest(BaseModel):
    client_name: str

    @field_validator("client_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Client name must be at least 2 characters")
        if len(v) > 200:
            raise ValueError("Client name too long")
        return v


class PartnerSwitchResponse(BaseModel):
    access_token: str
    client_company_id: uuid.UUID
    client_name: str


class PartnerTrustCenterInfo(BaseModel):
    slug: str
    public_url: str
    is_enabled: bool
