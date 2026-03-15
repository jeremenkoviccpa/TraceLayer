import re
from typing import Optional

from pydantic import BaseModel, field_validator

_VALID_FRAMEWORKS = {"soc2", "iso27001", "hipaa", "gdpr", "pci_dss", "ccpa", "nist_csf"}
_FW_LABELS = {
    "soc2": "SOC 2",
    "iso27001": "ISO 27001",
    "hipaa": "HIPAA",
    "gdpr": "GDPR",
    "pci_dss": "PCI DSS",
    "ccpa": "CCPA",
    "nist_csf": "NIST CSF",
}


class TrustPageSettingsResponse(BaseModel):
    is_enabled: bool
    slug: str
    show_score: bool
    show_policies: bool
    show_integrations: bool
    custom_headline: Optional[str]
    custom_message: Optional[str]
    frameworks: list[str]

    model_config = {"from_attributes": True}


class TrustPageUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    slug: Optional[str] = None
    show_score: Optional[bool] = None
    show_policies: Optional[bool] = None
    show_integrations: Optional[bool] = None
    custom_headline: Optional[str] = None
    custom_message: Optional[str] = None
    frameworks: Optional[list[str]] = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.match(r"^[a-z0-9-]+$", v):
                raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
            if len(v) < 2 or len(v) > 100:
                raise ValueError("Slug must be 2–100 characters")
        return v

    @field_validator("frameworks")
    @classmethod
    def validate_frameworks(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            for fw in v:
                if fw not in _VALID_FRAMEWORKS:
                    raise ValueError(f"Invalid framework: {fw}")
            if not v:
                raise ValueError("At least one framework must be selected")
        return v


# Policy model only exposes slug and content — we surface slug as the public identifier.
class PublicPolicyView(BaseModel):
    slug: str


class PublicControlScore(BaseModel):
    name: str
    score: int
    status: str


class PublicFrameworkView(BaseModel):
    framework: str
    label: str
    overall_score: int
    controls: list[PublicControlScore]


class PublicTrustPageView(BaseModel):
    company_name: str
    slug: str
    custom_headline: Optional[str]
    custom_message: Optional[str]
    show_score: bool
    show_policies: bool
    show_integrations: bool
    frameworks: list[PublicFrameworkView]
    policies: Optional[list[PublicPolicyView]]
    integrations: Optional[list[str]]
    generated_at: str
