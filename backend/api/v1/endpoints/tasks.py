from fastapi import APIRouter, HTTPException, status

from pydantic import BaseModel
from quiv import Task, Job
import db.repos.task_config as task_config_repo
from db.models.task_config import ScheduledTaskConfigRead, ScheduledTaskConfigUpdate
from tasks import scheduler
from tasks import schedules

tasks_router = APIRouter(tags=["Tasks", "Jobs"])


class TaskData(BaseModel):
    tasks: list[Task]
    jobs: list[Job]
    configs: list[ScheduledTaskConfigRead]


@tasks_router.get("/tasks-data")
async def get_task_data() -> TaskData:
    tasks = scheduler.get_all_tasks()
    jobs = scheduler.get_all_jobs()
    configs = task_config_repo.get_all()
    return TaskData(tasks=tasks, jobs=jobs, configs=configs)


@tasks_router.get("/task-configs/")
async def get_task_configs() -> list[ScheduledTaskConfigRead]:
    return task_config_repo.get_all()


@tasks_router.put("/task-configs/{task_key}")
async def update_task_config(
    task_key: str, task_id: str, update: ScheduledTaskConfigUpdate
) -> ScheduledTaskConfigRead:
    if update.task_name is None or update.interval_seconds is None or update.delay_seconds is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="task_name, interval_seconds, and delay_seconds are required.",
        )
    if task_key not in schedules.TASK_REGISTRY:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown task_key: {task_key!r}")
    if not update.task_name.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="task_name must not be empty.")
    try:
        return schedules.reschedule_task(
            task_key=task_key,
            task_id=task_id,
            task_name=update.task_name,
            interval_seconds=update.interval_seconds,
            delay_seconds=update.delay_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@tasks_router.get("/tasks/")
async def get_all_tasks() -> list[Task]:
    return scheduler.get_all_tasks()


@tasks_router.get("/tasks/{task_id}")
async def get_task(task_id: str) -> Task:
    return scheduler.get_task(task_id)


@tasks_router.post("/tasks/{task_id}/pause")
async def pause_task(task_id: str) -> bool:
    try:
        scheduler.pause_task(task_id)
        return True
    except Exception:
        return False


@tasks_router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str) -> bool:
    try:
        scheduler.resume_task(task_id)
        return True
    except Exception:
        return False


@tasks_router.post("/tasks/{task_id}/run")
async def run_task(task_id: str) -> str:
    return schedules.run_task_now(task_id)


@tasks_router.get("/jobs/")
async def get_all_jobs() -> list[Job]:
    return scheduler.get_all_jobs()


@tasks_router.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Job:
    return scheduler.get_job(job_id)


@tasks_router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> bool:
    try:
        scheduler.cancel_job(job_id)
        return True
    except Exception:
        return False
