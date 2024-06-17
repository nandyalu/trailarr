from fastapi import APIRouter

from core.tasks.task_runner import TaskRunner


tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@tasks_router.get("/schedules")
async def get_scheduled_tasks():
    return TaskRunner()._read_info_from_file(is_task=True)


@tasks_router.get("/queue")
async def get_task_queue():
    return TaskRunner()._read_info_from_file(is_task=False)
