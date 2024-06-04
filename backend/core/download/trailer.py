# Extract youtube video id from url
import datetime
import logging
import os
import re
import shutil
from threading import Semaphore

from yt_dlp import YoutubeDL

from config.config import config
from core.base.database.models.helpers import MediaTrailer
from core.download.video import download_video


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
    logging.debug(f"Searching youtube for trailer for '{movie_title}'...")
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
        logging.debug(f"Found trailer for {movie_title}: {result['id']}")
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
    logging.debug(f"Downloading trailer for {media.title} from {trailer_url}")
    output_file = download_video(trailer_url, f"/tmp/{media.id}-trailer.%(ext)s")
    if not output_file:
        if retry_count > 0:
            logging.debug(
                f"Trailer download failed for {media.title} from {trailer_url}, "
                f"trying again... [{3 - retry_count}/3]"
            )
            media.yt_id = None
            exclude.append(video_id)
            return download_trailer(
                media, trailer_folder, is_movie, retry_count - 1, exclude
            )

        return False
    logging.debug(f"Trailer downloaded for {media.title}, Moving to folder...")
    media.yt_id = video_id
    # Move the trailer to the specified folder
    if trailer_folder:
        trailer_path = os.path.join(media.folder_path, "Trailers")
    else:
        trailer_path = media.folder_path
    if not os.path.exists(trailer_path):
        os.makedirs(trailer_path)
    return move_trailer_to_folder(output_file, trailer_path, media.title)


def move_trailer_to_folder(src_path: str, dst_folder_path: str, new_title: str) -> bool:
    # Move the trailer file to the specified folder
    if not os.path.exists(src_path):
        logging.debug(f"Trailer file not found at: {src_path}")
        return False
    if not os.path.exists(dst_folder_path):
        logging.debug(f"Creating folder: {dst_folder_path}")
        os.makedirs(dst_folder_path)
    filename = os.path.basename(src_path)
    filename = f"{new_title} - Trailer-trailer{os.path.splitext(filename)[1]}"
    dst_file_path = os.path.join(dst_folder_path, filename)
    shutil.move(src_path, dst_file_path)
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
    logging.info(
        f"Downloading trailers for {len(media_list)} {'movies' if is_movie else 'series'}"
    )
    trailer_folder = False
    if is_movie:
        if config.trailer_folder_movie:
            trailer_folder = True
    else:
        if config.trailer_folder_series:
            trailer_folder = True
    sem = Semaphore(2)
    download_list = []
    for media in media_list:
        sem.acquire()
        logging.info(f"Downloading trailer for '[{media.id}]{media.title}'...")
        if download_trailer(media, trailer_folder, is_movie):
            media.downloaded_at = datetime.datetime.now()
            download_list.append(media)
            logging.info(
                f"Trailer downloaded for '[{media.id}]{media.title}' from [{media.yt_id}]"
            )
        else:
            logging.info(f"Trailer download failed for '[{media.id}]{media.title}'")
        sem.release()
    logging.info(
        f"Downloaded trailers for {len(download_list)} {'movies' if is_movie else 'series'}"
    )
    return download_list


# if __name__ == "__main__":
#     config_logging()
#     trailer_url = "https://www.youtube.com/watch?v=6ZfuNTqbHE8"
#     # download_video(trailer_url)
#     print(_get_ytdl_options())
