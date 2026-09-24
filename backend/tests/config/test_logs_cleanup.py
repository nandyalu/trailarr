"""Tests for delete_old_logs batch purge + VACUUM in config/logs/manager.py."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import text as sa_text
from sqlmodel import col, select

from config.logs.db_utils import (
    WAL_SIZE_LIMIT,
    async_engine,
    engine,
    get_logs_session,
    vacuum_logs_db,
)
from config.logs.manager import delete_old_logs
from config.logs.model import AppLogRecord, LogLevel

MARKER = "LogsCleanupTest"


def seed_logs(count: int, age_days: int) -> None:
    created = datetime.now() - timedelta(days=age_days)
    with get_logs_session() as session:
        for i in range(count):
            session.add(
                AppLogRecord(
                    created=created,
                    loggername=MARKER,
                    level=LogLevel.INFO,
                    message=f"seeded log {i} ({age_days}d old)",
                    filename="test_logs_cleanup.py",
                    lineno=1,
                    taskname=None,
                )
            )
        session.commit()


def marker_rows() -> list[AppLogRecord]:
    with get_logs_session() as session:
        stmt = select(AppLogRecord).where(
            col(AppLogRecord.loggername) == MARKER
        )
        return list(session.exec(stmt).all())


class TestDeleteOldLogs:

    @pytest.mark.asyncio
    async def test_deletes_old_rows_keeps_recent(self):
        seed_logs(5, age_days=40)
        seed_logs(3, age_days=1)

        deleted = await delete_old_logs(30)

        assert deleted >= 5  # at least our seeded old rows
        remaining = marker_rows()
        assert len(remaining) == 3
        assert all(
            r.created > datetime.now() - timedelta(days=30) for r in remaining
        )

    @pytest.mark.asyncio
    async def test_nothing_to_delete_skips_vacuum(self):
        with patch(
            "config.logs.manager.vacuum_logs_db", new=AsyncMock()
        ) as mock_vacuum:
            deleted = await delete_old_logs(days=10_000)

        assert deleted == 0
        mock_vacuum.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_vacuum_called_after_deletion(self):
        seed_logs(2, age_days=40)
        with patch(
            "config.logs.manager.vacuum_logs_db", new=AsyncMock()
        ) as mock_vacuum:
            deleted = await delete_old_logs(30)

        assert deleted >= 2
        mock_vacuum.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_vacuum_runs_for_real(self):
        """VACUUM must execute against the real SQLite file — it fails with
        'cannot VACUUM from within a transaction' if the connection isn't
        in autocommit mode, so this guards the isolation-level setup."""
        await vacuum_logs_db()

    @pytest.mark.asyncio
    async def test_vacuum_leaves_the_wal_empty(self):
        """VACUUM writes the full database into the WAL. The purge must
        empty the WAL file after it, or the file stays that large (#687)."""
        seed_logs(500, age_days=40)
        wal = Path(os.environ["APP_DATA_DIR"]) / "logs" / "logs.db-wal"

        await delete_old_logs(30)

        assert wal.stat().st_size == 0


class TestLogsDbPragmas:
    """Each connection to the log database must limit the WAL size. The
    engine sets this itself, because it opens its first connection before
    the listener in `database/engine.py` exists (#687)."""

    def test_sync_connection_limits_the_wal(self):
        with engine.connect() as connection:
            mode = connection.execute(sa_text("PRAGMA journal_mode"))
            limit = connection.execute(sa_text("PRAGMA journal_size_limit"))
            assert mode.scalar() == "wal"
            assert limit.scalar() == WAL_SIZE_LIMIT

    @pytest.mark.asyncio
    async def test_async_connection_limits_the_wal(self):
        async with async_engine.connect() as connection:
            result = await connection.execute(
                sa_text("PRAGMA journal_size_limit")
            )
            assert result.scalar() == WAL_SIZE_LIMIT
