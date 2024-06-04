from datetime import datetime
from typing import Callable

from pydantic import BaseModel, Field


class TaskInfo(BaseModel):
    name: str = Field(..., description="Name of the task")
    interval: int = Field(..., description="Interval in seconds")
    task_func: Callable = Field(..., description="Function to run")
    task_args: tuple = Field((), description="Arguments to pass to the task function")
    last_run_status: bool = Field(default=False, description="Status of last run")
    last_run_start: datetime | None = Field(
        default=None, description="Start date and time of last run"
    )
    last_run_end: datetime | None = Field(
        default=None, description="End date and time of last run"
    )
