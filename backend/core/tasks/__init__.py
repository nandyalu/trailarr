import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from core.tasks.task_logging import add_all_event_listeners

# Get the timezone from the environment variable
timezone = os.getenv("TZ", "ETC")

# Initialize a MemeoryJobStore for the scheduler
jobstores = {"default": MemoryJobStore()}

# Create a scheduler instance and start it in FastAPI's lifespan context
scheduler = BackgroundScheduler(jobstores=jobstores, timezone=timezone)

add_all_event_listeners(scheduler)


# Tasks to be created
# Todo: ✔ 1. Schedule refresh from API every hour, cleanup if task is running for more than 10 mins
# Todo: ✔ 2. Schedule downloading of images, after reresh from the API
# Todo: ✔ 3. Schedule downloading of trailers every hour, 15 mins after refresh
# Todo: 4. Schedule cleanup of failed downloads every 6 hours
# Todo: 5. Schedule check for deleted trailers every 24 hours
