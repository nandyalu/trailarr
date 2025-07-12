from sqlmodel import select
from config.logs.db_utils import get_logs_session
from config.logs.model import AppLogRecord
from config.settings import app_settings


def get_all_logs():
    """Retrieve all logs from the database."""

    level = app_settings.log_level
    with get_logs_session() as session:
        stmt = select(AppLogRecord).where(AppLogRecord.level == level)
        logs = session.exec(stmt).all()
        return logs
