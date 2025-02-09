from typing import Any

from pydantic import AliasPath, BaseModel, Field, field_validator

from core.base.database.models.media import MediaCreate


class RadarrDataParser(BaseModel):
    """Class to parse the data from Radarr."""

    connection_id: int = Field(default=0)
    arr_id: int = Field(validation_alias="id")
    is_movie: bool = Field(default=True)
    title: str = Field()
    clean_title: str = Field(validation_alias="cleanTitle", default="")
    year: int = Field()
    language: str = Field(
        validation_alias=AliasPath("originalLanguage", "name"), default="English"
    )
    overview: str | None = Field(default=None)
    runtime: int = Field(default=0)
    youtube_trailer_id: str | None = Field(
        validation_alias="youTubeTrailerId", default=None
    )
    studio: str = Field(default="")
    media_exists: bool = Field(
        default=False, validation_alias=AliasPath("statistics", "movieFileCount")
    )
    media_filename: str = Field(
        validation_alias=AliasPath("movieFile", "relativePath"), default=""
    )
    folder_path: str | None = Field(validation_alias="path", default="")
    imdb_id: str | None = Field(validation_alias="imdbId", default="")
    txdb_id: str = Field(validation_alias="tmdbId")
    title_slug: str = Field(validation_alias="titleSlug", default="")
    poster_url: str | None = None
    fanart_url: str | None = None
    arr_monitored: bool = Field(default=False, validation_alias="monitored")

    @field_validator("txdb_id", mode="before")
    @classmethod
    def parse_txdb_id(cls, v):
        return str(v)

    @field_validator("media_exists", mode="before")
    @classmethod
    def parse_media_exists(cls, v):
        return bool(v)


def parse_movie(connection_id: int, movie_data: dict[str, Any]) -> MediaCreate:
    """Parse the movie data from Radarr to a MovieCreate object.\n
    Args:
        connection_id (int): The connection id.
        movie_data (dict[str, Any]): The movie data from Radarr.\n
    Returns:
        MovieCreate: The movie data as a MovieCreate object."""
    movie_parsed = RadarrDataParser(**movie_data)
    movie_parsed.connection_id = connection_id

    # print(movie_parsed.model_dump())

    new_movie = MediaCreate.model_validate(movie_parsed.model_dump())
    for image in movie_data["images"]:
        # Check if the image is a poster or fanart
        if image["coverType"] == "poster":
            # Set first poster as the poster_url, if not already set
            if not new_movie.poster_url:
                new_movie.poster_url = str(image.get("remoteUrl", "")).strip()
        elif image["coverType"] == "fanart":
            # Set first fanart as the fanart_url, if not already set
            if not new_movie.fanart_url:
                new_movie.fanart_url = str(image.get("remoteUrl", "")).strip()
        # Break if both poster and fanart are set
        if new_movie.poster_url and new_movie.fanart_url:
            break

    return new_movie
