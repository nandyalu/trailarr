from datetime import datetime, timezone
from enum import Enum
from sqlmodel import Field, SQLModel, ForeignKey


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

    connection_id: int = Field(
        foreign_key=ForeignKey("connection.id", on_delete="CASCADE"), index=True
    )
    arr_id: int = Field(index=True)
    is_movie: bool = Field(default=True, index=True)
    title: str = Field(index=True)
    clean_title: str = Field(index=True, default="")
    year: int = Field(default_factory=get_current_year, index=True)
    language: str = Field(default="en", index=True)
    studio: str = Field(default="")
    media_exists: bool = Field(default=False)
    media_filename: str = Field(default="")
    overview: str | None = None
    runtime: int = 0
    # website: str | None = None
    youtube_trailer_id: str | None = None
    folder_path: str | None = None
    imdb_id: str | None = Field(default=None, index=True)
    txdb_id: str = Field(index=True)
    title_slug: str = Field(index=True, default="")
    poster_url: str | None = None
    fanart_url: str | None = None
    poster_path: str | None = None
    fanart_path: str | None = None
    trailer_exists: bool = Field(default=False)
    monitor: bool = Field(default=False)
    arr_monitored: bool = Field(default=False)
    status: MonitorStatus = Field(default=MonitorStatus.MISSING)


class Media(MediaBase, table=True):
    """Media model for the database. \n
    This class is used for database CRUD operations only \n
    Note: \n
        🚨**DO NOT USE THIS CLASS DIRECTLY.**🚨 \n
    Use MediaCreate, MediaRead, MediaUpdate models instead.
    """

    id: int | None = Field(default=None, primary_key=True)
    connection_id: int = Field(foreign_key="connection.id", index=True)
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

    connection_id: int | None = None
    arr_id: int | None = None
    title: str | None = None
    year: int | None = None
    language: str | None = None
    runtime: int | None = None
    txdb_id: str | None = None
    trailer_exists: bool | None = None
    monitor: bool | None = None
    arr_monitored: bool | None = None

    downloaded_at: datetime | None = None
    updated_at: datetime = Field(default_factory=get_current_time)
