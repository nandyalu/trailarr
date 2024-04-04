from typing import Any

from pydantic import AliasPath, BaseModel, Field

from backend.core.radarr.models import MovieCreate


class RadarrDataParser(BaseModel):
    """Class to parse the data from Radarr."""

    connection_id: int = Field(default=0)
    radarr_id: int = Field(validation_alias="id")
    title: str = Field()
    year: int = Field()
    language: str = Field(validation_alias=AliasPath("originalLanguage", "name"))
    overview: str | None = Field(default=None)
    runtime: int = Field(default=0)
    youtube_trailer_id: str | None = Field(validation_alias="youTubeTrailerId")
    folder_path: str | None = Field(validation_alias="folderPath")
    imdb_id: str | None = Field(validation_alias="imdbId")
    tmdb_id: str = Field(validation_alias="tmdbId")
    poster_url: str | None = None
    fanart_url: str | None = None
    radarr_monitored: bool = Field(default=False, validation_alias="monitored")


def parse_movie(connection_id: int, movie_data: dict[str, Any]) -> MovieCreate:
    """Parse the movie data from Radarr to a MovieCreate object.\n
    Args:
        connection_id (int): The connection id.
        movie_data (dict[str, Any]): The movie data from Radarr.\n
    Returns:
        MovieCreate: The movie data as a MovieCreate object."""
    movie_parsed = RadarrDataParser(**movie_data)
    movie_parsed.connection_id = connection_id
    new_movie = MovieCreate.model_validate(movie_parsed.model_dump())
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
