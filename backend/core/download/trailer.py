# Extract youtube video id from url
from datetime import datetime, timezone
from functools import partial
import os
import re
import shutil
from threading import Semaphore
import unicodedata

from yt_dlp import YoutubeDL

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.helpers import MediaTrailer
from core.download import video_analysis
from core.download.video import download_video

logger = ModuleLogger("TrailersDownloader")


def _get_youtube_id(url: str) -> str | None:
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
    if duration and duration > 600:
        logger.debug(f"Skipping long video (>10m): {id}")
        return "The video is longer than 10 minutes"
    title = str(info.get("title", ""))
    if "review" in title.lower():
        logger.debug(f"Skipping review video: {id}")
        return "The video is a review"


def _search_yt_for_trailer(
    movie_title: str,
    is_movie=True,
    movie_year: int | None = None,
    exclude: list[str] | None = None,
):
    """Search for trailer on youtube. \n
    Args:
        movie_title (str): Title of the movie or show.
        is_movie (bool): Whether the media type is movie or show.
        movie_year (str): Year of the movie or show. \n
    Returns:
        str | None: Youtube video id / None if not found."""
    logger.debug(f"Searching youtube for trailer for '{movie_title}'...")
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
    search_query = f"ytsearch5: {movie_title}"
    if movie_year:
        search_query += f" ({movie_year})"
    search_query += " movie" if is_movie else " series"
    search_query += " trailer"

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
        logger.debug(f"Found trailer for {movie_title}: {result['id']}")
        return str(result["id"])


def download_trailer(
    media: MediaTrailer,
    trailer_folder: bool,
    is_movie: bool,
    retry_count: int = 2,
    exclude: list[str] | None = None,
) -> bool:
    """Download trailer for a media object. \n
    Args:
        media (MediaTrailer): Media object.
        trailer_folder (bool): Whether to move the trailer to a separate folder.
        is_movie (bool): Whether the media type is movie or show. \n
    Returns:
        bool: True if trailer is downloaded successfully, False otherwise."""
    trailer_downloaded = False
    trailer_url = ""
    if not exclude:
        exclude = []
    if media.yt_id:
        if media.yt_id.startswith("http"):
            media.yt_id = _get_youtube_id(media.yt_id)
        video_id = media.yt_id
    else:
        # Search for trailer on youtube
        video_id = _search_yt_for_trailer(media.title, is_movie, media.year, exclude)
    if not video_id:
        trailer_downloaded = False
    else:
        # Download the trailer
        trailer_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.debug(f"Downloading trailer for {media.title} from {trailer_url}")
        tmp_output_file = f"/tmp/{media.id}-trailer.%(ext)s"
        output_file = download_video(trailer_url, tmp_output_file)
        tmp_output_file = tmp_output_file.replace(
            "%(ext)s", app_settings.trailer_file_format
        )
        # Check if the trailer is downloaded successfully
        if not output_file or not os.path.exists(tmp_output_file):
            trailer_downloaded = False
        else:
            # Verify the trailer has audio and video streams
            trailer_downloaded = video_analysis.verify_trailer_streams(output_file)
            if not trailer_downloaded:
                logger.debug(
                    f"Trailer has either no audio or video streams: {media.title}"
                )
                logger.debug(f"Deleting failed trailer file: {output_file}")
                try:
                    os.remove(output_file)
                except Exception as e:
                    logger.error(f"Failed to delete trailer file: {e}")

    # Retry downloading the trailer if failed
    if not trailer_downloaded:
        if retry_count > 0:
            logger.debug(
                f"Trailer download failed for {media.title} from {trailer_url}, "
                f"trying again... [{3 - retry_count}/3]"
            )
            media.yt_id = None
            if video_id:
                exclude.append(video_id)
            return download_trailer(
                media, trailer_folder, is_movie, retry_count - 1, exclude
            )

        return False
    logger.debug(f"Trailer downloaded for {media.title}, Moving to folder...")
    media.yt_id = video_id
    # Move the trailer to the specified folder
    if trailer_folder:
        trailer_path = os.path.join(media.folder_path, "Trailers")
    else:
        trailer_path = media.folder_path
    try:
        # if not os.path.exists(trailer_path):
        #     os.makedirs(trailer_path)
        return move_trailer_to_folder(output_file, trailer_path, media)
    except Exception as e:
        logger.error(f"Failed to move trailer to folder: {e}")
        return False


def get_folder_permissions(path: str) -> int:
    # Get the permissions of the directory (if exists)
    # otherwise get it's parent directory permissions (that exists, recursively)
    while not os.path.exists(path):
        path = os.path.dirname(path)
    parent_dir = os.path.dirname(path)
    return os.stat(parent_dir).st_mode


def normalize_filename(filename: str) -> str:
    # Normalize the filename to handle Unicode characters
    filename = (
        unicodedata.normalize("NFKD", filename)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    # Remove any character that is not alphanumeric, underscore, hyphen, comma, dot or space
    filename = re.sub(r"[^a-zA-Z0-9_,. -]", "_", filename)
    # Replace multiple spaces with a single space
    filename = re.sub(r"\s+", " ", filename)
    # Remove leading and trailing special characters
    filename = filename.strip("_.-")
    return filename


def get_trailer_path(
    src_path: str, dst_folder_path: str, media: MediaTrailer, increment_index: int = 1
) -> str:
    """Get the destination path for the trailer file. \n
    Checks if <new_title> - Trailer-trailer<ext> exists in the destination folder. \n
    If it exists, increments the index and checks again. \n
    Recursively increments the index until a non-existing filename is found. \n
    Example filenames: \n
    - <new_title> - Trailer-trailer.mp4 \n
    - <new_title> - Trailer 2-trailer.mp4 \n
    - <new_title> - Trailer 3-trailer.mp4 \n
    Args:
        src_path (str): Source path of the trailer file.
        dst_folder_path (str): Destination folder path.
        media (MediaTitle): MediaTitle object.
        increment_index (int): Index to increment the trailer number. \n
    Returns:
        str: Destination path for the trailer file."""
    # Get trailer file name format from settings
    title_format = app_settings.trailer_file_name
    if title_format.count("{") != title_format.count("}"):
        logger.error("Invalid title format, setting to default")
        return src_path
    title_opts = media.to_dict()  # Convert media object to dictionary for formatting
    title_opts["resolution"] = f"{app_settings.trailer_resolution}p"
    title_opts["vcodec"] = app_settings.trailer_video_format
    title_opts["acodec"] = app_settings.trailer_audio_format

    # Remove increment index if it's 0
    title_opts["ii"] = increment_index
    if increment_index == 1:
        title_format = title_format.replace("{ii}", "")
    else:
        # If increment index > 0 and not in title format, add it
        if "{ii}" not in title_format:
            # If title format ends with "-trailer.{ext}", add increment index before it
            if title_format.endswith("-trailer.{ext}"):
                title_format = title_format.replace(
                    "-trailer.{ext}", "{ii}-trailer.{ext}"
                )
            # If title format does not end with "-trailer.{ext}",
            # add increment index before extension
            else:
                title_format = title_format.replace(".{ext}", "{ii}.{ext}")
        # Add space before increment index
        title_format = title_format.replace("{ii}", "{ii: }")

    # Get filename from source path and extract extension
    filename = os.path.basename(src_path)
    _ext = os.path.splitext(filename)[1]
    _ext = _ext.replace(".", "")
    title_opts["ext"] = _ext

    # Format the title to get the new filename
    filename = title_format.format(**title_opts)

    # Normalize the filename
    filename = normalize_filename(filename)
    # Get the destination path
    dst_file_path = os.path.join(dst_folder_path, filename)
    # If file exists in destination, increment the index, else return path
    if os.path.exists(dst_file_path):
        return get_trailer_path(src_path, dst_folder_path, media, increment_index + 1)
    return dst_file_path


def move_trailer_to_folder(
    src_path: str, dst_folder_path: str, media: MediaTrailer
) -> bool:
    # Move the trailer file to the specified folder
    if not os.path.exists(src_path):
        logger.debug(f"Trailer file not found at: {src_path}")
        return False

    # Get destination permissions
    dst_permissions = get_folder_permissions(dst_folder_path)

    # Check if destination exists, else create it
    if not os.path.exists(dst_folder_path):
        logger.debug(f"Creating folder: {dst_folder_path}")
        os.makedirs(dst_folder_path, mode=dst_permissions)
        # Explicitly set the permissions for the folder
        os.chmod(dst_folder_path, dst_permissions)

    # Construct the new filename and move the file
    dst_file_path = get_trailer_path(src_path, dst_folder_path, media)
    shutil.move(src_path, dst_file_path)

    # Set the moved file's permissions to match the destination folder's permissions
    os.chmod(dst_file_path, dst_permissions)
    return True


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
    trailer_folder = False
    if is_movie:
        if app_settings.trailer_folder_movie:
            trailer_folder = True
    else:
        if app_settings.trailer_folder_series:
            trailer_folder = True
    sem = Semaphore(2)
    download_list = []
    for media in media_list:
        sem.acquire()
        logger.info(f"Downloading trailer for '[{media.id}]{media.title}'...")
        if download_trailer(media, trailer_folder, is_movie):
            media.downloaded_at = datetime.now(timezone.utc)
            download_list.append(media)
            logger.info(
                f"Trailer downloaded for '[{media.id}]{media.title}' from [{media.yt_id}]"
            )
        else:
            logger.info(f"Trailer download failed for '[{media.id}]{media.title}'")
        sem.release()
    logger.info(f"Downloaded trailers for {len(download_list)} {media_type}")
    return download_list
