import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class MemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    invite_url: str
    expires_at: datetime
    accepted_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInviteRequest(BaseModel):
    token: str
    password: str


class UpdateCompanyRequest(BaseModel):
    name: str
    gst_number: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    plan: str
    created_at: datetime
    onboarding_completed: bool
    is_partner_account: bool = False
    gst_number: Optional[str] = None

    model_config = {"from_attributes": True}
