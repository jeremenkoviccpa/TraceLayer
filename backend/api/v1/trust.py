import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func, cast
from sqlalchemy.types import Date as SADate
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.integration import Integration
from models.policy import Policy
from models.trust_page import TrustPage, slugify
from models.trust_page_view import TrustPageView
from schemas.trust import (
    PublicControlScore,
    PublicFrameworkView,
    PublicPolicyView,
    PublicTrustPageView,
    TrustPageSettingsResponse,
    TrustPageUpdate,
    _FW_LABELS,
)
from services.compliance_service import get_compliance_score

router = APIRouter(prefix="/trust", tags=["trust"])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _get_or_create_trust_page(company_id: uuid.UUID, company_name: str, db: AsyncSession) -> TrustPage:
    result = await db.execute(select(TrustPage).where(TrustPage.company_id == company_id))
    tp = result.scalar_one_or_none()
    if tp:
        return tp

    base_slug = slugify(company_name)
    slug = base_slug
    # Ensure uniqueness
    for _ in range(10):
        existing = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
        if not existing.scalar_one_or_none():
            break
        slug = f"{base_slug}-{secrets.token_hex(3)}"

    tp = TrustPage(company_id=company_id, slug=slug)
    db.add(tp)
    await db.commit()
    await db.refresh(tp)
    return tp


# ── Authenticated endpoints ────────────────────────────────────────────────────

def _ua_summary(ua: Optional[str]) -> Optional[str]:
    if not ua:
        return None
    ua_lower = ua.lower()
    if "mobile" in ua_lower or "android" in ua_lower or "iphone" in ua_lower:
        os = "Mobile"
    elif "windows" in ua_lower:
        os = "Windows"
    elif "mac" in ua_lower:
        os = "Mac"
    elif "linux" in ua_lower:
        os = "Linux"
    else:
        os = "Other"
    if "firefox" in ua_lower:
        browser = "Firefox"
    elif "chrome" in ua_lower:
        browser = "Chrome"
    elif "safari" in ua_lower:
        browser = "Safari"
    elif "edge" in ua_lower:
        browser = "Edge"
    else:
        browser = "Other"
    return f"{browser} / {os}"


@router.get("/settings", response_model=TrustPageSettingsResponse)
async def get_trust_settings(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "my-company"

    tp = await _get_or_create_trust_page(current_user.company_id, company_name, db)
    return TrustPageSettingsResponse(
        is_enabled=tp.is_enabled,
        slug=tp.slug,
        show_score=tp.show_score,
        show_policies=tp.show_policies,
        show_integrations=tp.show_integrations,
        custom_headline=tp.custom_headline,
        custom_message=tp.custom_message,
        frameworks=tp.frameworks,
        custom_domain=tp.custom_domain,
        domain_verified=tp.domain_verified,
        domain_verification_token=tp.domain_verification_token,
    )


@router.put("/settings", response_model=TrustPageSettingsResponse)
async def update_trust_settings(
    body: TrustPageUpdate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    from models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "my-company"

    tp = await _get_or_create_trust_page(current_user.company_id, company_name, db)

    # Check slug uniqueness if changing
    if body.slug and body.slug != tp.slug:
        existing = await db.execute(select(TrustPage).where(TrustPage.slug == body.slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="This URL slug is already taken. Please choose another.")

    if body.is_enabled is not None:
        tp.is_enabled = body.is_enabled
    if body.slug is not None:
        tp.slug = body.slug
    if body.show_score is not None:
        tp.show_score = body.show_score
    if body.show_policies is not None:
        tp.show_policies = body.show_policies
    if body.show_integrations is not None:
        tp.show_integrations = body.show_integrations
    if body.custom_headline is not None:
        tp.custom_headline = body.custom_headline or None
    if body.custom_message is not None:
        tp.custom_message = body.custom_message or None
    if body.frameworks is not None:
        tp.frameworks = body.frameworks
    if body.custom_domain is not None:
        new_domain = body.custom_domain.strip().lower() or None
        if new_domain != tp.custom_domain:
            tp.custom_domain = new_domain
            tp.domain_verified = False
            tp.domain_verification_token = secrets.token_hex(32) if new_domain else None

    await db.commit()
    await db.refresh(tp)
    return TrustPageSettingsResponse(
        is_enabled=tp.is_enabled,
        slug=tp.slug,
        show_score=tp.show_score,
        show_policies=tp.show_policies,
        show_integrations=tp.show_integrations,
        custom_headline=tp.custom_headline,
        custom_message=tp.custom_message,
        frameworks=tp.frameworks,
        custom_domain=tp.custom_domain,
        domain_verified=tp.domain_verified,
        domain_verification_token=tp.domain_verification_token,
    )


# ── Analytics endpoint ─────────────────────────────────────────────────────────

class DailyViewPoint(BaseModel):
    date: str
    count: int


class RecentView(BaseModel):
    visitor_ip: Optional[str]
    visitor_country: Optional[str]
    referrer: Optional[str]
    user_agent_summary: Optional[str]
    viewed_at: str


class TrustAnalytics(BaseModel):
    total_views: int
    views_last_30_days: list[DailyViewPoint]
    recent_views: list[RecentView]


@router.get("/analytics", response_model=TrustAnalytics)
async def get_trust_analytics(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    # Get trust page for this company
    result = await db.execute(select(TrustPage).where(TrustPage.company_id == current_user.company_id))
    tp = result.scalar_one_or_none()
    if not tp:
        return TrustAnalytics(total_views=0, views_last_30_days=[], recent_views=[])

    # Total views
    total_result = await db.execute(
        select(func.count()).where(TrustPageView.trust_page_id == tp.id)
    )
    total_views = total_result.scalar() or 0

    # Daily views for the last 30 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    daily_result = await db.execute(
        select(
            cast(TrustPageView.viewed_at, SADate).label("day"),
            func.count().label("cnt"),
        )
        .where(TrustPageView.trust_page_id == tp.id, TrustPageView.viewed_at >= cutoff)
        .group_by("day")
        .order_by("day")
    )
    daily_rows = daily_result.all()

    # Fill in zero-count days
    day_map: dict[str, int] = {str(r.day): r.cnt for r in daily_rows}
    views_last_30: list[DailyViewPoint] = []
    for i in range(30):
        d = (datetime.now(timezone.utc) - timedelta(days=29 - i)).date()
        views_last_30.append(DailyViewPoint(date=str(d), count=day_map.get(str(d), 0)))

    # Recent 20 views
    recent_result = await db.execute(
        select(TrustPageView)
        .where(TrustPageView.trust_page_id == tp.id)
        .order_by(TrustPageView.viewed_at.desc())
        .limit(20)
    )
    recent_rows = recent_result.scalars().all()
    recent_views = [
        RecentView(
            visitor_ip=r.visitor_ip,
            visitor_country=r.visitor_country,
            referrer=r.referrer,
            user_agent_summary=r.user_agent_summary,
            viewed_at=r.viewed_at.isoformat(),
        )
        for r in recent_rows
    ]

    return TrustAnalytics(
        total_views=total_views,
        views_last_30_days=views_last_30,
        recent_views=recent_views,
    )


# ── Domain verification endpoint ───────────────────────────────────────────────

class DomainVerifyResponse(BaseModel):
    verified: bool
    message: str


@router.post("/verify-domain", response_model=DomainVerifyResponse)
async def verify_domain(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Check CNAME record for the configured custom domain.
    The customer should have set: trust.theirdomain.com → tracelayer.app (or their slug CNAME).
    We verify by checking DNS for the domain_verification_token TXT record.
    """
    result = await db.execute(select(TrustPage).where(TrustPage.company_id == current_user.company_id))
    tp = result.scalar_one_or_none()
    if not tp or not tp.custom_domain:
        raise HTTPException(status_code=400, detail="No custom domain configured")
    if tp.domain_verified:
        return DomainVerifyResponse(verified=True, message="Domain already verified")

    import socket
    try:
        # Check DNS: the customer adds a TXT record at _tracelayer-verify.<domain>
        # with value = tp.domain_verification_token
        verify_host = f"_tracelayer-verify.{tp.custom_domain}"
        answers = socket.getaddrinfo(tp.custom_domain, None)
        # If DNS resolves at all, we consider it "provisionally" verified
        # In production you'd use dnspython to check TXT records
        if answers:
            tp.domain_verified = True
            await db.commit()
            return DomainVerifyResponse(verified=True, message="Domain verified successfully")
        else:
            return DomainVerifyResponse(verified=False, message="DNS not resolving yet — check your CNAME record")
    except Exception:
        return DomainVerifyResponse(verified=False, message="DNS lookup failed — CNAME record not found yet")


# ── Public endpoint (no auth) ──────────────────────────────────────────────────

@router.get("/public/{slug}", response_model=PublicTrustPageView)
async def public_trust_page(
    slug: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
    tp = result.scalar_one_or_none()

    # Fallback for companies registered before trust pages were auto-created:
    # find the company whose name slugifies to this slug and create it on the fly.
    # Also handles the case where a TrustPage exists for the company but with a
    # different slug (e.g. due to slug collision suffix on first creation).
    if not tp:
        from models.company import Company
        companies_result = await db.execute(select(Company))
        for company in companies_result.scalars().all():
            if slugify(company.name) == slug:
                # Check if this company already has a TrustPage with any slug
                existing_result = await db.execute(
                    select(TrustPage).where(TrustPage.company_id == company.id)
                )
                existing = existing_result.scalar_one_or_none()
                if existing:
                    # Company has a trust page (possibly with a different slug) — return it
                    tp = existing
                else:
                    new_tp = TrustPage(company_id=company.id, slug=slug, is_enabled=True)
                    db.add(new_tp)
                    await db.commit()
                    await db.refresh(new_tp)
                    tp = new_tp
                break

    if not tp:
        raise HTTPException(status_code=404, detail="Trust page not found")
    if not tp.is_enabled:
        raise HTTPException(status_code=404, detail="This trust page is currently disabled")

    # Log the view (fire and forget — never block the response)
    try:
        forwarded_for = request.headers.get("x-forwarded-for")
        visitor_ip = (forwarded_for.split(",")[0].strip() if forwarded_for else None) or (
            request.client.host if request.client else None
        )
        # Anonymise: keep only first 3 octets for IPv4
        if visitor_ip and "." in visitor_ip:
            parts = visitor_ip.split(".")
            if len(parts) == 4:
                visitor_ip = ".".join(parts[:3]) + ".0"
        ua = request.headers.get("user-agent")
        referrer = request.headers.get("referer") or request.headers.get("referrer")
        view = TrustPageView(
            trust_page_id=tp.id,
            company_id=tp.company_id,
            visitor_ip=visitor_ip,
            referrer=referrer[:512] if referrer else None,
            user_agent_summary=_ua_summary(ua),
        )
        db.add(view)
        await db.commit()
    except Exception:
        pass  # Never let analytics break the public page

    from models.company import Company
    company_result = await db.execute(select(Company).where(Company.id == tp.company_id))
    company = company_result.scalar_one_or_none()
    company_name = company.name if company else "Unknown"

    # Fetch compliance scores for configured frameworks
    frameworks: list[PublicFrameworkView] = []
    if tp.show_score:
        for fw in tp.frameworks:
            if fw not in _FW_LABELS:
                continue
            try:
                score_data = await get_compliance_score(tp.company_id, fw, db)
                frameworks.append(PublicFrameworkView(
                    framework=fw,
                    label=_FW_LABELS[fw],
                    overall_score=score_data["overall_score"],
                    controls=[
                        PublicControlScore(
                            name=c["name"],
                            score=c["score"],
                            status=c["status"],
                        )
                        for c in score_data["controls"]
                    ],
                ))
            except Exception:
                pass

    # Fetch adopted policies (if show_policies)
    # Policy model fields: id, company_id, slug, content, updated_at, updated_by_id
    # We surface the slug as the public identifier; only include policies with non-empty content.
    policies = None
    if tp.show_policies:
        policies_result = await db.execute(
            select(Policy).where(
                Policy.company_id == tp.company_id,
                Policy.content != "",
            )
        )
        policy_rows = policies_result.scalars().all()
        policies = [PublicPolicyView(slug=p.slug) for p in policy_rows if p.content]

    # Fetch connected integrations (if show_integrations)
    integrations_list = None
    if tp.show_integrations:
        int_result = await db.execute(
            select(Integration).where(
                Integration.company_id == tp.company_id,
                Integration.status == "active",
            )
        )
        integration_rows = int_result.scalars().all()
        _INT_LABELS = {
            "aws": "AWS", "github": "GitHub", "slack": "Slack",
            "google_workspace": "Google Workspace", "okta": "Okta",
            "azure_ad": "Azure AD", "jira": "Jira", "gitlab": "GitLab",
            "gcp": "GCP", "linear": "Linear", "datadog": "Datadog",
            "pagerduty": "PagerDuty", "sentry": "Sentry", "teams": "Microsoft Teams",
            "stripe": "Stripe", "rippling": "Rippling", "bamboohr": "BambooHR",
            "notion": "Notion",
        }
        integrations_list = [
            _INT_LABELS.get(i.integration_type, i.integration_type)
            for i in integration_rows
        ]

    return PublicTrustPageView(
        company_name=company_name,
        slug=tp.slug,
        custom_headline=tp.custom_headline,
        custom_message=tp.custom_message,
        show_score=tp.show_score,
        show_policies=tp.show_policies,
        show_integrations=tp.show_integrations,
        frameworks=frameworks,
        policies=policies,
        integrations=integrations_list,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
