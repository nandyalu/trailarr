from fastapi import APIRouter

from core.tasks import task_logging
from core.tasks import schedules

# from core.tasks.task_runner import TaskRunner


tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("/schedules")
async def get_scheduled_tasks() -> list[task_logging.TaskInfo]:
    return task_logging.get_all_tasks()


@tasks_router.get("/queue")
async def get_task_queue() -> list[task_logging.QueueInfo]:
    return task_logging.get_all_queue()


@tasks_router.get("/run/{task_id}")
async def run_task_now(task_id: str) -> str:
    return schedules.run_task_now(task_id)
