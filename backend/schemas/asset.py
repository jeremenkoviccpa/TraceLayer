import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssetCreate(BaseModel):
    name: str
    asset_type: str = "other"
    owner_user_id: Optional[str] = None
    environment: str = "production"
    classification: str = "internal"
    status: str = "active"
    vendor: Optional[str] = None
    version: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None


class AssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    owner_user_id: Optional[str] = None
    environment: Optional[str] = None
    classification: Optional[str] = None
    status: Optional[str] = None
    vendor: Optional[str] = None
    version: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    last_reviewed_at: Optional[datetime] = None


class AssetResponse(BaseModel):
    id: str
    company_id: str
    name: str
    asset_type: str
    owner_user_id: Optional[str]
    owner_name: Optional[str]
    environment: str
    classification: str
    status: str
    vendor: Optional[str]
    version: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]
    description: Optional[str]
    last_reviewed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
