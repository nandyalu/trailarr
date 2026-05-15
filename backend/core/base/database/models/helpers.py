from dataclasses import dataclass
from datetime import datetime

from core.base.database.models.base import AppSQLModel


@dataclass
class MediaImage:
    """Class for working with media images."""

    id: int
    is_poster: bool
    image_url: str | None
    image_path: str | None
    headers: dict | None = None  # extra HTTP headers (e.g. X-Plex-Token)


class MediaReadDC(AppSQLModel):
    id: int
    created: bool
    folder_path: str | None
    arr_monitored: bool
    monitor: bool


@dataclass(eq=False, repr=False, slots=True)
class MediaUpdateDC:
    id: int
    monitor: bool
    yt_id: str | None = None
    downloaded_at: datetime | None = None

    def model_dump(self) -> dict:
        """Dump MediaUpdateDC to dictionary."""
        return {
            "id": self.id,
            "monitor": self.monitor,
            "yt_id": self.yt_id,
            "downloaded_at": self.downloaded_at,
        }


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
