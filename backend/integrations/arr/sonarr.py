from typing import Any

from pydantic import AliasPath, BaseModel, Field, field_validator

from db.models.connection import ConnectionRead
from db.models.media import MediaCreate
from exceptions import InvalidResponseError
from integrations.arr.base import AsyncBaseArrManager
from services.arr_connection_manager import BaseConnectionManager


class SonarrManager(AsyncBaseArrManager):
    APPNAME = "Sonarr"

    def __init__(self, url: str, api_key: str):
        self.version = "v3"
        super().__init__(url, api_key, self.version)

    async def get_system_status(self) -> str:
        return await self._get_system_status(self.APPNAME)

    async def get_all_series(self) -> list[dict[str, Any]]:
        series = await self._request("GET", f"/api/{self.version}/series")
        if isinstance(series, list):
            return series
        raise InvalidResponseError("Invalid response from Sonarr API")

    async def get_series(self, sonarr_id: int) -> dict[str, Any]:
        series = await self._request("GET", f"/api/{self.version}/series/{sonarr_id}")
        if isinstance(series, dict):
            return series
        raise InvalidResponseError("Invalid response from Sonarr API")

    get_all_media = get_all_series
    get_media = get_series


class SonarrDataParser(BaseModel):
    connection_id: int = Field(default=0)
    arr_id: int = Field(validation_alias="id")
    is_movie: bool = Field(default=False)
    title: str = Field()
    clean_title: str = Field(validation_alias="cleanTitle", default="")
    year: int = Field()
    language: str = Field(validation_alias=AliasPath("originalLanguage", "name"), default="English")
    overview: str | None = Field(default=None)
    runtime: int = Field(default=0)
    youtube_trailer_id: str | None = Field(validation_alias="youTubeTrailerId", default="")
    studio: str = Field(default="", validation_alias="network")
    media_exists: bool = Field(default=False, validation_alias=AliasPath("statistics", "episodeFileCount"))
    media_filename: str = Field(default="")
    season_count: int = Field(default=0, validation_alias=AliasPath("statistics", "seasonCount"))
    folder_path: str | None = Field(validation_alias="path", default="")
    imdb_id: str | None = Field(validation_alias="imdbId", default="")
    tvdb_id: str = Field(validation_alias="tvdbId")
    tmdb_id: str = Field(default="", validation_alias="tmdbId")
    title_slug: str = Field(validation_alias="titleSlug", default="")
    poster_url: str | None = None
    fanart_url: str | None = None
    arr_monitored: bool = Field(default=False, validation_alias="monitored")

    @field_validator("tvdb_id", mode="before")
    @classmethod
    def parse_tvdb_id(cls, v):
        return str(v) if v else ""

    @field_validator("tmdb_id", mode="before")
    @classmethod
    def parse_tmdb_id(cls, v):
        s = str(v) if v else ""
        return "" if s == "0" else s

    @field_validator("media_exists", mode="before")
    @classmethod
    def parse_media_exists(cls, v):
        return bool(v)


def parse_series(connection_id: int, series_data: dict[str, Any]) -> MediaCreate:
    parsed = SonarrDataParser(**series_data)
    parsed.connection_id = connection_id
    new_series = MediaCreate.model_validate(parsed.model_dump())
    for image in series_data.get("images", []):
        if image["coverType"] == "poster" and not new_series.poster_url:
            new_series.poster_url = str(image.get("remoteUrl", "")).strip()
        elif image["coverType"] == "fanart" and not new_series.fanart_url:
            new_series.fanart_url = str(image.get("remoteUrl", "")).strip()
        if new_series.poster_url and new_series.fanart_url:
            break
    return new_series


class SonarrConnectionManager(BaseConnectionManager):
    def __init__(self, connection: ConnectionRead):
        sonarr_manager = SonarrManager(connection.url, connection.api_key)
        super().__init__(connection, sonarr_manager, parse_series, is_movie=False)
