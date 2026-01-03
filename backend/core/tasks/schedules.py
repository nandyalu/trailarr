import asyncio
from datetime import datetime, timedelta, timezone

from app_logger import ModuleLogger
from config.logging_context import get_new_trace_id, with_logging_context
from config.settings import app_settings
from core.download.trailers.missing import download_missing_trailers
from core.tasks import scheduler
from core.tasks.api_refresh import api_refresh
from core.tasks.cleanup import delete_old_logs, trailer_cleanup
from core.tasks.files_scan import scan_all_media_folders
from core.tasks.image_refresh import refresh_images
from core.updates.docker_check import check_for_updates

# from core.tasks.task_runner import TaskRunner

logger = ModuleLogger("BackgroundTasks")


@with_logging_context
def run_async(task, *, trace_id: str) -> None:
    """Run the async task in a separate event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(task())
    new_loop.close()
    return


def _check_for_update(*, trace_id: str):
    """Check for updates to the Docker image."""
    run_async(check_for_updates, trace_id=trace_id)
    return


def _refresh_api_data(*, trace_id: str):
    """Refreshes data from Arr APIs."""
    run_async(api_refresh, trace_id=trace_id)
    return


def _refresh_images(*, trace_id: str):
    """Refreshes all images in the database."""
    run_async(refresh_images, trace_id=trace_id)
    return


def _scan_disk_for_trailers(*, trace_id: str):
    """Scans the disk for trailers."""
    run_async(scan_all_media_folders, trace_id=trace_id)
    return


def _cleanup_trailers(*, trace_id: str):
    """Cleanup trailers without audio."""

    async def _cleanup_tasks():
        await delete_old_logs()
        await trailer_cleanup()

    run_async(_cleanup_tasks, trace_id=trace_id)
    return


def _download_missing_trailers(*, trace_id: str):
    """Download missing trailers."""
    run_async(download_missing_trailers, trace_id=trace_id)
    return


def refresh_api_data_job():
    """
    Schedules a background job to refresh Arr API data. \n
        - Runs once an hour, first run in 30 seconds. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_refresh_api_data,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="hourly_refresh_api_data_job",
        name="Arr Data Refresh",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=30),
        max_instances=1,
    )
    logger.info("API Refresh job scheduled!")
    return


def image_refresh_job():
    """Schedules a background job to refresh images.\n
        - Runs once every 6 hours, first run in 12 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_refresh_images,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        hours=6,
        id="image_refresh_job",
        name="Image Refresh",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=720),
        max_instances=1,
    )
    logger.info("Image refresh job scheduled!")
    return


def scan_disk_for_trailers_job():
    """Schedules a background job to scan disk for trailers.\n
        - Runs once an hour, first run in 8 minute. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_scan_disk_for_trailers,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="scan_disk_for_trailers_job",
        name="Scan Disk for Trailers",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=480),
        max_instances=1,
    )
    logger.info("Scan Disk for Trailers job scheduled!")
    return


def update_check_job():
    """Schedules a background job to check for image updates.\n
        - Runs once a day, first run in 4 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_check_for_update,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        days=1,
        id="docker_update_check_job",
        name="Docker Update Check",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=240),
        max_instances=1,
    )
    logger.info("Update Check job scheduled!")
    return


def trailer_cleanup_job():
    """Schedules a background job to cleanup trailers and other things.\n
        - Runs once a day, first run in 4 hours. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_cleanup_trailers,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        days=1,
        id="cleanup_job",
        name="Cleanup Task",
        next_run_time=datetime.now(timezone.utc) + timedelta(hours=4),
        max_instances=1,
    )
    logger.info("Cleanup job scheduled!")
    return


def download_missing_trailers_job():
    """Schedules a background job to download missing trailers. \n
        Runs once an hour, first run in 15 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_download_missing_trailers,
        kwargs={"trace_id": get_new_trace_id()},
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="download_missing_trailers_job",
        name="Download Missing Trailers",
        next_run_time=datetime.now(timezone.utc) + timedelta(seconds=900),
        max_instances=1,
    )
    logger.info("Download Missing Trailers job scheduled!")
    return


def schedule_all_tasks():
    """Schedules all tasks for the application. \n
    Returns:
        None
    """
    logger.info("Scheduling all background tasks!")

    # Schedule API Refresh to run every hour
    refresh_api_data_job()

    # Schedule update check task to run once a day, start in 4 minutes from now
    update_check_job()

    # Schedule disk scan task to run every hour, start in 10 minutes from now
    scan_disk_for_trailers_job()

    # Schedule trailer download task to run every hour, start in 15 minutes from now
    download_missing_trailers_job()

    # Schedule Image Refresh to run every 6 hours, start in 10 minutes from now
    image_refresh_job()

    # Schedule trailer cleanup task to run every hour, start in 5 minutes from now
    trailer_cleanup_job()

    logger.info("All tasks scheduled!")
    return


def run_task_now(task_id: str) -> str:
    """Run a scheduled task immediately. \n
    Args:
        task_id (str): The id of the task to run. \n
    Returns:
        str: Message indicating the task was triggered."""
    if not task_id:
        return "Unable to trigger task, 'task_id' not provided!"
    _task = scheduler.get_job(task_id)
    if not _task:
        return "Unable to trigger task, Task with 'task_id' not found!"
    _name = _task.name
    _next_run_time = datetime.now(timezone.utc) + timedelta(
        seconds=1
    )  # Start in 1 second
    scheduler.modify_job(job_id=task_id, next_run_time=_next_run_time)
    return f"'{_name}' Task triggered successfully!"
