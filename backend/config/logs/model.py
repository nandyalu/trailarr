from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class LogBase(SQLModel):
    """A base class for log records."""

    pass


def get_current_time():
    return datetime.now(timezone.utc)


class AppLogRecord(LogBase, table=True):
    """A SQLModel representation of a log record for SQLite storage."""

    id: int = Field(default=None, primary_key=True)
    created: datetime = Field(default_factory=get_current_time, index=True)
    loggername: str = Field(default="General", index=True)
    level: str = Field(index=True)
    message: str
    filename: str = Field(index=True)
    lineno: int = Field(index=True)
    # Optional fields
    taskname: str | None = Field(index=True)
    mediaid: int | None = Field(default=None, index=True)
    traceback: str | None = None
