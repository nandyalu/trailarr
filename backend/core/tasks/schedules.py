from backend.logger import logger
from backend.core.tasks.api_refresh import api_refresh
from backend.core.tasks.task_runner import TaskRunner


# TODO: Import all scheduled tasks here and run them in the background.


def schedule_all_tasks():
    logger.info("Scheduling all background tasks!")
    runner = TaskRunner()
    # Schedule API Refresh to run every hour
    runner.schedule_task("api_refresh", 3600, api_refresh, timeout=600)

    logger.info("All tasks scheduled!")


if __name__ == "__main__":
    schedule_all_tasks()
