"""Background task: daily audit log cleanup at 23:00."""
import asyncio
import logging
from datetime import datetime, timedelta

from config import settings
from database import SessionLocal
from services.system_audit_log_service import SystemAuditLogService

logger = logging.getLogger(__name__)


def _seconds_until_next_run(hour: int = 23, minute: int = 0) -> float:
    """Return seconds until the next occurrence of HH:MM (local time)."""
    now = datetime.now()
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def audit_log_cleanup_task() -> None:
    """Coroutine that wakes up daily at 23:00 and purges old audit logs."""
    retention_days = settings.AUDIT_LOG_RETENTION_DAYS
    logger.info(
        "Audit log cleanup task started. Retention: %d days. First run scheduled at 23:00.",
        retention_days,
    )

    while True:
        wait_secs = _seconds_until_next_run(hour=23, minute=0)
        logger.debug("Next audit log cleanup in %.0f seconds.", wait_secs)
        await asyncio.sleep(wait_secs)

        db = SessionLocal()
        try:
            deleted = SystemAuditLogService.delete_old_logs(db, retention_days)
            logger.info(
                "Audit log cleanup complete. Deleted %d records older than %d days.",
                deleted,
                retention_days,
            )
        except Exception as exc:
            logger.error("Audit log cleanup failed: %s", exc, exc_info=True)
        finally:
            db.close()

        # Sleep 60 s after running to avoid re-triggering within the same minute
        await asyncio.sleep(60)
