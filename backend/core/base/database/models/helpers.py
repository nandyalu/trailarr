from dataclasses import dataclass
from datetime import datetime
from sqlmodel import SQLModel

from core.base.database.models.media import MonitorStatus


@dataclass
class MediaImage:
    """Class for working with media images."""

    id: int
    is_poster: bool
    image_url: str | None
    image_path: str | None


# @dataclass
# class MediaTrailer:
#     """Class for working with media trailers."""

#     id: int
#     title: str
#     is_movie: bool
#     language: str
#     year: int
#     yt_id: str | None
#     folder_path: str
#     downloaded_at: datetime | None = None

#     def to_dict(self) -> dict:
#         """Convert MediaTrailer object to a dictionary."""
#         return asdict(self)


# @dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaReadDC(SQLModel):
    id: int
    created: bool
    folder_path: str | None
    arr_monitored: bool
    monitor: bool
    status: MonitorStatus
    trailer_exists: bool


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaUpdateDC:
    id: int
    monitor: bool
    status: MonitorStatus
    trailer_exists: bool | None = None
    yt_id: str | None = None
    downloaded_at: datetime | None = None


language_names = {
    "ar": "Arabic",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "hu": "Hungarian",
    "it": "Italian",
    "ja": "Japanese",
    "kn": "Kannada",
    "ko": "Korean",
    "ml": "Malayalam",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tr": "Turkish",
    "vi": "Vietnamese",
    "zh": "Chinese",
}
