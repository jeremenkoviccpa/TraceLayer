import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_partner, get_current_user
from core.config import settings
from core.security import create_access_token
from models.company import Company
from models.partner_client_payment import PartnerClientPayment
from models.trust_page import TrustPage
from models.user import User
from schemas.partner import (
    PartnerCheckoutRequest,
    PartnerClientResponse,
    PartnerSwitchResponse,
    PartnerTrustCenterInfo,
)
from services.billing_service import create_partner_client_checkout_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/partner", tags=["partner"])


async def _trust_slug(company_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(TrustPage).where(TrustPage.company_id == company_id))
    tp = result.scalar_one_or_none()
    return tp


@router.get("/clients", response_model=list[PartnerClientResponse])
async def list_clients(
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """List all client companies managed by this partner."""
    result = await db.execute(
        select(Company).where(Company.partner_id == current_user.company_id)
    )
    clients = result.scalars().all()

    out = []
    for c in clients:
        tp = await _trust_slug(c.id, db)
        out.append(PartnerClientResponse(
            id=c.id,
            name=c.name,
            plan=c.plan,
            created_at=c.created_at,
            trust_page_slug=tp.slug if tp else None,
            trust_page_enabled=tp.is_enabled if tp else False,
        ))
    return out


@router.post("/clients/checkout")
async def create_client_checkout(
    body: PartnerCheckoutRequest,
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Create a LemonSqueezy $99 checkout for a new client slot."""
    # Create a pending payment record for idempotency
    payment = PartnerClientPayment(
        id=uuid.uuid4(),
        partner_company_id=current_user.company_id,
        client_name=body.client_name,
        status="pending",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    try:
        url = await create_partner_client_checkout_url(
            partner_company_id=current_user.company_id,
            client_name=body.client_name,
            payment_id=payment.id,
            user_email=current_user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception:
        logger.exception("Failed to create partner checkout for company=%s", current_user.company_id)
        raise HTTPException(status_code=503, detail="Could not create checkout. Try again shortly.")

    return {"checkout_url": url, "payment_id": str(payment.id)}


@router.post("/clients/provision", response_model=PartnerClientResponse)
async def provision_client_direct(
    body: PartnerCheckoutRequest,
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Directly provision a client workspace without a payment step.
    Used when LemonSqueezy is not configured or as an admin override.
    """
    import secrets
    from models.trust_page import TrustPage, slugify

    client_company = Company(
        name=body.client_name,
        plan="growth",
        is_partner_account=False,
        partner_id=current_user.company_id,
        onboarding_completed=True,
    )
    db.add(client_company)
    await db.flush()

    base_slug = slugify(body.client_name)
    slug = base_slug
    for _ in range(10):
        existing = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{secrets.token_hex(3)}"

    trust_page = TrustPage(company_id=client_company.id, slug=slug)
    db.add(trust_page)

    payment = PartnerClientPayment(
        id=uuid.uuid4(),
        partner_company_id=current_user.company_id,
        client_company_id=client_company.id,
        client_name=body.client_name,
        status="manual",
    )
    db.add(payment)

    await db.commit()
    await db.refresh(client_company)

    logger.info(
        "Partner client provisioned directly: partner=%s client=%s",
        current_user.company_id, client_company.id,
    )

    return PartnerClientResponse(
        id=client_company.id,
        name=client_company.name,
        plan=client_company.plan,
        created_at=client_company.created_at,
        trust_page_slug=slug,
        trust_page_enabled=False,
    )


@router.get("/clients/{client_company_id}/switch", response_model=PartnerSwitchResponse)
async def switch_to_client(
    client_company_id: uuid.UUID,
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Issue a short-lived token scoped to the client's company_id."""
    result = await db.execute(
        select(Company).where(
            Company.id == client_company_id,
            Company.partner_id == current_user.company_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    token = create_access_token(
        user_id=str(current_user.id),
        company_id=str(client_company_id),
        extra_claims={"partner_id": str(current_user.company_id)},
        expire_minutes=60,
    )
    return PartnerSwitchResponse(
        access_token=token,
        client_company_id=client_company_id,
        client_name=client.name,
    )


@router.get("/clients/{client_company_id}/trust-center", response_model=PartnerTrustCenterInfo)
async def get_client_trust_center(
    client_company_id: uuid.UUID,
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """Return Trust Center link for a partner's client."""
    result = await db.execute(
        select(Company).where(
            Company.id == client_company_id,
            Company.partner_id == current_user.company_id,
        )
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    tp = await _trust_slug(client_company_id, db)
    if not tp:
        raise HTTPException(status_code=404, detail="Trust Center not yet provisioned for this client")

    return PartnerTrustCenterInfo(
        slug=tp.slug,
        public_url=f"{settings.app_frontend_url}/trust/{tp.slug}",
        is_enabled=tp.is_enabled,
    )


@router.get("/payments", response_model=list[dict])
async def list_payments(
    current_user: User = Depends(get_current_partner),
    db: AsyncSession = Depends(get_db),
):
    """List all client payments for this partner."""
    result = await db.execute(
        select(PartnerClientPayment)
        .where(PartnerClientPayment.partner_company_id == current_user.company_id)
        .order_by(PartnerClientPayment.created_at.desc())
    )
    payments = result.scalars().all()
    return [
        {
            "id": str(p.id),
            "client_name": p.client_name,
            "status": p.status,
            "amount_cents": p.amount_cents,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            "client_company_id": str(p.client_company_id) if p.client_company_id else None,
        }
        for p in payments
    ]
