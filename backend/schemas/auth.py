import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    account_type: str = "company"  # "company" | "partner"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    requires_2fa: Optional[bool] = None
    totp_token: Optional[str] = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    company_id: uuid.UUID
    role: str
    email_verified: bool

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None

    model_config = {"str_strip_whitespace": True}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class TwoFASetupResponse(BaseModel):
    secret: str
    qr_uri: str
    backup_codes: list[str]


class TwoFAEnableRequest(BaseModel):
    code: str


class TwoFADisableRequest(BaseModel):
    password: str


class TwoFAVerifyRequest(BaseModel):
    totp_token: str
    code: str


class TwoFABackupCodesRequest(BaseModel):
    password: str
