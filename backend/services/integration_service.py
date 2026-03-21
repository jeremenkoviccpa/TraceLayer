import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.base import IntegrationAuthError
from integrations.registry import get_adapter
from models.integration import Integration
from services import data_flow_service
from utils.encryption import encrypt_credentials


async def list_integrations(company_id: uuid.UUID, db: AsyncSession) -> list[Integration]:
    result = await db.execute(
        select(Integration).where(Integration.company_id == company_id)
    )
    return list(result.scalars().all())


async def connect_integration(
    company_id: uuid.UUID,
    integration_type: str,
    credentials: dict,
    db: AsyncSession,
) -> Integration:
    adapter = get_adapter(integration_type)

    try:
        await adapter.connect(credentials)
    except IntegrationAuthError as e:
        raise ValueError(f"Credential validation failed: {e}")

    credentials_enc = encrypt_credentials(credentials)

    result = await db.execute(
        select(Integration).where(
            Integration.company_id == company_id,
            Integration.integration_type == integration_type,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.credentials_enc = credentials_enc
        existing.status = "active"
        existing.last_error = None
        integration = existing
    else:
        integration = Integration(
            company_id=company_id,
            integration_type=integration_type,
            credentials_enc=credentials_enc,
        )
        db.add(integration)

    await db.commit()
    await db.refresh(integration)
    await data_flow_service.add_flow_for_integration(company_id, integration_type, db)
    return integration


async def disconnect_integration(
    company_id: uuid.UUID,
    integration_type: str,
    db: AsyncSession,
) -> bool:
    result = await db.execute(
        select(Integration).where(
            Integration.company_id == company_id,
            Integration.integration_type == integration_type,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        return False
    await db.delete(integration)
    await db.commit()
    await data_flow_service.remove_flows_for_integration(company_id, integration_type, db)
    return True
