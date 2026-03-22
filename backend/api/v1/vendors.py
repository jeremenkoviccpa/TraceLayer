import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.integration import Integration
from models.user import User
from models.vendor import Vendor
from schemas.vendor import VendorCreate, VendorResponse, VendorUpdate

# Known vendor profiles for each integration type (SOC 2 / ISO / HIPAA status as of 2025)
_INTEGRATION_VENDORS: dict[str, dict] = {
    "aws":              {"name": "Amazon Web Services (AWS)",  "category": "cloud",          "risk_level": "high",     "website": "https://aws.amazon.com",             "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "azure":            {"name": "Microsoft Azure",            "category": "cloud",          "risk_level": "high",     "website": "https://azure.microsoft.com",         "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "gcp":              {"name": "Google Cloud Platform",      "category": "cloud",          "risk_level": "high",     "website": "https://cloud.google.com",            "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "github":           {"name": "GitHub",                     "category": "other",          "risk_level": "medium",   "website": "https://github.com",                  "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "gitlab":           {"name": "GitLab",                     "category": "other",          "risk_level": "medium",   "website": "https://gitlab.com",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "bitbucket":        {"name": "Atlassian Bitbucket",        "category": "other",          "risk_level": "medium",   "website": "https://bitbucket.org",               "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "okta":             {"name": "Okta",                       "category": "identity",       "risk_level": "high",     "website": "https://www.okta.com",                "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "azure_ad":         {"name": "Microsoft Azure AD (Entra)", "category": "identity",       "risk_level": "high",     "website": "https://azure.microsoft.com",         "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "google_workspace": {"name": "Google Workspace",           "category": "other",          "risk_level": "high",     "website": "https://workspace.google.com",        "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "slack":            {"name": "Slack",                      "category": "communication",  "risk_level": "medium",   "website": "https://slack.com",                   "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "jira":             {"name": "Atlassian Jira",             "category": "other",          "risk_level": "medium",   "website": "https://www.atlassian.com",           "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "snyk":             {"name": "Snyk",                       "category": "security",       "risk_level": "medium",   "website": "https://snyk.io",                     "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "datadog":          {"name": "Datadog",                    "category": "other",          "risk_level": "medium",   "website": "https://www.datadoghq.com",           "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "pagerduty":        {"name": "PagerDuty",                  "category": "other",          "risk_level": "medium",   "website": "https://www.pagerduty.com",           "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "new_relic":        {"name": "New Relic",                  "category": "other",          "risk_level": "medium",   "website": "https://newrelic.com",                "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "splunk":           {"name": "Splunk",                     "category": "security",       "risk_level": "medium",   "website": "https://www.splunk.com",              "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "stripe":           {"name": "Stripe",                     "category": "payment",        "risk_level": "critical", "website": "https://stripe.com",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "hubspot":          {"name": "HubSpot",                    "category": "other",          "risk_level": "medium",   "website": "https://www.hubspot.com",             "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "salesforce":       {"name": "Salesforce",                 "category": "other",          "risk_level": "high",     "website": "https://www.salesforce.com",          "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "zendesk":          {"name": "Zendesk",                    "category": "other",          "risk_level": "medium",   "website": "https://www.zendesk.com",             "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": True},
    "intercom":         {"name": "Intercom",                   "category": "communication",  "risk_level": "medium",   "website": "https://www.intercom.com",            "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": True},
    "twilio":           {"name": "Twilio",                     "category": "communication",  "risk_level": "medium",   "website": "https://www.twilio.com",              "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": True},
    "sendgrid":         {"name": "SendGrid",                   "category": "communication",  "risk_level": "medium",   "website": "https://sendgrid.com",                "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "notion":           {"name": "Notion",                     "category": "other",          "risk_level": "medium",   "website": "https://www.notion.so",               "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "linear":           {"name": "Linear",                     "category": "other",          "risk_level": "low",      "website": "https://linear.app",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "bamboohr":         {"name": "BambooHR",                   "category": "hr",             "risk_level": "high",     "website": "https://www.bamboohr.com",            "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "greenhouse":       {"name": "Greenhouse",                 "category": "hr",             "risk_level": "medium",   "website": "https://www.greenhouse.io",           "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "checkr":           {"name": "Checkr",                     "category": "hr",             "risk_level": "high",     "website": "https://checkr.com",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "knowbe4":          {"name": "KnowBe4",                    "category": "security",       "risk_level": "medium",   "website": "https://www.knowbe4.com",             "soc2_certified": True,  "iso27001_certified": True,  "hipaa_certified": False},
    "wiz":              {"name": "Wiz",                        "category": "security",       "risk_level": "high",     "website": "https://www.wiz.io",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "digitalocean":     {"name": "DigitalOcean",               "category": "cloud",          "risk_level": "high",     "website": "https://www.digitalocean.com",        "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": True},
    "heroku":           {"name": "Heroku",                     "category": "cloud",          "risk_level": "high",     "website": "https://www.heroku.com",              "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "render":           {"name": "Render",                     "category": "cloud",          "risk_level": "medium",   "website": "https://render.com",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
    "vercel":           {"name": "Vercel",                     "category": "cloud",          "risk_level": "medium",   "website": "https://vercel.com",                  "soc2_certified": True,  "iso27001_certified": False, "hipaa_certified": False},
}

router = APIRouter(prefix="/vendors", tags=["vendors"])


def _to_response(v: Vendor) -> VendorResponse:
    return VendorResponse(
        id=str(v.id),
        company_id=str(v.company_id),
        name=v.name,
        category=v.category,
        risk_level=v.risk_level,
        website=v.website,
        contact_email=v.contact_email,
        soc2_certified=v.soc2_certified,
        iso27001_certified=v.iso27001_certified,
        hipaa_certified=v.hipaa_certified,
        review_date=v.review_date,
        notes=v.notes,
        report_file_url=v.report_file_url,
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


@router.get("", response_model=list[VendorResponse])
async def list_vendors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor)
        .where(Vendor.company_id == current_user.company_id)
        .order_by(Vendor.name)
    )
    return [_to_response(v) for v in result.scalars().all()]


@router.post("", response_model=VendorResponse, status_code=201)
async def create_vendor(
    body: VendorCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    v = Vendor(
        company_id=current_user.company_id,
        name=body.name,
        category=body.category,
        risk_level=body.risk_level,
        website=body.website,
        contact_email=body.contact_email,
        soc2_certified=body.soc2_certified,
        iso27001_certified=body.iso27001_certified,
        hipaa_certified=body.hipaa_certified,
        review_date=body.review_date,
        notes=body.notes,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return _to_response(v)


@router.patch("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: uuid.UUID,
    body: VendorUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.company_id == current_user.company_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(v, field, value)

    await db.commit()
    await db.refresh(v)
    return _to_response(v)


@router.post("/auto-populate", status_code=200)
async def auto_populate_vendors(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create vendor records for all active integrations using pre-filled compliance data."""
    integrations_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    active_types = {row[0] for row in integrations_result.all()}

    existing_result = await db.execute(
        select(Vendor.name).where(Vendor.company_id == current_user.company_id)
    )
    existing_names = {row[0].lower() for row in existing_result.all()}

    created = 0
    skipped = 0

    for integration_type in active_types:
        profile = _INTEGRATION_VENDORS.get(integration_type)
        if not profile:
            skipped += 1
            continue
        if profile["name"].lower() in existing_names:
            skipped += 1
            continue
        vendor = Vendor(
            company_id=current_user.company_id,
            name=profile["name"],
            category=profile["category"],
            risk_level=profile["risk_level"],
            website=profile.get("website"),
            soc2_certified=profile.get("soc2_certified", False),
            iso27001_certified=profile.get("iso27001_certified", False),
            hipaa_certified=profile.get("hipaa_certified", False),
            notes=f"Auto-populated from connected {integration_type} integration.",
        )
        db.add(vendor)
        existing_names.add(profile["name"].lower())
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}


@router.delete("/{vendor_id}", status_code=204)
async def delete_vendor(
    vendor_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vendor).where(
            Vendor.id == vendor_id,
            Vendor.company_id == current_user.company_id,
        )
    )
    v = result.scalar_one_or_none()
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    await db.delete(v)
    await db.commit()
