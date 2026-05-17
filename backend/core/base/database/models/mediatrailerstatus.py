from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlalchemy import Integer
from sqlmodel import Column, Field, String

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class TrailerStatusEnum(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNMONITORED = "unmonitored"
    NOT_AVAILABLE = "not_available"


class TrailerSourceEnum(str, Enum):
    APP = "app"
    MANUAL = "manual"


class MediaTrailerStatusBase(AppSQLModel):
    """Base model for MediaTrailerStatus.
    Note:
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨
    👉Use :class:`MediaTrailerStatus` for working with database.👈
    👉Use :class:`MediaTrailerStatusCreate` to create/update records.👈
    👉Use :class:`MediaTrailerStatusRead` to read data.👈
    """

    media_id: int
    profile_id: int | None = None
    season: int = Field(
        default=0, sa_column=Column(Integer, server_default="0", nullable=False)
    )
    sequence: int = Field(
        default=1, sa_column=Column(Integer, server_default="1", nullable=False)
    )
    status: TrailerStatusEnum = Field(
        default=TrailerStatusEnum.PENDING,
        sa_column=Column(String, nullable=False),
    )
    source: TrailerSourceEnum = Field(
        default=TrailerSourceEnum.APP,
        sa_column=Column(String, nullable=False),
    )
    linked_download_id: int | None = None


class MediaTrailerStatus(MediaTrailerStatusBase, table=True):
    """Database model for MediaTrailerStatus.
    Tracks per-profile, per-season, per-sequence trailer download state for a media item.

    Note:
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨
    """

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE", index=True)
    profile_id: int | None = Field(
        default=None,
        foreign_key="trailerprofile.id",
        ondelete="SET NULL",
        index=True,
    )
    linked_download_id: int | None = Field(
        default=None,
        foreign_key="download.id",
        ondelete="SET NULL",
    )
    created_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)


class MediaTrailerStatusCreate(MediaTrailerStatusBase):
    """Model for creating MediaTrailerStatus records."""

    pass


class MediaTrailerStatusRead(MediaTrailerStatusBase):
    """Model for reading MediaTrailerStatus records.
    Includes denormalised profile fields joined at query time.
    """

    id: int
    created_at: datetime
    updated_at: datetime
    # Joined from TrailerProfile for display
    profile_name: str | None = None
    video_type: str | None = None

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)
