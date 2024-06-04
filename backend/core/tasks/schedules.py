from app_logger import logger
from core.tasks.api_refresh import api_refresh
from core.tasks.download_trailers import download_missing_trailers
from core.tasks.image_refresh import refresh_images
from core.tasks.task_runner import TaskRunner


# TODO: Import all scheduled tasks here and run them in the background.


def schedule_all_tasks():
    logger.info("Scheduling all background tasks!")
    runner = TaskRunner()
    # Remove any existing task files
    runner.cleanup_tasks()
    # Schedule API Refresh to run every hour
    runner.schedule_task("api_refresh", 3600, api_refresh, timeout=600)
    # Schedule Image Refresh to run every 6 hours, start in 10 minutes from now
    runner.schedule_task(
        "refresh_images", 21600, refresh_images, task_args=(False,), delay=600
    )
    # Schedule trailer download task to run every hour, start in 15 minutes from now
    runner.schedule_task(
        "download_trailers", 3600, download_missing_trailers, delay=900
    )
    logger.info("All tasks scheduled!")


if __name__ == "__main__":
    schedule_all_tasks()
