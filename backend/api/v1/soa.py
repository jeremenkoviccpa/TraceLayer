from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.integration import Integration
from models.user import User
from models.soa_item import SoaItem
from schemas.soa_item import SoaItemResponse, SoaItemUpdate

# Map integration types → ISO 27001:2022 Annex A controls they provide evidence for
_INTEGRATION_SOA_MAP: dict[str, list[str]] = {
    "aws":              ["5.15", "5.17", "5.18", "5.23", "5.28", "8.15", "8.16", "8.20", "8.9"],
    "azure":            ["5.15", "5.17", "5.18", "5.23", "5.28", "8.15", "8.16", "8.20"],
    "gcp":              ["5.15", "5.17", "5.18", "5.23", "5.28", "8.15", "8.16"],
    "digitalocean":     ["5.23", "8.20"],
    "heroku":           ["5.23"],
    "render":           ["5.23"],
    "vercel":           ["5.23"],
    "okta":             ["5.15", "5.16", "5.17", "5.18", "8.2", "8.5"],
    "azure_ad":         ["5.15", "5.16", "5.17", "5.18", "8.2", "8.5"],
    "google_workspace": ["5.14", "5.15", "5.16", "5.17", "5.18"],
    "github":           ["5.18", "8.4", "8.25", "8.26", "8.27", "8.28", "8.32"],
    "gitlab":           ["5.18", "8.4", "8.25", "8.26", "8.27", "8.28", "8.32"],
    "bitbucket":        ["5.18", "8.4", "8.25", "8.26", "8.32"],
    "jira":             ["5.8", "8.4"],
    "asana":            ["5.8"],
    "slack":            ["5.14"],
    "snyk":             ["8.8", "8.26", "8.28", "8.29"],
    "wiz":              ["8.8", "8.20"],
    "qualys":           ["8.8"],
    "tenable":          ["8.8"],
    "datadog":          ["5.28", "8.15", "8.16"],
    "pagerduty":        ["8.15", "8.16"],
    "new_relic":        ["8.15", "8.16"],
    "splunk":           ["5.28", "8.15"],
    "elastic":          ["5.28", "8.15"],
    "knowbe4":          ["6.3"],
    "360learning":      ["6.3"],
    "bamboohr":         ["6.1", "6.2"],
    "greenhouse":       ["6.1"],
    "checkr":           ["6.1"],
    "intercom":         ["5.14"],
    "zendesk":          ["5.14"],
    "twilio":           ["5.14"],
    "sendgrid":         ["5.14"],
}

router = APIRouter(prefix="/soa", tags=["soa"])

# All 93 ISO 27001:2022 Annex A controls
ISO27001_CONTROLS = [
    # Organizational (5.1 - 5.37)
    ("5.1",  "Organizational", "Policies for information security"),
    ("5.2",  "Organizational", "Information security roles and responsibilities"),
    ("5.3",  "Organizational", "Segregation of duties"),
    ("5.4",  "Organizational", "Management responsibilities"),
    ("5.5",  "Organizational", "Contact with authorities"),
    ("5.6",  "Organizational", "Contact with special interest groups"),
    ("5.7",  "Organizational", "Threat intelligence"),
    ("5.8",  "Organizational", "Information security in project management"),
    ("5.9",  "Organizational", "Inventory of information and other associated assets"),
    ("5.10", "Organizational", "Acceptable use of information and other associated assets"),
    ("5.11", "Organizational", "Return of assets"),
    ("5.12", "Organizational", "Classification of information"),
    ("5.13", "Organizational", "Labelling of information"),
    ("5.14", "Organizational", "Information transfer"),
    ("5.15", "Organizational", "Access control"),
    ("5.16", "Organizational", "Identity management"),
    ("5.17", "Organizational", "Authentication information"),
    ("5.18", "Organizational", "Access rights"),
    ("5.19", "Organizational", "Information security in supplier relationships"),
    ("5.20", "Organizational", "Addressing information security within supplier agreements"),
    ("5.21", "Organizational", "Managing information security in the ICT supply chain"),
    ("5.22", "Organizational", "Monitoring, review and change management of supplier services"),
    ("5.23", "Organizational", "Information security for use of cloud services"),
    ("5.24", "Organizational", "Information security incident management planning and preparation"),
    ("5.25", "Organizational", "Assessment and decision on information security events"),
    ("5.26", "Organizational", "Response to information security incidents"),
    ("5.27", "Organizational", "Learning from information security incidents"),
    ("5.28", "Organizational", "Collection of evidence"),
    ("5.29", "Organizational", "Information security during disruption"),
    ("5.30", "Organizational", "ICT readiness for business continuity"),
    ("5.31", "Organizational", "Legal, statutory, regulatory and contractual requirements"),
    ("5.32", "Organizational", "Intellectual property rights"),
    ("5.33", "Organizational", "Protection of records"),
    ("5.34", "Organizational", "Privacy and protection of personal information"),
    ("5.35", "Organizational", "Independent review of information security"),
    ("5.36", "Organizational", "Compliance with policies, rules and standards for information security"),
    ("5.37", "Organizational", "Documented operating procedures"),
    # People (6.1 - 6.8)
    ("6.1", "People", "Screening"),
    ("6.2", "People", "Terms and conditions of employment"),
    ("6.3", "People", "Information security awareness, education and training"),
    ("6.4", "People", "Disciplinary process"),
    ("6.5", "People", "Responsibilities after termination or change of employment"),
    ("6.6", "People", "Confidentiality or non-disclosure agreements"),
    ("6.7", "People", "Remote working"),
    ("6.8", "People", "Information security event reporting"),
    # Physical (7.1 - 7.14)
    ("7.1",  "Physical", "Physical security perimeters"),
    ("7.2",  "Physical", "Physical entry"),
    ("7.3",  "Physical", "Securing offices, rooms and facilities"),
    ("7.4",  "Physical", "Physical security monitoring"),
    ("7.5",  "Physical", "Protecting against physical and environmental threats"),
    ("7.6",  "Physical", "Working in secure areas"),
    ("7.7",  "Physical", "Clear desk and clear screen"),
    ("7.8",  "Physical", "Equipment siting and protection"),
    ("7.9",  "Physical", "Security of assets off-premises"),
    ("7.10", "Physical", "Storage media"),
    ("7.11", "Physical", "Supporting utilities"),
    ("7.12", "Physical", "Cabling security"),
    ("7.13", "Physical", "Equipment maintenance"),
    ("7.14", "Physical", "Secure disposal or re-use of equipment"),
    # Technological (8.1 - 8.34)
    ("8.1",  "Technological", "User endpoint devices"),
    ("8.2",  "Technological", "Privileged access rights"),
    ("8.3",  "Technological", "Information access restriction"),
    ("8.4",  "Technological", "Access to source code"),
    ("8.5",  "Technological", "Secure authentication"),
    ("8.6",  "Technological", "Capacity management"),
    ("8.7",  "Technological", "Protection against malware"),
    ("8.8",  "Technological", "Management of technical vulnerabilities"),
    ("8.9",  "Technological", "Configuration management"),
    ("8.10", "Technological", "Information deletion"),
    ("8.11", "Technological", "Data masking"),
    ("8.12", "Technological", "Data leakage prevention"),
    ("8.13", "Technological", "Information backup"),
    ("8.14", "Technological", "Redundancy of information processing facilities"),
    ("8.15", "Technological", "Logging"),
    ("8.16", "Technological", "Monitoring activities"),
    ("8.17", "Technological", "Clock synchronization"),
    ("8.18", "Technological", "Use of privileged utility programs"),
    ("8.19", "Technological", "Installation of software on operational systems"),
    ("8.20", "Technological", "Networks security"),
    ("8.21", "Technological", "Security of network services"),
    ("8.22", "Technological", "Segregation of networks"),
    ("8.23", "Technological", "Web filtering"),
    ("8.24", "Technological", "Use of cryptography"),
    ("8.25", "Technological", "Secure development life cycle"),
    ("8.26", "Technological", "Application security requirements"),
    ("8.27", "Technological", "Secure system architecture and engineering principles"),
    ("8.28", "Technological", "Secure coding"),
    ("8.29", "Technological", "Security testing in development and acceptance"),
    ("8.30", "Technological", "Outsourced development"),
    ("8.31", "Technological", "Separation of development, test and production environments"),
    ("8.32", "Technological", "Change management"),
    ("8.33", "Technological", "Test information"),
    ("8.34", "Technological", "Protection of information systems during audit testing"),
]


@router.get("", response_model=list[SoaItemResponse])
async def get_soa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SoaItem)
        .where(SoaItem.company_id == current_user.company_id)
        .order_by(SoaItem.annex_ref)
    )
    return result.scalars().all()


@router.post("/initialize", response_model=list[SoaItemResponse])
async def initialize_soa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Seed all 93 ISO 27001:2022 Annex A controls for this company. Idempotent."""
    result = await db.execute(
        select(SoaItem).where(SoaItem.company_id == current_user.company_id)
    )
    existing = {item.annex_ref for item in result.scalars().all()}
    for ref, theme, title in ISO27001_CONTROLS:
        if ref not in existing:
            item = SoaItem(
                company_id=current_user.company_id,
                annex_ref=ref,
                annex_theme=theme,
                title=title,
            )
            db.add(item)
    await db.commit()
    result = await db.execute(
        select(SoaItem)
        .where(SoaItem.company_id == current_user.company_id)
        .order_by(SoaItem.annex_ref)
    )
    return result.scalars().all()


@router.post("/auto-progress", status_code=200)
async def auto_progress_soa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark SOA controls as in_progress based on active integrations. Never downgrades implemented controls."""
    # Ensure SOA is initialized first
    existing_result = await db.execute(
        select(SoaItem).where(SoaItem.company_id == current_user.company_id)
    )
    items = existing_result.scalars().all()
    if not items:
        for ref, theme, title in ISO27001_CONTROLS:
            db.add(SoaItem(company_id=current_user.company_id, annex_ref=ref, annex_theme=theme, title=title))
        await db.commit()
        existing_result = await db.execute(
            select(SoaItem).where(SoaItem.company_id == current_user.company_id)
        )
        items = existing_result.scalars().all()

    integrations_result = await db.execute(
        select(Integration.integration_type).where(
            Integration.company_id == current_user.company_id,
            Integration.status == "active",
        )
    )
    active_types = {row[0] for row in integrations_result.all()}

    # Collect all control refs that should be marked in_progress
    refs_to_advance: set[str] = set()
    for integration_type in active_types:
        for ref in _INTEGRATION_SOA_MAP.get(integration_type, []):
            refs_to_advance.add(ref)

    items_by_ref = {item.annex_ref: item for item in items}
    updated = 0
    for ref in refs_to_advance:
        item = items_by_ref.get(ref)
        if item and item.implementation_status == "not_started":
            item.implementation_status = "in_progress"
            updated += 1

    if updated:
        await db.commit()

    return {"updated": updated, "integrations_scanned": len(active_types)}


@router.patch("/{item_id}", response_model=SoaItemResponse)
async def update_soa_item(
    item_id: str,
    body: SoaItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(
        select(SoaItem).where(
            SoaItem.id == UUID(item_id),
            SoaItem.company_id == current_user.company_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(item, k, v)
    await db.commit()
    await db.refresh(item)
    return item
