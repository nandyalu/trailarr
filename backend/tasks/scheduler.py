import os

from quiv import Quiv, Event, Task, Job

from app_logger import ModuleLogger
from ws.manager import ws_manager

timezone = os.getenv("TZ", "UTC")
tasks_logger = ModuleLogger("Tasks")
scheduler = Quiv(timezone=timezone, logger=tasks_logger)


async def on_job_started_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(f"'{task.task_name}' Task Started", type="Info", reload="media,tasks")


async def on_job_completed_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(f"'{task.task_name}' Task Completed", type="Success", reload="media,tasks")


async def on_job_failed_event(event: Event, task: Task, job: Job) -> None:
    await ws_manager.broadcast(f"'{task.task_name}' Task Failed", type="Error", reload="media,tasks")


scheduler.add_listener(Event.JOB_STARTED, on_job_started_event)
scheduler.add_listener(Event.JOB_COMPLETED, on_job_completed_event)
scheduler.add_listener(Event.JOB_FAILED, on_job_failed_event)
