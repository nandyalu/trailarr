from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def get_current_time():
    return datetime.now()


def get_current_year():
    return datetime.now().year


class MovieBase(SQLModel):
    """Base class for the Movie model.

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use Movie, MovieCreate, MovieRead, or MovieUpdate.
    """

    connection_id: int = Field(foreign_key="connection.id", index=True)
    radarr_id: int = Field()
    title: str = Field(index=True)
    year: int = Field(default_factory=get_current_year, index=True)
    language: str = Field(default="en", index=True)
    overview: Optional[str] = None
    runtime: int = 0
    website: Optional[str] = None
    youtube_trailer_id: Optional[str] = None
    folder_path: Optional[str] = None
    imdb_id: Optional[str] = Field(default=None, index=True)
    tmdb_id: str = Field(index=True)
    poster_url: Optional[str] = None
    fanart_url: Optional[str] = None
    poster_path: Optional[str] = None
    fanart_path: Optional[str] = None
    trailer_exists: bool = Field(default=False)
    monitor: bool = Field(default=False)
    radarr_monitored: bool = Field(default=False)

    @property
    def arr_id(self):
        return self.radarr_id

    @property
    def txdb_id(self):
        return self.tmdb_id

    @txdb_id.setter
    def txdb_id(self, value: str):
        self.tmdb_id = value
        return


class Movie(MovieBase, table=True):
    """Movie model for the database. This is the main model for the application.

    Note:

        **DO NOT USE THIS CLASS DIRECTLY.**

    Use MovieCreate, MovieRead, or MovieUpdate instead.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    connection_id: int = Field(foreign_key="connection.id", index=True)

    added_at: datetime = Field(default_factory=get_current_time)
    updated_at: datetime = Field(default_factory=get_current_time)
    downloaded_at: Optional[datetime] = Field(default=None)


class MovieCreate(MovieBase):
    """Movie model for creating a new movie. This is used in the API while creating.

    Defaults:
    - year: current year
    - language: "en"
    - runtime: 0
    - trailer_exists: False
    - monitor: False
    - radarr_monitored: False
    """

    pass


class MovieRead(MovieBase):
    """Movie model for reading a movie. This is used in the API to return data."""

    id: int
    added_at: datetime
    updated_at: datetime
    downloaded_at: Optional[datetime]


class MovieUpdate(MovieBase):
    """Movie model for updating a movie. This is used in the API while updating.

    Defaults:
    - updated_at: current time [if any field is updated]
    """

    connection_id: Optional[int] = None
    radarr_id: Optional[int] = None

    title: Optional[str] = None
    year: Optional[int] = None
    language: Optional[str] = None
    runtime: Optional[int] = None
    trailer_exists: Optional[bool] = None
    monitor: Optional[bool] = None
    radarr_monitored: Optional[bool] = None
    downloaded_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=get_current_time)
