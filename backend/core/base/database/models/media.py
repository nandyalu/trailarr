from datetime import datetime, timezone
from enum import Enum
from sqlalchemy import Boolean, Column, String, text, Enum as sa_Enum
from sqlmodel import Field, Integer, SQLModel


def get_current_time():
    return datetime.now(timezone.utc)


def get_current_year():
    return datetime.now(timezone.utc).year


class MonitorStatus(Enum):
    """Monitor status for media. \n"""

    DOWNLOADED = "downloaded"
    DOWNLOADING = "downloading"
    MISSING = "missing"
    MONITORED = "monitored"


class MediaBase(SQLModel):
    """Base class for the Media model. \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use MediaCreate, MediaRead, MediaUpdate models instead.
    """

    connection_id: int
    arr_id: int = Field(index=True)
    is_movie: bool = Field(default=True, index=True)
    title: str = Field(index=True)
    clean_title: str = Field(
        default="",
        sa_column=Column(
            String, server_default=text("('')"), index=True, nullable=False
        ),
    )
    year: int = Field(default_factory=get_current_year, index=True)
    language: str = Field(default="en", index=True)
    studio: str = Field(
        default="",
        sa_column=Column(String, server_default=text("('')"), nullable=False),
    )
    media_exists: bool = Field(
        default=False,
        sa_column=Column(Boolean, server_default="0", nullable=False),
    )
    media_filename: str = Field(
        default="",
        sa_column=Column(String, server_default=text("('')"), nullable=False),
    )
    season_count: int = Field(
        default=0,
        sa_column=Column(Integer, server_default="0", nullable=False),
    )
    overview: str | None = None
    runtime: int = 0
    # website: str | None = None
    youtube_trailer_id: str | None = None
    folder_path: str | None = None
    imdb_id: str | None = Field(default=None, index=True)
    txdb_id: str = Field(index=True)
    title_slug: str = Field(
        default="",
        sa_column=Column(
            String, server_default=text("('')"), index=True, nullable=False
        ),
    )
    poster_url: str | None = None
    fanart_url: str | None = None
    poster_path: str | None = None
    fanart_path: str | None = None
    trailer_exists: bool = Field(default=False)
    monitor: bool = Field(default=False)
    arr_monitored: bool = Field(default=False)
    status: MonitorStatus = Field(
        default=MonitorStatus.MISSING,
        sa_column=Column(
            sa_Enum(MonitorStatus, native_enum=False),
            server_default=text("'MISSING'"),
            nullable=False,
        ),
    )


class Media(MediaBase, table=True):
    """Media model for the database. \n
    This class is used for database CRUD operations only \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use MediaCreate, MediaRead, MediaUpdate models instead.
    """

    id: int | None = Field(default=None, primary_key=True)
    connection_id: int = Field(
        foreign_key="connection.id", index=True, ondelete="CASCADE"
    )
    is_movie: bool = Field(default=True, index=True)

    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)
    downloaded_at: datetime | None = Field(default=None)


class MediaCreate(MediaBase):
    """Media model for creating a new media objects. \n
    Defaults:
    - is_movie: True
    - year: current year
    - language: "en"
    - runtime: 0
    - youtube_trailer_id: None
    - trailer_exists: False
    - monitor: False
    - arr_monitored: False
    """

    pass


class MediaRead(MediaBase):
    """Media model for reading media."""

    id: int
    added_at: datetime
    updated_at: datetime
    downloaded_at: datetime | None


class MediaUpdate(MediaBase):
    """Media model for updating media. \n
    Defaults:
    - updated_at: current time [if any field is updated]
    """

    connection_id: int | None = None  # type: ignore
    arr_id: int | None = None  # type: ignore
    title: str | None = None  # type: ignore
    year: int | None = None  # type: ignore
    language: str | None = None  # type: ignore
    runtime: int | None = None  # type: ignore
    txdb_id: str | None = None  # type: ignore
    trailer_exists: bool | None = None  # type: ignore
    monitor: bool | None = None  # type: ignore
    arr_monitored: bool | None = None  # type: ignore

    downloaded_at: datetime | None = None
    updated_at: datetime = Field(default_factory=get_current_time)
