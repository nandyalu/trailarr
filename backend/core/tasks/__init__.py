import os
from typing import Any

from quiv import Quiv, Event

from app_logger import ModuleLogger
from api.v1.websockets import ws_manager

# Get the timezone from the environment variable
timezone = os.getenv("TZ", "UTC")

# # Get a logger
tasks_logger = ModuleLogger("Tasks")

# Create a scheduler instance
scheduler = Quiv(timezone=timezone, logger=tasks_logger)


# Add event listeners to the scheduler
async def on_job_started_event(event: Event, data: dict[str, Any]) -> None:
    await ws_manager.broadcast(
        f"'{data['task_name']}' Task Started",
        type="Info",
        reload="media,tasks",
    )


async def on_job_completed_event(event: Event, data: dict[str, Any]) -> None:
    await ws_manager.broadcast(
        f"'{data['task_name']}' Task Completed",
        type="Success",
        reload="media,tasks",
    )


async def on_job_failed_event(event: Event, data: dict[str, Any]) -> None:
    await ws_manager.broadcast(
        f"'{data['task_name']}' Task Failed",
        type="Error",
        reload="media,tasks",
    )


scheduler.add_listener(Event.JOB_STARTED, on_job_started_event)
scheduler.add_listener(Event.JOB_COMPLETED, on_job_completed_event)
scheduler.add_listener(Event.JOB_FAILED, on_job_failed_event)
