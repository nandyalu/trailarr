from typing import Any

from pydantic import AliasPath, BaseModel, Field, field_validator

from core.base.database.models.media import MediaCreate


class SonarrDataParser(BaseModel):
    """Class to parse the data from Sonarr."""

    connection_id: int = Field(default=0)
    arr_id: int = Field(validation_alias="id")
    is_movie: bool = Field(default=False)
    title: str = Field()
    year: int = Field()
    language: str = Field(
        validation_alias=AliasPath("originalLanguage", "name"), default="en"
    )
    overview: str | None = Field(default=None)
    runtime: int = Field(default=0)
    # Sonarr does not have youtbetrailerid
    youtube_trailer_id: str | None = Field(
        validation_alias="youTubeTrailerId", default=""
    )
    folder_path: str | None = Field(validation_alias="path", default="")
    imdb_id: str | None = Field(validation_alias="imdbId", default="")
    txdb_id: str = Field(validation_alias="tvdbId")
    poster_url: str | None = None
    fanart_url: str | None = None
    arr_monitored: bool = Field(default=False, validation_alias="monitored")

    @field_validator("txdb_id", mode="before")
    @classmethod
    def parse_txdb_id(cls, v):
        return str(v)


def parse_series(connection_id: int, series_data: dict[str, Any]) -> MediaCreate:
    """Parse the series data from Sonarr to a SeriesCreate object.\n
    Args:
        connection_id (int): The connection id.
        series_data (dict[str, Any]): The series data from Radarr.\n
    Returns:
        SeriesCreate: The series data as a SeriesCreate object."""
    series_parsed = SonarrDataParser(**series_data)
    series_parsed.connection_id = connection_id

    # print(series_parsed.model_dump())

    new_series = MediaCreate.model_validate(series_parsed.model_dump())
    for image in series_data["images"]:
        # Check if the image is a poster or fanart
        if image["coverType"] == "poster":
            # Set first poster as the poster_url, if not already set
            if not new_series.poster_url:
                new_series.poster_url = str(image.get("remoteUrl", "")).strip()
        elif image["coverType"] == "fanart":
            # Set first fanart as the fanart_url, if not already set
            if not new_series.fanart_url:
                new_series.fanart_url = str(image.get("remoteUrl", "")).strip()
        # Break if both poster and fanart are set
        if new_series.poster_url and new_series.fanart_url:
            break

    return new_series


# from typing import Any

# from core.sonarr.models import SeriesCreate


# def parse_series(connection_id: int, series_data: dict[str, Any]) -> SeriesCreate:
#     """Parse the series data from Sonarr to a SeriesCreate object.

#     Args:
#         connection_id (int): The connection id.
#         series_data (dict[str, Any]): The series data from Sonarr.

#     Returns:
#         SeriesCreate: The series data as a SeriesCreate object."""
#     _sonarr_id = series_data.get("id", "")
#     _title = series_data.get("title", "")
#     _tvdb_id = series_data.get("tvdbId", "")
#     new_series = SeriesCreate(
#         connection_id=connection_id,
#         sonarr_id=_sonarr_id,
#         title=_title,
#         tvdb_id=_tvdb_id,
#     )

#     _year = series_data.get("year", "")
#     if _year:
#         new_series.year = int(_year)
#     _language = series_data.get("originalLanguage", {}).get("name", "")
#     if _language:
#         new_series.language = _language
#     new_series.overview = series_data.get("overview", "")
#     new_series.runtime = int(series_data.get("runtime", 0))
#     new_series.youtube_trailer_id = series_data.get("youTubeTrailerId", "")
#     new_series.folder_path = series_data.get("path", "")
#     new_series.imdb_id = series_data.get("imdbId", "")
#     for image in series_data["images"]:
#         if image["coverType"] == "poster":
#             new_series.poster_url = image["remoteUrl"]
#         elif image["coverType"] == "fanart":
#             new_series.fanart_url = image["remoteUrl"]
#     new_series.sonarr_monitored = series_data.get("monitored", False)

#     return new_series
