from __future__ import annotations
from datetime import datetime, timezone
from typing import List

from sqlmodel import Field, SQLModel

from core.base.database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class DownloadBase(AppSQLModel):
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
    media_id: int = Field(foreign_key="media.id")
    youtube_id: str
    file_exists: bool = True


class Download(DownloadBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

    media_id: int = Field(foreign_key="media.id", ondelete="CASCADE")


class DownloadCreate(DownloadBase):
    pass


class DownloadRead(DownloadBase):
    id: int
