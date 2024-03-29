from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


def get_current_time():
    return datetime.now()


class ArrType(Enum):
    RADARR = "radarr"
    SONARR = "sonarr"


class MonitorType(Enum):
    # MONITOR_ALL = "all"
    MONITOR_MISSING = "missing"
    MONITOR_NEW = "new"
    MONITOR_SYNC = "sync"


class ConnectionBase(SQLModel):
    """Base class for the Connection model

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use ConnectionCreate, ConnectionRead, or ConnectionUpdate instead.
    """

    name: str
    arr_type: ArrType
    url: str
    api_key: str
    monitor: MonitorType


class Connection(ConnectionBase, table=True):
    """Connection model for the database. This is the main model for the application.

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use ConnectionCreate, ConnectionRead, or ConnectionUpdate instead.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    added_at: datetime = Field(default_factory=get_current_time)


class ConnectionCreate(ConnectionBase):
    """Connection model for creating a new connection. This is used in the API while creating."""

    pass


class ConnectionRead(ConnectionBase):
    """Connection model for reading a connection. This is used in the API to return data."""

    id: int
    added_at: datetime


class ConnectionUpdate(ConnectionBase):
    """Connection model for updating a connection. This is used in the API while updating."""

    name: Optional[str] = None
    type: Optional[ArrType] = None
    url: Optional[str] = None
    api_key: Optional[str] = None
    monitor: Optional[MonitorType] = None
