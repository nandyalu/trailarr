from typing import Any

from pydantic import AliasPath, BaseModel, Field, field_validator

from db.models.connection import ConnectionRead
from db.models.media import MediaCreate
from exceptions import InvalidResponseError
from integrations.arr.base import AsyncBaseArrManager
from services.arr_connection_manager import BaseConnectionManager


class RadarrManager(AsyncBaseArrManager):
    APPNAME = "Radarr"

    def __init__(self, url: str, api_key: str):
        self.version = "v3"
        super().__init__(url, api_key, self.version)

    async def get_system_status(self) -> str:
        return await self._get_system_status(self.APPNAME)

    async def get_all_movies(self) -> list[dict[str, Any]]:
        movies = await self._request("GET", f"/api/{self.version}/movie")
        if isinstance(movies, list):
            return movies
        raise InvalidResponseError("Invalid response from Radarr API")

    async def get_movie(self, radarr_id: int) -> dict[str, Any]:
        movie = await self._request("GET", f"/api/{self.version}/movie/{radarr_id}")
        if isinstance(movie, dict):
            return movie
        raise InvalidResponseError("Invalid response from Radarr API")

    get_all_media = get_all_movies
    get_media = get_movie


class RadarrDataParser(BaseModel):
    connection_id: int = Field(default=0)
    arr_id: int = Field(validation_alias="id")
    is_movie: bool = Field(default=True)
    title: str = Field()
    clean_title: str = Field(validation_alias="cleanTitle", default="")
    year: int = Field()
    language: str = Field(validation_alias=AliasPath("originalLanguage", "name"), default="English")
    overview: str | None = Field(default=None)
    runtime: int = Field(default=0)
    youtube_trailer_id: str | None = Field(validation_alias="youTubeTrailerId", default=None)
    studio: str = Field(default="")
    media_exists: bool = Field(default=False, validation_alias=AliasPath("statistics", "movieFileCount"))
    media_filename: str = Field(validation_alias=AliasPath("movieFile", "relativePath"), default="")
    season_count: int = Field(default=0)
    folder_path: str | None = Field(validation_alias="path", default="")
    imdb_id: str | None = Field(validation_alias="imdbId", default="")
    tmdb_id: str = Field(validation_alias="tmdbId")
    tvdb_id: str = Field(default="")
    title_slug: str = Field(validation_alias="titleSlug", default="")
    poster_url: str | None = None
    fanart_url: str | None = None
    arr_monitored: bool = Field(default=False, validation_alias="monitored")

    @field_validator("tmdb_id", mode="before")
    @classmethod
    def parse_tmdb_id(cls, v):
        return str(v)

    @field_validator("media_exists", mode="before")
    @classmethod
    def parse_media_exists(cls, v):
        return bool(v)


def parse_movie(connection_id: int, movie_data: dict[str, Any]) -> MediaCreate:
    parsed = RadarrDataParser(**movie_data)
    parsed.connection_id = connection_id
    new_movie = MediaCreate.model_validate(parsed.model_dump())
    for image in movie_data.get("images", []):
        if image["coverType"] == "poster" and not new_movie.poster_url:
            new_movie.poster_url = str(image.get("remoteUrl", "")).strip()
        elif image["coverType"] == "fanart" and not new_movie.fanart_url:
            new_movie.fanart_url = str(image.get("remoteUrl", "")).strip()
        if new_movie.poster_url and new_movie.fanart_url:
            break
    return new_movie


class RadarrConnectionManager(BaseConnectionManager):
    def __init__(self, connection: ConnectionRead):
        radarr_manager = RadarrManager(connection.url, connection.api_key)
        super().__init__(connection, radarr_manager, parse_movie, is_movie=True)
