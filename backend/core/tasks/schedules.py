import threading
from typing import Callable

from app_logger import ModuleLogger
from config.logging_context import with_logging_context
from config.settings import app_settings
from core.base.database.manager.task_config import (
    create_task_config,
    get_task_config,
    update_task_config,
)
from core.base.database.models.task_config import (
    ScheduledTaskConfig,
    ScheduledTaskConfigRead,
)
import core.base.database.manager.connection as connection_manager
from core.base.database.models.connection import ArrType
from core.download.trailers.missing import download_missing_trailers
from core.tasks import scheduler
from core.tasks.api_refresh import api_refresh
from core.tasks.cleanup import delete_old_logs, trailer_cleanup
from core.tasks.files_scan import scan_all_media_folders
from core.tasks.image_refresh import refresh_images
from core.tasks.plex_trailer_refresh import refresh_plex_trailer_flags
from core.updates.docker_check import check_for_updates

logger = ModuleLogger("BackgroundTasks")


@with_logging_context
async def _check_for_update(*, _job_id: str | None = None):
    """Check for updates to the Docker image."""
    await check_for_updates()


@with_logging_context
async def _refresh_api_data(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Refreshes data from Arr APIs."""
    await api_refresh(_stop_event=_stop_event)


@with_logging_context
async def _refresh_images(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Refreshes all images in the database."""
    await refresh_images(_stop_event=_stop_event)


@with_logging_context
async def _scan_all_media_folders(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Scans the disk for trailers."""
    await scan_all_media_folders(_stop_event=_stop_event)


@with_logging_context
async def _cleanup_trailers(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Cleanup trailers without audio."""
    await delete_old_logs()
    await trailer_cleanup(_stop_event=_stop_event)


@with_logging_context
async def _download_missing_trailers(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Download missing trailers."""
    await download_missing_trailers(_stop_event=_stop_event)


@with_logging_context
async def _refresh_plex_trailer_flags(
    *, _job_id: str | None = None, _stop_event: threading.Event | None = None
):
    """Refresh the plex_trailer flag for all Plex-linked media items."""
    await refresh_plex_trailer_flags(_stop_event=_stop_event)


# Maps each stable task_key to its handler function.
TASK_REGISTRY: dict[str, Callable] = {
    "api_refresh": _refresh_api_data,
    "image_refresh": _refresh_images,
    "scan_disk": _scan_all_media_folders,
    "update_check": _check_for_update,
    "cleanup": _cleanup_trailers,
    "download_trailers": _download_missing_trailers,
    "plex_trailer_refresh": _refresh_plex_trailer_flags,
}


def _build_defaults() -> list[dict[str, str | float]]:
    """Return default task config dicts using current app settings."""
    monitor_interval_seconds = app_settings.monitor_interval * 60.0
    return [
        {
            "task_key": "api_refresh",
            "task_name": "Arr Data Refresh",
            "interval_seconds": monitor_interval_seconds,
            "delay_seconds": 30.0,
        },
        {
            "task_key": "update_check",
            "task_name": "Docker Update Check",
            "interval_seconds": 86400.0,
            "delay_seconds": 240.0,
        },
        {
            "task_key": "scan_disk",
            "task_name": "Scan All Media Folders",
            "interval_seconds": monitor_interval_seconds,
            "delay_seconds": 480.0,
        },
        {
            "task_key": "download_trailers",
            "task_name": "Download Missing Trailers",
            "interval_seconds": monitor_interval_seconds,
            "delay_seconds": 900.0,
        },
        {
            "task_key": "image_refresh",
            "task_name": "Image Refresh",
            "interval_seconds": 21600.0,
            "delay_seconds": 720.0,
        },
        {
            "task_key": "cleanup",
            "task_name": "Cleanup Task",
            "interval_seconds": 86400.0,
            "delay_seconds": 14400.0,
        },
    ]


def _get_or_create_config(
    task_key: str, defaults: dict[str, str | float]
) -> ScheduledTaskConfigRead:
    """Load config from DB; create from defaults if not yet persisted."""
    config = get_task_config(task_key)
    if config is None:
        config = create_task_config(ScheduledTaskConfig(**defaults))  # type: ignore
    return config


_PLEX_TRAILER_REFRESH_DEFAULTS: dict[str, str | float] = {
    "task_key": "plex_trailer_refresh",
    "task_name": "Refresh Plex Trailer Flags",
    "interval_seconds": 604800.0,  # 7 days
    "delay_seconds": 600.0,  # 10 minutes on startup
}


def schedule_all_tasks() -> None:
    """Schedule all background tasks, reading intervals from the DB.

    Falls back to hard-coded defaults and seeds the DB for any task
    that has no persisted configuration yet.
    """
    logger.info("Scheduling all background tasks!")
    for defaults in _build_defaults():
        task_key: str = defaults["task_key"]  # type: ignore
        config = _get_or_create_config(task_key, defaults)
        func = TASK_REGISTRY[task_key]
        scheduler.add_task(
            task_name=config.task_name,
            func=func,
            interval=config.interval_seconds,
            delay=config.delay_seconds,
            run_once=False,
        )
        # logger.info(f"Scheduled '{config.task_name}' (key={task_key!r})")

    # Schedule the Plex trailer refresh task only if a Plex connection exists.
    plex_connections = [
        c for c in connection_manager.read_all() if c.arr_type == ArrType.PLEX
    ]
    if plex_connections:
        config = _get_or_create_config(
            "plex_trailer_refresh", _PLEX_TRAILER_REFRESH_DEFAULTS
        )
        scheduler.add_task(
            task_name=config.task_name,
            func=TASK_REGISTRY["plex_trailer_refresh"],
            interval=config.interval_seconds,
            delay=config.delay_seconds,
            run_once=False,
        )
        logger.info("Scheduled 'Refresh Plex Trailer Flags' task.")

    logger.info("All tasks scheduled!")


def ensure_plex_trailer_refresh_scheduled(delay_seconds: float = 180.0) -> None:
    """Register the plex_trailer_refresh task, or trigger a one-shot run if already scheduled.

    Called when a Plex connection is added. On the first ever Plex connection
    the recurring weekly task is seeded into the DB and added to the scheduler.
    On subsequent Plex connection additions a one-shot run is triggered instead
    so the newly linked media items are scanned promptly.
    """
    existing_config = get_task_config("plex_trailer_refresh")
    func = TASK_REGISTRY["plex_trailer_refresh"]

    if existing_config is None:
        # First Plex connection — register the recurring weekly task.
        defaults = dict(_PLEX_TRAILER_REFRESH_DEFAULTS)
        defaults["delay_seconds"] = delay_seconds
        config = _get_or_create_config("plex_trailer_refresh", defaults)
        scheduler.add_task(
            task_name=config.task_name,
            func=func,
            interval=config.interval_seconds,
            delay=delay_seconds,
            run_once=False,
        )
        logger.info(
            f"Registered 'Refresh Plex Trailer Flags' task (first run in"
            f" {delay_seconds}s)."
        )
    else:
        # Task already registered — trigger an extra one-shot run.
        scheduler.add_task(
            task_name="Refresh Plex Trailer Flags (triggered)",
            func=func,
            interval=86400.0,
            delay=delay_seconds,
            run_once=True,
        )
        logger.info(
            f"Triggered one-shot 'Refresh Plex Trailer Flags' run in {delay_seconds}s."
        )


def reschedule_task(
    task_key: str,
    task_id: str,
    task_name: str,
    interval_seconds: float,
    delay_seconds: float,
) -> ScheduledTaskConfigRead:
    """Persist updated config and replace the live quiv task.

    Removes the old quiv task by its current name, then immediately
    re-registers it with the new parameters so the change takes effect
    without a restart.

    Returns the updated :class:`ScheduledTaskConfigRead`.
    """
    current = get_task_config(task_key)
    if current is None:
        raise ValueError(f"Unknown task_key: {task_key!r}")

    old_name = current.task_name
    updated = update_task_config(
        task_key, task_name, interval_seconds, delay_seconds
    )

    scheduler.remove_task(task_id)
    func = TASK_REGISTRY[task_key]
    scheduler.add_task(
        task_name=updated.task_name,
        func=func,
        interval=updated.interval_seconds,
        delay=updated.delay_seconds,
        run_once=False,
    )
    logger.info(
        f"Task '{old_name}' rescheduled as '{updated.task_name}'"
        f" (key={task_key!r})"
    )
    return updated


def run_task_now(task_id: str) -> str:
    """Run a scheduled task immediately.

    Args:
        task_id (str): The quiv task ID.
    Returns:
        str: Confirmation message.
    """
    if not task_id:
        return "Unable to trigger task, 'task_id' not provided!"
    scheduler.run_task_immediately(task_id)
    return f"'{task_id}' Task triggered successfully!"
