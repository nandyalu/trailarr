from fastapi import APIRouter

from core.tasks.task_logging import get_all_jobs, get_all_queue

# from core.tasks.task_runner import TaskRunner


tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("/schedules")
async def get_scheduled_tasks():
    return get_all_jobs()


@tasks_router.get("/queue")
async def get_task_queue():
    return get_all_queue()
