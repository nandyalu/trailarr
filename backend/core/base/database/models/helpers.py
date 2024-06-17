from dataclasses import dataclass
from datetime import datetime


@dataclass
class MediaImage:
    """Class for working with media images."""

    id: int
    is_poster: bool
    image_url: str | None
    image_path: str | None


@dataclass
class MediaTrailer:
    """Class for working with media trailers."""

    id: int
    title: str
    year: int
    yt_id: str | None
    folder_path: str
    downloaded_at: datetime | None = None


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaReadDC:
    id: int
    created: bool
    folder_path: str | None
    arr_monitored: bool
    monitor: bool


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaUpdateDC:
    id: int
    monitor: bool
    trailer_exists: bool
    yt_id: str | None = None
    downloaded_at: datetime | None = None
