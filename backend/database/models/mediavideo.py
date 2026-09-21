"""A video that Trailarr knows about for a media item.

The candidates table. One row is one video that Trailarr could download for
one media item, with the source that offered it. The resolver reads this
table to choose what to download, in the order USER, TMDB, ARR, SEARCH.

Each source owns its own rows. A TMDB refresh adds and removes TMDB rows, a
sync adds ARR rows, and a search writes back a SEARCH row. No automation
ever writes or removes a USER row: the user chose that video, so it stays
until the user removes it, even when the download of it fails.
"""

from datetime import datetime, timezone
from enum import Enum

from pydantic import field_validator
from sqlalchemy import Column, Enum as sa_Enum, UniqueConstraint
from sqlmodel import Field

from database.models.base import AppSQLModel


def get_current_time():
    return datetime.now(timezone.utc)


class VideoSource(str, Enum):
    """Who told Trailarr about this video.

    The resolver tries the sources in the order of this class: the choice of
    the user first, then the curated list from TMDB, then the id that Radarr
    or Sonarr gave, and last the result of a YouTube search.
    """

    USER = "user"
    TMDB = "tmdb"
    ARR = "arr"
    SEARCH = "search"


# The order the resolver uses. The position in this list is the precedence:
# a lower number wins.
SOURCE_PRECEDENCE: dict[str, int] = {
    VideoSource.USER.value: 0,
    VideoSource.TMDB.value: 1,
    VideoSource.ARR.value: 2,
    VideoSource.SEARCH.value: 3,
}

# Phase 9 replaces this with the full set of video types. Until then every
# row is a trailer, and the column exists so that no migration is necessary
# when the other types arrive.
VIDEO_TYPE_TRAILER = "trailer"


class MediaVideoBase(AppSQLModel):
    """
    Base model for MediaVideo.\n
    Note: \n
        🚨DO NOT USE THIS CLASS DIRECTLY.🚨 \n
    👉Use :class:`MediaVideo` for working with database.👈 \n
    👉Use :class:`MediaVideoCreate` to create/update videos.👈 \n
    👉Use :class:`MediaVideoRead` to read the data.👈
    """

    video_id: str  # The YouTube id, such as 'dQw4w9WgXcQ'
    source: VideoSource = Field(
        sa_column=Column(
            sa_Enum(VideoSource, native_enum=False),
            nullable=False,
            index=True,
        )
    )
    # NULL is the movie, or the series as a whole. A season number arrives
    # with the season profiles of Phase 10.
    season: int | None = Field(default=None, index=True)
    video_type: str = Field(default=VIDEO_TYPE_TRAILER, index=True)
    # The order inside one (media, type, season) group. TMDB returns its
    # list in a useful order, and this keeps it.
    sequence: int = 0
    language: str | None = None  # iso_639_1, such as 'en'
    name: str = ""  # The title that TMDB gives the video
    official: bool = False
    published_at: datetime | None = None
    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)


class MediaVideo(MediaVideoBase, table=True):
    """
    Database model for MediaVideo.\n
    Note: \n
        🚨DO NOT USE THIS CLASS OUTSIDE OF DATABASE MANAGER.🚨 \n
    👉Use :class:`MediaVideoCreate` to create/update videos.👈 \n
    👉Use :class:`MediaVideoRead` to read the data.👈
    """

    __table_args__ = (
        UniqueConstraint(
            "media_id", "video_id", name="uq_mediavideo_media_video"
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    media_id: int = Field(
        foreign_key="media.id", ondelete="CASCADE", index=True
    )

    @field_validator("added_at", "updated_at", "published_at", mode="after")
    @classmethod
    def update_to_utc_to_save(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        return cls.convert_to_utc(value)


class MediaVideoCreate(MediaVideoBase):
    """
    Model for creating/updating MediaVideo.
    """

    id: int | None = None
    media_id: int


class MediaVideoRead(MediaVideoBase):
    """
    Model for reading MediaVideo.
    """

    id: int
    media_id: int

    @field_validator("added_at", "updated_at", "published_at", mode="after")
    @classmethod
    def correct_timezone_after_read(
        cls, value: datetime | None
    ) -> datetime | None:
        if value is None:
            return None
        return cls.set_timezone_to_utc(value)
