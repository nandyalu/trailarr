from datetime import datetime as dt
import os
from pathlib import Path
import re
import unicodedata
import zoneinfo
import aiofiles.os

from core.base.database.manager import trailerprofile
from core.base.database.models.filefolderinfo import (
    FileFolderInfoCreate,
    FileFolderType,
)


class MediaScanner:
    """Handles scanning of folders and files of media."""

    VIDEO_EXTENSIONS = tuple([".avi", ".mkv", ".mp4", ".webm"])

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

    def is_trailer_file(self, file_name: str) -> bool:
        """Check if a file is a trailer file based on its name,\
            OR if it's in a trailer folder.\n
        Args:
            file_name (str): Name of the file to check.\n
        Returns:
            bool: True if the file is a trailer, False otherwise."""
        if not file_name:
            return False
        # Ensure file is a video file
        if not file_name.lower().endswith(self.VIDEO_EXTENSIONS):
            return False
        # Ensure file is not an episode file
        if re.search(r"s\d{1,2}e\d{1,2}", file_name, re.IGNORECASE):
            return False
        # Check if the file name contains 'trailer'
        if "trailer" in file_name.lower():
            return True
        # Check if file is in a trailer folder
        folder_name = Path(file_name).parent.name.lower().strip()
        if folder_name and folder_name in self.trailer_folders:
            return True
        return False

    async def _get_file_info(
        self, entry: os.DirEntry[str], media_id: int
    ) -> FileFolderInfoCreate:
        is_trailer = self.is_trailer_file(entry.name)
        info = await aiofiles.os.stat(entry.path)
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
