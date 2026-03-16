import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin
from models.audit_session import AuditSession
from models.company import Company
from schemas.audit_session import AuditSessionCreate, AuditSessionResponse, PublicAuditView, PublicFrameworkView, PublicControlScore
from services.compliance_service import get_compliance_score

router = APIRouter(prefix="/audit-sessions", tags=["audit-sessions"])

_FW_LABELS = {"soc2": "SOC 2", "iso27001": "ISO 27001", "hipaa": "HIPAA"}


# ── Admin endpoints (require auth + admin role) ───────────────────────────────

@router.post("", response_model=AuditSessionResponse, status_code=201)
async def create_audit_session(
    body: AuditSessionCreate,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    expires_at = None
    if body.expires_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_days)

    session = AuditSession(
        company_id=current_user.company_id,
        created_by_id=current_user.id,
        label=body.label,
        expires_at=expires_at,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[AuditSessionResponse])
async def list_audit_sessions(
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditSession)
        .where(AuditSession.company_id == current_user.company_id)
        .order_by(AuditSession.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{session_id}", status_code=204)
async def revoke_audit_session(
    session_id: uuid.UUID,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditSession).where(
            AuditSession.id == session_id,
            AuditSession.company_id == current_user.company_id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found")
    await db.delete(session)
    await db.commit()


# ── Public endpoint (no auth) ─────────────────────────────────────────────────

@router.get("/view/{token}", response_model=PublicAuditView)
async def public_audit_view(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AuditSession).where(AuditSession.token == token)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Invalid or expired link")

    if session.expires_at and session.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="This link has expired")

    company_result = await db.execute(
        select(Company).where(Company.id == session.company_id)
    )
    company = company_result.scalar_one_or_none()

    frameworks: list[PublicFrameworkView] = []
    for fw in ["soc2", "iso27001", "hipaa"]:
        try:
            score_data = await get_compliance_score(session.company_id, fw, db)
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

    return PublicAuditView(
        company_name=company.name if company else "Unknown",
        session_label=session.label,
        generated_at=datetime.now(timezone.utc).isoformat(),
        frameworks=frameworks,
    )
