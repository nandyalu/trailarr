from backend.app_logger import logger
from backend.core.tasks.api_refresh import api_refresh
from backend.core.tasks.image_refresh import refresh_images
from backend.core.tasks.task_runner import TaskRunner


# TODO: Import all scheduled tasks here and run them in the background.


def schedule_all_tasks():
    logger.info("Scheduling all background tasks!")
    runner = TaskRunner()
    # Schedule API Refresh to run every hour
    runner.schedule_task("api_refresh", 3600, api_refresh, timeout=600)
    # Schedule Image Refresh to run every 6 hours, start in 10 minutes from now
    runner.schedule_task(
        "refresh_images", 21600, refresh_images, task_args=(False,), delay=600
    )
    logger.info("All tasks scheduled!")


if __name__ == "__main__":
    schedule_all_tasks()
