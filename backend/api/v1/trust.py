import secrets
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.integration import Integration
from models.policy import Policy
from models.trust_page import TrustPage, slugify
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
    )


# ── Public endpoint (no auth) ──────────────────────────────────────────────────

@router.get("/public/{slug}", response_model=PublicTrustPageView)
async def public_trust_page(
    slug: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(TrustPage).where(TrustPage.slug == slug))
    tp = result.scalar_one_or_none()
    if not tp:
        raise HTTPException(status_code=404, detail="Trust page not found")
    if not tp.is_enabled:
        raise HTTPException(status_code=404, detail="This trust page is currently disabled")

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
