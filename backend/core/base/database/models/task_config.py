from sqlmodel import Field

from core.base.database.models.base import AppSQLModel


class _ScheduledTaskConfigBase(AppSQLModel):
    task_key: str
    """Internal stable identifier used to look up the handler function."""
    task_name: str
    """Display name shown to user; also used as the quiv task_name key."""
    interval_seconds: float
    delay_seconds: float


class ScheduledTaskConfig(_ScheduledTaskConfigBase, table=True):
    """Persists user-configurable schedule settings for each background task."""

    id: int | None = Field(default=None, primary_key=True)
    task_key: str = Field(unique=True)


class ScheduledTaskConfigRead(_ScheduledTaskConfigBase):
    id: int


class ScheduledTaskConfigUpdate(AppSQLModel):
    task_name: str | None = None
    interval_seconds: float | None = None
    delay_seconds: float | None = None
