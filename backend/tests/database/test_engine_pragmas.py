"""The SQLite pragmas belong to the application database only.

A listener on the `Engine` class reaches every engine in the process. That
put `foreign_keys=ON` on the temp database of the task scheduler. quiv
deletes a run-once task row while its job row still points at it, so each
manual download raised a foreign key error inside quiv's job runner and
lost one worker slot for good. After ten of them no task ran until a
restart, with no error in the log.
"""

import time

from quiv import Quiv
from sqlalchemy import Engine, create_engine, event, text

import database.engine as app_engine


def test_the_pragma_listener_is_on_the_app_engine_only():
    assert event.contains(
        app_engine.engine, "connect", app_engine.set_sqlite_pragma
    )
    assert not event.contains(Engine, "connect", app_engine.set_sqlite_pragma)


def test_another_engine_in_the_process_keeps_foreign_keys_off():
    other = create_engine("sqlite://")
    with other.connect() as connection:
        assert connection.execute(text("PRAGMA foreign_keys")).scalar() == 0


def test_a_run_once_task_gives_its_worker_slot_back():
    """One manual download is one run-once task. When it finishes, quiv
    must delete its task row and free its worker slot."""
    scheduler = Quiv(pool_size=2)
    try:
        with scheduler._engine.connect() as connection:
            assert (
                connection.execute(text("PRAGMA foreign_keys")).scalar() == 0
            )
        scheduler.add_task(
            task_name="Download Trailer for X",
            func=lambda: None,
            run_once=True,
            delay=0,
        )
        scheduler.start()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            jobs = scheduler.get_all_jobs()
            if (
                jobs
                and jobs[0].status == "completed"
                and scheduler._active_job_count == 0
            ):
                break
            time.sleep(0.05)
        assert [job.status for job in scheduler.get_all_jobs()] == [
            "completed"
        ]
        assert scheduler._active_job_count == 0
        assert scheduler.get_all_tasks(include_run_once=True) == []
    finally:
        scheduler.shutdown(timeout=1)
