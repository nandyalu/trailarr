from pathlib import Path
import re
import shutil
import sys
import unicodedata

from app_logger import ModuleLogger
from config.settings import app_settings
from db.models.media import MediaRead
from db.models.trailerprofile import TrailerProfileRead
from download import analysis as video_analysis
from download.analysis import VideoInfo
from exceptions import FileMoveFailedError, FolderNotFoundError, FolderPathEmptyError

logger = ModuleLogger("TrailersDownloader")

_IS_WINDOWS = sys.platform == "win32"


def get_folder_permissions(path: str | Path) -> int | None:
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


def normalize_filename(filename: str) -> str:
    _filename = unicodedata.normalize("NFKD", filename)
    _filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', " ", _filename)
    _filename = re.sub(r"\s+", " ", _filename)
    _filename = _filename.strip("_.-")
    logger.debug(f"Normalized filename: '{filename}' -> '{_filename}'")
    return _filename


def _extract_video_details(video_info: VideoInfo) -> tuple[int, str, str]:
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
    if increment_index == 1:
        logger.debug(f"Getting trailer filename for '{media.title}'...")
    title_format = profile.file_name
    if title_format.count("{") != title_format.count("}"):
        logger.error("Invalid title format, setting to default file name format")
        title_format = app_settings._DEFAULT_FILE_NAME
    title_opts = media.model_dump()
    title_opts["media_filename"] = Path(media.media_filename).stem
    title_opts["is_movie"] = "movie" if media.is_movie else "series"
    title_opts["youtube_id"] = media.youtube_trailer_id
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
    title_opts["ii"] = increment_index
    if increment_index == 1:
        title_format = title_format.replace("{ii}", "")
    else:
        if "{ii}" not in title_format:
            if title_format.endswith("-trailer.{ext}"):
                title_format = title_format.replace("-trailer.{ext}", "{ii}-trailer.{ext}")
            else:
                title_format = title_format.replace(".{ext}", "{ii}.{ext}")
        title_format = title_format.replace("{ii}", "{ii: }")
    filename = title_format.format(**title_opts)
    filename = normalize_filename(filename)
    return filename


def get_trailer_path(
    src_path: str | Path,
    dst_folder_path: str | Path,
    media: MediaRead,
    profile: TrailerProfileRead,
    increment_index: int = 1,
    video_info: VideoInfo | None = None,
) -> str:
    if increment_index == 1:
        logger.debug(f"Getting trailer path for '{media.title}'...")
    src_path = Path(src_path)
    dst_folder_path = Path(dst_folder_path)
    _ext = src_path.suffix.lstrip(".")
    filename = get_trailer_filename(media, profile, _ext, increment_index, video_info)
    dst_file_path = dst_folder_path / filename
    if dst_file_path.exists():
        logger.debug(f"File already exists at: {dst_file_path}, incrementing index...")
        return get_trailer_path(src_path, dst_folder_path, media, profile, increment_index + 1, video_info)
    logger.debug(f"Trailer path: {dst_file_path}")
    return str(dst_file_path)


def move_trailer_to_folder(
    src_path: str | Path,
    media: MediaRead,
    profile: TrailerProfileRead,
    video_info: VideoInfo | None = None,
) -> str:
    src_path = Path(src_path)
    logger.debug(f"Moving trailer to media folder: '{media.folder_path}'")
    if not src_path.exists():
        raise FileNotFoundError(f"Trailer file not found at: {src_path}")

    if profile.custom_folder == "{media_folder}":
        if not media.folder_path:
            raise FolderPathEmptyError(f"Folder path is empty or not set for media: {media.title} [{media.id}]")
        media_folder = Path(media.folder_path)
        if not media_folder.exists():
            raise FolderNotFoundError(folder_path=media.folder_path)
        if profile.folder_enabled:
            folder_name = profile.folder_name.strip()
            if not folder_name:
                logger.debug("Folder name is empty, using default folder name: 'Trailers'")
                folder_name = "Trailers"
            dst_folder_path = media_folder / folder_name
        else:
            dst_folder_path = media_folder
    else:
        title_opts = media.model_dump()
        title_opts["media_folder"] = media.folder_path
        title_opts["media_filename"] = Path(media.media_filename).stem
        title_opts["is_movie"] = "movie" if media.is_movie else "series"
        title_opts["youtube_id"] = media.youtube_trailer_id
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

    dst_permissions = get_folder_permissions(dst_folder_path)
    if not dst_folder_path.exists():
        logger.debug(f"Destination folder does not exist! Creating folder: '{dst_folder_path}'")
        if dst_permissions is not None:
            dst_folder_path.mkdir(parents=True, mode=dst_permissions)
            dst_folder_path.chmod(dst_permissions)
        else:
            dst_folder_path.mkdir(parents=True)

    dst_file_path = Path(get_trailer_path(src_path, dst_folder_path, media, profile, video_info=video_info))
    logger.debug(f"Moving trailer from '{src_path}' to '{dst_file_path}'")
    try:
        shutil.move(src_path, dst_file_path)
        if dst_permissions is not None:
            dst_file_path.chmod(dst_permissions)
    except Exception as e:
        if not dst_file_path.exists():
            if dst_permissions is not None:
                src_path.chmod(dst_permissions)
            shutil.copyfile(src_path, dst_file_path)
        if not dst_file_path.exists():
            raise FileMoveFailedError(f"Failed to move trailer file to {dst_file_path}: {e}")

    logger.debug(f"Trailer moved successfully to folder: '{dst_folder_path}'")
    return str(dst_file_path)


def verify_download(
    file_path: str | Path | None,
    title: str,
    profile: TrailerProfileRead,
) -> tuple[bool | None, VideoInfo | None]:
    if not file_path:
        return None, None
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return None, None

    is_valid, media_info = video_analysis.verify_and_analyze_trailer(
        str(file_path_obj), profile.min_duration, profile.max_duration
    )
    if not is_valid:
        logger.debug(f"Trailer verification failed for: {title}")
        logger.debug(f"Deleting failed trailer file: {file_path_obj}")
        try:
            file_path_obj.unlink()
        except Exception as e:
            logger.exception(f"Failed to delete trailer file: {e}")
        return is_valid, None
    return is_valid, media_info
