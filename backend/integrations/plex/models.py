from pathlib import Path

from pydantic import AliasPath, BaseModel, Field, field_validator, model_validator

_RESOLUTION_MAP = {
    "sd": 480, "hd": 720, "fhd": 1080, "2k": 1440,
    "uhd": 2160, "4k": 2160, "8k": 4320,
}


def _parse_resolution(value) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if value.isdigit():
            return int(value)
        return _RESOLUTION_MAP.get(value.lower(), 0)
    return 0


class PlexLibrarySection(BaseModel):
    allowSync: bool = Field(default=False)
    filters: bool = Field(default=False)
    refreshing: bool = Field(default=False)
    key: str = Field(default="")
    type: str = Field(default="")
    title: str = Field(default="")
    language: str = Field(default="")
    folders: list[str] = Field(alias="Location", default_factory=list)

    @field_validator("folders", mode="before")
    @classmethod
    def extract_and_filter_paths(cls, v) -> list[str]:
        if isinstance(v, list):
            return [loc["path"] for loc in v if isinstance(loc, dict) and "path" in loc]
        return []


class PlexEpisodeLeaf(BaseModel):
    grandparentRatingKey: str = Field(default="")
    media_filename: str = Field(
        validation_alias=AliasPath("Media", 0, "Part", 0, "file"), default=""
    )
    media_folder: str = Field(default="")

    @model_validator(mode="after")
    def derive_show_folder(self):
        if self.media_filename:
            self.media_folder = str(Path(self.media_filename).parent)
        return self


class PlexMediaExtra(BaseModel):
    type: str = Field(default="")
    title: str = Field(default="")
    subtype: str = Field(default="")
    guid: str = Field(default="")
    resolution: int = Field(default=0)
    language: str = Field(
        default="",
        validation_alias=AliasPath("Media", 0, "Part", 0, "Stream", 1, "language"),
    )

    @model_validator(mode="before")
    @classmethod
    def extract_best_resolution(cls, data):
        if not isinstance(data, dict):
            return data
        best = 0
        for media in data.get("Media", []):
            if isinstance(media, dict):
                res = _parse_resolution(media.get("videoResolution", 480))
                if res > best:
                    best = res
        data["resolution"] = best
        return data


class PlexMediaItem(BaseModel):
    ratingKey: str = Field(default="")
    key: str = Field(default="")
    guid: str = Field(default="")
    slug: str = Field(default="")
    studio: str = Field(default="")
    type: str = Field(default="")
    title: str = Field(default="")
    original_title: str = Field(default="")
    summary: str = Field(default="")
    year: int = Field(default=0)
    tagline: str = Field(default="")
    thumb: str = Field(default="")
    art: str = Field(default="")
    duration: int = Field(default=0)
    originallyAvailableAt: str | None = Field(default=None)
    addedAt: int | None = Field(default=None)
    updatedAt: int | None = Field(default=None)
    media_filename: str = Field(
        validation_alias=AliasPath("Media", 0, "Part", 0, "file"), default=""
    )
    media_folder: str = Field(default="")
    locations: list[str] = Field(alias="Location", default_factory=list)
    guids: list[str] = Field(validation_alias=AliasPath("Guid"), default_factory=list)
    imdb_id: str | None = Field(default=None)
    tmdb_id: int | None = Field(default=None)
    tvdb_id: int | None = Field(default=None)
    extras: list[PlexMediaExtra] = Field(
        default_factory=list,
        validation_alias=AliasPath("Extras", "Metadata"),
    )

    @field_validator("locations", mode="before")
    @classmethod
    def extract_location_paths(cls, v) -> list[str]:
        if isinstance(v, list):
            return [loc["path"] for loc in v if isinstance(loc, dict) and "path" in loc]
        return []

    @field_validator("guids", mode="before")
    @classmethod
    def extract_guids(cls, v) -> list[str]:
        if isinstance(v, list):
            return [g["id"] for g in v if isinstance(g, dict) and "id" in g]
        return []

    @field_validator("duration", mode="before")
    @classmethod
    def convert_duration_to_minutes(cls, v) -> int:
        if not v:
            return 0
        if isinstance(v, str) and v.isdigit():
            v = int(v)
        if isinstance(v, (int, float)):
            return int(v // 60000)
        return 0

    @model_validator(mode="after")
    def extract_ids_and_folder(self):
        for guid in self.guids:
            if guid.startswith("imdb://"):
                self.imdb_id = guid.replace("imdb://", "")
            elif guid.startswith("tmdb://"):
                try:
                    self.tmdb_id = int(guid.replace("tmdb://", ""))
                except ValueError:
                    self.tmdb_id = None
            elif guid.startswith("tvdb://"):
                try:
                    self.tvdb_id = int(guid.replace("tvdb://", ""))
                except ValueError:
                    self.tvdb_id = None
        if self.media_filename:
            self.media_folder = "/".join(self.media_filename.split("/")[:-1])
        elif self.locations:
            self.media_folder = self.locations[0]
        self.media_folder = self.media_folder.rstrip("/").rstrip("\\")
        return self
