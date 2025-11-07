from __future__ import annotations
from datetime import datetime, timezone

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
    size: int
    updated_at: datetime
    resolution: str
    video_format: str
    audio_format: str
    audio_channels: str
    file_format: str
    duration: int = 0
    subtitles: str = "unk"
    added_at: datetime = Field(default_factory=get_current_time)
    profile_id: int
    youtube_id: str
    file_exists: bool = True


class Download(DownloadBase, table=True):
    """
    Database model for Download.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`DownloadCreate` to create/update downloads.👈 \n
    👉Use :class:`DownloadRead` to read the data.👈
    """

    id: int | None = Field(default=None, primary_key=True)

    media_id: int | None = Field(
        default=None, foreign_key="media.id", ondelete="CASCADE"
    )


class DownloadCreate(DownloadBase):
    """
    Model for creating/updating Download.
    """

    id: int | None = None
    media_id: int | None = None


class DownloadRead(DownloadBase):
    """
    Model for reading Download.
    """

    id: int
    media_id: int
