import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.incident import Incident
from models.user import User
from schemas.incident import IncidentCreate, IncidentResponse, IncidentUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_response(incident: Incident, reporter_map: dict) -> IncidentResponse:
    reporter_id = incident.reporter_user_id
    reporter_name = reporter_map.get(reporter_id) if reporter_id else None
    return IncidentResponse(
        id=str(incident.id),
        company_id=str(incident.company_id),
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        detected_at=incident.detected_at,
        resolved_at=incident.resolved_at,
        affected_systems=incident.affected_systems,
        root_cause=incident.root_cause,
        lessons_learned=incident.lessons_learned,
        reporter_user_id=str(reporter_id) if reporter_id else None,
        reporter_name=reporter_name,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
    )


@router.get("", response_model=list[IncidentResponse])
async def list_incidents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Incident)
        .where(Incident.company_id == current_user.company_id)
        .order_by(Incident.created_at.desc())
    )
    incidents = result.scalars().all()

    reporter_ids = {i.reporter_user_id for i in incidents if i.reporter_user_id is not None}
    reporter_map: dict = {}
    if reporter_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(reporter_ids))
        )
        for row in users_result.all():
            reporter_map[row.id] = row.full_name or row.email

    return [_to_response(i, reporter_map) for i in incidents]


@router.post("", response_model=IncidentResponse, status_code=201)
async def create_incident(
    body: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reporter_user_id: Optional[uuid.UUID] = None
    if body.reporter_user_id:
        res = await db.execute(
            select(User).where(
                User.id == uuid.UUID(body.reporter_user_id),
                User.company_id == current_user.company_id,
            )
        )
        reporter = res.scalar_one_or_none()
        if not reporter:
            raise HTTPException(status_code=400, detail="reporter_user_id does not belong to your company")
        reporter_user_id = reporter.id

    incident = Incident(
        company_id=current_user.company_id,
        title=body.title,
        description=body.description,
        severity=body.severity,
        status=body.status,
        detected_at=body.detected_at,
        resolved_at=body.resolved_at,
        affected_systems=body.affected_systems,
        root_cause=body.root_cause,
        lessons_learned=body.lessons_learned,
        reporter_user_id=reporter_user_id,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)

    reporter_map: dict = {}
    if reporter_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == reporter_user_id))
        row = res.one_or_none()
        if row:
            reporter_map[row.id] = row.full_name or row.email

    return _to_response(incident, reporter_map)


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: uuid.UUID,
    body: IncidentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id, Incident.company_id == current_user.company_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    update_data = body.model_dump(exclude_unset=True)

    if "reporter_user_id" in update_data:
        raw_id = update_data.pop("reporter_user_id")
        if raw_id is None:
            incident.reporter_user_id = None
        else:
            res = await db.execute(
                select(User).where(User.id == uuid.UUID(raw_id), User.company_id == current_user.company_id)
            )
            reporter = res.scalar_one_or_none()
            if not reporter:
                raise HTTPException(status_code=400, detail="reporter_user_id does not belong to your company")
            incident.reporter_user_id = reporter.id

    for field, value in update_data.items():
        setattr(incident, field, value)

    await db.commit()
    await db.refresh(incident)

    reporter_map: dict = {}
    if incident.reporter_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == incident.reporter_user_id))
        row = res.one_or_none()
        if row:
            reporter_map[row.id] = row.full_name or row.email

    return _to_response(incident, reporter_map)


@router.delete("/{incident_id}", status_code=204)
async def delete_incident(
    incident_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Incident).where(Incident.id == incident_id, Incident.company_id == current_user.company_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    await db.delete(incident)
    await db.commit()
