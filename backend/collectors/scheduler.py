import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors.runner import run_collector_job

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def schedule_integration(
    company_id: str,
    integration_type: str,
    interval_hours: int = 24,
) -> None:
    job_id = f"collect_{company_id}_{integration_type}"
    scheduler.add_job(
        run_collector_job,
        "interval",
        hours=interval_hours,
        args=[company_id, integration_type],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,  # allow up to 1h late if server was down
    )
    logger.info("Scheduled collection: %s every %dh", job_id, interval_hours)


def unschedule_integration(company_id: str, integration_type: str) -> None:
    job_id = f"collect_{company_id}_{integration_type}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Removed schedule: %s", job_id)


async def start() -> None:
    scheduler.start()
    logger.info("Scheduler started")


async def stop() -> None:
    scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped")
