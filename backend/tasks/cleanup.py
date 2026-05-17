"""Scheduled tasks: trailer cleanup and log pruning."""
import threading

from config.logging_context import with_logging_context
from config.logs import manager as logs_manager
from app_logger import ModuleLogger
from services.cleanup_service import trailer_cleanup

logger = ModuleLogger("CleanupTasks")


async def delete_old_logs():  # pragma: no cover
    logger.info("Running old logs cleanup task...")
    deleted_count = await logs_manager.delete_old_logs(30)
    logger.info(f"Old logs cleanup task completed. Deleted {deleted_count} logs older than 30 days.")


@with_logging_context
async def trailer_cleanup_job(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
) -> None:
    await trailer_cleanup(_stop_event=_stop_event)
