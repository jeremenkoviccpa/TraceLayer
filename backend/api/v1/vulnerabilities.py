import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.vulnerability import Vulnerability
from models.evidence import Evidence
from models.user import User
from schemas.vulnerability import VulnerabilityCreate, VulnerabilityResponse, VulnerabilityUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vulnerabilities", tags=["vulnerabilities"])


def _to_response(vuln: Vulnerability, owner_map: dict) -> VulnerabilityResponse:
    owner_id = vuln.owner_user_id
    return VulnerabilityResponse(
        id=str(vuln.id),
        company_id=str(vuln.company_id),
        title=vuln.title,
        cve_id=vuln.cve_id,
        severity=vuln.severity,
        status=vuln.status,
        affected_system=vuln.affected_system,
        discovered_at=vuln.discovered_at,
        due_date=vuln.due_date,
        resolved_at=vuln.resolved_at,
        description=vuln.description,
        remediation_notes=vuln.remediation_notes,
        owner_user_id=str(owner_id) if owner_id else None,
        owner_name=owner_map.get(owner_id) if owner_id else None,
        created_at=vuln.created_at,
        updated_at=vuln.updated_at,
    )


@router.get("", response_model=list[VulnerabilityResponse])
async def list_vulnerabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vulnerability)
        .where(Vulnerability.company_id == current_user.company_id)
        .order_by(Vulnerability.created_at.desc())
    )
    vulns = result.scalars().all()

    owner_ids = {v.owner_user_id for v in vulns if v.owner_user_id is not None}
    owner_map: dict = {}
    if owner_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(owner_ids))
        )
        for row in users_result.all():
            owner_map[row.id] = row.full_name or row.email

    return [_to_response(v, owner_map) for v in vulns]


@router.post("", response_model=VulnerabilityResponse, status_code=201)
async def create_vulnerability(
    body: VulnerabilityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_user_id: Optional[uuid.UUID] = None
    if body.owner_user_id:
        res = await db.execute(
            select(User).where(User.id == uuid.UUID(body.owner_user_id), User.company_id == current_user.company_id)
        )
        owner = res.scalar_one_or_none()
        if not owner:
            raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
        owner_user_id = owner.id

    vuln = Vulnerability(
        company_id=current_user.company_id,
        title=body.title,
        cve_id=body.cve_id,
        severity=body.severity,
        status=body.status,
        affected_system=body.affected_system,
        discovered_at=body.discovered_at,
        due_date=body.due_date,
        resolved_at=body.resolved_at,
        description=body.description,
        remediation_notes=body.remediation_notes,
        owner_user_id=owner_user_id,
    )
    db.add(vuln)
    await db.commit()
    await db.refresh(vuln)

    owner_map: dict = {}
    if owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(vuln, owner_map)


@router.patch("/{vuln_id}", response_model=VulnerabilityResponse)
async def update_vulnerability(
    vuln_id: uuid.UUID,
    body: VulnerabilityUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vuln_id, Vulnerability.company_id == current_user.company_id)
    )
    vuln = result.scalar_one_or_none()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    update_data = body.model_dump(exclude_unset=True)

    if "owner_user_id" in update_data:
        raw_id = update_data.pop("owner_user_id")
        if raw_id is None:
            vuln.owner_user_id = None
        else:
            res = await db.execute(
                select(User).where(User.id == uuid.UUID(raw_id), User.company_id == current_user.company_id)
            )
            owner = res.scalar_one_or_none()
            if not owner:
                raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
            vuln.owner_user_id = owner.id

    for field, value in update_data.items():
        setattr(vuln, field, value)

    await db.commit()
    await db.refresh(vuln)

    owner_map: dict = {}
    if vuln.owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == vuln.owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(vuln, owner_map)


@router.post("/auto-detect", status_code=200)
async def auto_detect_vulnerabilities(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Scan collected integration evidence and auto-create vulnerability records for known security issues."""
    evidence_result = await db.execute(
        select(Evidence).where(Evidence.company_id == current_user.company_id)
    )
    all_evidence = evidence_result.scalars().all()

    existing_result = await db.execute(
        select(Vulnerability.title).where(Vulnerability.company_id == current_user.company_id)
    )
    existing_titles = {row[0] for row in existing_result.all()}

    created = 0
    skipped = 0
    now = datetime.now(timezone.utc)

    for ev in all_evidence:
        data = ev.data or {}
        findings: list[dict] = []

        if ev.evidence_type == "iam_users":
            username = data.get("username", data.get("UserName", "unknown"))
            mfa_enabled = data.get("mfa_enabled", data.get("MFAEnabled", None))
            if mfa_enabled is False:
                findings.append({
                    "title": f"MFA not enabled — AWS IAM user: {username}",
                    "severity": "high",
                    "affected_system": "AWS IAM",
                    "description": f"IAM user '{username}' does not have MFA enabled. This increases the risk of account compromise if credentials are stolen.",
                    "remediation_notes": "Enable MFA for this IAM user in the AWS Console under IAM → Users → Security credentials.",
                })

        elif ev.evidence_type == "repositories":
            name = data.get("full_name", data.get("name", "unknown"))
            private = data.get("private", True)
            archived = data.get("archived", False)
            if not private and not archived:
                findings.append({
                    "title": f"Public GitHub repository: {name}",
                    "severity": "info",
                    "affected_system": "GitHub",
                    "description": f"Repository '{name}' is publicly visible. Verify this is intentional and does not expose sensitive code or credentials.",
                    "remediation_notes": "If this repository should not be public, change its visibility to Private in GitHub repository settings.",
                })

        for finding in findings:
            if finding["title"] in existing_titles:
                skipped += 1
                continue
            vuln = Vulnerability(
                company_id=current_user.company_id,
                title=finding["title"],
                severity=finding["severity"],
                status="open",
                affected_system=finding.get("affected_system"),
                description=finding.get("description"),
                remediation_notes=finding.get("remediation_notes"),
                discovered_at=now,
            )
            db.add(vuln)
            existing_titles.add(finding["title"])
            created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}


@router.delete("/{vuln_id}", status_code=204)
async def delete_vulnerability(
    vuln_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vulnerability).where(Vulnerability.id == vuln_id, Vulnerability.company_id == current_user.company_id)
    )
    vuln = result.scalar_one_or_none()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    await db.delete(vuln)
    await db.commit()
