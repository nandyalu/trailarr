import threading
from typing import Callable

from app_logger import ModuleLogger
from config.logging_context import with_logging_context
import db.repos.connection as connection_repo
import db.repos.task_config as task_config_repo
from db.models.connection import ArrType
from db.models.task_config import ScheduledTaskConfig, ScheduledTaskConfigRead
from download.pipeline import download_missing_trailers
from tasks.scheduler import scheduler
from tasks.api_refresh import api_refresh
from tasks.cleanup import delete_old_logs
from tasks.files_scan import scan_all_media_folders
from services.cleanup_service import trailer_cleanup
from services.image_service import refresh_images
from services.plex_service import refresh_plex_trailer_flags
from services.tmdb_service import refresh_tmdb_videos
from utils.docker_check import check_for_updates

logger = ModuleLogger("BackgroundTasks")


@with_logging_context
async def _check_for_update(*, _job_id: str | None = None):
    await check_for_updates()


@with_logging_context
async def _refresh_api_data(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await api_refresh(_stop_event=_stop_event)


@with_logging_context
async def _refresh_images(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await refresh_images(_stop_event=_stop_event)


@with_logging_context
async def _scan_all_media_folders(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await scan_all_media_folders(_stop_event=_stop_event)


@with_logging_context
async def _cleanup_trailers(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await delete_old_logs()
    await trailer_cleanup(_stop_event=_stop_event)


@with_logging_context
async def _download_missing_trailers(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await download_missing_trailers(_stop_event=_stop_event)


@with_logging_context
async def _refresh_plex_trailer_flags(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await refresh_plex_trailer_flags(_stop_event=_stop_event)


@with_logging_context
async def _refresh_tmdb_videos(*, _job_id: str | None = None, _stop_event: threading.Event | None = None):
    await refresh_tmdb_videos(_stop_event=_stop_event)


TASK_REGISTRY: dict[str, Callable] = {
    "api_refresh": _refresh_api_data,
    "image_refresh": _refresh_images,
    "scan_disk": _scan_all_media_folders,
    "update_check": _check_for_update,
    "cleanup": _cleanup_trailers,
    "download_trailers": _download_missing_trailers,
    "plex_trailer_refresh": _refresh_plex_trailer_flags,
    "tmdb_refresh": _refresh_tmdb_videos,
}

_DEFAULT_MONITOR_INTERVAL_SECONDS = 3600.0


def _build_defaults() -> list[dict[str, str | float]]:
    return [
        {"task_key": "api_refresh", "task_name": "Arr Data Refresh", "interval_seconds": _DEFAULT_MONITOR_INTERVAL_SECONDS, "delay_seconds": 30.0},
        {"task_key": "update_check", "task_name": "Docker Update Check", "interval_seconds": 86400.0, "delay_seconds": 240.0},
        {"task_key": "scan_disk", "task_name": "Scan All Media Folders", "interval_seconds": _DEFAULT_MONITOR_INTERVAL_SECONDS, "delay_seconds": 480.0},
        {"task_key": "download_trailers", "task_name": "Download Missing Trailers", "interval_seconds": _DEFAULT_MONITOR_INTERVAL_SECONDS, "delay_seconds": 900.0},
        {"task_key": "image_refresh", "task_name": "Image Refresh", "interval_seconds": 21600.0, "delay_seconds": 720.0},
        {"task_key": "cleanup", "task_name": "Cleanup Task", "interval_seconds": 86400.0, "delay_seconds": 14400.0},
    ]


def _get_or_create_config(task_key: str, defaults: dict[str, str | float]) -> ScheduledTaskConfigRead:
    config = task_config_repo.get(task_key)
    if config is None:
        config = task_config_repo.create(ScheduledTaskConfig(**defaults))  # type: ignore
    return config


_PLEX_TRAILER_REFRESH_DEFAULTS: dict[str, str | float] = {
    "task_key": "plex_trailer_refresh",
    "task_name": "Refresh Plex Trailer Flags",
    "interval_seconds": 604800.0,
    "delay_seconds": 600.0,
}

_TMDB_REFRESH_DEFAULTS: dict[str, str | float] = {
    "task_key": "tmdb_refresh",
    "task_name": "Refresh TMDB Videos",
    "interval_seconds": 604800.0,
    "delay_seconds": 1800.0,
}


def schedule_all_tasks() -> None:
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

    tmdb_config = _get_or_create_config("tmdb_refresh", _TMDB_REFRESH_DEFAULTS)
    scheduler.add_task(
        task_name=tmdb_config.task_name,
        func=TASK_REGISTRY["tmdb_refresh"],
        interval=tmdb_config.interval_seconds,
        delay=tmdb_config.delay_seconds,
        run_once=False,
    )

    plex_connections = [c for c in connection_repo.read_all() if c.arr_type == ArrType.PLEX]
    if plex_connections:
        config = _get_or_create_config("plex_trailer_refresh", _PLEX_TRAILER_REFRESH_DEFAULTS)
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
    func = TASK_REGISTRY["plex_trailer_refresh"]
    config = _get_or_create_config("plex_trailer_refresh", _PLEX_TRAILER_REFRESH_DEFAULTS)
    all_tasks = scheduler.get_all_tasks(include_run_once=False)
    is_scheduled = any(t.task_name == config.task_name for t in all_tasks)
    if not is_scheduled:
        scheduler.add_task(
            task_name=config.task_name,
            func=func,
            interval=config.interval_seconds,
            delay=delay_seconds,
            run_once=False,
        )
        logger.info(f"Registered 'Refresh Plex Trailer Flags' task (first run in {delay_seconds}s).")
    else:
        scheduler.add_task(
            task_name="Refresh Plex Trailer Flags (triggered)",
            func=func,
            interval=86400.0,
            delay=delay_seconds,
            run_once=True,
        )
        logger.info(f"Triggered one-shot 'Refresh Plex Trailer Flags' run in {delay_seconds}s.")


def reschedule_task(
    task_key: str,
    task_id: str,
    task_name: str,
    interval_seconds: float,
    delay_seconds: float,
) -> ScheduledTaskConfigRead:
    current = task_config_repo.get(task_key)
    if current is None:
        raise ValueError(f"Unknown task_key: {task_key!r}")
    old_name = current.task_name
    updated = task_config_repo.update(task_key, task_name, interval_seconds, delay_seconds)
    scheduler.remove_task(task_id)
    func = TASK_REGISTRY[task_key]
    scheduler.add_task(
        task_name=updated.task_name,
        func=func,
        interval=updated.interval_seconds,
        delay=updated.delay_seconds,
        run_once=False,
    )
    logger.info(f"Task '{old_name}' rescheduled as '{updated.task_name}' (key={task_key!r})")
    return updated


def run_task_now(task_id: str) -> str:
    if not task_id:
        return "Unable to trigger task, 'task_id' not provided!"
    scheduler.run_task_immediately(task_id)
    return f"'{task_id}' Task triggered successfully!"
