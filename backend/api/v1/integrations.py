from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from collectors.runner import run_collector_job
from collectors.scheduler import schedule_integration, unschedule_integration
from core.database import get_db
from core.deps import get_current_user
from models.user import User
from schemas.integrations import ConnectRequest, IntegrationResponse
from services.billing_service import check_integration_limit
from services.integration_service import (
    connect_integration,
    disconnect_integration,
    list_integrations,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("", response_model=list[IntegrationResponse])
async def get_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_integrations(current_user.company_id, db)


@router.post("/connect", response_model=IntegrationResponse, status_code=201)
async def connect(
    body: ConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        body.validate_type()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        await check_integration_limit(current_user.company_id, db)
    except ValueError as e:
        raise HTTPException(status_code=402, detail=str(e))

    try:
        integration = await connect_integration(
            current_user.company_id,
            body.integration_type,
            body.credentials,
            db,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Schedule recurring collection after successful connect
    schedule_integration(
        str(current_user.company_id),
        body.integration_type,
    )

    return integration


@router.delete("/{integration_type}", status_code=204)
async def disconnect(
    integration_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    removed = await disconnect_integration(current_user.company_id, integration_type, db)
    if not removed:
        raise HTTPException(status_code=404, detail="Integration not found")

    unschedule_integration(str(current_user.company_id), integration_type)


@router.post("/{integration_type}/collect", status_code=202)
async def trigger_collect(
    integration_type: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(
        run_collector_job,
        str(current_user.company_id),
        integration_type,
    )
    return {"message": "Collection job queued"}
