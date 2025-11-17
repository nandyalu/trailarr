from datetime import datetime, timezone

from pydantic import field_validator
from sqlmodel import Field

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class DownloadBase(AppSQLModel):
    """
    Base model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`Download` for working with database.👈 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """

    path: str
    file_name: str
    file_hash: str
    size: int  # Size in bytes
    resolution: int  # e.g., 1080, 2160
    file_format: str  # e.g., "mp4", "mkv", "webm"
    video_format: str  # e.g., "h264", "h265", "av1"
    audio_format: str  # e.g., "aac", "ac3", "opus"
    audio_language: str | None = None  # e.g., "eng", "tel"
    subtitle_format: str | None = None  # e.g., "srt", "ass", or None
    subtitle_language: str | None = None  # e.g., "eng", or None
    duration: int = 0  # Duration in seconds
    youtube_id: str = "unknown0000"
    youtube_channel: str = "unknownchannel"
    file_exists: bool = True
    profile_id: int = 0  # ID of the TrailerProfile used
    added_at: datetime  # When trailer was downloaded (from file)
    updated_at: datetime  # When file was last modified (from file)


class Download(DownloadBase, table=True):
    """
    Database model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE")


class DownloadCreate(DownloadBase):
    """
    Model for creating/updating Download.
    """

    id: int | None = None
    media_id: int


class DownloadRead(DownloadBase):
    """
    Model for reading Download.
    """

    id: int
    media_id: int

    @field_validator("added_at", "updated_at", mode="after")
    @classmethod
    def correct_timezone(cls, value: datetime) -> datetime:
        return cls.set_timezone_to_utc(value)


class DownloadUpdate(AppSQLModel):
    """
    Model for updating Download.
    Only updatable fields should be included.
    """

    file_exists: bool | None = None
    updated_at: datetime | None = None
