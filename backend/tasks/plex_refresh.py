"""Scheduled task: Plex trailer flag refresh."""
import threading

from config.logging_context import with_logging_context
from services.plex_service import refresh_plex_trailer_flags


@with_logging_context
async def plex_refresh_job(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
) -> None:
    await refresh_plex_trailer_flags(_stop_event=_stop_event)
