from pytz import utc

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore

from app_logger import ModuleLogger
from core.tasks.task_logging import add_all_event_listeners

# Get the timezone from the environment variable
timezone = utc  # os.getenv("TZ", "UTC")

# Initialize a MemeoryJobStore for the scheduler
jobstores = {"default": MemoryJobStore()}

# Configure executors
executors = {
    "default": ThreadPoolExecutor(10),
    "processpool": ProcessPoolExecutor(10),
}

# Get a logger
tasks_logger = ModuleLogger("Tasks")

# Create a scheduler instance and start it in FastAPI's lifespan context
scheduler = BackgroundScheduler(
    jobstores=jobstores,
    timezone=timezone,
    logger=tasks_logger,
    executors=executors,
)

add_all_event_listeners(scheduler)
