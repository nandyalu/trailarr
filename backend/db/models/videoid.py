from datetime import datetime, timezone

from pydantic import field_validator
from sqlalchemy import Integer
from sqlmodel import Column, Field, String

from db.models.base import AppSQLModel


def _now():
    return datetime.now(timezone.utc)


class VideoIdSourceEnum:
    ARR = "arr"
    TMDB = "tmdb"
    USER = "user"


class VideoIdBase(AppSQLModel):
    """Base model for VideoId.
    Note:
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨
    👉Use :class:`VideoId` for working with database.👈
    👉Use :class:`VideoIdCreate` to create records.👈
    👉Use :class:`VideoIdRead` to read data.👈
    """

    media_id: int
    youtube_id: str
    video_type: str = Field(
        default="trailer",
        sa_column=Column(String, nullable=False),
    )
    source: str = Field(
        default=VideoIdSourceEnum.USER,
        sa_column=Column(String, nullable=False),
    )
    language: str = Field(
        default="",
        sa_column=Column(String, server_default="", nullable=False),
    )
    season: int = Field(
        default=0,
        sa_column=Column(Integer, server_default="0", nullable=False),
    )


class VideoId(VideoIdBase, table=True):
    """Database model for VideoId.
    Stores YouTube IDs for media items, sourced from Arr connections, TMDB, or user input.

    Note:
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨
    """

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE", index=True)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_utc(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)


class VideoIdCreate(VideoIdBase):
    """Model for creating VideoId records (user-provided)."""

    pass


class VideoIdRead(VideoIdBase):
    """Model for reading VideoId records."""

    id: int
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)
