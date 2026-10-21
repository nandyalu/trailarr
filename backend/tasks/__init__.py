import atexit
import os

from quiv import Quiv, Event, Task, Job

from app_logger import ModuleLogger
from api.v1.websockets import ws_manager

# Get the timezone from the environment variable
timezone = os.getenv("TZ", "UTC")

# # Get a logger
tasks_logger = ModuleLogger("Tasks")

# Create a scheduler instance
scheduler = Quiv(timezone=timezone, logger=tasks_logger)

# Quiv writes its state to a database in the system temp folder when the
# scheduler is built, and only shutdown() deletes that file. The lifespan in
# main.py calls shutdown(). Tests and one-off scripts import this package and
# exit without the lifespan, and each of them left one file in /tmp.
# shutdown_scheduler() stops the scheduler once, from the lifespan or at exit.
# A second quiv shutdown() raises, so the guard is not optional.
_scheduler_stopped = False


def shutdown_scheduler(timeout: float | None = None) -> None:
    """Stop the scheduler and remove its database. A second call does nothing."""
    global _scheduler_stopped
    if _scheduler_stopped:
        return
    _scheduler_stopped = True
    scheduler.shutdown(timeout=timeout)


atexit.register(shutdown_scheduler, timeout=1)


# Add event listeners to the scheduler
async def on_job_started_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(
        f"'{task.task_name}' Task Started",
        type="Info",
        reload="media,tasks,downloading",
    )


async def on_job_completed_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(
        f"'{task.task_name}' Task Completed",
        type="Success",
        reload="media,tasks,downloading",
    )


async def on_job_failed_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(
        f"'{task.task_name}' Task Failed",
        type="Error",
        reload="media,tasks,downloading",
    )


scheduler.add_listener(Event.JOB_STARTED, on_job_started_event)
scheduler.add_listener(Event.JOB_COMPLETED, on_job_completed_event)
scheduler.add_listener(Event.JOB_FAILED, on_job_failed_event)
