from contextlib import contextmanager
from datetime import datetime
from typing import Generator, Sequence

from apscheduler import events
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job
from sqlalchemy import StaticPool
from sqlmodel import Field, SQLModel, Session, create_engine, select


def get_current_time():
    return datetime.now()


class TaskInfo(SQLModel):
    name: str
    task_id: str
    interval: int = Field(default=0)
    last_run_duration: int = Field(default=0)
    last_run_start: datetime | None = Field(default=None)
    last_run_status: str = Field(default="Not Run Yet")
    next_run: datetime | None = Field(default=None)


class TaskInfoDB(TaskInfo, table=True):
    id: int | None = Field(default=None, primary_key=True)


class QueueInfo(SQLModel):
    name: str
    queue_id: str
    duration: int = Field(default=0)
    finished: datetime | None = Field(default=None)
    # queued: datetime = Field(default_factory=get_current_time)
    started: datetime = Field(default_factory=get_current_time)
    status: str = Field(default="Queued")


class QueueInfoDB(QueueInfo, table=True):
    id: int | None = Field(default=None, primary_key=True)


# Use an in-memory SQLite database for saving tasks info,
# as we don't need to persist this with app restart
# sqlite_url = "sqlite:////data/tasks.db"
sqlite_url = "sqlite:///:memory:"
engine = create_engine(
    sqlite_url,
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
SQLModel.metadata.create_all(engine)


@contextmanager
def _get_session() -> Generator[Session, None, None]:
    """Provide a SQLModel session for tasks in memory database \n
    Yields:
        Session: A SQLModel session \n
    Example:: \n
        with _get_session() as session:
            movie_1 = Movie(title=..., year=..., ...)
            session.add(movie_1)
            session.commit()
    """
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def _get_task(task_id: str) -> TaskInfoDB | None:
    """Get a task from the in-memory database. \n
    Args:
        task_id (str): Task ID to get. \n
    Returns:
        TaskInfoDB: Task with the given ID. \n
    """
    with _get_session() as session:
        _task_db = session.exec(
            select(TaskInfoDB).where(TaskInfoDB.task_id == task_id)
        ).first()
    if not _task_db:
        return None
    # if _task_db.last_run_start:
    #     _task_db.last_run_start = _task_db.last_run_start.replace(tzinfo=timezone.utc)
    return _task_db


def save_task(task: TaskInfo) -> None:
    """Save a task to the in-memory database. \n
    Args:
        task (TaskInfo): Task to be saved. \n
    Returns:
        None \n
    """
    with _get_session() as session:
        task_db = TaskInfoDB.model_validate(task)
        session.add(task_db)
        session.commit()
    return None


def update_task(task: TaskInfo) -> None:
    """Update a task in the in-memory database. \n
    Args:
        task (TaskInfo): Task to be updated. \n
    Returns:
        None \n
    """
    _task_db = _get_task(task.task_id)
    if not _task_db:
        save_task(task)
        return

    # Update the task info with new values
    _task_db.interval = task.interval
    _task_db.last_run_duration = task.last_run_duration
    _task_db.last_run_start = task.last_run_start
    _task_db.last_run_status = task.last_run_status
    _task_db.next_run = task.next_run

    # Save to the database
    with _get_session() as session:
        session.add(_task_db)
        session.commit()
    return None


def _get_queue(queue_id: str) -> QueueInfoDB | None:
    """Get a task from the in-memory database. \n
    Args:
        task_id (str): Task ID to get. \n
    Returns:
        TaskInfoDB: Task with the given ID. \n
    """
    with _get_session() as session:
        _queue_db = session.exec(
            select(QueueInfoDB).where(QueueInfoDB.queue_id == queue_id)
        ).first()
    if not _queue_db:
        return None
    return _queue_db


def save_queue(queue: QueueInfo) -> None:
    """Save a task to the in-memory database. \n
    Args:
        task (TaskInfo): Task to be saved. \n
    Returns:
        None \n
    """
    with _get_session() as session:
        queue_db = QueueInfoDB.model_validate(queue)
        session.add(queue_db)
        session.commit()
    return None


def update_queue(queue: QueueInfo) -> None:
    """Update a task in the in-memory database. \n
    Args:
        task (TaskInfo): Task to be updated. \n
    Returns:
        None \n
    """
    _queue_db = _get_queue(queue.queue_id)
    if not _queue_db:
        save_queue(queue)
        return

    # Update the task info with new values
    _queue_db.duration = queue.duration
    _queue_db.finished = queue.finished
    _queue_db.status = queue.status

    # Save to the database
    with _get_session() as session:
        session.add(_queue_db)
        session.commit()
    return None


def _to_read_list(db_task_list: Sequence[TaskInfoDB]) -> list[TaskInfo]:
    """-->>This is a private method<<-- \n
    Convert a list of TaskInfoDB objects to a list of TaskInfo objects.\n"""
    if not db_task_list or len(db_task_list) == 0:
        return []
    task_read_list: list[TaskInfo] = []
    for db_media in db_task_list:
        task_read = TaskInfo.model_validate(db_media)
        task_read_list.append(task_read)
    return task_read_list


def _to_read_queue_list(db_queue_list: Sequence[QueueInfoDB]) -> list[QueueInfo]:
    """-->>This is a private method<<-- \n
    Convert a list of TaskInfoDB objects to a list of TaskInfo objects.\n"""
    if not db_queue_list or len(db_queue_list) == 0:
        return []
    queue_read_list: list[QueueInfo] = []
    for db_queue in db_queue_list:
        queue_read = QueueInfo.model_validate(db_queue)
        queue_read_list.append(queue_read)
    return queue_read_list


def get_all_jobs() -> list[TaskInfo]:
    """Returns all jobs scheduled in the scheduler. \n
    Returns:
        sequence: List of all jobs scheduled in the scheduler.
    """
    with _get_session() as session:
        _jobs_list = session.exec(select(TaskInfoDB)).all()
    return _to_read_list(_jobs_list)


def get_all_queue() -> list[QueueInfo]:
    """Returns all jobs scheduled in the scheduler. \n
    Returns:
        sequence: List of all jobs scheduled in the scheduler.
    """
    with _get_session() as session:
        _queue_list = session.exec(select(QueueInfoDB)).all()
    return _to_read_queue_list(_queue_list)


def task_added_event(event: events.JobEvent) -> None:
    """Event handler for task added event."""
    from core.tasks import scheduler

    _job: Job | None = scheduler.get_job(event.job_id)
    if not _job:
        return
    _task = TaskInfo(
        name=_job.name,
        task_id=_job.id,
    )
    # Save tasks only if they have an interval (recurring)
    if "interval_length" in _job.trigger.__dir__():
        _interval = int(_job.trigger.interval_length)
        _task.interval = _interval
        _next_run = _job.next_run_time
        _task.next_run = _next_run
        update_task(_task)
    return


def _get_task_next_run(task_id: str) -> datetime | None:
    """Get the next run time for a task."""
    from core.tasks import scheduler

    _job: Job | None = scheduler.get_job(task_id)
    if _job:
        return _job.next_run_time
    return None


def task_started_event(event: events.JobEvent) -> None:
    """Event handler for task started event."""
    # Update task with started time and clear last run duration
    task = _get_task(event.job_id)
    if not task:
        return
    task.last_run_start = get_current_time()
    task.last_run_duration = 0
    task.last_run_status = "Running"
    task.next_run = _get_task_next_run(event.job_id)
    update_task(task)

    # Add a queue entry for the task
    queue = QueueInfo(
        name=task.name,
        queue_id=f"{task.task_id}",
        started=task.last_run_start,
        status="Running",
    )
    save_queue(queue)
    return


def task_finished_event(event: events.JobEvent) -> None:
    """Event handler for task finished event."""
    # Update task with finished time and duration
    task = _get_task(event.job_id)
    if not task:
        return
    _duration = 0
    if task.last_run_start:
        _duration = get_current_time() - task.last_run_start
        _duration = int(_duration.total_seconds())
        task.last_run_duration = _duration
    task.last_run_status = "Finished"
    task.next_run = _get_task_next_run(event.job_id)
    update_task(task)

    # Update queue entry for the task
    queue = QueueInfo(
        name=task.name,
        queue_id=f"{task.task_id}",
        duration=_duration,
        finished=get_current_time(),
        status="Finished",
    )
    update_queue(queue)
    return


def task_error_event(event: events.JobEvent) -> None:
    """Event handler for task error event."""
    # Update task with finished time and duration
    task = _get_task(event.job_id)
    if not task:
        return
    _duration = 0
    if task.last_run_start:
        _duration = get_current_time() - task.last_run_start
        _duration = int(_duration.total_seconds())
        task.last_run_duration = _duration
    task.last_run_status = "Error"
    task.next_run = _get_task_next_run(event.job_id)
    update_task(task)

    # Update queue entry for the task
    queue = QueueInfo(
        name=task.name,
        queue_id=f"{task.task_id}",
        duration=_duration,
        finished=get_current_time(),
        status="Error",
    )
    update_queue(queue)
    return


# Add Event Listeners
def add_all_event_listeners(scheduler: BaseScheduler):
    """Add all event listeners to the scheduler."""
    # Schedule added event
    scheduler.add_listener(task_added_event, events.EVENT_JOB_ADDED)
    # Scheduled task started event
    scheduler.add_listener(task_started_event, events.EVENT_JOB_SUBMITTED)
    # Scheduled task finished event
    scheduler.add_listener(task_finished_event, events.EVENT_JOB_EXECUTED)
