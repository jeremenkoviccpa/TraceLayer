import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from collectors.runner import run_collector_job

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()



def schedule_integration(
    company_id: str,
    integration_type: str,
    interval_hours: int = 24,
    run_now: bool = False,
) -> None:
    from datetime import datetime, timezone, timedelta
    job_id = f"collect_{company_id}_{integration_type}"
    # run_now=True: fire 30s after scheduling (used on connect or startup retry)
    next_run = datetime.now(timezone.utc) + timedelta(seconds=30) if run_now else None
    kwargs: dict = dict(
        trigger="interval",
        hours=interval_hours,
        args=[company_id, integration_type],
        id=job_id,
        replace_existing=True,
        misfire_grace_time=3600,
    )
    if next_run:
        kwargs["next_run_time"] = next_run
    scheduler.add_job(run_collector_job, **kwargs)
    logger.info("Scheduled collection: %s every %dh%s", job_id, interval_hours, " (immediate)" if run_now else "")


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


def schedule_partner_nudges() -> None:
    """Schedule daily partner onboarding nudge emails at 10:30 UTC (Day 1, 3, 7)."""
    from services.partner_nudge_service import send_partner_nudges

    scheduler.add_job(
        send_partner_nudges,
        "cron",
        hour=10,
        minute=30,
        id="partner_nudges",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled partner onboarding nudge emails (10:30 UTC)")


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


def schedule_risk_detection() -> None:
    """Schedule nightly automated risk detection at 02:00 UTC."""
    from services.risk_detector import run_risk_detection_all_companies

    scheduler.add_job(
        run_risk_detection_all_companies,
        "cron",
        hour=2,
        minute=0,
        id="auto_risk_detection",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled auto risk detection (02:00 UTC)")


def schedule_auto_detection() -> None:
    """Schedule nightly training + background check auto-detection at 02:15 UTC."""
    from services.auto_detector import run_auto_detection_all_companies

    scheduler.add_job(
        run_auto_detection_all_companies,
        "cron",
        hour=2,
        minute=15,
        id="auto_detection",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled auto detection (02:15 UTC)")


def schedule_detection_digest() -> None:
    """Nightly digest email summarising overnight auto-detections at 03:00 UTC."""
    from services.detection_digest_service import run_detection_digest_all_companies

    scheduler.add_job(
        run_detection_digest_all_companies,
        "cron",
        hour=3,
        minute=0,
        id="detection_digest",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled detection digest emails (03:00 UTC)")


def schedule_control_owner_reminders() -> None:
    """Weekly reminder emails to control owners with pending controls (Mon 09:30 UTC)."""
    from services.control_owner_service import run_control_owner_reminders

    scheduler.add_job(
        run_control_owner_reminders,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=30,
        id="control_owner_reminders",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled control owner reminders (Mon 09:30 UTC)")


def schedule_framework_monitor() -> None:
    """Weekly check of all framework source manifests for updates (Mon 09:00 UTC)."""
    from jobs.framework_monitor_job import run_framework_monitor

    scheduler.add_job(
        run_framework_monitor,
        "cron",
        day_of_week="mon",
        hour=9,
        minute=0,
        id="framework_source_monitor",
        replace_existing=True,
        misfire_grace_time=3600,
    )
    logger.info("Scheduled framework source monitor (Mon 09:00 UTC)")
