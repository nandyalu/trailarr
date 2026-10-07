"""The kinds of video that a profile can download.

TMDB sorts the videos of a title into types: trailers, teasers, clips,
featurettes, and more. A profile asks for one type, and a download
records the type it has. A featurette can then never count as the
trailer of a title.

Trailarr stores the type as a lowercase string in a plain VARCHAR
column, the same shape that Phase 8 wrote into `mediavideo.video_type`.
A new type needs no migration: add a member here.

Only the TRAILER type can fall back to a YouTube search. Every other
type comes from TMDB only (plans/phase-09-video-types.md, decision 5).
"""

from enum import Enum
from pathlib import Path


class VideoType(str, Enum):
    """A kind of video. The values are what the database stores."""

    TRAILER = "trailer"
    TEASER = "teaser"
    CLIP = "clip"
    FEATURETTE = "featurette"
    BEHIND_THE_SCENES = "behind_the_scenes"
    BLOOPERS = "bloopers"
    OTHER = "other"


VIDEO_TYPES: list[str] = [video_type.value for video_type in VideoType]
DEFAULT_VIDEO_TYPE = VideoType.TRAILER.value

# What a person reads in the UI and in the log.
VIDEO_TYPE_LABELS: dict[str, str] = {
    VideoType.TRAILER.value: "Trailer",
    VideoType.TEASER.value: "Teaser",
    VideoType.CLIP.value: "Clip",
    VideoType.FEATURETTE.value: "Featurette",
    VideoType.BEHIND_THE_SCENES.value: "Behind the Scenes",
    VideoType.BLOOPERS.value: "Bloopers",
    VideoType.OTHER.value: "Other",
}


def normalize_video_type(value: str | VideoType | None) -> str:
    """Return the stored form of a video type.

    Args:
        value (str | VideoType | None): A type, in any case. None and the
            empty string mean the default, a trailer.

    Returns:
        str: The lowercase value that the database stores.

    Raises:
        ValueError: If the value is not a known type.
    """
    if value is None:
        return DEFAULT_VIDEO_TYPE
    if isinstance(value, VideoType):
        return value.value
    normalized = value.strip().lower()
    if not normalized:
        return DEFAULT_VIDEO_TYPE
    if normalized not in VIDEO_TYPES:
        raise ValueError(
            f"Invalid video type: '{value}'. Valid types are: {VIDEO_TYPES}"
        )
    return normalized


def is_trailer_type(value: str | VideoType | None) -> bool:
    """True when the type is the trailer type, the only type that can
    search YouTube."""
    return normalize_video_type(value) == VideoType.TRAILER.value


def video_type_label(value: str | VideoType | None) -> str:
    """The label of a type for a log line or a message."""
    return VIDEO_TYPE_LABELS.get(normalize_video_type(value), "Other")


# TMDB writes its types in title case with spaces. The mapping is explicit
# and not a `.lower()`, so a type that TMDB adds later lands in OTHER
# instead of raising. `Opening Credits` exists for series.
_TMDB_TYPES: dict[str, VideoType] = {
    "trailer": VideoType.TRAILER,
    "teaser": VideoType.TEASER,
    "clip": VideoType.CLIP,
    "featurette": VideoType.FEATURETTE,
    "behind the scenes": VideoType.BEHIND_THE_SCENES,
    "bloopers": VideoType.BLOOPERS,
    "opening credits": VideoType.OTHER,
}


def video_type_from_tmdb(tmdb_type: str) -> VideoType:
    """Map the `type` field of a TMDB video to a VideoType.

    Args:
        tmdb_type (str): The type as TMDB writes it, such as
            'Behind the Scenes'.

    Returns:
        VideoType: The matching type, or OTHER for a type Trailarr does
            not know.
    """
    return _TMDB_TYPES.get(tmdb_type.strip().lower(), VideoType.OTHER)


# What Trailarr WRITES (decision 6). Only names that both Plex and
# Jellyfin read. Neither player knows a teaser or bloopers, and Plex does
# not know a clip, so a teaser is written as a trailer (the players show
# it as one, and the download row still records `teaser`), a clip as a
# scene, and bloopers as other.
FILE_SUFFIXES: dict[str, str] = {
    VideoType.TRAILER.value: "trailer",
    VideoType.TEASER.value: "trailer",
    VideoType.CLIP.value: "scene",
    VideoType.FEATURETTE.value: "featurette",
    VideoType.BEHIND_THE_SCENES.value: "behindthescenes",
    VideoType.BLOOPERS.value: "other",
    VideoType.OTHER.value: "other",
}

FOLDER_NAMES: dict[str, str] = {
    VideoType.TRAILER.value: "Trailers",
    VideoType.TEASER.value: "Trailers",
    VideoType.CLIP.value: "Scenes",
    VideoType.FEATURETTE.value: "Featurettes",
    VideoType.BEHIND_THE_SCENES.value: "Behind The Scenes",
    VideoType.BLOOPERS.value: "Other",
    VideoType.OTHER.value: "Other",
}


def file_suffix(value: str | VideoType | None) -> str:
    """The file name suffix that both players read for a type, without
    the hyphen. Example: 'featurette' for `Movie (2020)-featurette.mkv`."""
    return FILE_SUFFIXES[normalize_video_type(value)]


def folder_name(value: str | VideoType | None) -> str:
    """The folder name that both players read for a type."""
    return FOLDER_NAMES[normalize_video_type(value)]


# What Trailarr READS (decisions 2 and 4). Wider than what it writes: it
# accepts every name of Plex and of Jellyfin, so a file that another tool
# placed is classified too. TMDB has no interview type, and most
# interviews on TMDB are featurettes, so an interview counts as one.
_SUFFIX_TO_TYPE: dict[str, VideoType] = {
    "trailer": VideoType.TRAILER,
    "teaser": VideoType.TEASER,
    "clip": VideoType.CLIP,
    "scene": VideoType.CLIP,
    "featurette": VideoType.FEATURETTE,
    "interview": VideoType.FEATURETTE,
    "behindthescenes": VideoType.BEHIND_THE_SCENES,
    "bloopers": VideoType.BLOOPERS,
    "short": VideoType.OTHER,
    "deleted": VideoType.OTHER,
    "extra": VideoType.OTHER,
    "sample": VideoType.OTHER,
    "other": VideoType.OTHER,
}

_FOLDER_TO_TYPE: dict[str, VideoType] = {
    "trailer": VideoType.TRAILER,
    "trailers": VideoType.TRAILER,
    "teasers": VideoType.TEASER,
    "clips": VideoType.CLIP,
    "scenes": VideoType.CLIP,
    "featurettes": VideoType.FEATURETTE,
    "interviews": VideoType.FEATURETTE,
    "behind the scenes": VideoType.BEHIND_THE_SCENES,
    "bloopers": VideoType.BLOOPERS,
    "shorts": VideoType.OTHER,
    "deleted scenes": VideoType.OTHER,
    "extras": VideoType.OTHER,
    "samples": VideoType.OTHER,
    "other": VideoType.OTHER,
    "others": VideoType.OTHER,
}

# The folder names that mark a video as an extra, in lowercase. The
# scanner adds the folder names of the profiles to this set.
EXTRA_FOLDER_NAMES: frozenset[str] = frozenset(_FOLDER_TO_TYPE)

# Longest first, so `-behindthescenes` is not read as `-scenes`.
_SUFFIXES_BY_LENGTH = sorted(_SUFFIX_TO_TYPE, key=len, reverse=True)


def classify_by_suffix(file_path: str | Path) -> VideoType | None:
    """The type that the suffix of a file name gives, or None.

    Plex requires the name to end in the suffix exactly, so only the
    end of the stem counts: `Movie (2020)-featurette.mkv` is a
    featurette, `featurette of Movie.mkv` is not.
    """
    stem = Path(file_path).stem.strip().lower()
    for suffix in _SUFFIXES_BY_LENGTH:
        if stem.endswith(f"-{suffix}"):
            return _SUFFIX_TO_TYPE[suffix]
    return None


def classify_by_folder(file_path: str | Path) -> VideoType | None:
    """The type that the parent folder of a file gives, or None."""
    parent = Path(file_path).parent.name.strip().lower()
    return _FOLDER_TO_TYPE.get(parent)


def classify_extra_name(file_path: str | Path) -> VideoType | None:
    """Classify a video file by its name and folder.

    The suffix wins over the folder, because it is more specific
    (wargame W2: `Trailers/Movie-teaser.mkv` is a teaser). A name with
    'trailer' anywhere in it is a trailer, as before this phase. A file
    that matches nothing returns None: it is a media file, not an extra.

    Args:
        file_path (str | Path): The path of the file.

    Returns:
        VideoType | None: The type, or None for a file that is not an
            extra.
    """
    by_suffix = classify_by_suffix(file_path)
    if by_suffix is not None:
        return by_suffix
    by_folder = classify_by_folder(file_path)
    if by_folder is not None:
        return by_folder
    if "trailer" in Path(file_path).name.lower():
        return VideoType.TRAILER
    return None


# Words in a profile that say it downloads something other than a
# trailer (decision 7). A profile with one of these in its search query,
# file name, folder name or include words, and the trailer type, gets a
# nudge in the log at startup.
HACKY_PROFILE_KEYWORDS: tuple[str, ...] = (
    "teaser",
    "clip",
    "featurette",
    "behind the scenes",
    "behindthescenes",
    "bloopers",
    "interview",
)


def hacky_profile_keyword(*texts: str) -> str | None:
    """The first keyword that marks a trailer profile as a profile for
    another type of video, or None."""
    joined = " ".join(text.lower() for text in texts if text)
    for keyword in HACKY_PROFILE_KEYWORDS:
        if keyword in joined:
            return keyword
    return None
