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
from core.download.trailers.missing import download_missing_trailers
from core.tasks import scheduler
from core.tasks.api_refresh import api_refresh
from core.tasks.cleanup import delete_old_logs, trailer_cleanup
from core.tasks.files_scan import scan_all_media_folders
from core.tasks.image_refresh import refresh_images
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


# Maps each stable task_key to its handler function.
TASK_REGISTRY: dict[str, Callable] = {
    "api_refresh": _refresh_api_data,
    "image_refresh": _refresh_images,
    "scan_disk": _scan_all_media_folders,
    "update_check": _check_for_update,
    "cleanup": _cleanup_trailers,
    "download_trailers": _download_missing_trailers,
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
    logger.info("All tasks scheduled!")


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
