"""What TMDB tells Trailarr about a video."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TMDBVideo(BaseModel):
    """One entry of the `results` list of a TMDB videos response.

    TMDB lists videos of every site and every type. Trailarr keeps only
    what it can download and play: a YouTube video of a type it wants.
    """

    key: str = ""  # The id at the site — the YouTube id for a YouTube video
    name: str = ""
    site: str = ""
    type: str = ""  # 'Trailer', 'Teaser', 'Clip', ...
    official: bool = False
    size: int = 0
    language: str | None = Field(default=None, alias="iso_639_1")
    country: str | None = Field(default=None, alias="iso_3166_1")
    published_at: datetime | None = None

    model_config = {"populate_by_name": True}

    @field_validator("language", "country", mode="after")
    @classmethod
    def empty_string_is_no_value(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @property
    def is_youtube(self) -> bool:
        """True when Trailarr can download the video.

        TMDB also lists Vimeo and other sites, and Trailarr downloads from
        YouTube only — wargame W3.
        """
        return self.site.strip().lower() == "youtube" and bool(
            self.key.strip()
        )
