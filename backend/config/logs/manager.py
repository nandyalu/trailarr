import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete as sa_delete
from sqlmodel import col, desc, or_, select
from config.logs.db_utils import (
    compact_logs_db,
    flush_logs_to_db,
    get_async_logs_session,
)
from config.logs.model import (
    AppLogRecord,
    AppLogRecordRead,
    LOG_LEVELS,
    LogLevel,
)
from config.settings import app_settings


async def get_all_logs(
    level: LogLevel | None = None,
    offset: int = 0,
    limit: int = 1000,
    filter: str | None = None,
) -> list[AppLogRecordRead]:
    """Retrieve all logs from the database."""

    if level is None:
        level = LogLevel[app_settings.log_level]
    async with get_async_logs_session() as session:
        stmt = select(AppLogRecord)
        stmt = _apply_log_filter(stmt, filter)
        # Get log levels greater than or equal to the specified level
        _given_val = LOG_LEVELS.get(level.value.upper(), 20)
        _levels_to_get = [
            _level
            for _level, _value in LOG_LEVELS.items()
            if _value >= _given_val
        ]
        stmt = stmt.where(col(AppLogRecord.level).in_(_levels_to_get))
        stmt = (
            stmt.offset(offset)
            .limit(limit)
            .order_by(desc(AppLogRecord.created))
        )
        logs = await session.exec(stmt)
        return [AppLogRecordRead(**log.model_dump()) for log in logs.all()]


def _apply_log_filter(stmt, filter: str | None):
    """Apply a filter to the log query statement."""
    if not filter:
        return stmt
    filter = filter.strip()
    if not filter or len(filter) < 3:
        return stmt
    stmt = stmt.where(
        or_(
            col(AppLogRecord.message).ilike(f"%{filter}%"),
            col(AppLogRecord.loggername).ilike(f"%{filter}%"),
            col(AppLogRecord.traceback).ilike(f"%{filter}%"),
            col(AppLogRecord.filename).ilike(f"%{filter}%"),
            col(AppLogRecord.lineno).ilike(f"%{filter}%"),
            col(AppLogRecord.taskname).ilike(f"%{filter}%"),
        )
    )
    return stmt


async def delete_old_logs(days: int = 30) -> int:
    """Delete logs older than the specified number of days."""
    date_threshold = datetime.now() - timedelta(days=days)
    async with get_async_logs_session() as session:
        result = await session.execute(
            sa_delete(AppLogRecord).where(
                col(AppLogRecord.created) < date_threshold
            )
        )
        await session.commit()
        deleted = result.rowcount or 1  # type: ignore
    if deleted > 0:
        # Truncate the WAL then compact freed pages off the main file
        await asyncio.to_thread(flush_logs_to_db)
        await asyncio.to_thread(compact_logs_db)
    return deleted
