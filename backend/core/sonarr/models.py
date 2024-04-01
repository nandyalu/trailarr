from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def get_current_time():
    return datetime.now()


def get_current_year():
    return datetime.now().year


class SeriesBase(SQLModel):
    """Base class for the Series model.

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use Series, SeriesCreate, SeriesRead, or SeriesUpdate.
    """

    connection_id: int = Field(foreign_key="connection.id", index=True)
    sonarr_id: int = Field()
    title: str = Field(index=True)
    year: int = Field(default_factory=get_current_year, index=True)
    language: str = Field(default="en", index=True)
    overview: Optional[str] = None
    runtime: int = 0
    # website: Optional[str] = None
    youtube_trailer_id: Optional[str] = None
    folder_path: Optional[str] = None
    imdb_id: Optional[str] = Field(default=None, index=True)
    tvdb_id: str = Field(index=True)
    poster_url: Optional[str] = None
    fanart_url: Optional[str] = None
    poster_path: Optional[str] = None
    fanart_path: Optional[str] = None
    trailer_exists: bool = Field(default=False)
    monitor: bool = Field(default=False)
    sonarr_monitored: bool = Field(default=False)

    @property
    def arr_id(self):
        return self.sonarr_id

    @property
    def txdb_id(self):
        return self.tvdb_id

    @txdb_id.setter
    def txdb_id(self, value: str):
        self.tmdb_id = value
        return


class Series(SeriesBase, table=True):
    """Series model for the database. This is the main model for the application.

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use SeriesCreate, SeriesRead, or SeriesUpdate instead.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    connection_id: int = Field(foreign_key="connection.id", index=True)

    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)
    downloaded_at: Optional[datetime] = Field(default=None)


class SeriesCreate(SeriesBase):
    """Series model for creating a new series. This is used in the API while creating.

    Defaults:
    - year: current year
    - language: "en"
    - runtime: 0
    - trailer_exists: False
    - monitor: False
    - sonarr_monitored: False
    """

    pass


class SeriesRead(SeriesBase):
    """Series model for reading a series. This is used in the API to return data."""

    id: int
    added_at: datetime
    updated_at: datetime
    downloaded_at: Optional[datetime]


class SeriesUpdate(SeriesBase):
    """Series model for updating a series. This is used in the API while updating.

    Defaults:
    - updated_at: current time [if any field is updated]
    """

    connection_id: Optional[int] = None
    sonarr_id: Optional[int] = None

    title: Optional[str] = None
    year: Optional[int] = None
    language: Optional[str] = None
    runtime: Optional[int] = None
    tvdb_id: Optional[str] = None
    trailer_exists: Optional[bool] = None
    monitor: Optional[bool] = None
    sonarr_monitored: Optional[bool] = None
    downloaded_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=get_current_time)
