from datetime import datetime as dt
import os
from pathlib import Path
import re
import unicodedata
import zoneinfo
import aiofiles.os

from app_logger import ModuleLogger
from core.base.database.manager import trailerprofile
from core.base.database.models.filefolderinfo import (
    FileFolderInfoCreate,
    FileFolderType,
)
from core.download import video_analysis

logger = ModuleLogger("MediaScanner")


class MediaScanner:
    """Handles scanning of folders and files of media."""

    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])
    # A video file >= this size is treated as a real media file, not a trailer.
    MEDIA_FILE_MIN_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
    # Files with 'trailer' in name below this size are trailers without needing ffprobe.
    TRAILER_QUICK_MAX_SIZE_BYTES = 200 * 1024 * 1024  # 200 MB
    # Matches the default max_duration in TrailerProfile — anything longer is not a trailer.
    TRAILER_MAX_DURATION_SECONDS = 600  # 10 minutes

    def __init__(self) -> None:

        self.tz = self._get_system_timezone()
        self.trailer_folders = self.get_trailer_folders()

    @staticmethod
    def _get_system_timezone() -> zoneinfo.ZoneInfo:
        """Get the system timezone from TZ environment variable or default to UTC."""
        tz_env = os.environ.get("TZ", "UTC")
        return zoneinfo.ZoneInfo(tz_env)

    @staticmethod
    def get_trailer_folders() -> set[str]:
        """Get a list of trailer folder names.\n
        Returns:
            set[str]: Set with trailer folder names."""
        # Get the trailer folders from the trailerprofile module
        trailer_folders = trailerprofile.get_trailer_folders()
        # Add 'trailer' and 'trailers' to the list
        trailer_folders.add("trailer")
        trailer_folders.add("trailers")
        trailer_folders = {
            folder.lower().strip() for folder in trailer_folders
        }
        return trailer_folders

    async def _check_large_name_trailer(self, file_path: str) -> bool:
        """Use ffprobe to verify a large inline file with 'trailer' in its name.

        Checks duration: anything over TRAILER_MAX_DURATION_SECONDS is a movie
        or TV episode, not a trailer.
        Args:
            file_path (str): The path of the file to check.
        Returns:
            bool: True if the file is a trailer, False if not.
        """
        media_info = video_analysis.get_media_info(file_path)
        if media_info is None:
            return False
        if media_info.duration_seconds <= 0:
            return False
        is_trailer = (
            media_info.duration_seconds <= self.TRAILER_MAX_DURATION_SECONDS
        )
        if not is_trailer:
            logger.debug(
                f"'{Path(file_path).name}' duration"
                f" {media_info.duration_seconds}s exceeds"
                f" {self.TRAILER_MAX_DURATION_SECONDS}s limit — not treated as"
                " trailer"
            )
        return is_trailer

    async def is_trailer_file(
        self, file_path: str, file_size_bytes: int | None = None
    ) -> bool:
        """Check if a file is a trailer based on its path and size. \n
        If the file is large but has `trailer` in its name,
        does a quick check with `ffprobe` to confirm.
        Args:
            file_path (str): The path of the file to check.
            file_size_bytes (int, Optional=None): The size of the file in bytes, if known.
                If None, size-based heuristics will be skipped.
        Returns:
            - `True` confirmed trailer (folder-based or small inline file).
            - `False` confirmed not a trailer.
        """
        if not file_path:
            return False
        # Ensure file is a video file before applying trailer heuristics.
        if not file_path.lower().endswith(self.VIDEO_EXTENSIONS):
            return False
        file_name = Path(file_path).name
        # Exclude files that look like TV episodes (e.g. "S01E01") to avoid false positives.
        if re.search(r"s\d{1,2}e\d{1,2}", file_name, re.IGNORECASE):
            return False
        # Folder placement is authoritative — no size limit applies.
        folder_name = Path(file_path).parent.name.lower().strip()
        if folder_name and folder_name in self.trailer_folders:
            return True
        # If 'trailer' is in the file name, it could be a trailer — but
        # if it's large, we can't be sure without ffprobe.
        if "trailer" not in file_name.lower():
            return False
        if (
            file_size_bytes is not None
            and file_size_bytes >= self.TRAILER_QUICK_MAX_SIZE_BYTES
        ):
            # Too large for a quick answer — caller must run ffprobe.
            return await self._check_large_name_trailer(file_path)
        return True

    async def _get_file_info(
        self, entry: os.DirEntry[str], media_id: int
    ) -> FileFolderInfoCreate:
        info = await aiofiles.os.stat(entry.path)
        is_trailer = await self.is_trailer_file(entry.path, info.st_size)
        return FileFolderInfoCreate(
            type=FileFolderType.FILE,
            name=unicodedata.normalize("NFKD", entry.name),
            size=info.st_size,
            path=entry.path,
            modified=dt.fromtimestamp(info.st_ctime, tz=self.tz),
            is_trailer=is_trailer,
            media_id=media_id,
        )

    async def get_folder_files(
        self, folder_path: str, media_id: int
    ) -> FileFolderInfoCreate | None:
        """Get information about all files and [sub]folders in a given \
            folder (recursively).\n
        Args:
            folder_path (str): Path of the folder to search.
        Returns:
            FolderInfo|None:
                - FolderInfo object representing files and folders \
                    inside a given folder.
                - None: If the folder is empty or does not exist."""
        _is_dir = await aiofiles.os.path.isdir(folder_path)
        if not _is_dir:
            return None
        # Scan the directory entries
        dir_info: list[FileFolderInfoCreate] = []
        for entry in await aiofiles.os.scandir(folder_path):
            if entry.is_file():
                dir_info.append(await self._get_file_info(entry, media_id))
            elif entry.is_dir():
                child_dir_info = await self.get_folder_files(
                    entry.path, media_id
                )
                if child_dir_info:
                    dir_info.append(child_dir_info)

        # Sort the list of files and folders by name, folders first and \
        # then files
        dir_info.sort(key=lambda x: x)
        # Calculate total size of the folder
        dir_size = sum(p.stat().st_size for p in Path(folder_path).rglob("*"))
        dir_path = Path(folder_path)
        # Build and return the FolderInfo object
        return FileFolderInfoCreate(
            type=FileFolderType.FOLDER,
            name=unicodedata.normalize("NFKD", dir_path.name),
            children=dir_info,
            size=dir_size,
            path=folder_path,
            modified=dt.fromtimestamp(dir_path.stat().st_ctime, tz=self.tz),
            media_id=media_id,
        )

    def _has_media_file(self, folder_info: FileFolderInfoCreate) -> bool:
        """Recursively check if any video file >= 100 MB exists in the tree."""
        for child in folder_info.children:
            if child.type == FileFolderType.FILE:
                if (
                    child.size >= self.MEDIA_FILE_MIN_SIZE_BYTES
                    and child.name.lower().endswith(self.VIDEO_EXTENSIONS)
                ):
                    return True
            elif child.type == FileFolderType.FOLDER:
                if self._has_media_file(child):
                    return True
        return False

    async def check_media_exists(
        self,
        folder_info: FileFolderInfoCreate | None,
        folder_path: str = "",
        media_id: int = 0,
    ) -> bool:
        """Check if a media file (video >= 100 MB) exists in the folder tree.

        Uses pre-fetched folder_info to avoid a second disk scan. If
        folder_info is None and folder_path is provided, scans the folder
        first via get_folder_files.
        """
        if folder_info is None:
            if not folder_path:
                return False
            folder_info = await self.get_folder_files(folder_path, media_id)
            if folder_info is None:
                return False
        return self._has_media_file(folder_info)

    def get_trailer_paths(self, folder_info: FileFolderInfoCreate) -> set[str]:
        """Get a list of trailer file paths from the given FolderInfo object.\n
        Args:
            folder_info (FolderInfo): The FolderInfo object to scan.\n
        Returns:
            set[str]: Set of trailer file paths found in the folder."""
        trailer_paths: set[str] = set()

        def _scan_folder(info: FileFolderInfoCreate) -> None:
            for child in info.children:
                if child.type == FileFolderType.FILE and child.is_trailer:
                    trailer_paths.add(child.path)
                elif child.type == FileFolderType.FOLDER:
                    _scan_folder(child)

        _scan_folder(folder_info)
        return trailer_paths
