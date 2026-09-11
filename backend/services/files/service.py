"""Reading, renaming and deleting files for the API.

The handlers in `api/v1/files.py` decide which HTTP status a refusal gets.
This module holds what that decision is based on — the path and file-type
checks — and the work itself.

`is_path_safe` guards every path that arrives from a request. Keep it that
way: these endpoints take a path from the caller and open it.
"""

import os
from pathlib import PurePath

import database.manager.download as download_manager
from services.files.files_handler import FilesHandler
from services.trailers.trailers.service import rename_trailer_download

CHUNK_SIZE = 1024 * 1024 * 5  # 5 MB

# System folders that a request path must never point into. These are the
# Linux ones. Windows keeps its system folders under a drive letter, which
# is not fixed, so those are matched by name in UNSAFE_WINDOWS_ROOT_NAMES.
UNSAFE_PATHS = [
    "/app",
    "/bin",
    "/boot",
    "/etc",
    "/lib",
    "/sbin",
    "/usr",
    "/var",
]

# Folder names directly under a Windows drive that hold the system.
UNSAFE_WINDOWS_ROOT_NAMES = frozenset(
    {"windows", "program files", "program files (x86)", "programdata"}
)

# The shortest path a media file can have: a root, a folder, and the file.
MIN_PATH_PARTS = 4

VALID_VIDEO_EXTENSIONS = (".mkv", ".mp4", ".avi", ".webm")
VALID_TEXT_EXTENSIONS = (".txt", ".srt", ".log", ".json", ".py", ".sh")


def is_path_safe(path: str) -> bool:
    """Check if the path is safe.\n
    Args:
        path (str): Path to check.
    Returns:
        bool: True if the path is safe, False otherwise.

    TODO (hygiene H13): this is still a denylist of system folders. An
    allowlist built from the connection root folders would be stronger,
    because Trailarr already knows where its media lives. Do not extend the
    list below — replace the approach. See plans/hygiene-backlog.md."""
    if not path:
        return False
    # normpath resolves any '..' in the path before it is checked
    pure_path = PurePath(os.path.normpath(path))
    # A relative path would be resolved against the working directory, which
    # the caller does not choose. Refuse it instead of guessing.
    if not pure_path.is_absolute():
        return False
    # Compare whole folder names. A plain string prefix would also refuse a
    # real library at /variable/media, for starting with '/var'.
    for unsafe_path in UNSAFE_PATHS:
        unsafe = PurePath(unsafe_path)
        if pure_path == unsafe or unsafe in pure_path.parents:
            return False
    # On Windows the system folders sit under a drive letter
    if (
        len(pure_path.parts) > 1
        and pure_path.parts[1].lower() in UNSAFE_WINDOWS_ROOT_NAMES
    ):
        return False
    # Check the path is deep enough. Count folders, not '/' characters:
    # a Windows path is separated by backslashes and has no '/' at all.
    if len(pure_path.parts) < MIN_PATH_PARTS:
        return False
    return True


def is_video_file(file_path: str) -> bool:
    """Check the extension against the video types the player accepts."""
    return file_path.endswith(VALID_VIDEO_EXTENSIONS)


def is_readable_text_file(file_path: str) -> bool:
    """Check the extension against the text types the reader accepts."""
    return os.path.splitext(file_path)[1] in VALID_TEXT_EXTENSIONS


def read_text_file(file_path: str) -> str:
    """Read a text file and remove the whitespace at both ends."""
    with open(file_path, "r") as file:
        return file.read().strip()


def read_video_chunk(
    file_path: str, range_header: str
) -> tuple[bytes, dict[str, str]]:
    """Read one byte range of a video file.

    A range with no end reads CHUNK_SIZE bytes. An end past the file reads
    to the end of the file.

    Args:
        file_path (str): The video file to read.
        range_header (str): The Range header, such as "bytes=0-".

    Returns:
        tuple[bytes, dict[str, str]]: The bytes read, and the headers that
        describe which part of the file they are.
    """
    start, end = range_header.replace("bytes=", "").split("-")
    filesize = os.path.getsize(file_path)
    start = int(start)
    end = int(end) if end else start + CHUNK_SIZE
    if end > filesize:
        end = filesize
    with open(file_path, "rb") as video:
        video.seek(start)
        data = video.read(end - start)
    headers = {
        "Content-Range": f"bytes {str(start)}-{str(end - 1)}/{filesize}",
        "Accept-Ranges": "bytes",
    }
    return data, headers


async def rename_file_or_folder(
    old_path: str, new_path: str, media_id: int = -1
) -> bool:
    """Rename a file or folder, and follow it in the database.

    When the renamed file is a trailer of the given media, the download row
    for it moves to the new path too. Nothing is written to the database if
    the rename itself fails.

    Args:
        old_path (str): The path now.
        new_path (str): The path to give it.
        media_id (int): The media that owns the file, or -1 to skip the
            database update.

    Returns:
        bool: True when the rename succeeded.
    """
    renamed_status = await FilesHandler.rename_file_fol(old_path, new_path)
    if media_id != -1 and renamed_status:
        all_downloads = download_manager.read_by_media_id(media_id)
        matching_download = next(
            (d for d in all_downloads if d.path == old_path), None
        )
        if matching_download:
            await rename_trailer_download(matching_download, new_path)
    return renamed_status


async def delete_file_or_folder(path: str, media_id: int = -1) -> bool:
    """Delete a file or folder, and follow it in the database.

    A download row that points at the deleted path is marked deleted.
    Nothing is written to the database if the delete itself fails.

    Args:
        path (str): The file or folder to delete.
        media_id (int): The media that owns the file, or -1 to skip the
            database update.

    Returns:
        bool: True when the delete succeeded.
    """
    deleted_status = await FilesHandler.delete_file_fol(path)
    if media_id != -1 and deleted_status:
        all_downloads = download_manager.read_by_media_id(media_id)
        for d in all_downloads:
            if d.path == path:
                download_manager.mark_as_deleted(d.id)
    return deleted_status
