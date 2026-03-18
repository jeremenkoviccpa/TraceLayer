import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.vulnerability import Vulnerability
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
