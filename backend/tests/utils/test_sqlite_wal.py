"""Tests for utils/sqlite_wal.py on a real SQLite database.

SQLite does not raise when a TRUNCATE checkpoint cannot finish. It
reports "busy" in its result row. These tests make a reader hold the WAL
open, so the checkpoint really is busy (Copilot review on #696).
"""

import asyncio
import os
import time

from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import create_async_engine

from utils.sqlite_wal import truncate_wal, truncate_wal_async


def _wal_engine(url: str):
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=0")
        cursor.close()

    return engine


def _write_rows(engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE IF NOT EXISTS t (v TEXT)"))
        for i in range(200):
            connection.execute(text("INSERT INTO t VALUES (:v)"), {"v": "x" * 500})


def test_an_idle_wal_is_emptied(tmp_path):
    db = tmp_path / "idle.db"
    engine = _wal_engine(f"sqlite:///{db}")
    _write_rows(engine)
    assert os.path.getsize(f"{db}-wal") > 0

    with engine.connect() as connection:
        assert truncate_wal(connection) is True
    assert os.path.getsize(f"{db}-wal") == 0


def test_a_reader_makes_it_busy_and_it_says_so(tmp_path):
    db = tmp_path / "busy.db"
    engine = _wal_engine(f"sqlite:///{db}")
    _write_rows(engine)

    reader = engine.connect()
    reader.execute(text("BEGIN"))
    reader.execute(text("SELECT count(*) FROM t")).fetchone()
    try:
        # Another write after the reader's snapshot, so the WAL has frames
        # the reader still needs.
        _write_rows(engine)
        with engine.connect() as connection:
            assert truncate_wal(connection, attempts=2, pause=0.01) is False
        assert os.path.getsize(f"{db}-wal") > 0
    finally:
        reader.rollback()
        reader.close()

    with engine.connect() as connection:
        assert truncate_wal(connection) is True
    assert os.path.getsize(f"{db}-wal") == 0


def test_the_async_version_tries_again_until_the_reader_leaves(tmp_path):
    db = tmp_path / "async.db"
    sync_engine = _wal_engine(f"sqlite:///{db}")
    _write_rows(sync_engine)
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db}")

    reader = sync_engine.connect()
    reader.execute(text("BEGIN"))
    reader.execute(text("SELECT count(*) FROM t")).fetchone()
    _write_rows(sync_engine)

    async def run() -> bool:
        async def release_soon():
            await asyncio.sleep(0.05)
            reader.rollback()
            reader.close()

        async with async_engine.connect() as connection:
            await connection.exec_driver_sql("PRAGMA busy_timeout=0")
            release = asyncio.create_task(release_soon())
            done = await truncate_wal_async(connection, attempts=20, pause=0.02)
            await release
            return done

    assert asyncio.run(run()) is True
    assert os.path.getsize(f"{db}-wal") == 0
    asyncio.run(async_engine.dispose())


def _slow_engine(url: str):
    """An engine with the busy timeout of the app: 20 seconds."""
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=20000")
        cursor.close()

    return engine


def test_a_short_busy_timeout_bounds_the_wait_and_is_put_back(tmp_path):
    """A connection of the app waits 20 seconds for a busy database. A
    checkpoint at a stop must not, because Docker stops the container
    after 10 (Copilot review on #696). The connection goes back to the
    pool, so its own timeout must come back too."""
    db = tmp_path / "slow.db"
    engine = _slow_engine(f"sqlite:///{db}")
    _write_rows(engine)

    reader = engine.connect()
    reader.execute(text("BEGIN"))
    reader.execute(text("SELECT count(*) FROM t")).fetchone()
    try:
        _write_rows(engine)
        with engine.connect() as connection:
            started = time.monotonic()
            done = truncate_wal(connection, busy_timeout_ms=200)
            waited = time.monotonic() - started
            timeout = connection.execute(text("PRAGMA busy_timeout")).scalar()
        assert done is False
        assert waited < 5
        assert timeout == 20000
    finally:
        reader.rollback()
        reader.close()


def test_the_async_version_puts_the_busy_timeout_back(tmp_path):
    db = tmp_path / "async-timeout.db"
    _write_rows(_slow_engine(f"sqlite:///{db}"))
    async_engine = create_async_engine(f"sqlite+aiosqlite:///{db}")

    async def run() -> tuple[bool, int]:
        async with async_engine.connect() as connection:
            await connection.exec_driver_sql("PRAGMA busy_timeout=20000")
            done = await truncate_wal_async(connection, busy_timeout_ms=200)
            result = await connection.execute(text("PRAGMA busy_timeout"))
            return done, result.scalar()

    assert asyncio.run(run()) == (True, 20000)
    asyncio.run(async_engine.dispose())
