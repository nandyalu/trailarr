import asyncio
from datetime import datetime, timedelta
from time import sleep
from app_logger import ModuleLogger, logger
from core.tasks import scheduler
from core.tasks.api_refresh import api_refresh
from core.tasks.download_trailers import download_missing_trailers
from core.tasks.image_refresh import refresh_images

# from core.tasks.task_runner import TaskRunner

logging = ModuleLogger("BackgroundTasks")


def run_async(task) -> None:
    """Run the async task in a separate event loop."""
    sleep(10)
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
        hours=1,
        id="hourly_refresh_api_data_job",
        name="Arr Data Refresh",
        next_run_time=datetime.now() + timedelta(seconds=30),
        max_instances=1,
    )
    logging.info("API Refresh job scheduled!")
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
    logging.info("Image refresh job scheduled!")
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
        hours=1,
        id="download_missing_trailers_job",
        name="Download Missing Trailers",
        next_run_time=datetime.now() + timedelta(seconds=900),
        max_instances=1,
    )
    logging.info("Download Missing Trailers job scheduled!")
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

    # Schedule trailer download task to run every hour, start in 15 minutes from now
    download_missing_trailers_job()

    logger.info("All tasks scheduled!")


if __name__ == "__main__":
    schedule_all_tasks()
    scheduler.start()
    # print(get_all_jobs())
    while True:
        sleep(10)
        # print(get_all_jobs())
        print("Running")
