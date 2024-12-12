import os
import re
import shutil
import unicodedata
from app_logger import ModuleLogger
from config.settings import app_settings
from core.base.database.models.helpers import MediaTrailer
from core.download import video_analysis

logger = ModuleLogger("TrailersDownloader")


def trailer_folder_needed(is_movie: bool) -> bool:
    """Check if trailer folder is needed based on app settings. \n
    Args:
        is_movie (bool): Whether the media type is movie or show. \n
    Returns:
        bool: True if trailer folder is needed, False otherwise."""
    if is_movie:
        if app_settings.trailer_folder_movie:
            return True
    else:
        if app_settings.trailer_folder_series:
            return True
    return False


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
    logger.debug(f"Normalizing filename: {filename}")
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
    logger.debug(f"Normalized filename: {filename}")
    return filename


def get_trailer_filename(media: MediaTrailer, ext: str, increment_index: int) -> str:
    """Get the trailer filename based on app settings. \n
    Args:
        media (MediaTrailer): MediaTrailer object.
        ext (str): Extension of the trailer file.
        increment_index (int): Index to increment the trailer number. \n
    Returns:
        str: Trailer filename."""
    logger.debug(f"Getting trailer filename for '{media.title}'...")
    # Get trailer file name format from settings
    title_format = app_settings.trailer_file_name
    if title_format.count("{") != title_format.count("}"):
        logger.error("Invalid title format, setting to default file name format")
        title_format = app_settings._DEFAULT_FILE_NAME
    title_opts = media.to_dict()  # Convert media object to dictionary for formatting
    title_opts["resolution"] = f"{app_settings.trailer_resolution}p"
    title_opts["vcodec"] = app_settings.trailer_video_format
    title_opts["acodec"] = app_settings.trailer_audio_format
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
    logger.debug(f"Getting trailer path for '{media.title}'...")

    # Get filename from source path and extract extension
    filename = os.path.basename(src_path)
    _ext = os.path.splitext(filename)[1]
    _ext = _ext.replace(".", "")

    # Format the title to get the new filename
    filename = get_trailer_filename(media, _ext, increment_index)

    # Get the destination path
    dst_file_path = os.path.join(dst_folder_path, filename)
    # If file exists in destination, increment the index, else return path
    if os.path.exists(dst_file_path):
        logger.debug(f"File already exists at: {dst_file_path}, incrementing index...")
        return get_trailer_path(src_path, dst_folder_path, media, increment_index + 1)
    logger.debug(f"Trailer path: {dst_file_path}")
    return dst_file_path


def move_trailer_to_folder(
    src_path: str, media: MediaTrailer, trailer_folder: bool | None = None
) -> bool:
    """Move the trailer file to the specified folder. \n
    Args:
        src_path (str): Source path of the trailer file.
        media (MediaTitle): MediaTitle object.
        trailer_folder (bool, Optional=None): Whether to move the trailer to a separate folder. \n
    Raises:
        FileNotFoundError: If the trailer file is not found at the source path.
        Exception: Any other exceptions raised while moving file.\n
    Returns:
        bool: True if trailer is moved successfully, False otherwise."""
    logger.debug(f"Moving trailer to media folder: '{media.folder_path}'")
    # Move the trailer file to the specified folder
    if not os.path.exists(src_path):
        logger.debug(f"Trailer file not found at: {src_path}")
        raise FileNotFoundError(f"Trailer file not found at: {src_path}")
    # Get the destination path
    if trailer_folder is None:
        # Check if trailer folder is needed based on app settings
        trailer_folder = trailer_folder_needed(media.is_movie)
    if trailer_folder:
        # Create a separate folder for trailers if enabled
        dst_folder_path = os.path.join(media.folder_path, "Trailers")
    else:
        # Else, move the trailer to the media folder
        dst_folder_path = media.folder_path
    # Get destination permissions
    dst_permissions = get_folder_permissions(dst_folder_path)

    # Check if destination exists, else create it
    if not os.path.exists(dst_folder_path):
        logger.debug(f"Destination folder does not exist! Creating folder: '{dst_folder_path}'")
        os.makedirs(dst_folder_path, mode=dst_permissions)
        # Explicitly set the permissions for the folder
        logger.debug(
            f"Setting permissions for folder: '{dst_folder_path}' to '{oct(dst_permissions)}'"
        )
        os.chmod(dst_folder_path, dst_permissions)

    # Construct the new filename and move the file
    dst_file_path = get_trailer_path(src_path, dst_folder_path, media)
    logger.debug(f"Moving trailer from '{src_path}' to '{dst_file_path}'")
    shutil.move(src_path, dst_file_path)

    # Set the moved file's permissions to match the destination folder's permissions
    logger.debug(f"Setting permissions for file: '{dst_file_path}' to '{oct(dst_permissions)}'")
    os.chmod(dst_file_path, dst_permissions)
    logger.debug(f"Trailer moved successfully to folder: '{dst_folder_path}'")
    return True


def verify_download(tmp_output_file: str, output_file: str, title: str) -> bool:
    """Verify if the trailer is downloaded successfully. \n
    Also checks if the trailer has audio and video streams. \n
    Args:
        tmp_output_file (str): Temporary output file path.
        output_file (str): Output file path.
        title (str): Title of the media. \n
    Returns:
        bool: True if trailer is downloaded successfully, False otherwise."""
    # Check if the trailer is downloaded successfully
    if not output_file or not os.path.exists(tmp_output_file):
        trailer_downloaded = False
    else:
        # Verify the trailer has audio and video streams
        trailer_downloaded = video_analysis.verify_trailer_streams(output_file)
        if not trailer_downloaded:
            logger.debug(
                f"Trailer has either no audio or video streams: {title}"
            )
            logger.debug(f"Deleting failed trailer file: {output_file}")
            try:
                os.remove(output_file)
            except Exception as e:
                logger.error(f"Failed to delete trailer file: {e}")
    return trailer_downloaded