"""Work out where a trailer file goes, and put it there.

The name and the folder come from the trailer profile. The file is written
to a temporary folder first and moved when it is complete, so a partial
download is never seen as a trailer.
"""

from pathlib import Path
import re
import shutil
import sys
import unicodedata
from app_logger import ModuleLogger
from config.settings import app_settings
from database.models.media import MediaRead
from database.models.trailerprofile import TrailerProfileRead
from database.models import video_type as video_types
from services.trailers import video_analysis
from services.trailers.video_analysis import VideoInfo
from exceptions import (
    FileMoveFailedError,
    FolderNotFoundError,
    FolderPathEmptyError,
)

logger = ModuleLogger("TrailersDownloader")

# Windows doesn't support Unix-style permissions
_IS_WINDOWS = sys.platform == "win32"


def get_folder_permissions(path: str | Path) -> int | None:
    """Get the permissions of the directory (if exists) \n
    Otherwise get it's parent directory permissions (that exists, recursively). \n
    On Windows, returns None since Unix permissions don't apply. \n
    Args:
        path (str | Path): Path of the directory. \n
    Returns:
        int | None: Permissions of the directory, or None on Windows."""
    if _IS_WINDOWS:
        return None
    path = Path(path)
    logger.debug(f"Getting permissions for folder: {path}")
    while not path.exists():
        path = path.parent
    parent_dir = path.parent
    _permissions = parent_dir.stat().st_mode
    logger.debug(f"Folder permissions: {oct(_permissions)}")
    return _permissions


def _create_media_folder(folder_path: str) -> bool:
    """Create a missing media folder via the files handler.

    Imported lazily: files_handler imports this module for
    get_folder_permissions, so a module-level import would be circular.
    """
    from services.files.files_handler import FilesHandler

    return FilesHandler.create_folder(folder_path)


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
    *,
    video_id: str = "",
) -> str:
    """Get the trailer filename based on app settings. \n
    Args:
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        ext (str): Extension of the trailer file.
        increment_index (int): Index to increment the trailer number.
        video_info (VideoInfo | None): Actual downloaded video info for
            accurate naming. Falls back to profile settings if None.
        video_id (str): The YouTube id of the video being downloaded, for
            the `{youtube_id}` token. Empty when it is not known. \n
    Returns:
        str: Trailer filename."""
    if increment_index == 1:
        logger.debug(
            f"Trailarr gets the file name of the"
            f" {video_types.video_type_label(profile.video_type).lower()} for"
            f" '{media.title}'."
        )
    # Get trailer file name format from settings
    title_format = profile.file_name
    if title_format.count("{") != title_format.count("}"):
        logger.error(
            "The title format is not valid. Trailarr uses the default file"
            " name format."
        )
        title_format = app_settings._DEFAULT_FILE_NAME
    # Convert media object to dictionary for formatting
    title_opts = media.model_dump()
    # Replace the media filename with the filename without extension
    title_opts["media_filename"] = Path(media.media_filename).stem
    title_opts["is_movie"] = "movie" if media.is_movie else "series"
    title_opts["youtube_id"] = video_id or ""
    # A missing TMDB or TVDB id writes nothing, not 'None'.
    for key in ("tmdb_id", "tvdb_id"):
        title_opts[key] = title_opts.get(key) or ""
    # The suffix that Plex and Jellyfin read for the type of the profile:
    # 'trailer', 'featurette', 'scene', ... (decision 6 of Phase 9).
    title_opts["video_type"] = video_types.file_suffix(profile.video_type)
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
            # A player reads the type from the end of the name, so the
            # index goes before a type suffix: `-trailer.{ext}`,
            # `-featurette.{ext}` or the `{video_type}` token.
            suffix = _type_suffix_at_end(title_format)
            if suffix:
                title_format = title_format.replace(
                    suffix, "{ii}" + suffix
                )
            # If title format does not end with a type suffix,
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


def _type_suffix_at_end(title_format: str) -> str | None:
    """The type suffix a file name template ends with, or None.

    Example: `-trailer.{ext}` for the default template, and
    `-{video_type}.{ext}` for a template that uses the token.
    """
    if title_format.endswith("-{video_type}.{ext}"):
        return "-{video_type}.{ext}"
    for suffix in set(video_types.FILE_SUFFIXES.values()):
        candidate = f"-{suffix}.{{ext}}"
        if title_format.endswith(candidate):
            return candidate
    return None


def get_trailer_path(
    src_path: str | Path,
    dst_folder_path: str | Path,
    media: MediaRead,
    profile: TrailerProfileRead,
    increment_index: int = 1,
    video_info: VideoInfo | None = None,
    *,
    video_id: str = "",
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
        src_path (str | Path): Source path of the trailer file.
        dst_folder_path (str | Path): Destination folder path.
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        increment_index (int): Index to increment the trailer number.
        video_info (VideoInfo | None): Actual downloaded video info.
        video_id (str): The YouTube id of the video, for the
            `{youtube_id}` token. Empty when it is not known. \n
    Returns:
        str: Destination path for the trailer file."""
    if increment_index == 1:
        logger.debug(
            f"Trailarr gets the path of the"
            f" {video_types.video_type_label(profile.video_type).lower()} for"
            f" '{media.title}'."
        )

    src_path = Path(src_path)
    dst_folder_path = Path(dst_folder_path)

    # Get extension from source path (without the dot)
    _ext = src_path.suffix.lstrip(".")

    # Format the title to get the new filename
    filename = get_trailer_filename(
        media, profile, _ext, increment_index, video_info, video_id=video_id
    )

    # Get the destination path
    dst_file_path = dst_folder_path / filename
    # If file exists in destination, increment the index, else return path
    if dst_file_path.exists():
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
            video_id=video_id,
        )
    logger.debug(
        f"The path of the"
        f" {video_types.video_type_label(profile.video_type).lower()}"
        f" is '{dst_file_path}'."
    )
    return str(dst_file_path)


def move_trailer_to_folder(
    src_path: str | Path,
    media: MediaRead,
    profile: TrailerProfileRead,
    video_info: VideoInfo | None = None,
    *,
    video_id: str = "",
) -> str:
    """Move the trailer file to the specified folder.
    Args:
        src_path (str | Path): Source path of the trailer file.
        media (MediaRead): MediaRead object.
        profile (TrailerProfileRead): Trailer Profile used to download.
        video_info (VideoInfo | None): Actual downloaded video info.
        video_id (str): The YouTube id of the video, for the
            `{youtube_id}` token. Empty when it is not known.
    Raises:
        FileNotFoundError: If the trailer file is not found at the source path.
        FolderPathEmptyError: If the media folder path is empty.
        FolderNotFoundError: If the media folder does not exist.
        Exception: Any other exceptions raised while moving file.
    Returns:
        str: Destination path if trailer is moved successfully."""
    src_path = Path(src_path)
    kind = video_types.video_type_label(profile.video_type).lower()
    logger.debug(
        f"Trailarr moves the {kind} to the media folder"
        f" '{media.folder_path}'."
    )
    # Move the trailer file to the specified folder
    if not src_path.exists():
        raise FileNotFoundError(
            f"Trailarr found no {kind} file at '{src_path}'."
        )

    # Get the destination path, create subfolder if enabled
    if profile.custom_folder == "{media_folder}":
        # If custom folder is set to media folder, use media folder path
        # Check if media folder path exists
        if not media.folder_path:
            raise FolderPathEmptyError(
                f"The media item '{media.title}' has no folder path."
            )
        media_folder = Path(media.folder_path)
        if not media_folder.exists():
            # The download gate creates the folder when the user enabled
            # that; this is the last line of defence for other callers.
            if not app_settings.create_missing_folders or not (
                _create_media_folder(media.folder_path)
            ):
                raise FolderNotFoundError(folder_path=media.folder_path)
        if profile.folder_enabled:
            folder_name = profile.folder_name.strip()
            if not folder_name:
                # The folder that both players read for the type of the
                # profile: 'Trailers', 'Featurettes', 'Scenes', ...
                folder_name = video_types.folder_name(profile.video_type)
                logger.debug(
                    "Folder name is empty, using default folder name:"
                    f" '{folder_name}'"
                )
            # The template token for the per-type folder name.
            folder_name = folder_name.replace(
                "{video_type}", video_types.folder_name(profile.video_type)
            )
            # Create a separate folder for trailers if enabled
            dst_folder_path = media_folder / folder_name
        else:
            # Else, move the trailer to the media folder
            dst_folder_path = media_folder
    else:
        # Format the custom folder path
        title_opts = media.model_dump()
        title_opts["media_folder"] = media.folder_path
        # Replace the media filename with the filename without extension
        title_opts["media_filename"] = Path(media.media_filename).stem
        title_opts["is_movie"] = "movie" if media.is_movie else "series"
        title_opts["youtube_id"] = video_id or ""
        # A missing TMDB or TVDB id writes nothing, not 'None'.
        for key in ("tmdb_id", "tvdb_id"):
            title_opts[key] = title_opts.get(key) or ""
        title_opts["video_type"] = video_types.folder_name(
            profile.video_type
        )
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
        dst_folder_path = Path(profile.custom_folder.format(**title_opts))

    # Get destination permissions
    dst_permissions = get_folder_permissions(dst_folder_path)

    # Check if destination exists, else create it
    if not dst_folder_path.exists():
        logger.debug(
            "Destination folder does not exist! Creating folder:"
            f" '{dst_folder_path}'"
        )
        if dst_permissions is not None:
            dst_folder_path.mkdir(parents=True, mode=dst_permissions)
            # Explicitly set the permissions for the folder
            logger.debug(
                f"Setting permissions for folder: '{dst_folder_path}' to"
                f" '{oct(dst_permissions)}'"
            )
            dst_folder_path.chmod(dst_permissions)
        else:
            dst_folder_path.mkdir(parents=True)

    # Construct the new filename
    dst_file_path = Path(
        get_trailer_path(
            src_path,
            dst_folder_path,
            media,
            profile,
            video_info=video_info,
            video_id=video_id,
        )
    )
    logger.debug(
        f"Trailarr moves the {kind} from '{src_path}' to"
        f" '{dst_file_path}'."
    )

    # The size of the download. A move to another file system is a copy,
    # and the copy must have the same size (#705).
    src_size = src_path.stat().st_size
    try:
        shutil.move(src_path, dst_file_path)
    except Exception as e:
        _recover_failed_move(
            src_path, dst_file_path, src_size, kind, e, media_id=media.id
        )

    dst_size = _file_size(dst_file_path)
    if dst_size != src_size:
        # An empty or short file is not a trailer. The download is still
        # in the temporary folder when the copy failed, so the retry of
        # the download task can try again.
        _remove_partial_file(dst_file_path, kind)
        raise FileMoveFailedError(
            f"Trailarr could not move the {kind} to '{dst_file_path}'. The"
            f" copy has {dst_size or 0} bytes, but the download has"
            f" {src_size} bytes."
        )
    # After a failed move, the download can still be in the temporary
    # folder. The copy is complete, so Trailarr removes it.
    src_path.unlink(missing_ok=True)

    # Give the file the permissions of the destination folder. Some
    # folders let the app write a file but not change it (#285). The file
    # is complete, so the move is a success.
    if dst_permissions is not None:
        logger.debug(
            f"Setting permissions for file: '{dst_file_path}' to"
            f" '{oct(dst_permissions)}'"
        )
        try:
            dst_file_path.chmod(dst_permissions)
        except OSError as e:
            logger.debug(
                f"Trailarr could not set the permissions of"
                f" '{dst_file_path}': {e}"
            )

    logger.debug(
        f"Trailarr moved the {kind} to the folder '{dst_folder_path}'."
    )
    return str(dst_file_path)


def _file_size(path: Path) -> int | None:
    """The size of the file in bytes, or None when Trailarr cannot read it."""
    try:
        return path.stat().st_size
    except OSError:
        return None


def _remove_partial_file(path: Path, kind: str) -> None:
    """Delete the file that a failed copy left. A failure is logged only:
    the caller raises the error of the move."""
    try:
        path.unlink(missing_ok=True)
    except OSError as e:
        logger.error(
            f"Trailarr could not delete the incomplete {kind} at"
            f" '{path}': {e}"
        )


def _recover_failed_move(
    src_path: Path,
    dst_file_path: Path,
    src_size: int,
    kind: str,
    error: Exception,
    *,
    media_id: int,
) -> None:
    """Continue after `shutil.move` raised.

    A move to another file system copies the file and then its attributes.
    When the folder does not let the app change the attributes, the move
    raises after a complete copy (#285). Then the file is in place.

    A copy that stopped before the end leaves an empty or short file
    (#705). Trailarr deletes it and copies the download one more time. The
    caller compares the sizes again.

    Args:
        src_path (Path): The download in the temporary folder.
        dst_file_path (Path): The new path of the trailer.
        src_size (int): The size of the download in bytes.
        kind (str): The video type, for the log lines.
        error (Exception): The error of the move.
        media_id (int): The media item, for the link of the log line.
    Raises:
        FileMoveFailedError: If the download is not in the temporary
            folder any more.
        Exception: Any error of the second copy. An OSError stays an
            OSError, so the caller can tell a full disk from other errors.
    """
    if _file_size(dst_file_path) == src_size:
        logger.debug(
            f"Trailarr copied the {kind} to '{dst_file_path}', but could"
            f" not copy the file attributes: {error}"
        )
        return
    logger.warning(
        f"Trailarr could not move the {kind} to '{dst_file_path}': {error}."
        " Trailarr copies it again.",
        **logger.media(media_id),
    )
    _remove_partial_file(dst_file_path, kind)
    if not src_path.exists():
        raise FileMoveFailedError(
            f"Trailarr could not move the {kind} to '{dst_file_path}'. The"
            f" download is not in the temporary folder: {error}"
        )
    try:
        shutil.copyfile(src_path, dst_file_path)
    except Exception:
        _remove_partial_file(dst_file_path, kind)
        raise


def verify_download(
    file_path: str | Path | None,
    title: str,
    profile: TrailerProfileRead,
) -> tuple[bool | None, VideoInfo | None]:
    """Verify if the trailer is downloaded successfully. \n
    Also checks if the trailer has audio and video streams. \n
    Args:
        file_path (str | Path | None): Path of the trailer file to verify.
        title (str): Title of the media (for logging purposes).
        profile (TrailerProfileRead): Trailer Profile used to download. \n
    Returns:
        tuple[bool | None, VideoInfo | None]: Verification result and video info.
            - (True, VideoInfo): Valid trailer.
            - (False, None): Invalid trailer (missing streams, duration out of bounds).
            - (None, None): File missing or could not be analyzed.
    """
    if not file_path:
        return None, None
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return None, None

    # Verify and analyze the trailer in one pass
    is_valid, media_info = video_analysis.verify_and_analyze_trailer(
        str(file_path_obj), profile.min_duration, profile.max_duration
    )

    if not is_valid:
        kind = video_types.video_type_label(profile.video_type).lower()
        logger.debug(f"The {kind} for '{title}' failed the checks.")
        logger.debug(
            f"Trailarr deletes the failed {kind} file '{file_path_obj}'."
        )
        try:
            file_path_obj.unlink()
        except Exception as e:
            logger.exception(
                f"Trailarr could not delete the {kind} file: {e}"
            )
        return is_valid, None

    return is_valid, media_info
