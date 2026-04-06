"""Penetration test tracking with per-finding detail (SOC 2 CC9.1)."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.pen_test_v2 import PenTestV2, PenTestFinding
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pen-tests-v2", tags=["pen-tests-v2"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class PenTestCreate(BaseModel):
    name: str
    vendor_name: Optional[str] = None
    test_type: str = "external"  # external | internal | web_app | api | cloud
    scope: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    report_url: Optional[str] = None
    executive_summary: Optional[str] = None


class PenTestUpdate(BaseModel):
    name: Optional[str] = None
    vendor_name: Optional[str] = None
    test_type: Optional[str] = None
    status: Optional[str] = None
    scope: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    report_url: Optional[str] = None
    executive_summary: Optional[str] = None


class FindingCreate(BaseModel):
    title: str
    severity: str = "medium"  # critical | high | medium | low | info
    description: Optional[str] = None
    recommendation: Optional[str] = None
    cvss_score: Optional[float] = None
    cve_id: Optional[str] = None
    ticket_url: Optional[str] = None


class FindingUpdate(BaseModel):
    status: Optional[str] = None  # open | in_remediation | remediated | accepted
    severity: Optional[str] = None
    remediation_notes: Optional[str] = None
    ticket_url: Optional[str] = None
    description: Optional[str] = None
    recommendation: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(status_code=422, detail=f"Invalid datetime: {value}")


def _finding_dict(f: PenTestFinding) -> dict:
    return {
        "id": str(f.id),
        "pen_test_id": str(f.pen_test_id),
        "company_id": str(f.company_id),
        "title": f.title,
        "severity": f.severity,
        "status": f.status,
        "description": f.description,
        "recommendation": f.recommendation,
        "cvss_score": f.cvss_score,
        "cve_id": f.cve_id,
        "remediation_notes": f.remediation_notes,
        "remediated_at": f.remediated_at.isoformat() if f.remediated_at else None,
        "ticket_url": f.ticket_url,
        "created_at": f.created_at.isoformat(),
        "updated_at": f.updated_at.isoformat(),
    }


def _test_dict(pt: PenTestV2, findings: list, *, include_findings: bool = False) -> dict:
    severity_counts: dict = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    open_count = 0
    for f in findings:
        if f.severity in severity_counts:
            severity_counts[f.severity] += 1
        if f.status == "open":
            open_count += 1

    d = {
        "id": str(pt.id),
        "company_id": str(pt.company_id),
        "name": pt.name,
        "vendor_name": pt.vendor_name,
        "test_type": pt.test_type,
        "status": pt.status,
        "scope": pt.scope,
        "started_at": pt.started_at.isoformat() if pt.started_at else None,
        "completed_at": pt.completed_at.isoformat() if pt.completed_at else None,
        "report_url": pt.report_url,
        "executive_summary": pt.executive_summary,
        "created_by_id": str(pt.created_by_id) if pt.created_by_id else None,
        "created_at": pt.created_at.isoformat(),
        "updated_at": pt.updated_at.isoformat(),
        "severity_counts": severity_counts,
        "open_count": open_count,
        "total_findings": len(findings),
    }
    if include_findings:
        d["findings"] = [_finding_dict(f) for f in findings]
    return d


async def _get_test_or_404(test_id: uuid.UUID, company_id: uuid.UUID, db: AsyncSession) -> PenTestV2:
    result = await db.execute(
        select(PenTestV2).where(
            PenTestV2.id == test_id,
            PenTestV2.company_id == company_id,
        )
    )
    pt = result.scalar_one_or_none()
    if not pt:
        raise HTTPException(status_code=404, detail="Pen test not found")
    return pt


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_pen_tests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PenTestV2)
        .where(PenTestV2.company_id == current_user.company_id)
        .order_by(PenTestV2.created_at.desc())
    )
    tests = result.scalars().all()
    out = []
    for pt in tests:
        findings_result = await db.execute(
            select(PenTestFinding).where(PenTestFinding.pen_test_id == pt.id)
        )
        findings = findings_result.scalars().all()
        out.append(_test_dict(pt, list(findings)))
    return out


@router.post("", status_code=201)
async def create_pen_test(
    body: PenTestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    pt = PenTestV2(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        name=body.name,
        vendor_name=body.vendor_name,
        test_type=body.test_type,
        status="scheduled",
        scope=body.scope,
        started_at=_parse_dt(body.started_at),
        completed_at=_parse_dt(body.completed_at),
        report_url=body.report_url,
        executive_summary=body.executive_summary,
        created_by_id=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(pt)
    await db.commit()
    await db.refresh(pt)
    return _test_dict(pt, [])


@router.get("/{test_id}")
async def get_pen_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = await _get_test_or_404(test_id, current_user.company_id, db)
    findings_result = await db.execute(
        select(PenTestFinding).where(PenTestFinding.pen_test_id == pt.id)
    )
    findings = findings_result.scalars().all()
    return _test_dict(pt, list(findings), include_findings=True)


@router.patch("/{test_id}")
async def update_pen_test(
    test_id: uuid.UUID,
    body: PenTestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = await _get_test_or_404(test_id, current_user.company_id, db)
    update_data = body.model_dump(exclude_unset=True)

    for field in ("started_at", "completed_at"):
        if field in update_data:
            update_data[field] = _parse_dt(update_data[field])

    for field, value in update_data.items():
        setattr(pt, field, value)

    pt.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(pt)

    findings_result = await db.execute(
        select(PenTestFinding).where(PenTestFinding.pen_test_id == pt.id)
    )
    findings = findings_result.scalars().all()
    return _test_dict(pt, list(findings))


@router.delete("/{test_id}", status_code=204)
async def delete_pen_test(
    test_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pt = await _get_test_or_404(test_id, current_user.company_id, db)
    await db.delete(pt)
    await db.commit()


@router.post("/{test_id}/findings", status_code=201)
async def add_finding(
    test_id: uuid.UUID,
    body: FindingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_test_or_404(test_id, current_user.company_id, db)
    now = datetime.now(timezone.utc)
    finding = PenTestFinding(
        id=uuid.uuid4(),
        pen_test_id=test_id,
        company_id=current_user.company_id,
        title=body.title,
        severity=body.severity,
        status="open",
        description=body.description,
        recommendation=body.recommendation,
        cvss_score=body.cvss_score,
        cve_id=body.cve_id,
        ticket_url=body.ticket_url,
        created_at=now,
        updated_at=now,
    )
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return _finding_dict(finding)


@router.patch("/{test_id}/findings/{finding_id}")
async def update_finding(
    test_id: uuid.UUID,
    finding_id: uuid.UUID,
    body: FindingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_test_or_404(test_id, current_user.company_id, db)
    result = await db.execute(
        select(PenTestFinding).where(
            PenTestFinding.id == finding_id,
            PenTestFinding.pen_test_id == test_id,
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(finding, field, value)

    if body.status == "remediated" and not finding.remediated_at:
        finding.remediated_at = datetime.now(timezone.utc)

    finding.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(finding)
    return _finding_dict(finding)


@router.delete("/{test_id}/findings/{finding_id}", status_code=204)
async def delete_finding(
    test_id: uuid.UUID,
    finding_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_test_or_404(test_id, current_user.company_id, db)
    result = await db.execute(
        select(PenTestFinding).where(
            PenTestFinding.id == finding_id,
            PenTestFinding.pen_test_id == test_id,
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    await db.delete(finding)
    await db.commit()
