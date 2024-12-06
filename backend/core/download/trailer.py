# Extract youtube video id from url
from datetime import datetime, timezone
from functools import partial
import re
from threading import Semaphore

from yt_dlp import YoutubeDL

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.helpers import MediaTrailer, language_names
from core.download.video import download_video
from core.download import trailer_file, video_analysis
from exceptions import DownloadFailedError

logger = ModuleLogger("TrailersDownloader")


def _extract_youtube_id(url: str) -> str | None:
    """Extract youtube video id from url. \n
    Args:
        url (str): URL of the youtube video. \n
    Returns:
        str | None: Youtube video id / None if invalid URL."""
    regex = re.compile(
        r"^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|\&v=)([^#\&\?]*).*"
    )
    match = regex.match(url)
    if match and len(match.group(2)) == 11:
        return match.group(2)
    else:
        return None


def _yt_search_filter(info: dict, *, incomplete, exclude: list[str] | None):
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
    min_duration = app_settings.trailer_min_duration
    if duration and duration < min_duration:
        logger.debug(f"Skipping short video (<{min_duration}): {id}")
        return f"The video is shorter than {min_duration} seconds"
    max_duration = app_settings.trailer_max_duration
    if duration and duration > max_duration:
        logger.debug(f"Skipping long video (>{max_duration}): {id}")
        return f"The video is longer than {max_duration} seconds"
    title = str(info.get("title", ""))
    if "review" in title.lower():
        logger.debug(f"Skipping review video: {id}")
        return "The video is a review"
    exclude_words = app_settings.exclude_words
    if exclude_words:
        if "," in exclude_words:
            exclude_words = exclude_words.split(",")
            for word in exclude_words:
                word = word.strip()
                if word in title.lower():
                    logger.debug(f"Skipping video with excluded word '{word}': {id}")
                    return "The video contains an excluded word"
        else:
            if exclude_words in title.lower():
                logger.debug(
                    f"Skipping video with excluded word '{exclude_words}': {id}"
                )
                return "The video contains an excluded word"


def _search_yt_for_trailer(
    media: MediaTrailer,
    exclude: list[str] | None = None,
) -> str | None:
    """Search for trailer on youtube. \n
    Args:
        media (MediaTrailer): Media object.
        exclude (list[str], Optional): List of video ids to exclude. \n
    Returns:
        str | None: Youtube video id / None if not found."""
    logger.debug(f"Searching youtube for trailer for '{media.title}'...")
    # Set options
    filter_func = partial(_yt_search_filter, exclude=exclude)
    options = {
        "format": "bestvideo[height<=?1080]+bestaudio",
        "match_filter": filter_func,
        "noplaylist": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        # Fix issue with youtube-dl not being able to download some videos
        # See https://github.com/yt-dlp/yt-dlp/issues/9554
        # "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
        "noprogress": True,
        "no_warnings": True,
        "quiet": True,
    }
    # Construct search query with keywords for 5 search results
    search_query_format = app_settings.trailer_search_query
    format_opts = media.to_dict()  # Convert media object to dictionary for formatting
    format_opts["is_movie"] = "movie" if media.is_movie else "series"
    # Remove year from search query if 0
    if media.year == 0:
        format_opts["year"] = ""
    # Replace language code with language name
    format_opts["language"] = language_names.get(media.language, media.language)
    # Get search query by replacing supplied options
    search_query = search_query_format.format(**format_opts)
    # Remove extra spaces and trailing spaces
    search_query = search_query.replace("  ", " ").strip()
    # Add ytsearch5: prefix to search query
    search_query = f"ytsearch5: {search_query}"
    # Append "trailer" to search query if not already present
    if "trailers" not in search_query:
        search_query += " trailer"
    # search_query = f"ytsearch5: {media.title}"
    # if media.year:
    #     search_query += f" ({media.year})"
    # search_query += " movie" if media.is_movie else " series"
    # search_query += " trailer"

    # Search for video
    with YoutubeDL(options) as ydl:
        search_results = ydl.extract_info(search_query, download=False, process=True)

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


def _get_yt_id(media: MediaTrailer, exclude: list[str] | None = None) -> str | None:
    """Get youtube video id for the media object. \n
    Search for trailer on youtube if not found. \n
    Args:
        media (MediaTrailer): Media object.
        exclude (list[str], Optional=None): List of video ids to exclude. \n
    Returns:
        str | None: Youtube video id / None if not found."""
    video_id = ""
    if media.yt_id:
        if "youtu" in media.yt_id:
            video_id = _extract_youtube_id(media.yt_id)
        else:
            video_id = media.yt_id
    if video_id:
        return video_id
    # Search for trailer on youtube
    video_id = _search_yt_for_trailer(media, exclude)
    return video_id


def download_trailer(
    media: MediaTrailer,
    trailer_folder: bool | None = None,
    # is_movie: bool,
    retry_count: int = 2,
    exclude: list[str] | None = None,
) -> bool:
    """Download trailer for a media object. \n
    Args:
        media (MediaTrailer): Media object.
        trailer_folder (bool, Optional): Whether to move the trailer to a separate folder.
        retry_count (int, Optional=2): Number of retries to download the trailer.
        exclude (list[str], Optional=None): List of video ids to exclude. \n
    Raises:
        DownloadFailedError: If trailer download fails. \n
    Returns:
        bool: True if trailer is downloaded successfully, False otherwise."""
    output_file = ""
    trailer_downloaded = False
    trailer_url = ""
    if not exclude:
        exclude = []
    # Get youtube video id for the media object, search youtube if not found
    video_id = _get_yt_id(media, exclude)
    if not video_id:
        trailer_downloaded = False
    else:
        # Download the trailer
        trailer_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Downloading trailer for {media.title} from {trailer_url}")
        tmp_output_file = f"/tmp/{media.id}-trailer.%(ext)s"
        output_file = download_video(trailer_url, tmp_output_file)
        tmp_output_file = tmp_output_file.replace(
            "%(ext)s", app_settings.trailer_file_format
        )
        # Check if the trailer is downloaded successfully and verify audio/video streams
        trailer_downloaded = trailer_file.verify_download(
            tmp_output_file, output_file, media.title
        )
        # Remove silence at end of video if enabled
        if app_settings.trailer_remove_silence:
            output_file = video_analysis.remove_silence_at_end(output_file)

    # Retry downloading the trailer if failed
    if not trailer_downloaded:
        if retry_count > 0:
            logger.info(
                f"Trailer download failed for {media.title} from {trailer_url}, "
                f"trying again... [{3 - retry_count}/3]"
            )
            media.yt_id = None
            if video_id:
                exclude.append(video_id)
            return download_trailer(media, trailer_folder, retry_count - 1, exclude)
        raise DownloadFailedError(f"Failed to download trailer for {media.title}")
    logger.info(f"Trailer downloaded for {media.title}, Moving to folder...")
    media.yt_id = video_id  # Update the youtube video id
    
    # Move the trailer to the specified folder
    try:
        trailer_file.move_trailer_to_folder(output_file, media, trailer_folder)
        logger.info(
            f"Trailer Downloaded successfully for {media.title} from {trailer_url}"
        )
        return True
    except Exception as e:
        _move_res_msg = str(e)
        logger.error(f"Failed to move trailer to folder: {_move_res_msg}")
        raise DownloadFailedError(f"Failed to move trailer to folder: {_move_res_msg}")


def download_trailers(
    media_list: list[MediaTrailer], is_movie: bool
) -> list[MediaTrailer]:
    """Download trailers for a list of media objects. \n
    Args:
        media_list (list[MediaTrailer]): List of media objects.
        is_movie (bool): Whether the media type is movie or show. \n
    Returns:
        list[MediaTrailer]: List of media objects for which trailers are downloaded."""
    media_type = "movies" if is_movie else "series"
    logger.info(f"Downloading trailers for {len(media_list)} monitored {media_type}...")
    trailer_folder = trailer_file.trailer_folder_needed(is_movie)
    sem = Semaphore(2)
    download_list = []
    for media in media_list:
        sem.acquire()
        logger.info(f"Downloading trailer for '[{media.id}]{media.title}'...")
        try:
            if download_trailer(media, trailer_folder):
                media.downloaded_at = datetime.now(timezone.utc)
                download_list.append(media)
                logger.info(
                    f"Trailer downloaded for '[{media.id}]{media.title}' from [{media.yt_id}]"
                )
            else:
                logger.info(f"Trailer download failed for '[{media.id}]{media.title}'")
        except Exception as e:
            logger.error(
                f"Failed to download trailer for '[{media.id}]{media.title}': {e}"
            )
        sem.release()
    logger.info(f"Downloaded trailers for {len(download_list)} {media_type}")
    return download_list


# Uncomment below for testing, change logging level to DEBUG for additional logs
# if __name__ == "__main__":
#     mediaT = MediaTrailer(
#         id=1,
#         title="The Matrix",
#         year=1999,
#         yt_id="pLWda_RrQn4",
#         folder_path="/tmp/The Matrix (1999)",
#     )
#     res = download_trailer(mediaT, False, True)
#     if res:
#         print(res)
