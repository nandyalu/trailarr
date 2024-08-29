# Extract youtube video id from url
from datetime import datetime, timezone
import os
import re
import shutil
from threading import Semaphore
import unicodedata

from yt_dlp import YoutubeDL

from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.helpers import MediaTrailer
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
    options = {
        "format": "bestvideo[height<=?1080]+bestaudio",
        "noplaylist": True,
        "extract_flat": "discard_in_playlist",
        "fragment_retries": 10,
        # Fix issue with youtube-dl not being able to download some videos
        # See https://github.com/yt-dlp/yt-dlp/issues/9554
        "extractor_args": {"youtube": {"player_client": ["ios", "web"]}},
        "noprogress": True,
        "no_warnings": True,
        "quiet": True,
    }
    # Construct search query with keywords
    search_query = f"ytsearch: {movie_title}"
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
    # Return the first search result video id
    if not exclude:
        exclude = []
    for result in search_results["entries"]:
        if result["id"] in exclude:
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
        return False
    # Download the trailer
    trailer_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.debug(f"Downloading trailer for {media.title} from {trailer_url}")
    output_file = download_video(trailer_url, f"/tmp/{media.id}-trailer.%(ext)s")
    if not output_file:
        if retry_count > 0:
            logger.debug(
                f"Trailer download failed for {media.title} from {trailer_url}, "
                f"trying again... [{3 - retry_count}/3]"
            )
            media.yt_id = None
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
        if not os.path.exists(trailer_path):
            os.makedirs(trailer_path)
        return move_trailer_to_folder(output_file, trailer_path, media.title)
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
    filename = re.sub(r"[^a-zA-Z0-9_-,. ]", "_", filename)

    # Remove leading and trailing special characters
    filename = filename.strip("_.-")
    return filename


def get_trailer_path(
    src_path: str, dst_folder_path: str, new_title: str, increment_index: int = 1
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
        new_title (str): New title of the media.
        increment_index (int): Index to increment the trailer number. \n
    Returns:
        str: Destination path for the trailer file."""
    filename = os.path.basename(src_path)
    _ext = os.path.splitext(filename)[1]
    if increment_index > 1:
        filename = f"{new_title} - Trailer {increment_index}-trailer{_ext}"
    else:
        filename = f"{new_title} - Trailer-trailer{_ext}"
    # Normalize the filename
    filename = normalize_filename(filename)
    # Get the destination path
    dst_file_path = os.path.join(dst_folder_path, filename)
    # If file exists in destination, increment the index, else return path
    if os.path.exists(dst_file_path):
        return get_trailer_path(
            src_path, dst_folder_path, new_title, increment_index + 1
        )
    return dst_file_path


def move_trailer_to_folder(src_path: str, dst_folder_path: str, new_title: str) -> bool:
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

    # Construct the new filename and move the file
    dst_file_path = get_trailer_path(src_path, dst_folder_path, new_title)
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
