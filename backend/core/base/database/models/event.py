from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlalchemy import Column, String, text, Enum as sa_Enum
from sqlmodel import Field

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class EventType(str, Enum):
    """Types of events that can be tracked."""

    MEDIA_ADDED = "media_added"
    MONITOR_CHANGED = "monitor_changed"
    YOUTUBE_ID_CHANGED = "youtube_id_changed"
    TRAILER_DETECTED = "trailer_detected"
    TRAILER_DOWNLOADED = "trailer_downloaded"
    TRAILER_DELETED = "trailer_deleted"
    DOWNLOAD_SKIPPED = "download_skipped"
    PLEX_LINKED = "plex_linked"
    PLEX_UNLINKED = "plex_unlinked"
    PLEX_SCAN_TRIGGERED = "plex_scan_triggered"
    ARR_LINKED = "arr_linked"
    ARR_UNLINKED = "arr_unlinked"


class EventSource(str, Enum):
    """Source of the event."""

    USER = "user"
    SYSTEM = "system"


class EventBase(AppSQLModel):
    """Base class for the Event model. \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use EventCreate, EventRead models instead.
    """

    media_id: int
    event_type: EventType = Field(
        sa_column=Column(
            sa_Enum(EventType, native_enum=False),
            nullable=False,
            index=True,
        )
    )
    source: EventSource = Field(
        default=EventSource.USER,
        sa_column=Column(
            sa_Enum(EventSource, native_enum=False),
            server_default=text("'USER'"),
            nullable=False,
            index=True,
        ),
    )
    source_detail: str = Field(
        default="",
        sa_column=Column(
            String, server_default=text("('')"), nullable=False, index=True
        ),
    )
    old_value: str | None = None
    new_value: str | None = None


class Event(EventBase, table=True):
    """Event model for the database. \n
    This class is used for database CRUD operations only \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use EventCreate, EventRead models instead.
    """

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(
        foreign_key="media.id", index=True, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=get_current_time, index=True)


class EventCreate(EventBase):
    """Event model for creating new event objects. \n
    Defaults:
        - source: EventSource.USER
        - source_detail: ""
        - old_value: None
        - new_value: None
    """

    pass


class EventRead(EventBase):
    """Event model for reading events."""

    id: int
    created_at: datetime

    @field_validator("created_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)
