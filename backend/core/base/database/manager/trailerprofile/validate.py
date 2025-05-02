from core.base.database.models.trailerprofile import (
    TrailerProfile,
    TrailerProfileCreate,
)

VALID_AUDIO_FORMATS = ["aac", "ac3", "eac3", "flac", "opus", "copy"]
VALID_FILE_FORMATS = ["mkv", "mp4", "webm"]
VALID_VIDEO_FORMATS = ["h264", "hevc", "vp8", "vp9", "av1", "copy"]
VALID_VIDEO_RESOLUTIONS = [240, 360, 480, 720, 1080, 1440, 2160]
VALID_SUBTITLES_FORMATS = ["srt", "vtt"]

VALID_YT_DICT = {
    "clean_title": "clean_title",
    "imdb_id": "imdb_id",
    "is_movie": "is_movie",
    "language": "language",
    "media_filename": "media_filename",
    "studio": "studio",
    "title": "title",
    "title_slug": "title_slug",
    "txdb_id": "txdb_id",
    "year": "year",
}

VALID_FILE_DICT = {
    "clean_title": "clean_title",
    "imdb_id": "imdb_id",
    "is_movie": "is_movie",
    "language": "language",
    "media_filename": "media_filename",
    "studio": "studio",
    "title": "title",
    "title_slug": "title_slug",
    "txdb_id": "txdb_id",
    "year": "year",
    "acodec": "audio_format",
    "resolution": "video_resolution",
    "vcodec": "video_format",
    "youtube_id": "youtube_id",
}


def file_format_valid(file_format: str) -> bool:
    """
    Validate the file format.
    Args:
        file_format (str): File format
    Returns:
        bool: True if the file format is valid.
    Raises:
        ValueError: If the file format is invalid
    """
    if file_format in VALID_FILE_FORMATS:
        return True
    raise ValueError(
        f"Invalid file format: {file_format}. Valid formats are:"
        f" {VALID_FILE_FORMATS}"
    )


def file_name_valid(file_name: str) -> bool:
    """
    Validate the file name template to ensure variables used are valid.
    Args:
        file_name (str): File name template
    Returns:
        bool: True if the file name is valid.
    Raises:
        ValueError: If the file name template is invalid
    """
    # Try to replace file_name template with valid variables
    try:
        file_name.format(**VALID_FILE_DICT)
    except Exception as e:
        raise ValueError(f"Invalid file name template: '{file_name}'. {e}")
    return True


def folder_name_valid(folder_name: str) -> bool:
    """
    Validate the folder name is not empty.
    Args:
        folder_name (str): Folder name
    Returns:
        bool: True if the folder name is valid.
    Raises:
        ValueError: If the folder name is empty or whitespace
    """
    if bool(folder_name.strip()):
        return True
    raise ValueError("Folder name cannot be empty or whitespace.")


def audio_format_valid(audio_format: str) -> bool:
    """
    Validate the audio format.
    Args:
        audio_format (str): Audio format
    Returns:
        bool: True if the audio format is valid.
    Raises:
        ValueError: If the audio format is invalid
    """
    if audio_format in VALID_AUDIO_FORMATS:
        return True
    raise ValueError(
        f"Invalid audio format: {audio_format}. Valid formats are:"
        f" {VALID_AUDIO_FORMATS}"
    )


def audio_volume_level_valid(audio_volume_level: int) -> bool:
    """
    Validate the audio volume level. Between 1 and 200 (both inclusive).
    Args:
        audio_volume_level (int): Audio volume level
    Returns:
        bool: True if the audio volume level is valid.
    Raises:
        ValueError: If the audio volume level is invalid
    """
    if 1 <= audio_volume_level <= 200:
        return True
    raise ValueError(
        f"Invalid audio volume level: {audio_volume_level}. "
        "Valid range is 1 to 200."
    )


def video_resolution_valid(video_resolution: int) -> bool:
    """
    Validate the video resolution.
    Args:
        video_resolution (int): Video resolution
    Returns:
        bool: True if the video resolution is valid.
    Raises:
        ValueError: If the video resolution is invalid
    """
    if video_resolution in VALID_VIDEO_RESOLUTIONS:
        return True
    raise ValueError(
        f"Invalid video resolution: {video_resolution}. Valid resolutions are:"
        f" {VALID_VIDEO_RESOLUTIONS}"
    )


def video_format_valid(video_format: str) -> bool:
    """
    Validate the video format.
    Args:
        video_format (str): Video format
    Returns:
        bool: True if the video format is valid.
    Raises:
        ValueError: If the video format is invalid
    """
    if video_format in VALID_VIDEO_FORMATS:
        return True
    raise ValueError(
        f"Invalid video format: {video_format}. Valid formats are:"
        f" {VALID_VIDEO_FORMATS}"
    )


def subtitles_format_valid(subtitles_format: str) -> bool:
    """
    Validate the subtitles format.
    Args:
        subtitles_format (str): Subtitles format
    Returns:
        bool: True if the subtitles format is valid.
    Raises:
        ValueError: If the subtitles format is invalid
    """
    if subtitles_format in VALID_SUBTITLES_FORMATS:
        return True
    raise ValueError(
        f"Invalid subtitles format: {subtitles_format}. Valid formats are:"
        f" {VALID_SUBTITLES_FORMATS}"
    )


def duration_valid(min_duration: int, max_duration: int) -> bool:
    """
    Validate the duration.
    Args:
        min_duration (int): Minimum duration
        max_duration (int): Maximum duration
    Returns:
        bool: True if the duration is valid.
    Raises:
        ValueError: If the duration is invalid
    """
    if min_duration < 30:
        raise ValueError(
            "Minimum duration should be at least 30 seconds. "
            f"Provided: {min_duration} seconds."
        )
    if max_duration < 90:
        raise ValueError(
            "Maximum duration should be at least 90 seconds. "
            f"Provided: {max_duration} seconds."
        )
    if max_duration > 600:
        raise ValueError(
            "Maximum duration should be at most 600 seconds. "
            f"Provided: {max_duration} seconds."
        )
    if max_duration - min_duration < 60:
        raise ValueError(
            "Duration difference should be at least 60 seconds. Provided:"
            f" {min_duration} seconds (min), {max_duration} seconds (max)."
        )
    return True


def search_query_valid(search_query: str) -> bool:
    """
    Validate the search query.
    Args:
        search_query (str): Search query
    Returns:
        bool: True if the search query is valid.
    Raises:
        ValueError: If the search query is invalid
    """
    # Try to replace search_query template with valid variables
    try:
        search_query.format(**VALID_YT_DICT)
    except Exception as e:
        raise ValueError(
            f"Invalid search query template: '{search_query}'. {e}"
        )
    return True


def validate_trailerprofile(
    trailerprofile: TrailerProfileCreate | TrailerProfile,
) -> bool:
    """
    Validate the trailer profile.
    Args:
        trailerprofile (TrailerProfile): TrailerProfile object
    Returns:
        bool: True if the trailer profile is valid.
    Raises:
        ValueError: If the trailer profile is invalid.
    """
    if not file_format_valid(trailerprofile.file_format):
        return False
    if not file_name_valid(trailerprofile.file_name):
        return False
    if not folder_name_valid(trailerprofile.folder_name):
        return False
    if not audio_format_valid(trailerprofile.audio_format):
        return False
    if not audio_volume_level_valid(trailerprofile.audio_volume_level):
        return False
    if not video_resolution_valid(trailerprofile.video_resolution):
        return False
    if not video_format_valid(trailerprofile.video_format):
        return False
    if not subtitles_format_valid(trailerprofile.subtitles_format):
        return False
    if not duration_valid(
        trailerprofile.min_duration, trailerprofile.max_duration
    ):
        return False
    if not search_query_valid(trailerprofile.search_query):
        return False
    return True
