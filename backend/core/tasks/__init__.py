import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from app_logger import ModuleLogger
from core.tasks.task_logging import add_all_event_listeners

# Get the timezone from the environment variable
timezone = os.getenv("TZ", "UTC")

# Initialize a MemeoryJobStore for the scheduler
jobstores = {"default": MemoryJobStore()}

# Get a logger
tasks_logger = ModuleLogger("Tasks")

# Create a scheduler instance and start it in FastAPI's lifespan context
scheduler = BackgroundScheduler(
    jobstores=jobstores, timezone=timezone, logger=tasks_logger
)

add_all_event_listeners(scheduler)
