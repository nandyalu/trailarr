"""A notification channel and the events it subscribes to."""

from datetime import datetime, timezone

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field

from database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


def mask_apprise_url(url: str) -> str:
    """Mask an Apprise URL for display — these embed tokens/credentials.
    Keeps the scheme and a short prefix: 'discord://12ab****'."""
    if "://" not in url:
        return "****"
    scheme, rest = url.split("://", 1)
    return f"{scheme}://{rest[:4]}****"


class NotificationChannelBase(AppSQLModel):
    """
    Base model for NotificationChannel — an Apprise destination plus which
    event types it subscribes to.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`NotificationChannelCreate` to create/update channels.👈 \n
    👉Use :class:`NotificationChannelRead` to read the data.👈
    """

    name: str = Field(index=True, unique=True)
    enabled: bool = Field(default=True)
    # EventType NAMES (VARCHAR semantics — new event types need no
    # migration; unknown stored names are ignored harmlessly)
    event_types: list[str] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    # SYSTEM-sourced events only by default — a user clicking around
    # shouldn't echo their own actions to Discord
    include_user_events: bool = Field(default=False)


class NotificationChannel(NotificationChannelBase, table=True):
    """
    Database model for NotificationChannel.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    """

    id: int | None = Field(default=None, primary_key=True)
    # The Apprise URL — SECRET (contains tokens). Never returned by the
    # API; see NotificationChannelRead.url_masked.
    url: str
    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)


class NotificationChannelCreate(NotificationChannelBase):
    """Model for creating/updating NotificationChannel. On update, an empty
    url means 'keep the existing one' (the API never echoes it back)."""

    id: int | None = None
    url: str = ""


class NotificationChannelRead(NotificationChannelBase):
    """Read model — the Apprise URL is write-only; only a masked form is
    ever exposed."""

    id: int
    url_masked: str = ""
    added_at: datetime
    updated_at: datetime

    @field_validator("added_at", "updated_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)
