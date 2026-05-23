"""Scheduled task: media image refresh."""
import threading

from config.logging_context import with_logging_context
from services.image_service import refresh_images


@with_logging_context
async def image_refresh_job(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
) -> None:
    await refresh_images(_stop_event=_stop_event)
