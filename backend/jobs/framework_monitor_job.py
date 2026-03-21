from __future__ import annotations

"""
Weekly job: check all framework source manifests for updates.
Runs every Monday at 09:00 UTC.
"""
import logging

from core.database import AsyncSessionLocal
from services.framework_monitor_service import check_all_frameworks

logger = logging.getLogger(__name__)


async def run_framework_monitor() -> None:
    """Check all framework source manifests for changes."""
    logger.info("Running weekly framework source monitor")
    try:
        async with AsyncSessionLocal() as db:
            results = await check_all_frameworks(db)
            changed = [r for r in results if r.get("changed")]
            logger.info(
                "Framework monitor complete: %d checked, %d changed",
                len(results),
                len(changed),
            )
            if changed:
                logger.warning(
                    "Frameworks with pending updates: %s",
                    [r["framework"] for r in changed],
                )
    except Exception as exc:
        logger.exception("Framework monitor job failed: %s", exc)
