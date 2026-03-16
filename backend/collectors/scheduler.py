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


def schedule_weekly_reports() -> None:
    """Schedule weekly compliance digest emails every Monday at 09:00 UTC."""
    from services.weekly_report_service import send_weekly_reports

    scheduler.add_job(
        send_weekly_reports,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        id="weekly_compliance_reports",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled weekly compliance reports (Mon 09:00 UTC)")


def schedule_daily_alerts() -> None:
    """Schedule daily compliance alerts at 08:00 UTC."""
    from services.alert_service import run_daily_alerts_job

    scheduler.add_job(
        run_daily_alerts_job,
        "cron",
        hour=8,
        minute=0,
        id="daily_alerts",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled daily compliance alerts (08:00 UTC)")


def schedule_activation_nudges() -> None:
    """Schedule daily activation nudge emails at 10:00 UTC (Day 1, 3, 7)."""
    from services.activation_nudge_service import send_activation_nudges

    scheduler.add_job(
        send_activation_nudges,
        "cron",
        hour=10,
        minute=0,
        id="activation_nudges",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled activation nudge emails (10:00 UTC)")
