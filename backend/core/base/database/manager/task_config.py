from sqlmodel import Session, select

from core.base.database.models.task_config import (
    ScheduledTaskConfig,
    ScheduledTaskConfigRead,
)
from core.base.database.utils.engine import read_session, write_session


@read_session
def get_all_task_configs(
    *,
    _session: Session = None,  # type: ignore
) -> list[ScheduledTaskConfigRead]:
    task_configs = list(_session.exec(select(ScheduledTaskConfig)).all())
    return [
        ScheduledTaskConfigRead.model_validate(config)
        for config in task_configs
    ]


@read_session
def get_task_config(
    task_key: str,
    *,
    _session: Session = None,  # type: ignore
) -> ScheduledTaskConfigRead | None:
    config = _session.exec(
        select(ScheduledTaskConfig).where(
            ScheduledTaskConfig.task_key == task_key
        )
    ).first()
    if config is None:
        return None
    return ScheduledTaskConfigRead.model_validate(config)


@write_session
def create_task_config(
    config: ScheduledTaskConfig, *, _session: Session = None  # type: ignore
) -> ScheduledTaskConfigRead:
    _session.add(config)
    _session.commit()
    _session.refresh(config)
    return ScheduledTaskConfigRead.model_validate(config)


@write_session
def update_task_config(
    task_key: str,
    task_name: str,
    interval_seconds: float,
    delay_seconds: float,
    *,
    _session: Session = None,  # type: ignore
) -> ScheduledTaskConfigRead:
    config = _session.exec(
        select(ScheduledTaskConfig).where(
            ScheduledTaskConfig.task_key == task_key
        )
    ).first()
    if config is None:
        raise ValueError(f"No task config found for task_key: {task_key!r}")
    config.task_name = task_name
    config.interval_seconds = interval_seconds
    config.delay_seconds = delay_seconds
    _session.add(config)
    _session.commit()
    _session.refresh(config)
    return ScheduledTaskConfigRead.model_validate(config)
