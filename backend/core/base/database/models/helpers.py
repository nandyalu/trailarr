from dataclasses import dataclass


@dataclass
class MediaImage:
    """Class for working with media images."""

    id: int
    is_poster: bool
    image_url: str | None
    image_path: str | None


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaReadDC:
    id: int
    created: bool
    folder_path: str | None
    arr_monitored: bool


@dataclass(eq=False, frozen=True, repr=False, slots=True)
class MediaUpdateDC:
    id: int
    monitor: bool
    trailer_exists: bool
