import os
import re
import shutil
import unicodedata
from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.media import MediaRead
from core.base.database.models.trailerprofile import TrailerProfileRead
from core.download import video_analysis
from core.download.video_analysis import VideoInfo
from exceptions import (
    FileMoveFailedError,
    FolderNotFoundError,
    FolderPathEmptyError,
)

logger = ModuleLogger("TrailersDownloader")


def get_folder_permissions(path: str) -> int:
    """Get the permissions of the directory (if exists) \n
    Otherwise get it's parent directory permissions (that exists, recursively). \n
    Args:
        path (str): Path of the directory. \n
    Returns:
        int: Permissions of the directory."""
    # Get the permissions of the directory (if exists)
    # otherwise get it's parent directory permissions (that exists, recursively)
    logger.debug(f"Getting permissions for folder: {path}")
    while not os.path.exists(path):
        path = os.path.dirname(path)
    parent_dir = os.path.dirname(path)
    _permissions = os.stat(parent_dir).st_mode
    logger.debug(f"Folder permissions: {oct(_permissions)}")
    return _permissions


def normalize_filename(filename: str) -> str:
    """Normalize the filename to handle Unicode characters. \n
    Args:
        filename (str): Filename to normalize. \n
    Returns:
        str: Normalized filename."""
    # Normalize the filename to handle Unicode characters
    _filename = unicodedata.normalize("NFKD", filename)

    # Remove any character that is not supported by Unix or Windows file systems
    _filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", _filename)
    # Replace multiple spaces with a single space
    _filename = re.sub(r"\s+", " ", _filename)
    # Remove leading and trailing special characters
    _filename = _filename.strip("_.-")
    logger.debug(f"Normalized filename: '{filename}' -> '{_filename}'")
    return _filename


def _extract_video_details(video_info: VideoInfo) -> tuple[int, str, str]:
    """Extract resolution and codecs from VideoInfo streams.
    Args:
        video_info (VideoInfo): Video info object.
    Returns:
        tuple[int, str, str]: Resolution, video codec, audio codec.
    """
    resolution = 0
    video_codec = "unknown"
    audio_codec = "unknown"
    for stream in video_info.streams:
        if stream.codec_type == "video" and stream.coded_height > 0:
            resolution = stream.coded_height
            video_codec = stream.codec_name
        elif stream.codec_type == "audio" and audio_codec == "unknown":
            audio_codec = stream.codec_name
    return resolution, video_codec, audio_codec


def get_trailer_filename(
    media: MediaRead,
    profile: TrailerProfileRead,
    ext: str,
    increment_index: int,
    video_info: VideoInfo | None = None,
) -> str:
    """Get the trailer filename based on app settings. \n
    Args:
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        ext (str): Extension of the trailer file.
        increment_index (int): Index to increment the trailer number.
        video_info (VideoInfo | None): Actual downloaded video info for
            accurate naming. Falls back to profile settings if None. \n
    Returns:
        str: Trailer filename."""
    if increment_index == 1:
        logger.debug(f"Getting trailer filename for '{media.title}'...")
    # Get trailer file name format from settings
    title_format = profile.file_name
    if title_format.count("{") != title_format.count("}"):
        logger.error(
            "Invalid title format, setting to default file name format"
        )
        title_format = app_settings._DEFAULT_FILE_NAME
    # Convert media object to dictionary for formatting
    title_opts = media.model_dump()
    # Replace the media filename with the filename without extension
    _filename_wo_ext, _ = os.path.splitext(media.media_filename)
    title_opts["media_filename"] = _filename_wo_ext
    title_opts["is_movie"] = "movie" if media.is_movie else "series"
    title_opts["youtube_id"] = media.youtube_trailer_id
    # Use actual downloaded resolution/codecs if available, else fallback to profile
    if video_info:
        resolution, vcodec, acodec = _extract_video_details(video_info)
        title_opts["resolution"] = f"{resolution}p"
        title_opts["vcodec"] = vcodec
        title_opts["acodec"] = acodec
    else:
        title_opts["resolution"] = f"{profile.video_resolution}p"
        title_opts["vcodec"] = profile.video_format
        title_opts["acodec"] = profile.audio_format
    title_opts["ext"] = ext

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

    # Format the title to get the new filename
    filename = title_format.format(**title_opts)

    # Normalize the filename
    filename = normalize_filename(filename)
    return filename


def get_trailer_path(
    src_path: str,
    dst_folder_path: str,
    media: MediaRead,
    profile: TrailerProfileRead,
    increment_index: int = 1,
    video_info: VideoInfo | None = None,
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
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        increment_index (int): Index to increment the trailer number.
        video_info (VideoInfo | None): Actual downloaded video info. \n
    Returns:
        str: Destination path for the trailer file."""
    if increment_index == 1:
        logger.debug(f"Getting trailer path for '{media.title}'...")

    # Get filename from source path and extract extension
    filename = os.path.basename(src_path)
    _ext = os.path.splitext(filename)[1]
    _ext = _ext.replace(".", "")

    # Format the title to get the new filename
    filename = get_trailer_filename(
        media, profile, _ext, increment_index, video_info
    )

    # Get the destination path
    dst_file_path = os.path.join(dst_folder_path, filename)
    # If file exists in destination, increment the index, else return path
    if os.path.exists(dst_file_path):
        logger.debug(
            f"File already exists at: {dst_file_path}, incrementing index..."
        )
        return get_trailer_path(
            src_path,
            dst_folder_path,
            media,
            profile,
            increment_index + 1,
            video_info,
        )
    logger.debug(f"Trailer path: {dst_file_path}")
    return dst_file_path


def move_trailer_to_folder(
    src_path: str,
    media: MediaRead,
    profile: TrailerProfileRead,
    video_info: VideoInfo | None = None,
) -> str:
    """Move the trailer file to the specified folder.
    Args:
        src_path (str): Source path of the trailer file.
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        video_info (VideoInfo | None): Actual downloaded video info.
    Raises:
        FileNotFoundError: If the trailer file is not found at the source path.
        FolderPathEmptyError: If the media folder path is empty.
        FolderNotFoundError: If the media folder does not exist.
        Exception: Any other exceptions raised while moving file.
    Returns:
        str: Destination path if trailer is moved successfully."""
    logger.debug(f"Moving trailer to media folder: '{media.folder_path}'")
    # Move the trailer file to the specified folder
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"Trailer file not found at: {src_path}")

    # Get the destination path, create subfolder if enabled
    if profile.custom_folder == "{media_folder}":
        # If custom folder is set to media folder, use media folder path
        # Check if media folder path exists
        if not media.folder_path:
            raise FolderPathEmptyError(
                "Folder path is empty or not set for media:"
                f" {media.title} [{media.id}]"
            )
        if not os.path.exists(media.folder_path):
            raise FolderNotFoundError(folder_path=media.folder_path)
        if profile.folder_enabled:
            folder_name = profile.folder_name.strip()
            if not folder_name:
                logger.debug(
                    "Folder name is empty, using default folder name:"
                    " 'Trailers'"
                )
                folder_name = "Trailers"
            # Create a separate folder for trailers if enabled
            dst_folder_path = os.path.join(media.folder_path, folder_name)
        else:
            # Else, move the trailer to the media folder
            dst_folder_path = media.folder_path
    else:
        # Format the custom folder path
        title_opts = media.model_dump()
        title_opts["media_folder"] = media.folder_path
        # Replace the media filename with the filename without extension
        _filename_wo_ext, _ = os.path.splitext(media.media_filename)
        title_opts["media_filename"] = _filename_wo_ext
        title_opts["is_movie"] = "movie" if media.is_movie else "series"
        title_opts["youtube_id"] = media.youtube_trailer_id
        # Use actual downloaded info if available, else fallback to profile
        if video_info:
            resolution, vcodec, acodec = _extract_video_details(video_info)
            title_opts["resolution"] = f"{resolution}p"
            title_opts["vcodec"] = vcodec
            title_opts["acodec"] = acodec
        else:
            title_opts["resolution"] = f"{profile.video_resolution}p"
            title_opts["vcodec"] = profile.video_format
            title_opts["acodec"] = profile.audio_format
        title_opts["ext"] = profile.file_format
        dst_folder_path = profile.custom_folder.format(**title_opts)

    # Get destination permissions
    dst_permissions = get_folder_permissions(dst_folder_path)

    # Check if destination exists, else create it
    if not os.path.exists(dst_folder_path):
        logger.debug(
            "Destination folder does not exist! Creating folder:"
            f" '{dst_folder_path}'"
        )
        os.makedirs(dst_folder_path, mode=dst_permissions)
        # Explicitly set the permissions for the folder
        logger.debug(
            f"Setting permissions for folder: '{dst_folder_path}' to"
            f" '{oct(dst_permissions)}'"
        )
        os.chmod(dst_folder_path, dst_permissions)

    # Construct the new filename
    dst_file_path = get_trailer_path(
        src_path, dst_folder_path, media, profile, video_info=video_info
    )
    logger.debug(f"Moving trailer from '{src_path}' to '{dst_file_path}'")

    # Fixes https://github.com/nandyalu/trailarr/issues/285
    # Sometimes shutil.move fails when app only has write permissions without modify
    # The actual file will be moved but attributes won't be set in those cases
    try:
        # Move the file to destination
        shutil.move(src_path, dst_file_path)
        # Set the moved file's permissions to match the destination folder's permissions
        logger.debug(
            f"Setting permissions for file: '{dst_file_path}' to"
            f" '{oct(dst_permissions)}'"
        )
        os.chmod(dst_file_path, dst_permissions)
    except Exception as e:
        # Check if file is copied to destination
        if not os.path.exists(dst_file_path):
            # Try setting permissions on source file first and then normal copying
            os.chmod(src_path, dst_permissions)
            shutil.copyfile(src_path, dst_file_path)

        if not os.path.exists(dst_file_path):
            raise FileMoveFailedError(
                f"Failed to move trailer file to {dst_file_path}: {e}"
            )

    logger.debug(f"Trailer moved successfully to folder: '{dst_folder_path}'")
    return dst_file_path


def verify_download(
    file_path: str,
    title: str,
    profile: TrailerProfileRead,
) -> tuple[bool | None, VideoInfo | None]:
    """Verify if the trailer is downloaded successfully. \n
    Also checks if the trailer has audio and video streams. \n
    Args:
        file_path (str): Path of the trailer file to verify.
        title (str): Title of the media (for logging purposes).
        profile (TrailerProfileRead): Trailer Profile used to download. \n
    Returns:
        tuple[bool | None, VideoInfo | None]: Verification result and video info.
            - (True, VideoInfo): Valid trailer.
            - (False, None): Invalid trailer (missing streams, duration out of bounds).
            - (None, None): File missing or could not be analyzed.
    """
    if not file_path or not os.path.exists(file_path):
        return None, None

    # Verify and analyze the trailer in one pass
    is_valid, media_info = video_analysis.verify_and_analyze_trailer(
        file_path, profile.min_duration, profile.max_duration
    )

    if not is_valid:
        logger.debug(f"Trailer verification failed for: {title}")
        logger.debug(f"Deleting failed trailer file: {file_path}")
        try:
            os.remove(file_path)
        except Exception as e:
            logger.exception(f"Failed to delete trailer file: {e}")
        return is_valid, None

    return is_valid, media_info
