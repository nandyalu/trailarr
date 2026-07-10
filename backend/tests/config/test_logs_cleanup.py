"""Tests for delete_old_logs batch purge + VACUUM in config/logs/manager.py."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import col, select

from config.logs.db_utils import get_logs_session, vacuum_logs_db
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
