from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, field_validator


class SSOConfigCreate(BaseModel):
    domain: str               # e.g. "acme.com"
    issuer: str               # e.g. "https://dev-xxx.okta.com/oauth2/default"
    client_id: str
    client_secret: str
    scopes: str = "openid email profile"

    @field_validator("domain")
    @classmethod
    def strip_domain(cls, v: str) -> str:
        return v.lower().strip().lstrip("@")

    @field_validator("issuer")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


class SSOConfigUpdate(BaseModel):
    domain: Optional[str] = None
    issuer: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    scopes: Optional[str] = None
    enabled: Optional[bool] = None


class SSOConfigOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    enabled: bool
    domain: str
    issuer: str
    client_id: str
    scopes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SSOCheckOut(BaseModel):
    sso_enabled: bool
    company_id: Optional[uuid.UUID] = None
