"""Scheduled task: weekly TMDB video availability refresh."""
import threading

from config.logging_context import with_logging_context
from services.tmdb_service import refresh_tmdb_videos


@with_logging_context
async def tmdb_refresh_job(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
) -> None:
    await refresh_tmdb_videos(_stop_event=_stop_event)
