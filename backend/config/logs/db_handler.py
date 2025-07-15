from datetime import datetime
import logging
import traceback
from logging import LogRecord

from config.logs.db_utils import get_logs_session
from config.logs.model import AppLogRecord


def get_synthetic_traceback():
    try:
        raise Exception("Synthetic traceback for logging context")
    except Exception:
        exc = "".join(
            traceback.format_exc().splitlines(keepends=True)
        )  # skip the synthetic message
    return exc


# def get_trimmed_traceback():
#     """Trim the traceback to exclude the current file."""
#     tb_stacks = traceback.extract_stack()
#     trimmed_stacks = []
#     for line in tb_stacks:
#         if "logging/__init__.py" in line.filename:
#             break  # Stop at the first occurrence of the logging module
#         trimmed_stacks.append(line)
#     return "".join(traceback.format_list(trimmed_stacks))


class DatabaseLoggingHandler(logging.Handler):
    def __init__(self):
        super().__init__()

    def emit(self, record: LogRecord):
        try:
            # Include tracebacks for errors and above
            _tb = None
            if record.levelno >= logging.ERROR:
                if record.exc_info:
                    _tb = "".join(traceback.format_exception(*record.exc_info))
                else:
                    # If not in an exception handler, get the current stack traceback
                    _tb = get_synthetic_traceback()

            # Format timestamp and task name if available
            _created = datetime.fromtimestamp(record.created)
            _taskName = "General"
            if hasattr(record, "taskName"):
                _taskName = record.taskName
            _mediaid = getattr(record, "mediaid", None)
            _loggername = record.name
            if "alembic" in _loggername:
                _loggername = "AlembicMigrations"
            elif "apscheduler" in _loggername:
                _loggername = "Tasks"

            # Create a log record instance for the database
            log_record = AppLogRecord(
                created=_created,
                loggername=_loggername,
                level=record.levelname,
                message=record.getMessage(),
                filename=record.module,
                lineno=record.lineno,
                taskname=_taskName,
                mediaid=_mediaid,
                traceback=_tb,
            )
            with get_logs_session() as session:
                session.add(log_record)
                session.commit()
        except Exception:
            self.handleError(record)
