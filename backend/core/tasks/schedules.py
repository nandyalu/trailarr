import asyncio
from datetime import datetime, timedelta

from app_logger import ModuleLogger
from config.settings import app_settings
from core.tasks import scheduler
from core.tasks.api_refresh import api_refresh
from core.tasks.cleanup import trailer_cleanup
from core.tasks.download_trailers import download_missing_trailers
from core.tasks.image_refresh import refresh_images

# from core.tasks.task_runner import TaskRunner

logger = ModuleLogger("BackgroundTasks")


def run_async(task) -> None:
    """Run the async task in a separate event loop."""
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    new_loop.run_until_complete(task())
    new_loop.close()
    return


def _refresh_api_data():
    """Refreshes data from Arr APIs."""
    run_async(api_refresh)
    return


def _refresh_images():
    """Refreshes all images in the database."""
    run_async(refresh_images)
    return


def _cleanup_trailers():
    """Cleanup trailers without audio."""
    run_async(trailer_cleanup)
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
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="hourly_refresh_api_data_job",
        name="Arr Data Refresh",
        next_run_time=datetime.now() + timedelta(seconds=30),
        max_instances=1,
    )
    logger.info("API Refresh job scheduled!")
    return


def image_refresh_job():
    """Schedules a background job to refresh images.\n
        - Runs once every 6 hours, first run in 10 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_refresh_images,
        trigger="interval",
        hours=6,
        id="image_refresh_job",
        name="Image Refresh",
        next_run_time=datetime.now() + timedelta(seconds=600),
        max_instances=1,
    )
    logger.info("Image refresh job scheduled!")
    return


def trailer_cleanup_job():
    """Schedules a background job to cleanup trailers.\n
        - Runs once an hour (default, or monitor_interval), first run in 5 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=_cleanup_trailers,
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="trailer_cleanup_job",
        name="Trailer Cleanup",
        next_run_time=datetime.now() + timedelta(seconds=300),
        max_instances=1,
    )
    logger.info("Trailer Cleanup job scheduled!")
    return


def download_missing_trailers_job():
    """Schedules a background job to download missing trailers. \n
        Runs once an hour, first run in 15 minutes. \n
    Returns:
        None
    """
    scheduler.add_job(
        func=download_missing_trailers,
        trigger="interval",
        minutes=app_settings.monitor_interval,
        id="download_missing_trailers_job",
        name="Download Missing Trailers",
        next_run_time=datetime.now() + timedelta(seconds=900),
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

    # Schedule Image Refresh to run every 6 hours, start in 10 minutes from now
    image_refresh_job()

    # Schedule trailer cleanup task to run every hour, start in 5 minutes from now
    trailer_cleanup_job()

    # Schedule trailer download task to run every hour, start in 15 minutes from now
    download_missing_trailers_job()

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
    _next_run_time = datetime.now() + timedelta(seconds=1)  # Start in 1 second
    scheduler.modify_job(job_id=task_id, next_run_time=_next_run_time)
    return f"'{_name}' Task triggered successfully!"
