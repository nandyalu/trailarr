# from sqlmodel import Field

# from core.base.database.models.media import (
#     MediaCreate,
#     MediaDB,
#     MediaRead,
#     MediaUpdate,
# )


# class Movie(MediaDB):
#     """Movie model for the database. This is the main model for the application.

#     Note:

#         **DO NOT USE THIS CLASS DIRECTLY.**

#     Use MovieCreate, MovieRead, or MovieUpdate instead.
#     """

#     id: int | None = Field(default=None, primary_key=True)
#     connection_id: int = Field(foreign_key="connection.id", index=True)
#     is_movie: bool = True
#     arr_id: int = Field(alias="radarr_id", index=True)
#     txdb_id: str = Field(alias="tmdb_id", index=True)
#     arr_monitored: bool = Field(alias="radarr_monitored", default=False)


# class MovieCreate(MediaCreate):
#     """Movie model for creating a new movie. This is used in the API while creating.

#     Defaults:
#     - year: current year
#     - language: "en"
#     - runtime: 0
#     - trailer_exists: False
#     - monitor: False
#     - arr_monitored: False
#     """

#     arr_id: int = Field(alias="radarr_id")
#     txdb_id: str = Field(alias="tmdb_id")
#     arr_monitored: bool = Field(alias="radarr_monitored", default=False)


# class MovieRead(MediaRead):
#     """Movie model for reading a movie. This is used in the API to return data."""

#     arr_id: int = Field(alias="radarr_id")
#     txdb_id: str = Field(alias="tmdb_id")
#     arr_monitored: bool = Field(alias="radarr_monitored", default=False)


# class MovieUpdate(MediaUpdate):
#     """Movie model for updating a movie. This is used in the API while updating.

#     Defaults:
#     - updated_at: current time [if any field is updated]
#     """

#     arr_id: int | None = Field(alias="radarr_id", default=None)
#     txdb_id: str | None = Field(alias="tmdb_id", default=None)
#     arr_monitored: bool | None = Field(alias="radarr_monitored", default=None)
