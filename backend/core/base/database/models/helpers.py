from dataclasses import dataclass, asdict
from datetime import datetime

from core.base.database.models.media import MonitorStatus


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

    def to_dict(self) -> dict:
        """Convert MediaTrailer object to a dictionary."""
        return asdict(self)


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaReadDC:
    id: int
    created: bool
    folder_path: str | None
    arr_monitored: bool
    monitor: bool
    status: MonitorStatus


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaUpdateDC:
    id: int
    monitor: bool
    status: MonitorStatus
    trailer_exists: bool | None = None
    yt_id: str | None = None
    downloaded_at: datetime | None = None
