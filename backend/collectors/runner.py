import logging
import uuid

from core.database import AsyncSessionLocal
from services.collector_service import run_collection

logger = logging.getLogger(__name__)


async def run_collector_job(company_id: str, integration_type: str) -> None:
    """
    Top-level job function called by the scheduler or background tasks.
    Creates its own DB session so it can run outside request context.
    """
    logger.info("Collector job started: company=%s integration=%s", company_id, integration_type)
    async with AsyncSessionLocal() as db:
        try:
            count = await run_collection(uuid.UUID(company_id), integration_type, db)
            logger.info(
                "Collector job done: company=%s integration=%s records=%d",
                company_id, integration_type, count,
            )
        except Exception as e:
            logger.error(
                "Collector job error: company=%s integration=%s error=%s",
                company_id, integration_type, e,
            )
