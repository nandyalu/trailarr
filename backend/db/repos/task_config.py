from sqlmodel import Session, select

from db.models.task_config import ScheduledTaskConfig, ScheduledTaskConfigRead
from db.engine import read_session, write_session


@read_session
def get_all(*, _session: Session = None) -> list[ScheduledTaskConfigRead]:  # type: ignore
    configs = list(_session.exec(select(ScheduledTaskConfig)).all())
    return [ScheduledTaskConfigRead.model_validate(c) for c in configs]


@read_session
def get(task_key: str, *, _session: Session = None) -> ScheduledTaskConfigRead | None:  # type: ignore
    config = _session.exec(
        select(ScheduledTaskConfig).where(ScheduledTaskConfig.task_key == task_key)
    ).first()
    return ScheduledTaskConfigRead.model_validate(config) if config else None


@write_session
def create(config: ScheduledTaskConfig, *, _session: Session = None) -> ScheduledTaskConfigRead:  # type: ignore
    _session.add(config)
    _session.commit()
    _session.refresh(config)
    return ScheduledTaskConfigRead.model_validate(config)


@write_session
def update(
    task_key: str,
    task_name: str,
    interval_seconds: float,
    delay_seconds: float,
    *,
    _session: Session = None,  # type: ignore
) -> ScheduledTaskConfigRead:
    config = _session.exec(
        select(ScheduledTaskConfig).where(ScheduledTaskConfig.task_key == task_key)
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
