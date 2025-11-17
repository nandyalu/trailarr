from datetime import datetime, timezone
from enum import Enum
from pydantic import field_validator
from sqlmodel import Field, SQLModel


class LogBase(SQLModel):
    """A base class for log records."""

    pass


def get_current_time():
    return datetime.now(timezone.utc)


LOG_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "EXCEPTION": 40,
    "CRITICAL": 50,
}


class LogLevel(Enum):
    """Enumeration for log levels."""

    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    EXCEPTION = "EXCEPTION"
    CRITICAL = "CRITICAL"


class AppLogRecord(LogBase, table=True):
    """A SQLModel representation of a log record for SQLite storage."""

    id: int = Field(default=None, primary_key=True)
    created: datetime = Field(default_factory=get_current_time, index=True)
    loggername: str = Field(default="General", index=True)
    level: LogLevel = Field(index=True)
    message: str
    filename: str = Field(index=True)
    lineno: int = Field(index=True)
    # Optional fields
    taskname: str | None = Field(index=True)
    mediaid: int | None = Field(default=None, index=True)
    traceback: str | None = None


class AppLogRecordRead(LogBase):
    """A read model for log records with timezone correction."""

    id: int
    created: datetime
    loggername: str
    level: LogLevel
    message: str
    filename: str
    lineno: int
    taskname: str | None
    mediaid: int | None
    traceback: str | None

    @field_validator("created", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        if isinstance(value, datetime) and value.tzinfo is None:
            # Assume naive datetime loaded from DB is UTC
            return value.replace(tzinfo=timezone.utc)
        return value
