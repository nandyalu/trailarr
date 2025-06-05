from functools import partial
import os
import re

from yt_dlp import YoutubeDL

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.media import MediaRead
from core.base.database.models.helpers import language_names
from core.base.database.models.trailerprofile import TrailerProfileRead

logger = ModuleLogger("TrailersDownloader")


def extract_youtube_id(url: str) -> str | None:
    """Extract youtube video id from url. \n
    Args:
        url (str): URL of the youtube video. \n
    Returns:
        str|None: Youtube video id / None if invalid URL."""
    regex = re.compile(
        r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
    )
    match = regex.match(url)
    if match and len(match.group(2)) == 11:
        return match.group(2)
    else:
        return None


def __has_included_words(include_words: str, title: str) -> bool:
    """Check if the title contains all of the included words."""
    if not include_words:
        return True
    # Split and filter out empty/whitespace-only words
    include_list = [w.strip() for w in include_words.split(",") if w.strip()]
    if not include_list:
        return True
    for word in include_list:
        if word.lower() not in title.lower():
            logger.debug(
                f"Included word '{word}' not found in title '{title}'"
            )
            return False
    return True


def __has_excluded_words(exclude_words: str, title: str) -> bool:
    """Check if the title contains any of the excluded words."""
    if not exclude_words:
        return False
    # Split and filter out empty/whitespace-only words
    exclude_list = [w.strip() for w in exclude_words.split(",") if w.strip()]
    if not exclude_list:
        return False
    for word in exclude_list:
        if word.lower() in title.lower():
            logger.debug(f"Excluded word '{word}' found in title '{title}'")
            return True
    return False


def _yt_search_filter(
    info: dict,
    *,
    incomplete,
    profile: TrailerProfileRead,
    exclude: list[str] | None,
):
    """Filter for videos shorter than 10 minutes and not a review."""
    id = info.get("id")
    if not id:
        return None
    if not exclude:
        exclude = []
    if id in exclude:
        logger.debug(f"Skipping video in excluded list: {id}")
        return "Video in excluded list"
    duration = int(info.get("duration", 0))
    min_duration = profile.min_duration
    if duration and duration < min_duration:
        logger.debug(f"Skipping short video (<{min_duration}): {id}")
        return f"The video is shorter than {min_duration} seconds"
    max_duration = profile.max_duration
    if duration and duration > max_duration:
        logger.debug(f"Skipping long video (>{max_duration}): {id}")
        return f"The video is longer than {max_duration} seconds"
    title = str(info.get("title", ""))
    if "review" in title.lower():
        logger.debug(f"Skipping review video: {id}")
        return "The video is a review"
    # Check if the title contains all of the included words
    if not __has_included_words(profile.include_words, title):
        return "The video does not contain all of the included words"
    # Filter out videos with excluded words
    if __has_excluded_words(profile.exclude_words, title):
        return "The video contains an excluded word"


def search_yt_for_trailer(
    media: MediaRead,
    profile: TrailerProfileRead,
    exclude: list[str] | None = None,
) -> str | None:
    """Search for trailer on youtube. \n
    Args:
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): The trailer profile to use.
        exclude (list[str], Optional): List of video ids to exclude. \n
    Returns:
        str | None: Youtube video id / None if not found."""
    logger.debug(f"Searching youtube for trailer for '{media.title}'...")
    # Set options
    filter_func = partial(_yt_search_filter, profile=profile, exclude=exclude)
    options = {
        "format": "bestvideo[height<=?1080]+bestaudio",
        "match_filter": filter_func,
        "noplaylist": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        "noprogress": True,
        "no_warnings": True,
        "quiet": True,
    }
    if app_settings.yt_cookies_path:
        logger.debug(f"Using cookies file: {app_settings.yt_cookies_path}")
        options["cookiefile"] = f"{app_settings.yt_cookies_path}"
    # Construct search query with keywords for 5 search results
    search_query_format = profile.search_query
    # Convert media object to dictionary for formatting
    format_opts = media.model_dump()
    format_opts["is_movie"] = "movie" if media.is_movie else "series"
    # Remove year from search query if 0
    if media.year == 0:
        format_opts["year"] = ""
    # Replace the media filename with the filename without extension
    _filename_wo_ext, _ = os.path.splitext(media.media_filename)
    format_opts["media_filename"] = _filename_wo_ext
    # Replace language code with language name
    format_opts["language"] = language_names.get(
        media.language, media.language
    )
    # Get search query by replacing supplied options
    search_query = search_query_format.format(**format_opts)
    # Remove extra spaces and trailing spaces
    search_query = search_query.replace("  ", " ").strip()
    # Add ytsearch5: prefix to search query
    search_query = f"ytsearch10: {search_query}"
    # Append "trailer" to search query if not already present
    if "trailers" not in search_query:
        search_query += " trailer"
    logger.debug(f"Using Search query: {search_query}")
    # Search for video
    with YoutubeDL(options) as ydl:
        search_results = ydl.extract_info(
            search_query, download=False, process=True
        )

    # If results are invalid, return None
    if not search_results:
        return None
    if not isinstance(search_results, dict):
        return None
    if "entries" not in search_results:
        return None
    # Return the first search result video id that matches the criteria
    if not exclude:
        exclude = []
    for result in search_results["entries"]:
        # Skip if video id is in exclude list
        if result["id"] in exclude:
            logger.debug(f"Skipping excluded video: {result['id']}")
            continue
        logger.debug(f"Found trailer for {media.title}: {result['id']}")
        return str(result["id"])


def get_video_id(
    media: MediaRead,
    profile: TrailerProfileRead,
    exclude: list[str] | None = None,
) -> str | None:
    """Get youtube video id for the media object. \n
    Search for trailer on youtube if not found. \n
    Args:
        media (MediaRead): Media object.
        profile (TrailerProfileRead): The trailer profile to use.
        exclude (list[str], Optional=None): List of video ids to exclude. \n
    Returns:
        str|None: Youtube video id / None if not found."""
    video_id = ""
    if media.youtube_trailer_id:
        if "youtu" in media.youtube_trailer_id:
            video_id = extract_youtube_id(media.youtube_trailer_id)
        else:
            video_id = media.youtube_trailer_id
    if video_id:
        return video_id
    # Search for trailer on youtube
    video_id = search_yt_for_trailer(media, profile, exclude)
    return video_id
