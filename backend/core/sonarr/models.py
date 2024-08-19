# from sqlmodel import Field

# from core.base.database.models.media import (
#     MediaCreate,
#     MediaDB,
#     MediaRead,
#     MediaUpdate,
# )


# class Series(MediaDB):
#     """Series model for the database. This is the main model for the application.

#     Note:

#         **DO NOT USE THIS CLASS DIRECTLY.**

#     Use SeriesCreate, SeriesRead, or SeriesUpdate instead.
#     """

#     id: int | None = Field(default=None, primary_key=True)
#     connection_id: int = Field(foreign_key="connection.id", index=True)
#     is_movie: bool = False
#     arr_id: int = Field(alias="sonarr_id", index=True)
#     txdb_id: str = Field(alias="tvdb_id", index=True)
#     arr_monitored: bool = Field(alias="sonarr_monitored", default=False)


# class SeriesCreate(MediaCreate):
#     """Series model for creating a new series. This is used in the API while creating.

#     Defaults:
#     - year: current year
#     - language: "en"
#     - runtime: 0
#     - trailer_exists: False
#     - monitor: False
#     - sonarr_monitored: False
#     """

#     arr_id: int = Field(alias="sonarr_id")
#     txdb_id: str = Field(alias="tvdb_id")
#     arr_monitored: bool = Field(alias="sonarr_monitored", default=False)


# class SeriesRead(MediaRead):
#     """Series model for reading a series. This is used in the API to return data."""

#     arr_id: int = Field(alias="sonarr_id")
#     txdb_id: str = Field(alias="tvdb_id")
#     arr_monitored: bool = Field(alias="sonarr_monitored", default=False)


# class SeriesUpdate(MediaUpdate):
#     """Series model for updating a series. This is used in the API while updating.

#     Defaults:
#     - updated_at: current time [if any field is updated]
#     """

#     arr_id: int = Field(alias="sonarr_id", default=None)
#     txdb_id: str = Field(alias="tvdb_id", default=None)
#     arr_monitored: bool = Field(alias="sonarr_monitored", default=False)
