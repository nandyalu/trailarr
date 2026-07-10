from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlmodel import col, desc, or_, select
from config.logs.db_utils import get_async_logs_session, vacuum_logs_db
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
    """Delete logs older than the specified number of days in a single
    statement, then VACUUM to return the freed pages to the filesystem
    (skipped when nothing was deleted — VACUUM rewrites the whole file)."""
    date_threshold = datetime.now() - timedelta(days=days)
    async with get_async_logs_session() as session:
        stmt = delete(AppLogRecord).where(
            col(AppLogRecord.created) < date_threshold
        )
        result = await session.exec(stmt)  # type: ignore[call-overload]
        await session.commit()
        count = result.rowcount or 0
    if count:
        await vacuum_logs_db()
    return count
